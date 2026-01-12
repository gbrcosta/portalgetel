# 📘 Guia de Uso - Portal RFID Biamar UR4

## 🎯 Visão Geral

Sistema POC para monitoramento de produção através de portal RFID com duas telas principais:
- **Dashboard**: Monitoramento em tempo real
- **Auditoria**: Histórico completo com filtros avançados

---

## 📊 Dashboard

### O que você vê:

#### Métricas Principais (Cards Grandes)
1. **📦 Produzido Hoje** 
   - Quantidade de peças finalizadas no dia atual
   - Resetado automaticamente à meia-noite

2. **🏆 Total Geral**
   - Histórico completo de todas as peças produzidas
   - Acumula desde o início do sistema

3. **⚡ Em Produção**
   - Peças atualmente passando pelo portal
   - Contador em tempo real

#### Métricas Secundárias
4. **⏱️ Tempo Médio Hoje**
   - Média de tempo de produção das peças de hoje
   - Útil para acompanhar performance diária

5. **⏰ Tempo Médio Geral**
   - Média histórica de todos os tempos de produção
   - Baseline para comparação

#### Lista de Produção em Andamento
- Mostra todas as tags atualmente entre a Antena 1 e Antena 2
- Exibe tempo decorrido em tempo real
- Atualiza automaticamente a cada 3 segundos

---

## 🔍 Auditoria

### Filtros Disponíveis

1. **Data Início / Data Fim**
   - Filtra sessões por período específico
   - Formato: AAAA-MM-DD
   - Padrão: dia atual

2. **Tag ID**
   - Busca por ID específico de tag
   - Aceita busca parcial (ex: "TAG001" encontra "TAG0010", "TAG0011", etc.)

3. **Status**
   - **Todos**: Exibe todas as sessões
   - **Em Produção**: Apenas tags ainda no portal
   - **Finalizado**: Apenas tags que completaram o ciclo

### Ações

#### 🔍 Aplicar Filtros
- Aplica os critérios selecionados
- Atualiza tabela e resumo

#### 🔄 Limpar
- Remove todos os filtros
- Retorna à visualização completa

#### 📥 Exportar CSV
- Gera arquivo Excel/CSV com os dados filtrados
- Inclui: ID, Tag ID, Entrada, Saída, Tempo, Status
- Nome do arquivo: `auditoria-rfid-AAAA-MM-DD.csv`

### Resumo do Período

Após aplicar filtros, você vê:
- **Total de Registros**: Quantidade de sessões no período
- **Finalizados**: Quantas foram completadas
- **Tempo Médio**: Média de produção no período filtrado

### Tabela de Histórico

Exibe todas as sessões com:
- **ID**: Número sequencial da sessão
- **Tag ID**: Identificador da etiqueta RFID
- **Entrada (Antena 1)**: Data/hora de detecção na entrada
- **Saída (Antena 2)**: Data/hora de detecção na saída
- **Tempo de Produção**: Duração total no formato `Xh Ym Zs`
- **Status**: 
  - ⚡ Em Produção (amarelo)
  - ✅ Finalizado (verde)

### Log de Eventos RFID

Lista cronológica de todas as detecções:
- Cada evento mostra:
  - Tag ID detectada
  - Qual antena (1 = Entrada / 2 = Saída)
  - Data e hora exata

---

## 💡 Casos de Uso Comuns

### 1. Verificar Produção do Dia
1. Acesse **Dashboard**
2. Veja card "Produzido Hoje"
3. Compare com "Tempo Médio Hoje" para avaliar performance

### 2. Rastrear Tag Específica
1. Acesse **Auditoria**
2. Digite o ID no campo "Tag ID"
3. Clique em "Aplicar Filtros"
4. Veja histórico completo da tag

### 3. Análise Semanal
1. Acesse **Auditoria**
2. Defina "Data Início" = início da semana
3. Defina "Data Fim" = fim da semana
4. Clique "Aplicar Filtros"
5. Veja resumo e exporte CSV se necessário

### 4. Identificar Tags Travadas
1. Acesse **Auditoria**
2. Selecione Status = "Em Produção"
3. Clique "Aplicar Filtros"
4. Tags muito antigas podem estar travadas

### 5. Gerar Relatório
1. Acesse **Auditoria**
2. Configure período desejado
3. Aplique filtros
4. Clique "Exportar CSV"
5. Abra no Excel para análise

---

## ⚙️ Configurações

### Atualização Automática
- **Dashboard**: Atualiza a cada 3 segundos automaticamente
- **Auditoria**: Manual (para não perder filtros aplicados)

### Indicador de Status
- 🟢 **Online**: Sistema conectado à API
- 🔴 **Offline**: Verifique se a API está rodando

---

## 🚨 Troubleshooting

### Dashboard não atualiza
1. Verifique indicador de status no rodapé
2. Confirme que `start_api.bat` está rodando
3. Atualize a página (F5)

### Filtros não funcionam
1. Clique em "Limpar"
2. Reaplique os filtros um por vez
3. Verifique formato das datas

### Exportar CSV não funciona
1. Verifique se há dados filtrados
2. Permita download no navegador
3. Tente outro navegador (Chrome/Edge recomendados)

---

## 📞 Suporte POC

Este é um sistema em **Proof of Concept (POC)**. 

Para demonstração e testes, use o modo de simulação do leitor RFID.

**Getel Soluções em Tecnologia LTDA**
