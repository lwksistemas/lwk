# ⚡ Quick Start - Sistema de Backup

## 🚀 Início Rápido em 5 Minutos

### 1. ✅ Verificar Instalação

```bash
cd backend
source ../.venv/bin/activate
python manage.py check
```

**Resultado esperado:** `System check identified no issues (0 silenced).`

---

### 2. 📤 Testar Exportação Manual

#### Via Django Shell:
```bash
python manage.py shell
```

```python
from superadmin.models import Loja
from superadmin.backup_service import BackupService

# Buscar uma loja
loja = Loja.objects.first()
print(f"Loja: {loja.nome}")

# Exportar backup
service = BackupService()
result = service.exportar_loja(loja_id=loja.id, incluir_imagens=False)

if result['success']:
    print(f"✅ Backup criado: {result['arquivo_nome']}")
    print(f"   Tamanho: {result['tamanho_mb']:.2f} MB")
    print(f"   Registros: {result['total_registros']}")
    
    # Salvar arquivo
    with open(f"/tmp/{result['arquivo_nome']}", 'wb') as f:
        f.write(result['arquivo_bytes'])
    print(f"   Salvo em: /tmp/{result['arquivo_nome']}")
else:
    print(f"❌ Erro: {result['erro']}")
```

---

### 3. ⚙️ Configurar Backup Automático

```python
from superadmin.models import Loja, ConfiguracaoBackup
from datetime import time

# Buscar loja
loja = Loja.objects.first()

# Criar configuração
config = ConfiguracaoBackup.objects.create(
    loja=loja,
    backup_automatico_ativo=True,
    horario_envio=time(3, 0, 0),  # 03:00 AM
    frequencia='semanal',
    dia_semana=0,  # Segunda-feira
    incluir_imagens=False,
    manter_ultimos_n_backups=5
)

print(f"✅ Configuração criada para {loja.nome}")
print(f"   Frequência: {config.get_frequencia_display()}")
print(f"   Horário: {config.horario_envio}")
```

---

### 4. 📋 Ver Histórico

```python
from superadmin.models import HistoricoBackup

# Listar últimos 10 backups
backups = HistoricoBackup.objects.order_by('-created_at')[:10]

for backup in backups:
    print(f"{backup.loja.nome}: {backup.status_display}")
    print(f"  {backup.get_tamanho_formatado()} - {backup.total_registros} registros")
    print(f"  {backup.created_at.strftime('%d/%m/%Y %H:%M')}")
    print()
```

---

### 5. 🔧 Configurar Celery (Opcional)

#### Instalar:
```bash
pip install celery redis
```

#### Iniciar Redis:
```bash
redis-server
```

#### Iniciar Workers (em terminais separados):
```bash
# Terminal 1: Worker
celery -A config worker -l info

# Terminal 2: Beat (agendador)
celery -A config beat -l info
```

#### Testar Task:
```python
from superadmin.tasks import executar_backups_automaticos

# Executar manualmente
result = executar_backups_automaticos()
print(result)
```

---

## 📡 Endpoints da API

### Exportar Backup
```bash
curl -X POST \
  http://localhost:8000/api/superadmin/lojas/1/exportar_backup/ \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"incluir_imagens": false}' \
  --output backup.zip
```

### Configurar Backup Automático
```bash
curl -X PUT \
  http://localhost:8000/api/superadmin/lojas/1/atualizar_configuracao_backup/ \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "backup_automatico_ativo": true,
    "horario_envio": "03:00:00",
    "frequencia": "semanal",
    "dia_semana": 0,
    "manter_ultimos_n_backups": 5
  }'
```

### Ver Histórico
```bash
curl -X GET \
  "http://localhost:8000/api/superadmin/lojas/1/historico_backups/?limit=10" \
  -H "Authorization: Bearer SEU_TOKEN"
```

---

## 🐛 Troubleshooting Rápido

### Erro: "Loja não encontrada"
```python
# Criar loja de teste
from superadmin.models import Loja, TipoLoja, PlanoAssinatura
from django.contrib.auth.models import User

tipo = TipoLoja.objects.first()
plano = PlanoAssinatura.objects.first()
owner = User.objects.create_user('teste', 'teste@example.com', 'senha123')

loja = Loja.objects.create(
    nome='Loja Teste',
    tipo_loja=tipo,
    plano=plano,
    owner=owner,
    database_name='loja_teste'
)
```

### Erro: "Banco de dados não criado"
```python
loja.database_created = True
loja.save()
```

### Ver Logs
```bash
tail -f logs/django.log | grep backup
```

---

## 📚 Documentação Completa

- **Guia Completo:** `GUIA_USO_SISTEMA_BACKUP.md`
- **Documentação Técnica:** `SISTEMA_BACKUP_IMPLEMENTACAO_COMPLETA.md`
- **README:** `README_SISTEMA_BACKUP.md`

---

## ✅ Checklist Rápido

- [ ] Migrations aplicadas
- [ ] Sistema verificado (sem erros)
- [ ] Loja de teste criada
- [ ] Backup manual testado
- [ ] Configuração criada
- [ ] Histórico verificado
- [ ] (Opcional) Celery configurado

---

**Pronto! Sistema funcionando em 5 minutos!** 🎉
