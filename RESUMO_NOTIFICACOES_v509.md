# Sistema de Notificações - v509

## 📋 Resumo

Implementado o Sistema de Notificações por Email para alertar sobre violações de segurança críticas, com agrupamento inteligente para evitar spam e resumo diário automático.

## ✅ Implementação Concluída

### Arquivos Criados

#### 1. Serviço de Notificações
- **Caminho**: `backend/superadmin/notifications.py`
- **Linhas de código**: ~250 linhas
- **Classe**: `NotificationService`

#### 2. Templates de Email
- **Violação Individual**: `backend/superadmin/templates/superadmin/email_violacao.html`
- **Resumo Diário**: `backend/superadmin/templates/superadmin/email_resumo_diario.html`

#### 3. Task Agendada
- **Arquivo**: `backend/superadmin/tasks.py`
- **Função**: `send_daily_summary()`

#### 4. Configurações
- **Arquivo**: `backend/config/settings.py`
- **Variáveis**: `SECURITY_NOTIFICATION_EMAILS`, `SITE_URL`

### Funcionalidades Implementadas

#### 1. Notificação de Violações Críticas ✅

**Critérios de Envio**:
- Criticidade: Alta ou Crítica
- Tipos notificáveis:
  - `brute_force` (Força Bruta)
  - `privilege_escalation` (Escalação de Privilégios)
  - `cross_tenant` (Acesso Cross-Tenant)
  - `mass_deletion` (Exclusão em Massa)

**Conteúdo do Email**:
- Tipo da violação
- Criticidade (badge colorido)
- Data/Hora
- Usuário (nome + email)
- Loja
- IP Address
- Descrição detalhada
- Detalhes técnicos
- Link para dashboard de alertas
- Ação recomendada

**Design**:
- Header roxo com gradiente
- Badge colorido por criticidade
- Grid de informações
- Botão CTA para ver detalhes
- Footer com timestamp

#### 2. Agrupamento de Notificações ✅

**Objetivo**: Evitar spam de emails

**Implementação**:
- Intervalo mínimo: 15 minutos entre notificações do mesmo tipo
- Cache em memória: `_ultimas_notificacoes` (tipo -> timestamp)
- Verificação automática antes de enviar

**Exemplo**:
```
10:00 - Brute Force detectado → Email enviado
10:05 - Brute Force detectado → Email agrupado (não enviado)
10:10 - Brute Force detectado → Email agrupado (não enviado)
10:16 - Brute Force detectado → Email enviado (15 min passados)
```

#### 3. Resumo Diário ✅

**Agendamento**: Diariamente às 8h (Django-Q)

**Conteúdo**:
- Total de violações (últimas 24h)
- Distribuição por criticidade (4 cards)
- Distribuição por status (4 badges)
- Top 10 violações críticas
- Data do resumo

**Estatísticas**:
- Por criticidade: Crítica, Alta, Média, Baixa
- Por status: Nova, Investigando, Resolvida, Falso Positivo

**Condições**:
- Só envia se houver violações
- Só envia se houver destinatários configurados

#### 4. Integração com Detector ✅

**Localização**: `backend/superadmin/security_detector.py`

**Método**: `_create_violation()`

**Lógica**:
```python
# Após criar violação
if criticidade in ['alta', 'critica']:
    NotificationService.enviar_notificacao_violacao(violacao)
```

**Tratamento de Erros**:
- Try/except para não quebrar detecção
- Log de erros detalhado
- Continua execução mesmo se email falhar

#### 5. Configuração de Destinatários ✅

**Variável de Ambiente**:
```bash
SECURITY_NOTIFICATION_EMAILS=admin@exemplo.com,seguranca@exemplo.com
```

**Fallback**:
- Se não configurado, usa `ADMINS` do Django
- Se `ADMINS` vazio, não envia (log de warning)

**Formato**:
- Lista separada por vírgulas
- Espaços são removidos automaticamente
- Emails vazios são ignorados

#### 6. Task Agendada ✅

**Arquivo**: `backend/superadmin/tasks.py`

**Função**: `send_daily_summary()`

**Características**:
- Logging completo (início, sucesso, erro)
- Tempo de execução registrado
- Retorna dict com resultado
- Tratamento robusto de erros

**Schedule**: Configurado em `setup_security_schedules`

### Integração com Sistema

#### Fluxo Completo
```
1. Detector analisa logs (a cada 5 min)
   ↓
2. Violação crítica detectada
   ↓
3. Violação criada no banco
   ↓
4. NotificationService verifica agrupamento
   ↓
5. Email enviado (se permitido)
   ↓
6. Violação marcada como notificada
   ↓
7. SuperAdmin recebe email
   ↓
8. SuperAdmin acessa dashboard
```

#### Schedules Django-Q
1. **detect_security_violations**: A cada 5 minutos
2. **cleanup_old_logs**: Diariamente às 3h
3. **send_security_notifications**: A cada 15 minutos (legado)
4. **send_daily_summary**: Diariamente às 8h (NOVO)

### Templates de Email

#### Template de Violação Individual

**Estrutura**:
- Header com gradiente roxo
- Alert box com tipo e criticidade
- Grid de informações (4 campos)
- Descrição textual
- Detalhes técnicos (monospace)
- Botão CTA "Ver Detalhes Completos"
- Box de ação recomendada (amarelo)
- Footer com timestamp

**Cores por Criticidade**:
- Crítica: Vermelho (#c00)
- Alta: Laranja (#d63031)

**Responsivo**: Adapta para mobile

#### Template de Resumo Diário

**Estrutura**:
- Header com data
- Grid de estatísticas (2x2)
- Seção "Por Criticidade" (badges)
- Seção "Violações Críticas" (top 10)
- Box de recomendação (azul)
- Footer com timestamp

**Cards de Estatísticas**:
- Total de Violações
- Críticas
- Novas
- Resolvidas

**Cores**:
- Números: Roxo (#667eea)
- Badges: Cores semânticas

### Configurações

#### Variáveis de Ambiente

**Obrigatórias**:
```bash
# Email SMTP
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=seu-email@gmail.com
EMAIL_HOST_PASSWORD=sua-senha-app
DEFAULT_FROM_EMAIL=Sistema <noreply@exemplo.com>
```

**Opcionais**:
```bash
# Notificações de Segurança
SECURITY_NOTIFICATION_EMAILS=admin@exemplo.com,seguranca@exemplo.com
SITE_URL=https://lwksistemas.com.br
```

#### Settings.py

**Adicionado**:
```python
# Configurações de Notificações de Segurança
SECURITY_NOTIFICATION_EMAILS = config(
    'SECURITY_NOTIFICATION_EMAILS',
    default='',
    cast=lambda v: [email.strip() for email in v.split(',') if email.strip()]
)
SITE_URL = config('SITE_URL', default='http://localhost:3000')
```

**Desenvolvimento**:
```python
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```
- Emails aparecem no console (não envia de verdade)

### Métodos da Classe NotificationService

#### Públicos
1. **enviar_notificacao_violacao(violacao)**
   - Envia email para violação individual
   - Verifica tipo, criticidade e agrupamento
   - Marca violação como notificada
   - Retorna: bool (sucesso)

2. **enviar_resumo_diario()**
   - Envia resumo das últimas 24h
   - Calcula estatísticas
   - Retorna: bool (sucesso)

#### Privados
1. **_pode_enviar_notificacao(tipo)**
   - Verifica agrupamento
   - Retorna: bool

2. **_registrar_envio(tipo)**
   - Atualiza cache de últimas notificações

3. **_enviar_email(violacao)**
   - Renderiza template
   - Envia via SMTP
   - Retorna: bool

4. **_obter_destinatarios()**
   - Retorna lista de emails
   - Fallback para ADMINS

5. **_obter_url_detalhes(violacao)**
   - Constrói URL do dashboard
   - Retorna: string

### Logging

**Níveis Utilizados**:
- `DEBUG`: Verificações de agrupamento, violações existentes
- `INFO`: Notificações enviadas, resumos enviados
- `WARNING`: Sem destinatários, sem violações
- `ERROR`: Erros ao enviar email, erros gerais

**Exemplos**:
```
INFO: Notificação enviada para violação 123
INFO: Resumo diário enviado: 15 violações
WARNING: Nenhum destinatário configurado para notificações
ERROR: Erro ao enviar email: SMTPAuthenticationError
```

## 📊 Exemplos de Uso

### Configurar Destinatários

**Arquivo**: `.env`
```bash
SECURITY_NOTIFICATION_EMAILS=admin@lwk.com.br,seguranca@lwk.com.br
SITE_URL=https://lwksistemas.com.br
```

### Testar Envio Manual

**Console Django**:
```python
from superadmin.models import ViolacaoSeguranca
from superadmin.notifications import NotificationService

# Buscar violação crítica
violacao = ViolacaoSeguranca.objects.filter(criticidade='critica').first()

# Enviar notificação
sucesso = NotificationService.enviar_notificacao_violacao(violacao)
print(f"Enviado: {sucesso}")
```

### Testar Resumo Diário

**Console Django**:
```python
from superadmin.notifications import NotificationService

# Enviar resumo
sucesso = NotificationService.enviar_resumo_diario()
print(f"Resumo enviado: {sucesso}")
```

### Configurar Schedule

**Terminal**:
```bash
python manage.py setup_security_schedules
```

**Saída**:
```
✅ Schedule criado: send_daily_summary (diariamente às 8h)
```

## 🔧 Configuração

### Dependências
- Django email system (built-in)
- Django templates (built-in)
- Django-Q (já instalado)

### Permissões
- Nenhuma permissão especial necessária
- Emails enviados em background (Django-Q)

### Limites
- **Agrupamento**: 15 minutos por tipo
- **Resumo**: Últimas 24 horas
- **Top violações**: 10 críticas no resumo

## 📈 Métricas e Performance

### Otimizações Implementadas
- **Cache em memória**: Evita queries para verificar agrupamento
- **Queries otimizadas**: Agregações para estatísticas
- **Templates pré-compilados**: Renderização rápida
- **Envio assíncrono**: Não bloqueia detecção

### Casos de Uso Cobertos
1. ✅ Alerta imediato para violações críticas
2. ✅ Prevenção de spam de emails
3. ✅ Resumo diário para visão geral
4. ✅ Link direto para investigação
5. ✅ Configuração flexível de destinatários

## 🎯 Próximos Passos

### Tarefa 15.3: Notificações em Tempo Real (Frontend)
- [ ] Implementar polling ou WebSocket
- [ ] Exibir toast/banner para violações críticas
- [ ] Badge de contador no menu

### Melhorias Futuras (Opcional)
- [ ] Notificações por Slack/Telegram
- [ ] Configuração de horários de envio
- [ ] Filtros personalizados por usuário
- [ ] Histórico de notificações enviadas
- [ ] Métricas de abertura de emails

## 📝 Notas Técnicas

1. **Agrupamento**: Cache em memória (não persiste entre restarts)
2. **Templates**: HTML responsivo com fallback para texto plano
3. **SMTP**: Usa configurações padrão do Django
4. **Desenvolvimento**: Console backend (emails no terminal)
5. **Produção**: Configurar SMTP real (Gmail, SendGrid, etc.)

## ✅ Checklist de Conclusão

- [x] Serviço de notificações criado
- [x] Agrupamento implementado (15 min)
- [x] Templates de email criados (2)
- [x] Integração com detector
- [x] Task de resumo diário
- [x] Schedule configurado
- [x] Configurações adicionadas
- [x] Logging completo
- [x] Tratamento de erros
- [x] Validação (0 erros no check)
- [x] Tarefa 15.1 e 15.2 marcadas como concluídas
- [x] Documentação criada

## 🎉 Resultado

Sistema de Notificações totalmente funcional, permitindo:
- Alertas automáticos para violações críticas
- Agrupamento inteligente (evita spam)
- Resumo diário com estatísticas
- Templates HTML profissionais
- Configuração flexível de destinatários
- Integração transparente com detector
- Logging completo para troubleshooting

**Falta apenas**: Notificações em tempo real no frontend (Tarefa 15.3)
