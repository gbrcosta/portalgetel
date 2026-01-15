// Configuração da API
const API_URL = `http://${window.location.hostname}:8000/api`;
const REFRESH_INTERVAL = 3000; // 3 segundos

// Estado da aplicação
let isConnected = false;
let currentView = 'dashboard';
let filteredSessions = [];
let lastRejectedReadingId = 0; // Para rastrear novas leituras rejeitadas

// Funções de Notificação
function showNotification(title, message, type = 'info') {
    const container = document.getElementById('notificationContainer');
    
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    
    const iconMap = {
        error: '🚫',
        warning: '⚠️',
        success: '✅',
        info: 'ℹ️'
    };
    
    notification.innerHTML = `
        <div class="notification-icon">${iconMap[type] || iconMap.info}</div>
        <div class="notification-content">
            <div class="notification-title">${title}</div>
            <div class="notification-message">${message}</div>
        </div>
        <button class="notification-close" onclick="this.parentElement.remove()">×</button>
    `;
    
    container.appendChild(notification);
    
    // Auto remover após 8 segundos
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-in';
        setTimeout(() => notification.remove(), 300);
    }, 8000);
}

// Navegação entre views
function switchView(viewName) {
    // Atualizar botões de navegação
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.view === viewName) {
            btn.classList.add('active');
        }
    });
    
    // Atualizar views
    document.querySelectorAll('.view-container').forEach(view => {
        view.classList.remove('active');
    });
    document.getElementById(`${viewName}-view`).classList.add('active');
    
    currentView = viewName;
    
    // Carregar dados da view
    if (viewName === 'dashboard') {
        refreshDashboard();
    } else if (viewName === 'auditoria') {
        loadAuditData();
    }
}

// Funções utilitárias
function formatDateTime(dateString) {
    if (!dateString) return '--:--:--';
    const date = new Date(dateString);
    return date.toLocaleString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

function formatTime(dateString) {
    if (!dateString) return '--:--:--';
    const date = new Date(dateString);
    return date.toLocaleTimeString('pt-BR');
}

function formatDuration(seconds) {
    if (!seconds) return '--';
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
        return `${hours}h ${minutes}m ${secs}s`;
    } else if (minutes > 0) {
        return `${minutes}m ${secs}s`;
    } else {
        return `${secs}s`;
    }
}

function calculateElapsedTime(startTime) {
    const start = new Date(startTime);
    const now = new Date();
    const diffSeconds = Math.floor((now - start) / 1000);
    return formatDuration(diffSeconds);
}

// Atualizar status da API
function updateAPIStatus(online) {
    const statusElement = document.getElementById('apiStatus');
    if (online) {
        statusElement.textContent = 'Online';
        statusElement.className = 'status-indicator online';
        isConnected = true;
    } else {
        statusElement.textContent = 'Offline';
        statusElement.className = 'status-indicator offline';
        isConnected = false;
    }
}

// Atualizar timestamp da última atualização
function updateLastUpdateTime() {
    const now = new Date();
    document.getElementById('lastUpdate').textContent = now.toLocaleTimeString('pt-BR');
}

// Buscar estatísticas do dashboard
async function fetchDashboardStats() {
    try {
        console.log('📊 Buscando estatísticas do dashboard...');
        const response = await fetch(`${API_URL}/stats`);
        if (!response.ok) throw new Error('Erro ao buscar estatísticas');
        
        const stats = await response.json();
        console.log('📊 Estatísticas recebidas:', stats);
        
        // Atualizar cards principais
        document.getElementById('activeSessions').textContent = stats.active_sessions;
        document.getElementById('completedToday').textContent = stats.completed_today;
        document.getElementById('totalCompleted').textContent = stats.total_completed;
        
        // Atualizar tempos médios
        document.getElementById('avgDuration').textContent = formatDuration(stats.average_duration);
        document.getElementById('avgDurationToday').textContent = formatDuration(stats.average_duration_today);
        
        console.log('✅ Dashboard atualizado com sucesso!');
        updateAPIStatus(true);
    } catch (error) {
        console.error('❌ Erro ao buscar estatísticas:', error);
        updateAPIStatus(false);
    }
}

// Buscar sessões ativas
async function fetchActiveSessions() {
    try {
        const response = await fetch(`${API_URL}/sessions/active`);
        if (!response.ok) throw new Error('Erro ao buscar sessões ativas');
        
        const sessions = await response.json();
        const container = document.getElementById('activeSessions-list');
        
        if (sessions.length === 0) {
            container.innerHTML = '<p class="empty-state">Nenhuma sessão ativa no momento</p>';
        } else {
            container.innerHTML = sessions.map(session => {
                const elapsedTime = calculateElapsedTime(session.antenna_1_time);
                return `
                    <div class="session-item">
                        <div class="session-tag">🏷️ ${session.tag_id}</div>
                        <div class="session-info">
                            <div class="session-time">
                                <strong>Início:</strong> ${formatTime(session.antenna_1_time)}
                            </div>
                        </div>
                        <div class="session-duration">${elapsedTime}</div>
                    </div>
                `;
            }).join('');
        }
    } catch (error) {
        console.error('Erro ao buscar sessões ativas:', error);
    }
}

// Buscar histórico de sessões
async function fetchSessionsHistory() {
    try {
        const response = await fetch(`${API_URL}/sessions?limit=50`);
        if (!response.ok) throw new Error('Erro ao buscar histórico');
        
        const sessions = await response.json();
        const tbody = document.getElementById('sessionsTableBody');
        
        if (sessions.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="empty-state">Nenhuma sessão registrada</td></tr>';
        } else {
            tbody.innerHTML = sessions.map(session => `
                <tr>
                    <td><strong>${session.tag_id}</strong></td>
                    <td>${formatDateTime(session.antenna_1_time)}</td>
                    <td>${formatDateTime(session.antenna_2_time)}</td>
                    <td><strong>${formatDuration(session.duration_seconds)}</strong></td>
                    <td>
                        <span class="status-badge status-${session.status}">
                            ${session.status === 'em_producao' ? '⚡ Em Produção' : '✅ Finalizado'}
                        </span>
                    </td>
                </tr>
            `).join('');
        }
    } catch (error) {
        console.error('Erro ao buscar histórico de sessões:', error);
    }
}

// Buscar eventos recentes
async function fetchRecentEvents() {
    try {
        const response = await fetch(`${API_URL}/events/recent?limit=20`);
        if (!response.ok) throw new Error('Erro ao buscar eventos');
        
        const events = await response.json();
        const container = document.getElementById('recentEvents');
        
        if (events.length === 0) {
            container.innerHTML = '<p class="empty-state">Nenhum evento registrado</p>';
        } else {
            container.innerHTML = events.map(event => `
                <div class="event-item antenna-${event.antenna_number}">
                    <div class="event-info">
                        <span class="event-tag">${event.tag_id}</span>
                        <span class="event-antenna antenna-${event.antenna_number}-badge">
                            Antena ${event.antenna_number} ${event.antenna_number === 1 ? '(Entrada)' : '(Saída)'}
                        </span>
                    </div>
                    <span class="event-time">${formatTime(event.event_time)}</span>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('Erro ao buscar eventos recentes:', error);
    }
}

// Monitorar leituras rejeitadas (etiquetas bloqueadas)
async function checkRejectedReadings() {
    try {
        const response = await fetch(`${API_URL}/rejected/recent?limit=10`);
        if (!response.ok) return;
        
        const rejected = await response.json();
        
        // Verificar se há novas leituras rejeitadas
        if (rejected.length > 0 && rejected[0].id > lastRejectedReadingId) {
            const newRejections = rejected.filter(r => r.id > lastRejectedReadingId);
            
            newRejections.forEach(rejection => {
                // Notificar apenas erros de validação (não tags já produzidas)
                if (rejection.reason_type === 'validation') {
                    showNotification(
                        '⚠️ VALIDAÇÃO FALHOU',
                        `Tag ${rejection.tag_id}: ${rejection.reason}`,
                        'warning'
                    );
                }
                // Tipo 'blocked' (etiquetas já produzidas) não gera notificação
            });
            
            lastRejectedReadingId = rejected[0].id;
        }
    } catch (error) {
        console.log('Erro ao verificar leituras rejeitadas:', error);
    }
}

// Atualizar todos os dados do Dashboard
async function refreshDashboard() {
    await Promise.all([
        fetchDashboardStats(),
        fetchActiveSessions(),
        checkRejectedReadings()
    ]);
    updateLastUpdateTime();
}

// Carregar dados da Auditoria
async function loadAuditData() {
    await Promise.all([
        fetchAuditSessions(),
        fetchAuditEvents(),
        fetchRejectedReadings()
    ]);
    updateLastUpdateTime();
}

// Buscar leituras rejeitadas para auditoria
async function fetchRejectedReadings() {
    try {
        const response = await fetch(`${API_URL}/rejected/recent?limit=100`);
        if (!response.ok) throw new Error('Erro ao buscar leituras rejeitadas');
        
        const rejected = await response.json();
        const tbody = document.getElementById('rejectedTableBody');
        
        if (rejected.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="empty-state">Nenhuma leitura rejeitada</td></tr>';
        } else {
            tbody.innerHTML = rejected.map(r => {
                const typeMap = {
                    'blocked': '🚫 Bloqueado',
                    'validation': '⚠️ Validação',
                    'timeout': '⏱️ Timeout'
                };
                
                return `
                    <tr>
                        <td><strong>${r.tag_id}</strong></td>
                        <td>Antena ${r.antenna_number || 'N/A'}</td>
                        <td>${formatDateTime(r.event_time)}</td>
                        <td>${r.reason}</td>
                        <td><span class="status-badge status-em_producao">${typeMap[r.reason_type] || r.reason_type}</span></td>
                    </tr>
                `;
            }).join('');
        }
    } catch (error) {
        console.error('Erro ao buscar leituras rejeitadas:', error);
    }
}


// Buscar sessões para auditoria
async function fetchAuditSessions(filters = {}) {
    try {
        let url = `${API_URL}/sessions?limit=500`;
        
        const response = await fetch(url);
        if (!response.ok) throw new Error('Erro ao buscar sessões');
        
        let sessions = await response.json();
        
        // Aplicar filtros localmente
        sessions = applyLocalFilters(sessions, filters);
        filteredSessions = sessions;
        
        // Atualizar tabela
        const tbody = document.getElementById('auditTableBody');
        
        if (sessions.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="empty-state">Nenhum registro encontrado</td></tr>';
        } else {
            tbody.innerHTML = sessions.map(session => `
                <tr>
                    <td><strong>#${session.id}</strong></td>
                    <td><strong>${session.tag_id}</strong></td>
                    <td>${formatDateTime(session.antenna_1_time)}</td>
                    <td>${formatDateTime(session.antenna_2_time)}</td>
                    <td><strong>${formatDuration(session.duration_seconds)}</strong></td>
                    <td>
                        <span class="status-badge status-${session.status}">
                            ${session.status === 'em_producao' ? '⚡ Em Produção' : '✅ Finalizado'}
                        </span>
                    </td>
                </tr>
            `).join('');
        }
        
        // Atualizar resumo
        updateAuditSummary(sessions);
        
    } catch (error) {
        console.error('Erro ao buscar sessões de auditoria:', error);
    }
}

// Aplicar filtros locais
function applyLocalFilters(sessions, filters) {
    let filtered = [...sessions];
    
    // Filtro de data início
    if (filters.startDate) {
        const startDate = new Date(filters.startDate);
        filtered = filtered.filter(s => {
            const sessionDate = new Date(s.created_at);
            return sessionDate >= startDate;
        });
    }
    
    // Filtro de data fim
    if (filters.endDate) {
        const endDate = new Date(filters.endDate);
        endDate.setHours(23, 59, 59, 999);
        filtered = filtered.filter(s => {
            const sessionDate = new Date(s.created_at);
            return sessionDate <= endDate;
        });
    }
    
    // Filtro de tag
    if (filters.tagId && filters.tagId.trim() !== '') {
        filtered = filtered.filter(s => 
            s.tag_id.toLowerCase().includes(filters.tagId.toLowerCase())
        );
    }
    
    // Filtro de status
    if (filters.status && filters.status !== '') {
        filtered = filtered.filter(s => s.status === filters.status);
    }
    
    return filtered;
}

// Atualizar resumo da auditoria
function updateAuditSummary(sessions) {
    document.getElementById('summaryTotal').textContent = sessions.length;
    
    const finalized = sessions.filter(s => s.status === 'finalizado').length;
    document.getElementById('summaryFinalized').textContent = finalized;
    
    const durations = sessions
        .filter(s => s.duration_seconds)
        .map(s => s.duration_seconds);
    
    const avgTime = durations.length > 0 
        ? durations.reduce((a, b) => a + b, 0) / durations.length 
        : 0;
    
    document.getElementById('summaryAvgTime').textContent = formatDuration(avgTime);
}

// Buscar eventos para auditoria
async function fetchAuditEvents() {
    try {
        // Buscar eventos aceitos
        const eventsResponse = await fetch(`${API_URL}/events/recent?limit=100`);
        if (!eventsResponse.ok) throw new Error('Erro ao buscar eventos');
        const events = await eventsResponse.json();
        
        // Buscar leituras rejeitadas
        const rejectedResponse = await fetch(`${API_URL}/rejected/recent?limit=100`);
        const rejected = rejectedResponse.ok ? await rejectedResponse.json() : [];
        
        const container = document.getElementById('auditEvents');
        
        // Combinar e ordenar por data
        const allEvents = [
            ...events.map(e => ({...e, type: 'accepted'})),
            ...rejected.map(r => ({...r, type: 'rejected'}))
        ].sort((a, b) => new Date(b.event_time) - new Date(a.event_time)).slice(0, 50);
        
        if (allEvents.length === 0) {
            container.innerHTML = '<p class="empty-state">Nenhum evento no período</p>';
        } else {
            container.innerHTML = allEvents.map(event => {
                if (event.type === 'rejected') {
                    // Evento rejeitado
                    return `
                        <div class="event-item rejected-event">
                            <div class="event-info">
                                <span class="event-tag">❌ ${event.tag_id}</span>
                                <span class="event-antenna rejected-badge">
                                    ${event.antenna_number !== null ? `Antena ${event.antenna_number}` : 'N/A'} - REJEITADO
                                </span>
                                <span class="event-reason">${event.reason}</span>
                            </div>
                            <span class="event-time">${formatTime(event.event_time)}</span>
                        </div>
                    `;
                } else {
                    // Evento aceito
                    const ant = event.antenna_number;
                    const antText = ant === 1 ? 'Entrada' : ant === 2 ? 'Saída' : `Ant ${ant}`;
                    return `
                        <div class="event-item antenna-${ant}">
                            <div class="event-info">
                                <span class="event-tag">${event.tag_id}</span>
                                <span class="event-antenna antenna-${ant}-badge">
                                    Antena ${ant} (${antText})
                                </span>
                            </div>
                            <span class="event-time">${formatDateTime(event.event_time)}</span>
                        </div>
                    `;
                }
            }).join('');
        }
    } catch (error) {
        console.error('Erro ao buscar eventos de auditoria:', error);
    }
}

// Aplicar filtros
function applyFilters() {
    const filters = {
        startDate: document.getElementById('filterStartDate').value,
        endDate: document.getElementById('filterEndDate').value,
        tagId: document.getElementById('filterTag').value,
        status: document.getElementById('filterStatus').value
    };
    
    fetchAuditSessions(filters);
}

// Limpar filtros
function clearFilters() {
    document.getElementById('filterStartDate').value = '';
    document.getElementById('filterEndDate').value = '';
    document.getElementById('filterTag').value = '';
    document.getElementById('filterStatus').value = '';
    
    fetchAuditSessions();
}

// Exportar dados para CSV
function exportData() {
    if (filteredSessions.length === 0) {
        alert('Nenhum dado para exportar');
        return;
    }
    
    // Criar CSV
    let csv = 'ID,Tag ID,Entrada (Antena 1),Saída (Antena 2),Tempo de Produção (s),Status\n';
    
    filteredSessions.forEach(session => {
        csv += `${session.id},`;
        csv += `${session.tag_id},`;
        csv += `${session.antenna_1_time || ''},`;
        csv += `${session.antenna_2_time || ''},`;
        csv += `${session.duration_seconds || ''},`;
        csv += `${session.status}\n`;
    });
    
    // Download do arquivo
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `auditoria-rfid-${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}

// Atualizar todos os dados
async function refreshAllData() {
    if (currentView === 'dashboard') {
        await refreshDashboard();
    } else if (currentView === 'auditoria') {
        // Não atualiza automaticamente na auditoria para não perder filtros
    }
}

// Verificar status da API
async function checkAPIStatus() {
    try {
        const response = await fetch(`${API_URL.replace('/api', '/')}`);
        if (response.ok) {
            updateAPIStatus(true);
            if (!isConnected) {
                // Reconectou, atualizar todos os dados
                refreshAllData();
            }
        }
    } catch (error) {
        updateAPIStatus(false);
    }
}

// Inicializar aplicação
async function init() {
    console.log('Iniciando Portal RFID Dashboard...');
    
    // Configurar navegação
    document.querySelectorAll('.nav-btn').forEach(btn => {
        if (btn.dataset.view) {
            btn.addEventListener('click', () => switchView(btn.dataset.view));
        }
    });
    
    // Configurar data padrão de hoje nos filtros
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('filterStartDate').value = today;
    document.getElementById('filterEndDate').value = today;
    
    // Configurar tecla Enter no modal de senha
    document.getElementById('passwordInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            validatePassword();
        }
    });
    
    // Primeira carga de dados
    await refreshDashboard();
    
    // Configurar atualização automática (apenas dashboard)
    setInterval(() => {
        if (currentView === 'dashboard') {
            refreshAllData();
        }
    }, REFRESH_INTERVAL);
    
    // Verificar status da API periodicamente
    setInterval(checkAPIStatus, 5000);
    
    console.log('Dashboard inicializado com sucesso!');
}

// ==================== MODAL DE SENHA ====================

function showPasswordModal() {
    const modal = document.getElementById('passwordModal');
    modal.classList.add('show');
    document.getElementById('passwordInput').value = '';
    document.getElementById('passwordError').textContent = '';
    // Focar no input após um pequeno delay para garantir que o modal está visível
    setTimeout(() => document.getElementById('passwordInput').focus(), 100);
}

function closePasswordModal() {
    const modal = document.getElementById('passwordModal');
    modal.classList.remove('show');
    document.getElementById('passwordInput').value = '';
    document.getElementById('passwordError').textContent = '';
}

function validatePassword() {
    const input = document.getElementById('passwordInput').value;
    const errorDiv = document.getElementById('passwordError');
    
    // Gerar senha do dia (formato: ddmmaaaa)
    const today = new Date();
    const day = String(today.getDate()).padStart(2, '0');
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const year = String(today.getFullYear());
    const correctPassword = day + month + year;
    
    if (input === correctPassword) {
        closePasswordModal();
        switchView('configuracoes');
        loadConfigurationData();
        showNotification('✅ Acesso Permitido', 'Bem-vindo às configurações', 'success');
    } else {
        errorDiv.textContent = '❌ Senha incorreta! Use a data de hoje no formato ddmmaaaa';
        document.getElementById('passwordInput').value = '';
        document.getElementById('passwordInput').focus();
    }
}

// ==================== CONFIGURAÇÕES ====================

async function loadConfigurationData() {
    try {
        // Carregar informações do dispositivo UR4
        await refreshDeviceInfo();
        
        // Carregar estatísticas do banco
        const statsResponse = await fetch(`${API_URL}/stats`);
        if (statsResponse.ok) {
            const stats = await statsResponse.json();
            document.getElementById('totalSessions').textContent = stats.total_sessions || 0;
        }
        
        // Carregar total de tags
        const tagsResponse = await fetch(`${API_URL}/tags`);
        if (tagsResponse.ok) {
            const tags = await tagsResponse.json();
            document.getElementById('totalTags').textContent = tags.length || 0;
        }
        
        // Carregar configuração do backend (se houver)
        try {
            const configResponse = await fetch(`${API_URL}/config`);
            if (configResponse.ok) {
                const config = await configResponse.json();
                applyConfigToForm(config);
            }
        } catch (e) {
            console.log('Configuração não disponível no backend');
        }
    } catch (error) {
        console.error('Erro ao carregar dados de configuração:', error);
    }
}

async function refreshDeviceInfo() {
    try {
        // Sinalizar para o leitor atualizar
        await fetch(`${API_URL}/device/refresh`, { method: 'POST' });
        
        // Aguardar um pouco e buscar as informações
        await new Promise(resolve => setTimeout(resolve, 1500));
        
        const response = await fetch(`${API_URL}/device/info`);
        if (!response.ok) throw new Error('Erro ao buscar informações do dispositivo');
        
        const info = await response.json();
        
        // Atualizar status
        const statusElement = document.getElementById('deviceStatus');
        const statusDot = statusElement.querySelector('.status-dot');
        
        if (info.connected) {
            statusElement.innerHTML = '<span class="status-dot"></span> Conectado';
            statusDot.classList.remove('offline');
        } else {
            statusElement.innerHTML = '<span class="status-dot offline"></span> Desconectado';
            if (info.error) {
                statusElement.innerHTML += ` - ${info.error}`;
            }
        }
        
        // Atualizar informações
        document.getElementById('deviceSerial').textContent = info.serial_number || 'N/A';
        document.getElementById('deviceFirmware').textContent = info.firmware_version || 'N/A';
        document.getElementById('devicePort').textContent = info.port || 'N/A';
        document.getElementById('deviceAnt1Power').textContent = info.antenna1_power || 'N/A';
        document.getElementById('deviceAnt2Power').textContent = info.antenna2_power || 'N/A';
        document.getElementById('deviceWorkMode').textContent = info.work_mode || 'N/A';
        
        if (info.connected) {
            showNotification('✅ Atualizado', 'Informações do dispositivo atualizadas', 'success');
        } else {
            showNotification('⚠️ Desconectado', info.error || 'Dispositivo não está conectado', 'warning');
        }
        
    } catch (error) {
        console.error('Erro ao buscar informações do dispositivo:', error);
        document.getElementById('deviceStatus').innerHTML = '<span class="status-dot offline"></span> Erro ao comunicar';
        showNotification('❌ Erro', 'Não foi possível atualizar as informações', 'error');
    }
}


function applyConfigToForm(config) {
    if (config.antenna1_enabled !== undefined) {
        document.getElementById('configAntenna1').checked = config.antenna1_enabled;
    }
    if (config.antenna2_enabled !== undefined) {
        document.getElementById('configAntenna2').checked = config.antenna2_enabled;
    }
    if (config.antenna1_power !== undefined) {
        document.getElementById('configAntenna1Power').value = config.antenna1_power;
    }
    if (config.antenna2_power !== undefined) {
        document.getElementById('configAntenna2Power').value = config.antenna2_power;
    }
    if (config.serial_port !== undefined) {
        document.getElementById('configSerialPort').value = config.serial_port;
    }
}

async function saveConfiguration() {
    const config = {
        antenna1_enabled: document.getElementById('configAntenna1').checked,
        antenna2_enabled: document.getElementById('configAntenna2').checked,
        antenna1_power: parseInt(document.getElementById('configAntenna1Power').value),
        antenna2_power: parseInt(document.getElementById('configAntenna2Power').value),
        serial_port: document.getElementById('configSerialPort').value,
        block_duplicates: document.getElementById('configBlockDuplicates').checked,
        tag_length: parseInt(document.getElementById('configTagLength').value),
        refresh_interval: parseInt(document.getElementById('configRefreshInterval').value)
    };
    
    try {
        const response = await fetch(`${API_URL}/config`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(config)
        });
        
        if (response.ok) {
            const result = await response.json();
            showNotification(
                '✅ Configurações Salvas', 
                result.message || 'As configurações foram salvas e serão aplicadas automaticamente pelo leitor RFID', 
                'success'
            );
            
            // Aguardar e atualizar info do dispositivo para confirmar mudanças
            setTimeout(() => refreshDeviceInfo(), 2000);
        } else {
            const error = await response.json();
            showNotification('❌ Erro ao Salvar', error.detail || 'Não foi possível salvar as configurações', 'error');
        }
    } catch (error) {
        console.error('Erro ao salvar configuração:', error);
        showNotification('❌ Erro ao Salvar', 'Erro de comunicação com a API', 'error');
    }
}

function resetConfiguration() {
    if (!confirm('Deseja restaurar as configurações padrão?')) {
        return;
    }
    
    // Valores padrão
    document.getElementById('configAntenna1').checked = true;
    document.getElementById('configAntenna2').checked = true;
    document.getElementById('configAntenna1Power').value = 30;
    document.getElementById('configAntenna2Power').value = 30;
    document.getElementById('configSerialPort').value = 'AUTO';
    document.getElementById('configBlockDuplicates').checked = true;
    document.getElementById('configTagLength').value = 24;
    document.getElementById('configRefreshInterval').value = 3;
    
    showNotification('🔄 Configurações Restauradas', 'Configurações padrão aplicadas. Clique em Salvar para confirmar.', 'info');
}

async function clearDatabase() {
    const confirmation = prompt('⚠️ ATENÇÃO! Esta ação irá apagar TODOS os dados do banco de dados.\n\nDigite "CONFIRMAR" para prosseguir:');
    
    if (confirmation !== 'CONFIRMAR') {
        showNotification('ℹ️ Operação Cancelada', 'Nenhum dado foi apagado', 'info');
        return;
    }
    
    try {
        // Criar endpoint no backend para limpar dados (futuro)
        showNotification('⚠️ Função Não Implementada', 'A limpeza do banco deve ser feita manualmente no servidor', 'warning');
        
        // Alternativa: instruir o usuário
        alert('Para limpar o banco de dados:\n\n1. Pare o sistema\n2. Delete o arquivo: database/rfid_portal.db\n3. Reinicie o sistema\n\nO banco será recriado vazio automaticamente.');
    } catch (error) {
        console.error('Erro ao limpar banco:', error);
        showNotification('❌ Erro', 'Não foi possível limpar o banco de dados', 'error');
    }
}

// Iniciar quando o DOM estiver pronto
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

