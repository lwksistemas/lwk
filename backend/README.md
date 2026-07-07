# LWK Sistemas — Backend

API REST multi-tenant em Django 4.2 + Django REST Framework para gestão de lojas, CRM, clínicas e serviços.

## Stack

| Componente | Tecnologia |
|-----------|-----------|
| Framework | Django 4.2 + DRF 3.15 |
| Banco de dados | PostgreSQL (schemas isolados por tenant) |
| Cache | Redis (django-redis) |
| Task queue | django-q |
| Auth | JWT (simplejwt) com sessão única |
| Deploy | Railway (Docker multi-role) |
| Email | Resend API (fallback: Gmail SMTP) |

## Estrutura de Diretórios

```
backend/
├── config/           # Settings, URLs, middleware, WSGI
├── core/             # Biblioteca compartilhada (mixins, serializers, throttling, retry)
├── superadmin/       # Gestão de lojas, planos, billing, backup
├── tenants/          # Middleware e modelos de multi-tenancy
├── crm_vendas/       # CRM: leads, oportunidades, propostas, financeiro
├── clinica_estetica/ # Clínica: agendamentos, consultas, financeiro
├── clinica_beleza/   # Clínica de beleza (salão, agenda, lembretes)
├── cabeleireiro/     # App cabeleireiro/salão
├── asaas_integration/# Integração Asaas (boletos, PIX, webhook)
├── nfse_integration/ # Emissão de NFS-e
├── whatsapp/         # WhatsApp Cloud API (mensagens, lembretes)
├── notificacoes/     # Notificações in-app
├── push/             # Push notifications (VAPID)
├── homepage/         # Página pública da loja
├── scripts/          # Scripts utilitários e release
└── tests/            # Testes de segurança globais
```

## Setup Local

```bash
# 1. Criar virtualenv
python3 -m venv .venv && source .venv/bin/activate

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com DATABASE_URL, REDIS_URL, etc.

# 4. Rodar migrations
python manage.py migrate

# 5. Criar superuser
python manage.py createsuperuser

# 6. Rodar servidor
python manage.py runserver
```

## Variáveis de Ambiente Essenciais

| Variável | Descrição |
|----------|-----------|
| `DATABASE_URL` | URI PostgreSQL (obrigatório em produção) |
| `REDIS_URL` | URI Redis para cache e queue |
| `SECRET_KEY` | Chave secreta Django |
| `RESEND_API_KEY` | API key Resend para emails |
| `WEB_CONCURRENCY` | Número de workers Gunicorn (default: 4) |
| `LWK_PROCESS_ROLE` | `web` / `worker` / `cron` |

## Multi-Tenancy

Cada loja opera em um **schema PostgreSQL isolado**. O isolamento funciona em 3 camadas:

1. **Middleware** (`tenants/middleware.py`) — detecta tenant pelo header/URL e configura `search_path`
2. **Manager** (`core/mixins.py: LojaIsolationManager`) — filtra automaticamente por `loja_id`
3. **Router** (`config/db_router.py`) — direciona queries para o schema correto

## Deploy (Railway)

O `Dockerfile.railway` suporta 3 roles via `LWK_PROCESS_ROLE`:

- **web** — Gunicorn (API HTTP)
- **worker** — django-q (tasks assíncronas)
- **cron** — `executar_cron_lwks` a cada 15 min (lembretes, backups, cobrança)

## Testes

```bash
# Rodar todos os testes
pytest

# Testes específicos do CRM
pytest crm_vendas/tests/

# Testes de segurança
pytest tests/
```
