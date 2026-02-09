# Guia Django-Q - Sistema de Monitoramento de Segurança

## 📋 Visão Geral

O Django-Q foi configurado para executar tarefas agendadas de monitoramento de segurança automaticamente. Este guia explica como iniciar, monitorar e gerenciar o sistema.

## 🚀 Iniciando o Django-Q

### Desenvolvimento (Terminal)

Para testar em desenvolvimento, execute em um terminal separado:

```bash
cd backend
source venv/bin/activate
python manage.py qcluster
```

O cluster ficará rodando e você verá logs das tarefas sendo executadas.

### Produção (Background)

Para produção, use um gerenciador de processos como **Supervisor** ou **systemd**.

#### Opção 1: Supervisor (Recomendado)

1. Instale o Supervisor:
```bash
sudo apt-get install supervisor
```

2. Crie o arquivo de configuração `/etc/supervisor/conf.d/django-q.conf`:
```ini
[program:django-q]
command=/home/luiz/Documents/lwksistemas/backend/venv/bin/python manage.py qcluster
directory=/home/luiz/Documents/lwksistemas/backend
user=luiz
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/django-q.log
```

3. Recarregue o Supervisor:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start django-q
```

4. Verifique o status:
```bash
sudo supervisorctl status django-q
```

#### Opção 2: systemd

1. Crie o arquivo `/etc/systemd/system/django-q.service`:
```ini
[Unit]
Description=Django-Q Cluster
After=network.target

[Service]
Type=simple
User=luiz
WorkingDirectory=/home/luiz/Documents/lwksistemas/backend
ExecStart=/home/luiz/Documents/lwksistemas/backend/venv/bin/python manage.py qcluster
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

2. Habilite e inicie o serviço:
```bash
sudo systemctl daemon-reload
sudo systemctl enable django-q
sudo systemctl start django-q
```

3. Verifique o status:
```bash
sudo systemctl status django-q
```

## 📊 Tarefas Agendadas Configuradas

### 1. Detecção de Violações de Segurança
- **Função**: `superadmin.tasks.detect_security_violations`
- **Frequência**: A cada 5 minutos
- **Descrição**: Analisa logs e detecta padrões suspeitos (brute force, rate limit, cross-tenant, etc.)

### 2. Limpeza de Logs Antigos
- **Função**: `superadmin.tasks.cleanup_old_logs`
- **Frequência**: Diariamente às 3h da manhã
- **Descrição**: Remove logs com mais de 90 dias para otimizar o banco

### 3. Envio de Notificações
- **Função**: `superadmin.tasks.send_security_notifications`
- **Frequência**: A cada 15 minutos
- **Descrição**: Envia emails sobre violações críticas não notificadas

## 🔧 Comandos Úteis

### Verificar Schedules Configurados
```bash
python manage.py qmonitor
```

### Reconfigurar Schedules
```bash
python manage.py setup_security_schedules
```

### Ver Histórico de Tarefas (Django Admin)
Acesse: `http://localhost:8000/admin/django_q/`

### Executar Tarefa Manualmente (Teste)
```python
from superadmin.tasks import detect_security_violations
resultado = detect_security_violations()
print(resultado)
```

## 📝 Logs

### Ver Logs do Cluster
Se usando Supervisor:
```bash
sudo tail -f /var/log/django-q.log
```

Se usando systemd:
```bash
sudo journalctl -u django-q -f
```

### Logs das Tarefas
Os logs das tarefas são registrados no logger do Django. Configure em `settings.py`:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/django-tasks.log',
        },
    },
    'loggers': {
        'superadmin.tasks': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

## 🧪 Testando o Sistema

### 1. Verificar se Schedules Foram Criados
```bash
python manage.py shell
```

```python
from django_q.models import Schedule
schedules = Schedule.objects.all()
for s in schedules:
    print(f"{s.name}: {s.schedule_type} - Próxima execução: {s.next_run}")
```

### 2. Executar Detecção Manualmente
```bash
python manage.py detect_security_violations
```

### 3. Verificar Violações Criadas
```bash
python manage.py shell
```

```python
from superadmin.models import ViolacaoSeguranca
violacoes = ViolacaoSeguranca.objects.all()
print(f"Total de violações: {violacoes.count()}")
for v in violacoes[:5]:
    print(f"- {v.tipo}: {v.descricao}")
```

## ⚠️ Troubleshooting

### Problema: Cluster não inicia
**Solução**: Verifique se há erros no settings.py:
```bash
python manage.py check
```

### Problema: Tarefas não executam
**Solução**: Verifique se o cluster está rodando:
```bash
ps aux | grep qcluster
```

### Problema: Erro de timeout
**Solução**: Aumente o timeout em `settings.py`:
```python
Q_CLUSTER = {
    'timeout': 600,  # 10 minutos
    'retry': 660,    # Deve ser > timeout
}
```

### Problema: Muitas tarefas falhando
**Solução**: Verifique os logs e ajuste `max_attempts`:
```python
Q_CLUSTER = {
    'max_attempts': 5,  # Tentar até 5 vezes
}
```

## 📈 Monitoramento

### Dashboard do Django-Q (Admin)
Acesse: `http://localhost:8000/admin/django_q/`

Você verá:
- **Schedules**: Tarefas agendadas
- **Tasks**: Histórico de execuções
- **Success/Failures**: Estatísticas

### Métricas Importantes
- Taxa de sucesso das tarefas
- Tempo médio de execução
- Número de violações detectadas por hora
- Erros recorrentes

## 🔐 Segurança

### Boas Práticas
1. **Logs**: Sempre monitore os logs para detectar problemas
2. **Alertas**: Configure alertas para falhas críticas
3. **Backup**: Faça backup regular do banco de dados
4. **Recursos**: Monitore uso de CPU/memória do cluster
5. **Atualizações**: Mantenha Django-Q atualizado

### Permissões
Apenas SuperAdmins devem ter acesso ao Django-Q Admin.

## 📚 Referências

- [Documentação Django-Q2](https://django-q2.readthedocs.io/)
- [Configuração de Schedules](https://django-q2.readthedocs.io/en/master/schedules.html)
- [Troubleshooting](https://django-q2.readthedocs.io/en/master/configure.html)

## 🎯 Próximos Passos

1. ✅ Django-Q instalado e configurado
2. ✅ Schedules criados
3. ⏳ Iniciar cluster em produção
4. ⏳ Configurar monitoramento de logs
5. ⏳ Implementar frontend de alertas
