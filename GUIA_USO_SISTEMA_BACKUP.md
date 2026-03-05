# 📘 Guia de Uso - Sistema de Backup das Lojas

## 🎯 Visão Geral

Este guia explica como usar o sistema de backup implementado para fazer backup e restauração de dados das lojas.

---

## 🚀 Início Rápido

### 1. Executar Migrations

Primeiro, crie as tabelas no banco de dados:

```bash
cd backend
python manage.py makemigrations superadmin --name add_backup_models
python manage.py migrate
```

### 2. Testar Backup Manual

Acesse o dashboard do SuperAdmin e teste a exportação manual:

```bash
# Via API (usando curl)
curl -X POST \
  http://localhost:8000/api/superadmin/lojas/1/exportar_backup/ \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"incluir_imagens": false}' \
  --output backup.zip
```

---

## 📤 Exportar Backup Manual

### Via Dashboard (Frontend - a implementar)

1. Acesse o dashboard do SuperAdmin
2. Vá em "Gerenciar Lojas"
3. Clique no card da loja desejada
4. Clique em "⚙️ Backup"
5. Clique em "📤 Exportar Backup"
6. O arquivo ZIP será baixado automaticamente

### Via API

**Endpoint:** `POST /api/superadmin/lojas/{id}/exportar_backup/`

**Request:**
```json
{
  "incluir_imagens": false
}
```

**Response:** Arquivo ZIP para download

**Exemplo Python:**
```python
import requests

response = requests.post(
    'http://localhost:8000/api/superadmin/lojas/1/exportar_backup/',
    headers={'Authorization': 'Bearer SEU_TOKEN'},
    json={'incluir_imagens': False}
)

with open('backup.zip', 'wb') as f:
    f.write(response.content)

print(f"Backup salvo: backup.zip")
print(f"Total de registros: {response.headers['X-Total-Registros']}")
print(f"Tamanho: {response.headers['X-Tamanho-MB']} MB")
```

---

## 📥 Importar Backup

### Via Dashboard (Frontend - a implementar)

1. Acesse o dashboard do SuperAdmin
2. Vá em "Gerenciar Lojas"
3. Clique no card da loja desejada
4. Clique em "⚙️ Backup"
5. Clique em "📥 Importar Backup"
6. Selecione o arquivo ZIP
7. Confirme a importação

⚠️ **ATENÇÃO:** A importação substitui todos os dados existentes!

### Via API

**Endpoint:** `POST /api/superadmin/lojas/{id}/importar_backup/`

**Request:** Multipart form-data com arquivo

**Exemplo Python:**
```python
import requests

with open('backup.zip', 'rb') as f:
    files = {'arquivo': f}
    response = requests.post(
        'http://localhost:8000/api/superadmin/lojas/1/importar_backup/',
        headers={'Authorization': 'Bearer SEU_TOKEN'},
        files=files
    )

result = response.json()
print(f"Sucesso: {result['success']}")
print(f"Registros importados: {result['total_registros_importados']}")
```

---

## ⚙️ Configurar Backup Automático

### Via Dashboard (Frontend - a implementar)

1. Acesse o dashboard do SuperAdmin
2. Vá em "Gerenciar Lojas"
3. Clique no card da loja desejada
4. Clique em "⚙️ Backup"
5. Configure:
   - ✅ Ativar backup automático
   - 🕐 Horário de envio (ex: 03:00)
   - 📅 Frequência (diário/semanal/mensal)
   - 📧 Email será enviado automaticamente
6. Clique em "Salvar"

### Via API

**Endpoint:** `PUT /api/superadmin/lojas/{id}/atualizar_configuracao_backup/`

**Request:**
```json
{
  "backup_automatico_ativo": true,
  "horario_envio": "03:00:00",
  "frequencia": "semanal",
  "dia_semana": 0,
  "incluir_imagens": false,
  "manter_ultimos_n_backups": 5
}
```

**Exemplo Python:**
```python
import requests

config = {
    'backup_automatico_ativo': True,
    'horario_envio': '03:00:00',
    'frequencia': 'semanal',
    'dia_semana': 0,  # Segunda-feira
    'incluir_imagens': False,
    'manter_ultimos_n_backups': 5
}

response = requests.put(
    'http://localhost:8000/api/superadmin/lojas/1/atualizar_configuracao_backup/',
    headers={'Authorization': 'Bearer SEU_TOKEN'},
    json=config
)

result = response.json()
print(f"Configuração atualizada: {result['success']}")
```

---

## 📋 Ver Histórico de Backups

### Via API

**Endpoint:** `GET /api/superadmin/lojas/{id}/historico_backups/`

**Query params:**
- `limit`: Número de registros (padrão: 20)
- `tipo`: Filtrar por tipo (manual, automatico)
- `status`: Filtrar por status (processando, concluido, erro)

**Exemplo Python:**
```python
import requests

response = requests.get(
    'http://localhost:8000/api/superadmin/lojas/1/historico_backups/',
    headers={'Authorization': 'Bearer SEU_TOKEN'},
    params={'limit': 10, 'tipo': 'automatico'}
)

result = response.json()
print(f"Total de backups: {result['count']}")

for backup in result['historico']:
    print(f"- {backup['arquivo_nome']} ({backup['tamanho_formatado']})")
    print(f"  Status: {backup['status_display']}")
    print(f"  Data: {backup['created_at']}")
```

---

## 📧 Reenviar Backup por Email

### Via API

**Endpoint:** `POST /api/superadmin/lojas/{id}/reenviar_backup_email/`

**Request (opcional):**
```json
{
  "historico_id": 123
}
```

Se não fornecer `historico_id`, envia o último backup concluído.

**Exemplo Python:**
```python
import requests

response = requests.post(
    'http://localhost:8000/api/superadmin/lojas/1/reenviar_backup_email/',
    headers={'Authorization': 'Bearer SEU_TOKEN'},
    json={}  # Envia último backup
)

result = response.json()
print(f"Email enviado: {result['message']}")
```

---

## 🔧 Configurar Celery (Backup Automático)

### 1. Instalar Dependências

```bash
pip install celery redis
```

### 2. Configurar Redis

```bash
# Instalar Redis
sudo apt-get install redis-server

# Iniciar Redis
redis-server
```

### 3. Criar arquivo celery.py

Crie `backend/celery.py`:

```python
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

app = Celery('backend')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Configurar agendamento
app.conf.beat_schedule = {
    'executar-backups-automaticos': {
        'task': 'superadmin.tasks.executar_backups_automaticos',
        'schedule': crontab(minute=0),  # A cada hora
        'options': {
            'expires': 3600,
        }
    },
}

# Configurar retry
app.conf.task_annotations = {
    'superadmin.tasks.processar_backup_loja': {
        'rate_limit': '10/m',
        'time_limit': 1800,
        'max_retries': 3,
    },
}
```

### 4. Atualizar settings.py

Adicione em `backend/settings.py`:

```python
# Celery Configuration
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'America/Sao_Paulo'
```

### 5. Iniciar Workers

Em terminais separados:

```bash
# Terminal 1: Worker
celery -A backend worker -l info

# Terminal 2: Beat (agendador)
celery -A backend beat -l info
```

---

## 📊 Monitorar Backups

### Ver Logs

```bash
# Logs do Django
tail -f backend/logs/django.log | grep backup

# Logs do Celery
tail -f celery.log | grep backup
```

### Verificar Status

```python
from superadmin.models import ConfiguracaoBackup, HistoricoBackup

# Ver configurações ativas
configs = ConfiguracaoBackup.objects.filter(backup_automatico_ativo=True)
for config in configs:
    print(f"{config.loja.nome}: {config.get_frequencia_display()}")
    print(f"  Último backup: {config.ultimo_backup}")
    print(f"  Total: {config.total_backups_realizados}")

# Ver últimos backups
backups = HistoricoBackup.objects.order_by('-created_at')[:10]
for backup in backups:
    print(f"{backup.loja.nome}: {backup.status_display}")
    print(f"  {backup.get_tamanho_formatado()} - {backup.total_registros} registros")
```

---

## 🐛 Troubleshooting

### Erro: "Banco de dados da loja não foi criado"

**Solução:** Crie o banco isolado da loja primeiro:

```python
from superadmin.models import Loja

loja = Loja.objects.get(id=1)
# Criar banco via endpoint ou comando
```

### Erro: "Arquivo ZIP inválido ou corrompido"

**Solução:** Verifique se o arquivo não foi corrompido durante o download:

```bash
# Testar integridade do ZIP
unzip -t backup.zip
```

### Erro: "Erro ao enviar email"

**Solução:** Verifique configurações de email no `settings.py`:

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'seu-email@gmail.com'
EMAIL_HOST_PASSWORD = 'sua-senha'
DEFAULT_FROM_EMAIL = 'seu-email@gmail.com'
```

### Celery não está executando backups

**Solução:** Verifique se Beat está rodando:

```bash
# Ver processos Celery
ps aux | grep celery

# Reiniciar Beat
celery -A backend beat -l info
```

---

## 📚 Exemplos Práticos

### Exemplo 1: Backup Diário às 3h da manhã

```python
config = {
    'backup_automatico_ativo': True,
    'horario_envio': '03:00:00',
    'frequencia': 'diario',
    'incluir_imagens': False,
    'manter_ultimos_n_backups': 7  # Mantém 1 semana
}
```

### Exemplo 2: Backup Semanal (Segunda-feira)

```python
config = {
    'backup_automatico_ativo': True,
    'horario_envio': '02:00:00',
    'frequencia': 'semanal',
    'dia_semana': 0,  # Segunda-feira
    'incluir_imagens': False,
    'manter_ultimos_n_backups': 4  # Mantém 1 mês
}
```

### Exemplo 3: Backup Mensal (dia 1)

```python
config = {
    'backup_automatico_ativo': True,
    'horario_envio': '01:00:00',
    'frequencia': 'mensal',
    'dia_mes': 1,
    'incluir_imagens': True,
    'manter_ultimos_n_backups': 12  # Mantém 1 ano
}
```

---

## ✅ Checklist de Uso

### Configuração Inicial
- [ ] Executar migrations
- [ ] Instalar Celery e Redis
- [ ] Configurar celery.py
- [ ] Iniciar workers
- [ ] Testar backup manual

### Para Cada Loja
- [ ] Configurar backup automático
- [ ] Definir frequência
- [ ] Definir horário
- [ ] Testar envio de email
- [ ] Verificar histórico

### Manutenção
- [ ] Monitorar logs
- [ ] Verificar espaço em disco
- [ ] Testar restauração periodicamente
- [ ] Revisar configurações

---

## 🆘 Suporte

Em caso de dúvidas ou problemas:

1. Verifique os logs: `backend/logs/django.log`
2. Consulte a documentação técnica: `SISTEMA_BACKUP_IMPLEMENTACAO_COMPLETA.md`
3. Revise o código: Todos os arquivos estão bem documentados

---

**Desenvolvido com ❤️ para facilitar o gerenciamento de backups**
