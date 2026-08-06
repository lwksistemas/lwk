# LWK Sistemas — Estrutura do Projeto

**Atualizado em 06/08/2026**

## Stack Tecnológica

| Camada | Tecnologia | Versão |
|--------|-----------|--------|
| Backend | Django + DRF | 6.0.8 + 3.17.1 |
| Frontend | Next.js + React + TypeScript | 16.2.10 + 19.2 + 7.0.2 |
| Estilização | Tailwind CSS | 4.3.2 |
| Banco de dados | PostgreSQL (Docker local) | 18 |
| Cache/Filas | Redis (Docker local) | 7.4 |
| WhatsApp | Evolution API | 2.3.7 |
| Deploy | Magalu Cloud SP (Docker Compose) | Ubuntu 24.04 |
| Runtime | Python 3.13 / Node.js 22 | LTS |

## Arquitetura

- **Multi-tenant**: cada loja possui schema PostgreSQL próprio (`loja_<cpf_cnpj>`)
- **Isolamento**: models com `LojaIsolationMixin` + `LojaIsolationManager`
- **Apps por tipo de loja**: clinica_beleza, crm_vendas, cabeleireiro, hotel, restaurante
- **Service layer**: lógica de negócio em `*_service.py`, não em views/serializers
- **API RESTful**: DRF com APIView, GetObjectMixin, paginação retrocompatível

## Estrutura de Diretórios

```
lwksistemas/
├── backend/                    # Django (API, models, services, migrations)
│   ├── config/                 # Settings Django (settings_production.py)
│   ├── core/                   # Middlewares, mixins, utilitários, encryption, media_storage
│   ├── superadmin/             # Gestão de lojas, usuários, planos
│   ├── clinica_beleza/         # App clínica (consultas, recibos, agenda)
│   ├── crm_vendas/             # CRM de vendas (leads, propostas, contratos)
│   ├── cabeleireiro/           # App cabeleireiro
│   ├── hotel/                  # App hotel
│   ├── restaurante/            # App restaurante
│   ├── asaas_integration/      # Integração financeira (cobranças, NFS-e config)
│   ├── nfse_integration/       # Emissão NFS-e (ISSNet, Nacional, Asaas)
│   ├── agenda_base/            # Agenda compartilhada entre apps
│   ├── whatsapp/               # Integração WhatsApp (Evolution)
│   ├── tenants/                # Middleware multi-tenant
│   └── scripts/                # Scripts utilitários (worker, release, validação)
├── frontend/                   # Next.js 16 (App Router)
│   ├── app/                    # Páginas e rotas (App Router)
│   │   └── (dashboard)/        # Layout autenticado
│   │       └── loja/[slug]/    # Páginas por loja (clinica, crm, etc)
│   ├── components/             # Componentes React por módulo
│   ├── contexts/               # Context providers (auth, config, tema)
│   ├── hooks/                  # Custom hooks por domínio
│   └── lib/                    # Utilitários, API client, helpers
├── docker-compose.prod.yml     # Compose de produção (Magalu)
├── Dockerfile.magalu           # Dockerfile backend (Python 3.13)
├── Dockerfile.frontend         # Dockerfile frontend (Node 22, standalone)
├── deploy.sh                   # Script de deploy produção
├── deploy-beta.sh              # Script de deploy beta (staging)
├── backup.sh                   # Script de backup Postgres
├── requirements.txt            # Dependências raiz (compartilhadas)
└── .github/workflows/          # CI/CD (security audit)
```

## Infraestrutura (Magalu Cloud SP)

```
Servidor principal: 201.23.81.50 (8 vCPU, 16GB RAM, 150GB disco)
OS: Ubuntu 24.04 LTS
Usuário deploy: deploy (SSH por chave)

Docker Compose (/opt/lwk-erp/docker-compose.prod.yml):
  ├── postgres      (18-bookworm, porta 5432 local)
  ├── redis         (7-alpine, porta 6379 local)
  ├── backend       (Django/Gunicorn, porta 8080)
  ├── worker        (django-q2, 4 workers)
  ├── frontend      (Next.js standalone, porta 3000 — branch main)
  ├── frontend-beta (Next.js standalone, porta 3001 — branch staging)
  ├── evolution     (WhatsApp API v2.3.7, porta 8081)
  └── (volumes: pgdata, redisdata, media, staticfiles)

Nginx (proxy reverso + SSL):
  ├── lwksistemas.com.br           → frontend:3000
  ├── www.lwksistemas.com.br       → frontend:3000
  ├── api.lwksistemas.com.br       → backend:8080
  ├── beta.lwksistemas.com.br      → frontend-beta:3001
  └── evolution.lwksistemas.com.br → evolution:8081

Servidor de mídia: 201.23.87.251 (1 vCPU, 2GB RAM, 40GB disco)
  └── media.lwksistemas.com.br     → Flask API :9000 + Nginx (arquivos estáticos)

SSL: Let's Encrypt (auto-renova via Certbot)
Backup: cron diário 3h → /opt/lwk-erp/backups/ (7 dias retenção)
```

## Fluxo de Deploy

```bash
# Na máquina local ou CI:
ssh deploy@201.23.81.50
cd /opt/lwk-erp
git pull origin main
docker compose -f docker-compose.prod.yml up -d --build

# Ou usar o script:
./deploy.sh
```

## Domínios e DNS (Registro.br)

| Tipo | Nome | Destino |
|------|------|---------|
| A | lwksistemas.com.br | 201.23.81.50 |
| A | api.lwksistemas.com.br | 201.23.81.50 |
| A | www.lwksistemas.com.br | 201.23.81.50 |
| A | beta.lwksistemas.com.br | 201.23.81.50 |
| A | evolution.lwksistemas.com.br | 201.23.81.50 |
| MX | lwksistemas.com.br | inbound-smtp.sa-east-1.amazonaws.com |
| TXT | _dmarc.lwksistemas.com.br | v=DMARC1; p=none; |
| MX | send.lwksistemas.com.br | feedback-smtp.sa-east-1.amazonses.com |
| TXT | send.lwksistemas.com.br | v=spf1 include:amazonses.com ~all |

## Padrões de Código

### Backend
- Views: usar `APIView` com `GetObjectMixin` (de `views_base.py`)
- Service layer: lógica de negócio em `*_service.py`
- Mapeamento de campos: usar `map_field_names()` de `views_base.py`
- Resolução de loja: usar `resolve_loja_id_from_request()`
- Paginação: usar `paginate_queryset()` de `pagination.py`

### Frontend
- Componentes: `"use client"` no topo de páginas interativas
- Formulários grandes: página dedicada (não modal)
- Busca em listas: campo input + resultados como botões
- Cores: usar cor temática do tipo de loja

## Convenções de Commit

```
feat(modulo): nova funcionalidade
fix(modulo): correção de bug
refactor(modulo): refatoração sem mudança de comportamento
perf(modulo): otimização de performance
```

## Integrações Externas

| Serviço | Função | Variáveis |
|---------|--------|-----------|
| Asaas | Cobranças/boletos/PIX | ASAAS_API_KEY, ASAAS_WEBHOOK_TOKEN |
| Resend | Email transacional | RESEND_API_KEY |
| Evolution | WhatsApp | EVOLUTION_API_URL, EVOLUTION_API_KEY |
| Cloudinary | Upload imagens | CLOUDINARY_* |
| Memed | Prescrições médicas | MEMED_API_KEY_PROD, MEMED_SECRET_KEY_PROD |
| Google Calendar | Sincronização agenda | GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET |
| ISSNet Nacional | NFS-e Ribeirão Preto | Certificado A1 (.pfx) no banco |
