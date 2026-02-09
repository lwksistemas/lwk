# 👨‍💼 Guia de Uso - Sistema de Monitoramento para SuperAdmin

## 🎯 Visão Geral

Este guia ensina como usar o Sistema de Monitoramento e Segurança para proteger e auditar todas as lojas do sistema.

## 🚀 Acesso Inicial

### 1. Login

1. Acesse: `https://lwksistemas.com.br/superadmin/login`
2. Digite suas credenciais de SuperAdmin
3. Clique em "Entrar"

### 2. Dashboard Principal

Após o login, você verá:
- **Estatísticas gerais** (total de lojas, ativas, em trial, receita)
- **Menu de ações** com 10 cards
- **Badge de notificações** no header (🔔)

## 🚨 Monitoramento de Alertas

### Acessar Dashboard de Alertas

**Caminho**: Dashboard Principal → Card "Alertas de Segurança"  
**URL**: `/superadmin/dashboard/alertas`

### Funcionalidades

#### 1. Cards de Estatísticas

No topo da página, você verá 4 cards:
- **Total de Violações**: Número total detectado
- **Críticas**: Violações de alta prioridade
- **Não Resolvidas**: Aguardando investigação
- **Resolvidas Hoje**: Violações tratadas hoje

#### 2. Filtros

Use os filtros para encontrar violações específicas:
- **Status**: Nova, Investigando, Resolvida, Falso Positivo
- **Criticidade**: Crítica, Alta, Média, Baixa
- **Tipo**: Brute Force, Rate Limit, Cross-Tenant, etc.

**Exemplo**: Para ver apenas violações críticas não resolvidas:
1. Selecione "Nova" em Status
2. Selecione "Crítica" em Criticidade
3. Clique em "Aplicar Filtros"

#### 3. Lista de Violações

Cada violação mostra:
- **Badge de criticidade** (cor indica prioridade)
- **Tipo de violação** (ex: Tentativa de Brute Force)
- **Usuário envolvido**
- **Loja afetada**
- **Data/hora**
- **Botão "Ver Detalhes"**

#### 4. Detalhes da Violação

Ao clicar em "Ver Detalhes", você verá:
- **Descrição completa** da violação
- **Detalhes técnicos** (IPs, tentativas, janela de tempo)
- **Logs relacionados** (lista de ações suspeitas)
- **Botões de ação**:
  - ✅ **Resolver**: Marcar como resolvida
  - ❌ **Falso Positivo**: Marcar como falso alarme

#### 5. Resolver Violação

1. Clique em "Ver Detalhes" na violação
2. Analise os logs relacionados
3. Clique em "Resolver"
4. Digite suas notas de investigação
5. Clique em "Confirmar"

**Exemplo de notas**:
```
Investigado e confirmado como tentativa de ataque.
Usuário bloqueado temporariamente.
Senha resetada e notificação enviada ao proprietário da loja.
```

#### 6. Marcar como Falso Positivo

Use quando a violação não é uma ameaça real:

1. Clique em "Ver Detalhes"
2. Clique em "Marcar como Falso Positivo"
3. Digite o motivo
4. Clique em "Confirmar"

**Exemplo de motivo**:
```
Falso positivo - proprietário esqueceu senha e tentou várias vezes.
Senha recuperada com sucesso.
```

### Notificações em Tempo Real

#### Badge de Notificações

No header, ao lado do botão "Sair", você verá:
- **Ícone de sino** (🔔)
- **Badge vermelho** com número de alertas não lidos

#### Dropdown de Alertas

1. Clique no ícone de sino
2. Verá lista de violações críticas/altas recentes
3. Cada alerta mostra:
   - Criticidade (cor)
   - Tipo de violação
   - Descrição resumida
   - Usuário e data/hora
   - Link "Ver detalhes"

#### Ações no Dropdown

- **Marcar como lida**: Clique no "×" ao lado do alerta
- **Limpar tudo**: Clique em "Limpar tudo" no topo
- **Ver detalhes**: Clique em "Ver detalhes →" no alerta

#### Toast de Violações Críticas

Quando uma violação crítica é detectada:
- **Toast vermelho** aparece no canto superior direito
- **Título**: "🚨 Violação Crítica Detectada"
- **Mensagem**: Tipo e usuário envolvido
- **Duração**: 10 segundos (fecha automaticamente)

#### Notificações Nativas

Se você permitir notificações do navegador:
- **Popup do sistema** aparece mesmo com aba inativa
- **Som** (se configurado no navegador)
- **Clique** na notificação abre o dashboard

**Permitir notificações**:
1. Navegador pergunta na primeira vez
2. Clique em "Permitir"
3. Ou vá em Configurações do navegador → Notificações

## 📈 Dashboard de Auditoria

### Acessar

**Caminho**: Dashboard Principal → Card "Dashboard de Auditoria"  
**URL**: `/superadmin/dashboard/auditoria`

### Funcionalidades

#### 1. Seletor de Período

No topo, escolha o período de análise:
- **Últimos 7 dias**
- **Últimos 30 dias**
- **Últimos 90 dias**
- **Período customizado** (escolha datas específicas)

#### 2. Taxa de Sucesso

Card mostra:
- **Porcentagem** de ações bem-sucedidas
- **Indicador visual** (verde = bom, vermelho = problemas)

#### 3. Gráfico de Ações por Dia

**Tipo**: Gráfico de linhas  
**Mostra**: Número de ações por dia no período

**Uso**:
- Identificar dias com picos de atividade
- Detectar padrões anormais
- Planejar manutenções

#### 4. Gráfico de Ações por Tipo

**Tipo**: Gráfico de pizza  
**Mostra**: Distribuição de tipos de ação (criar, editar, excluir, etc.)

**Uso**:
- Ver quais ações são mais comuns
- Identificar comportamentos incomuns

#### 5. Gráfico de Horários de Pico

**Tipo**: Gráfico de barras  
**Mostra**: Distribuição de ações por hora do dia (0-23h)

**Uso**:
- Identificar horários de maior uso
- Planejar manutenções em horários de baixo uso
- Detectar atividades fora do horário comercial

#### 6. Top 10 Lojas Mais Ativas

**Tipo**: Tabela  
**Mostra**: Ranking de lojas por número de ações

**Uso**:
- Identificar lojas mais engajadas
- Detectar lojas com atividade anormal

#### 7. Top 10 Usuários Mais Ativos

**Tipo**: Tabela  
**Mostra**: Ranking de usuários por número de ações

**Uso**:
- Identificar usuários mais ativos
- Detectar contas comprometidas (atividade excessiva)

## 🔍 Busca de Logs

### Acessar

**Caminho**: Dashboard Principal → Card "Busca de Logs"  
**URL**: `/superadmin/dashboard/logs`

### Funcionalidades

#### 1. Busca por Texto Livre

Digite qualquer termo na caixa de busca:
- Busca em **detalhes**, **recurso** e **URL**
- Exemplo: "produto", "cliente", "pagamento"

#### 2. Filtros Avançados

Use os filtros para refinar a busca:

**Ação**:
- Login, Logout, Criar, Editar, Excluir, Visualizar, etc.

**Usuário**:
- Digite email do usuário

**Loja**:
- Selecione loja específica

**Status**:
- Sucesso ou Falha

**IP**:
- Digite endereço IP

**Período**:
- Data inicial e final

**Exemplo de busca**:
```
Texto: "produto"
Ação: Excluir
Loja: Loja Exemplo
Período: 01/02/2026 a 08/02/2026
```

#### 3. Resultados

Tabela mostra:
- **Data/Hora**
- **Usuário**
- **Loja**
- **Ação**
- **Recurso**
- **Status** (✓ sucesso, ✗ falha)
- **Botão "Ver Detalhes"**

#### 4. Detalhes do Log

Ao clicar em "Ver Detalhes":
- **Informações completas** do log
- **Detalhes técnicos** (JSON formatado)
- **IP e User Agent**
- **Método HTTP e URL**
- **Mensagem de erro** (se houver)

#### 5. Contexto Temporal

No modal de detalhes, clique em "Ver Contexto Temporal":
- **Timeline** mostra ações antes e depois
- **5 minutos antes** do log selecionado
- **5 minutos depois** do log selecionado

**Uso**:
- Entender sequência de ações
- Investigar comportamento suspeito
- Reconstruir eventos

#### 6. Buscas Salvas

**Salvar busca**:
1. Configure os filtros desejados
2. Clique em "Salvar Busca"
3. Digite um nome (ex: "Exclusões Suspeitas")
4. Clique em "Salvar"

**Carregar busca**:
1. Clique no dropdown "Buscas Salvas"
2. Selecione a busca desejada
3. Filtros são aplicados automaticamente

**Excluir busca**:
1. Abra o dropdown "Buscas Salvas"
2. Clique no "×" ao lado da busca
3. Confirme a exclusão

#### 7. Exportar Logs

**CSV**:
1. Configure os filtros
2. Clique em "Exportar CSV"
3. Arquivo é baixado automaticamente

**JSON**:
1. Configure os filtros
2. Clique em "Exportar JSON"
3. Arquivo é baixado automaticamente

**Uso**:
- Análise offline
- Relatórios para auditoria
- Backup de evidências

## 🛠️ Manutenção

### Limpeza de Logs Antigos

**Automática**: Executa diariamente às 3h da manhã

**Manual**:
1. Acesse o servidor
2. Execute: `python manage.py cleanup_old_logs`
3. Logs com mais de 90 dias são removidos

**Simular antes**:
```bash
python manage.py cleanup_old_logs --dry-run
```

### Arquivamento de Logs

**Quando**: Quando total de logs > 1 milhão

**Manual**:
```bash
# Arquivar em JSON
python manage.py archive_logs --format json

# Arquivar em CSV
python manage.py archive_logs --format csv
```

**Resultado**:
- Arquivo salvo em `logs/archive/`
- Logs antigos removidos do banco
- Estatísticas exibidas no console

### Limpar Cache

Se estatísticas estiverem desatualizadas:

```bash
python manage.py clear_stats_cache
```

## 📊 Casos de Uso Comuns

### Caso 1: Investigar Tentativa de Invasão

**Cenário**: Badge de notificação mostra alerta crítico

**Passos**:
1. Clique no badge de notificações (🔔)
2. Veja "Tentativa de Brute Force - João Silva"
3. Clique em "Ver detalhes"
4. Analise:
   - 6 tentativas de login falhadas
   - IP: 192.168.1.100
   - Período: 10 minutos
5. Vá para "Busca de Logs"
6. Filtre por:
   - Usuário: joao@example.com
   - IP: 192.168.1.100
   - Ação: Login
7. Veja histórico completo do usuário
8. Decisão:
   - Se legítimo: Marcar como falso positivo
   - Se ataque: Resolver e bloquear usuário

### Caso 2: Auditoria Mensal

**Cenário**: Gerar relatório de atividades do mês

**Passos**:
1. Acesse "Dashboard de Auditoria"
2. Selecione "Últimos 30 dias"
3. Capture screenshots:
   - Taxa de sucesso
   - Gráfico de ações por dia
   - Top 10 lojas
   - Top 10 usuários
4. Acesse "Busca de Logs"
5. Configure período: 01/01/2026 a 31/01/2026
6. Exporte CSV para análise detalhada
7. Compile relatório com:
   - Estatísticas gerais
   - Violações detectadas e resolvidas
   - Lojas mais ativas
   - Recomendações

### Caso 3: Investigar Exclusão em Massa

**Cenário**: Alerta de "Exclusão em Massa" detectado

**Passos**:
1. Acesse "Alertas de Segurança"
2. Filtre por tipo: "Mass Deletion"
3. Clique em "Ver Detalhes"
4. Veja:
   - 15 exclusões em 5 minutos
   - Usuário: Maria Santos
   - Loja: Loja Exemplo
5. Clique em log relacionado
6. Veja contexto temporal
7. Identifique:
   - Produtos excluídos
   - Motivo (limpeza legítima ou erro)
8. Ação:
   - Se legítimo: Marcar como falso positivo
   - Se erro: Contatar loja para restaurar
   - Se malicioso: Resolver e investigar

### Caso 4: Monitorar Loja Específica

**Cenário**: Loja reportou problemas, investigar atividades

**Passos**:
1. Acesse "Busca de Logs"
2. Filtre por:
   - Loja: Loja Exemplo
   - Período: Últimas 24 horas
3. Ordene por data (mais recente primeiro)
4. Analise:
   - Ações realizadas
   - Usuários ativos
   - Erros ocorridos
5. Se encontrar problemas:
   - Exporte logs para análise
   - Contate suporte técnico
   - Documente no sistema de tickets

## 🔔 Configurações de Notificações

### Email

**Destinatários**: Configurado em variáveis de ambiente

**Tipos que geram email**:
- Brute Force
- Privilege Escalation
- Cross-Tenant Access
- Mass Deletion

**Criticidades que geram email**:
- Crítica
- Alta

**Agrupamento**: Máximo 1 email a cada 15 minutos por tipo

### Navegador

**Permitir notificações**:
1. Navegador pergunta automaticamente
2. Clique em "Permitir"

**Desabilitar**:
1. Configurações do navegador
2. Privacidade e Segurança
3. Notificações
4. Bloquear site

### Toast

**Duração**:
- Crítica: 10 segundos
- Alta: 7 segundos

**Fechar manualmente**: Clique no "×"

## 📱 Acesso Mobile

O sistema é responsivo e funciona em dispositivos móveis:

**Recomendações**:
- Use navegador atualizado (Chrome, Safari, Firefox)
- Ative notificações para alertas em tempo real
- Dashboards se adaptam ao tamanho da tela
- Tabelas têm scroll horizontal

## 🆘 Solução de Problemas

### Notificações não aparecem

**Causa**: Permissão negada

**Solução**:
1. Configurações do navegador
2. Notificações
3. Permitir para o site

### Estatísticas desatualizadas

**Causa**: Cache não expirou

**Solução**:
1. Aguarde 5 minutos (cache expira automaticamente)
2. Ou execute: `python manage.py clear_stats_cache`

### Logs não aparecem

**Causa**: Filtros muito restritivos

**Solução**:
1. Clique em "Limpar Filtros"
2. Tente busca mais ampla

### Dashboard lento

**Causa**: Muitos logs no banco

**Solução**:
1. Execute limpeza: `python manage.py cleanup_old_logs`
2. Ou arquive: `python manage.py archive_logs`

## 📞 Suporte

**Dúvidas ou problemas?**

1. Clique no botão flutuante de suporte (canto inferior direito)
2. Ou entre em contato: suporte@lwksistemas.com.br
3. Ou consulte a documentação técnica

## 🎓 Boas Práticas

### Diariamente
- ✅ Verificar badge de notificações
- ✅ Revisar violações críticas
- ✅ Resolver ou marcar como falso positivo

### Semanalmente
- ✅ Acessar Dashboard de Auditoria
- ✅ Verificar lojas mais ativas
- ✅ Identificar padrões anormais

### Mensalmente
- ✅ Gerar relatório de auditoria
- ✅ Exportar logs para backup
- ✅ Revisar configurações de segurança
- ✅ Executar limpeza de logs antigos

### Sempre
- ✅ Documentar investigações nas notas
- ✅ Manter logs de ações críticas
- ✅ Comunicar incidentes à equipe
- ✅ Atualizar procedimentos de segurança

---

**Versão**: v513  
**Data**: 2026-02-08  
**Autor**: Equipe LWK Sistemas
