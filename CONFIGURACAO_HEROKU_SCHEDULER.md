# Configuração do Heroku Scheduler para Detecção de Violações de Segurança

## 📋 Visão Geral

O sistema de segurança do LWK Sistemas possui detecção automática de violações que precisa ser executada periodicamente. Este documento explica como configurar o Heroku Scheduler para executar essas verificações automaticamente.

## 🔍 Tipos de Violações Detectadas

O sistema detecta automaticamente os seguintes tipos de violações:

1. **Brute Force** - Múltiplas tentativas de login falhadas (>5 em 10 minutos)
2. **Rate Limit Exceeded** - Excesso de requisições (>100 em 1 minuto)
3. **Cross-Tenant Access** - Tentativa de acessar dados de outra loja
4. **Privilege Escalation** - Tentativa de acessar recursos sem permissão
5. **Mass Deletion** - Exclusão em massa de registros (>10 em 5 minutos)
6. **IP Change** - Mudança suspeita de IP (>2 IPs diferentes em 24 horas)

## ⚙️ Configuração do Heroku Scheduler

### Passo 1: Instalar o Add-on Heroku Scheduler

```bash
# No terminal, execute:
heroku addons:create scheduler:standard -a lwksistemas
```

### Passo 2: Abrir o Dashboard do Scheduler

```bash
heroku addons:open scheduler -a lwksistemas
```

Ou acesse diretamente: https://dashboard.heroku.com/apps/lwksistemas/scheduler

### Passo 3: Criar o Job Agendado

No dashboard do Heroku Scheduler, clique em **"Create job"** e configure:

**Comando:**
```bash
python manage.py detect_security_violations
```

**Frequência:** `Every 10 minutes`

**Dyno Size:** `Standard-1X` (ou o mesmo tipo usado pela aplicação)

### Passo 4: Salvar e Ativar

Clique em **"Save Job"** para ativar a detecção automática.

## 🧪 Testar Manualmente

Para testar o comando antes de agendar:

```bash
# Localmente
python manage.py detect_security_violations

# No Heroku
heroku run python manage.py detect_security_violations -a lwksistemas
```

## 📊 Monitoramento

### Ver Logs de Execução

```bash
heroku logs --tail --ps scheduler -a lwksistemas
```

### Verificar Violações Detectadas

Acesse o dashboard de segurança:
https://lwksistemas.com.br/superadmin/dashboard/alertas

## 🔧 Ajustes de Sensibilidade

Se necessário, você pode ajustar os parâmetros de detecção editando o arquivo:
`backend/superadmin/security_detector.py`

Parâmetros configuráveis:
- `time_window_minutes` - Janela de tempo para análise
- `max_attempts` - Número máximo de tentativas permitidas
- `max_actions` - Número máximo de ações permitidas
- `max_deletions` - Número máximo de exclusões permitidas

## 📝 Notas Importantes

1. **Middleware em Tempo Real**: O middleware `SecurityLoggingMiddleware` já detecta violações de cross-tenant e rate limit em tempo real, sem necessidade de agendamento.

2. **Notificações**: Violações com criticidade "alta" ou "crítica" geram notificações automáticas para os administradores.

3. **Performance**: O comando é otimizado e executa em ~2-5 segundos, não impactando a performance da aplicação.

4. **Custo**: O Heroku Scheduler Standard é gratuito para até 50 jobs por mês. Com execução a cada 10 minutos, teremos ~4.320 execuções/mês, o que pode gerar custo adicional. Considere ajustar para 30 minutos se necessário.

## 🚨 Alternativas de Frequência

Dependendo do nível de segurança desejado:

- **Alta Segurança**: A cada 5-10 minutos (recomendado)
- **Segurança Moderada**: A cada 30 minutos
- **Segurança Básica**: A cada 1 hora

## ✅ Status Atual

- ✅ Comando implementado: `detect_security_violations`
- ✅ SecurityDetector com 6 métodos de detecção
- ✅ Middleware de segurança ativo
- ⏳ Heroku Scheduler: **PENDENTE DE CONFIGURAÇÃO**

## 📞 Suporte

Em caso de dúvidas ou problemas, consulte os logs do Heroku ou entre em contato com a equipe de desenvolvimento.
