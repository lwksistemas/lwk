# 🔒 Sistema de Segurança - LWK Sistemas

## 📋 Visão Geral

O sistema possui detecção automática de violações de segurança que monitora e alerta sobre atividades suspeitas em tempo real.

## ✅ Status Atual da Implementação

### Componentes Implementados

✅ **Modelo de Dados** (`ViolacaoSeguranca`)
- Armazena todas as violações detectadas
- Criticidade automática baseada no tipo
- Status de investigação (nova, investigando, resolvida, falso positivo)

✅ **Detector de Segurança** (`SecurityDetector`)
- 6 métodos de detecção implementados
- Análise de logs com queries otimizadas
- Criação automática de violações

✅ **Middleware de Segurança** (`SecurityLoggingMiddleware`)
- Detecção em tempo real de cross-tenant access
- Registro de todos os acessos no `HistoricoAcessoGlobal`
- Bloqueio automático de acessos não autorizados

✅ **Rate Limiting** (`RateLimitMiddleware`)
- Proteção contra abuso de API
- Limite de 60 requisições por minuto por usuário

✅ **Frontend - Dashboard de Alertas**
- Página: `/superadmin/dashboard/alertas`
- Filtros por Status, Criticidade e Tipo
- Estatísticas em tempo real
- Lista detalhada de violações

## 🔍 Tipos de Violações Detectadas

| Tipo | Descrição | Criticidade | Detecção |
|------|-----------|-------------|----------|
| **Brute Force** | >5 tentativas de login falhadas em 10 min | Alta | Automática |
| **Rate Limit Exceeded** | >100 requisições em 1 minuto | Média | Tempo Real |
| **Cross-Tenant Access** | Acesso a dados de outra loja | Crítica | Tempo Real |
| **Privilege Escalation** | Acesso não autorizado a recursos | Crítica | Automática |
| **Mass Deletion** | >10 exclusões em 5 minutos | Alta | Automática |
| **IP Change** | >2 IPs diferentes em 24 horas | Baixa | Automática |

## 🚀 Comandos Disponíveis

### 1. Executar Detecção de Violações

```bash
# Localmente
python manage.py detect_security_violations

# No Heroku
heroku run python manage.py detect_security_violations -a lwksistemas
```

### 2. Verificar Status do Sistema

```bash
# Localmente
python manage.py security_status

# No Heroku
heroku run python manage.py security_status -a lwksistemas
```

## ⚙️ Configuração do Heroku Scheduler

### Opção 1: Script Automático

```bash
./setup-heroku-scheduler.sh
```

### Opção 2: Manual

1. **Instalar o add-on:**
```bash
heroku addons:create scheduler:standard -a lwksistemas
```

2. **Abrir o dashboard:**
```bash
heroku addons:open scheduler -a lwksistemas
```

3. **Criar job com as configurações:**
   - **Comando:** `python manage.py detect_security_violations`
   - **Frequência:** `Every 10 minutes`
   - **Dyno Size:** `Standard-1X`

4. **Salvar e ativar**

## 📊 Monitoramento

### Dashboard Web
Acesse: https://lwksistemas.com.br/superadmin/dashboard/alertas

### Logs do Heroku
```bash
# Ver logs do scheduler
heroku logs --tail --ps scheduler -a lwksistemas

# Ver logs gerais
heroku logs --tail -a lwksistemas
```

### Verificar Status
```bash
heroku run python manage.py security_status -a lwksistemas
```

## 🔧 Ajustes de Sensibilidade

Para ajustar os parâmetros de detecção, edite:
`backend/superadmin/security_detector.py`

**Parâmetros configuráveis:**

```python
# Brute Force
detect_brute_force(time_window_minutes=10, max_attempts=5)

# Rate Limit
detect_rate_limit(time_window_minutes=1, max_actions=100)

# Cross-Tenant
detect_cross_tenant(time_window_minutes=60)

# Privilege Escalation
detect_privilege_escalation(time_window_minutes=60)

# Mass Deletion
detect_mass_deletion(time_window_minutes=5, max_deletions=10)

# IP Change
detect_ip_change(time_window_hours=24)
```

## 🚨 Notificações

Violações com criticidade **alta** ou **crítica** geram notificações automáticas para os administradores do sistema.

## 📈 Performance

- **Tempo de execução:** ~2-5 segundos
- **Impacto:** Mínimo (executa em background)
- **Queries otimizadas:** Uso de agregações e índices

## 🔐 Segurança em Camadas

1. **Middleware (Tempo Real)**
   - Bloqueia acessos não autorizados imediatamente
   - Registra todos os acessos

2. **Detector Periódico (A cada 10 min)**
   - Analisa padrões suspeitos nos logs
   - Detecta ataques coordenados

3. **Dashboard de Alertas**
   - Visualização centralizada
   - Investigação e resolução de violações

## 📝 Próximos Passos

1. ✅ Implementar todos os tipos de violação
2. ✅ Criar dashboard de alertas
3. ✅ Implementar middleware de segurança
4. ⏳ **Configurar Heroku Scheduler** (PENDENTE)
5. ⏳ Implementar notificações por email
6. ⏳ Adicionar relatórios de segurança

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique os logs: `heroku logs --tail -a lwksistemas`
2. Execute o status: `heroku run python manage.py security_status -a lwksistemas`
3. Consulte a documentação completa: `CONFIGURACAO_HEROKU_SCHEDULER.md`

---

**Última atualização:** 01/04/2026
