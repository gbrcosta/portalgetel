// Configuração da API
const API_URL = 'http://localhost:8000/api';
const REFRESH_INTERVAL = 3000; // 3 segundos

// Estado da aplicação
let isConnected = false;
let currentView = 'dashboard';
let filteredSessions = [];

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

// Atualizar todos os dados do Dashboard
async function refreshDashboard() {
    await Promise.all([
        fetchDashboardStats(),
        fetchActiveSessions()
    ]);
    updateLastUpdateTime();
}

// Carregar dados da Auditoria
async function loadAuditData() {
    await Promise.all([
        fetchAuditSessions(),
        fetchAuditEvents()
    ]);
    updateLastUpdateTime();
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
        btn.addEventListener('click', () => switchView(btn.dataset.view));
    });
    
    // Configurar data padrão de hoje nos filtros
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('filterStartDate').value = today;
    document.getElementById('filterEndDate').value = today;
    
    // Primeira carga de dados
    await refreshDashboard();

    // (config screen removed)
    
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

// Iniciar quando o DOM estiver pronto
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

// config functions removed (UI not present)
