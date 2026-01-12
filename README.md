# Portal RFID - Biamar UR4

Sistema de monitoramento de produção utilizando portal RFID com robô UR4. **Projeto em POC (Proof of Concept)**.

## 📋 Descrição

Este sistema monitora tags RFID através de 2 antenas conectadas ao UR4:
- **Antena 1**: Detecta entrada na produção (início)
- **Antena 2**: Detecta saída da produção (fim)

O sistema registra automaticamente o tempo de produção de cada tag e apresenta:
- **Dashboard**: Monitoramento em tempo real com métricas principais
- **Auditoria**: Histórico completo com filtros por período e etiquetas

## 🏗️ Estrutura do Projeto

```
Biamar UR4/
├── backend/          # API REST (FastAPI)
│   ├── main.py      # Servidor API
│   └── models.py    # Modelos de dados e banco
├── frontend/         # Interface web (Dashboard)
│   ├── index.html   # Página principal
│   ├── styles.css   # Estilos
│   └── app.js       # Lógica do dashboard
├── scripts/          # Scripts de integração
│   └── ur4_rfid_reader.py  # Leitor RFID UR4
├── database/         # Banco de dados SQLite
│   └── rfid_portal.db (criado automaticamente)
└── requirements.txt  # Dependências Python
```

## 🚀 Instalação

### 1. Instalar Dependências

```powershell
pip install -r requirements.txt
```

### 2. Configurar IP do UR4

Edite o arquivo `scripts\ur4_rfid_reader.py` e configure o IP do seu UR4:

```python
UR4_IP = "192.168.1.100"  # Altere para o IP do seu UR4
```

### 3. Configurar Antenas RFID

No arquivo `scripts\ur4_rfid_reader.py`, configure os registradores das antenas:

```python
ANTENNA_1_REGISTER = 0  # Digital Input da Antena 1
ANTENNA_2_REGISTER = 1  # Digital Input da Antena 2
```

## ▶️ Como Executar

### 1. Iniciar o Servidor API (Backend)

Em um terminal, execute:

```powershell
cd backend
python main.py
```

A API estará disponível em: `http://localhost:8000`

### 2. Iniciar o Leitor RFID

Em outro terminal, execute:

```powershell
cd scripts
python ur4_rfid_reader.py
```

**Modos de operação:**
- **Modo Normal**: Conecta ao UR4 e lê as antenas reais
- **Modo Simulação**: Se não conseguir conectar ao UR4, simula a detecção de tags

### 3. Abrir o Dashboard

Abra o arquivo `frontend\index.html` em um navegador web moderno (Chrome, Firefox, Edge).

O dashboard atualizará automaticamente a cada 2 segundos.

## 📊 Funcionalidades do Dashboard

### Tela Principal - Dashboard
**Atualização automática a cada 3 segundos**

#### Métricas em Destaque
- **Produzido Hoje**: Quantidade de peças finalizadas no dia atual
- **Total Geral**: Total histórico de todas as peças produzidas
- **Em Produção**: Peças atualmente no portal (em tempo real)

#### Tempos de Produção
- **Tempo Médio Hoje**: Performance do dia atual
- **Tempo Médio Geral**: Baseline histórico

#### Produção em Andamento
- Lista de todas as tags atualmente entre as antenas
- Tempo decorrido em tempo real
- Atualização automática

### Tela de Auditoria
**Atualização manual (preserva filtros)**

#### Filtros Avançados
- **Período**: Data início e fim
- **Tag ID**: Busca por etiqueta específica
- **Status**: Em produção ou finalizado

#### Funcionalidades
- 📊 Resumo estatístico do período filtrado
- 📋 Tabela completa com histórico detalhado
- 🔔 Log cronológico de todos os eventos RFID
- 📥 **Exportação para CSV/Excel** dos dados filtrados

#### Casos de Uso
1. Rastrear tag específica
2. Análise de período (dia/semana/mês)
3. Identificar tags travadas no sistema
4. Gerar relatórios para análise

## 🔌 API Endpoints

### GET `/`
Status da API

### POST `/api/rfid/event`
Registra evento de detecção RFID
```json
{
    "tag_id": "TAG0001",
    "antenna_number": 1
}
```

### GET `/api/sessions`
Lista todas as sessões de produção

### GET `/api/sessions/active`
Lista apenas sessões ativas (em produção)

### GET `/api/stats`
Retorna estatísticas do dashboard

### GET `/api/events/recent`
Lista eventos recentes de detecção

## 🔧 Integração com UR4

O sistema se conecta ao UR4 via socket TCP na porta 30002 (porta padrão).

### Leitura dos Inputs Digitais

O script lê os inputs digitais do UR4 onde as antenas RFID estão conectadas:
```python
get_digital_in(0)  # Antena 1
get_digital_in(1)  # Antena 2
```

### Detecção de Eventos

O sistema detecta quando um input muda de LOW para HIGH (borda de subida), indicando que uma tag foi detectada.

## 💾 Banco de Dados

O sistema utiliza SQLite com 3 tabelas principais:

### `rfid_tags`
- Cadastro de todas as tags RFID
- Descrição e status de cada tag

### `production_sessions`
- Sessões de produção (entrada e saída)
- Tempo de duração calculado automaticamente
- Status: `em_producao` ou `finalizado`

### `rfid_events`
- Log de todos os eventos de detecção
- Referência à antena e sessão

## 🎯 Fluxo de Operação

1. **Tag entra na Antena 1**
   - Sistema cria nova sessão de produção
   - Registra timestamp de entrada
   - Status: `em_producao`
   - Aparece no dashboard "Em Produção"

2. **Tag detectada na Antena 2**
   - Sistema busca sessão ativa da tag
   - Registra timestamp de saída
   - Calcula tempo de produção automaticamente
   - Status: `finalizado`
   - Incrementa contador "Produzido Hoje"

3. **Dashboard atualiza automaticamente**
   - Estatísticas recalculadas
   - Médias atualizadas
   - Histórico disponível na Auditoria

## 📖 Documentação

- **[GUIA_USO.md](GUIA_USO.md)**: Guia completo de uso do sistema com exemplos práticos
- Inclui casos de uso, troubleshooting e boas práticas
3000; // 3 segundos (3000ms)
```

### Alterar Intervalo de Leitura das Antenas

Em `scripts\ur4_rfid_reader.py`:
```python
time.sleep(0.1)  # 100ms entre leituras
```

### Alterar Porta da API

Em `backend\main.py`:
```python
uvicorn.run(app, host="0.0.0.0", port=8000)
```

## 📝 Notas Importantes - POC

- Este é um **sistema em POC (Proof of Concept)** para demonstração
- O sistema requer que a API esteja rodando para o dashboard funcionar
- O leitor RFID pode operar em **modo simulação** para testes sem hardware
- Certifique-se de que o UR4 está acessível na rede para modo produção
- O dashboard usa requisições HTTP locais (localhost)
- **Dados são armazenados localmente em SQLite**

## 🎯 Recursos da POC

✅ Dashboard em tempo real  
✅ Auditoria com filtros avançados  
✅ Exportação de dados para CSV  
✅ Modo simulação para testes  
✅ Interface responsiva  
✅ Banco de dados local  
✅ API REST documentada  

## 📝 Notas Importantes

- O sistema requer que a API esteja rodando para o dashboard funcionar
- O leitor RFID pode operar em modo simulação para testes
- Certifique-se de que o UR4 está acessível na rede
- O dashboard usa requisições HTTP locais (localhost)

## 🔐 Segurança

Para uso em produção, considere:
- Adicionar autenticação à API
- Usar HTTPS
- ImplemPOC desenvolvido para Biamar - Getel Soluções em Tecnologia LTDA

---

**Versão**: 1.0 POC  
**Data**: Janeiro 2026  
**Status**: Proof of Concept - Demonstração
- Adicionar logs de auditoria

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique se a API está rodando (`http://localhost:8000`)
2. Verifique a conexão com o UR4
3. Consulte os logs no terminal

## 📄 Licença

Sistema desenvolvido para Biamar - Getel Soluções em Tecnologia LTDA
