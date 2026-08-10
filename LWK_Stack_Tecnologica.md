# LWK Sistemas — Stack Tecnológica

**Atualizado em 10/08/2026**

## Infraestrutura

| Camada | Tecnologia | Versão |
|--------|-----------|--------|
| Servidor principal | Magalu Cloud SP (BV8-16-150) | Ubuntu 24.04 LTS |
| Servidor de mídia | Magalu Cloud SP (BV1-2-40) | Ubuntu 24.04 LTS |
| Container | Docker + Compose | 29.1 / 2.40 |
| Proxy/SSL | Nginx + Certbot (Let's Encrypt) | 1.24 |
| Backend runtime | Python | 3.13 |
| Frontend runtime | Node.js | 22 LTS |

## Backend

| Tecnologia | Versão | Função |
|-----------|--------|--------|
| Django | 6.1 | Framework web Python |
| Django REST Framework | 3.18.0 | API RESTful |
| PostgreSQL | 18.4 | Banco de dados multi-tenant |
| Redis | 7.4 | Cache e filas |
| django-q2 | 1.10 | Task queue (workers) |
| Gunicorn | 26.0 | Servidor WSGI |
| xmlsec | 1.3 | Assinatura digital NFS-e |
| lxml | 6.1 | Processamento XML |

## Frontend

| Tecnologia | Versão | Função |
|-----------|--------|--------|
| Next.js | 16.3.0 | Framework React (App Router) |
| React | 19.2.8 | Biblioteca de UI |
| TypeScript | 7.0.2 | Tipagem estática (versão instalada no frontend) |
| Tailwind CSS | 4.3.3 | Estilização |

## Integrações

| Serviço | Função | Hospedagem |
|---------|--------|-----------|
| Servidor de Mídia | Upload imagens/PDFs (substituiu Cloudinary) | Magalu SP (201.23.87.251) |
| Evolution API | WhatsApp (mensagens, notificações) | Magalu SP (mesmo servidor) |
| Asaas | Cobranças, boletos, PIX | API externa |
| Resend | Email transacional | API externa |
| Memed | Prescrições médicas | API externa |
| ISSNet Nacional | NFS-e (Ribeirão Preto) | Webservice prefeitura |

## Arquitetura

```
┌─────────────────────────────────────────────────────────────────┐
│              Magalu Cloud SP — 201.23.81.50                       │
│              8 vCPU · 16 GB RAM · 150 GB                         │
│                                                                  │
│  Nginx (SSL Let's Encrypt — auto-renova)                         │
│    ├── lwksistemas.com.br      → Next.js :3000 (produção)        │
│    ├── beta.lwksistemas.com.br → Next.js :3001 (staging)         │
│    ├── api.lwksistemas.com.br  → Django/Gunicorn :8080           │
│    └── evolution.lwksistemas.com.br → Evolution API :8081        │
│                                                                  │
│  Docker Compose:                                                  │
│    ├── frontend       (Next.js 16 standalone — branch main)      │
│    ├── frontend-beta  (Next.js 16 standalone — branch staging)   │
│    ├── backend        (Django 6 + Gunicorn, 4 workers)           │
│    ├── worker         (django-q2, 4 processos)                   │
│    ├── evolution      (WhatsApp API v2.3.7)                      │
│    ├── postgres       (18-bookworm)                              │
│    └── redis          (7-alpine)                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│              Magalu Cloud SP — 201.23.87.251                       │
│              1 vCPU · 2 GB RAM · 40 GB                            │
│                                                                  │
│  Nginx (SSL Let's Encrypt)                                        │
│    └── media.lwksistemas.com.br                                  │
│          ├── GET  /files/{cnpj}/{folder}/{file}  (servir imagem) │
│          ├── POST /upload/{cnpj}/                (upload)        │
│          └── GET  /health                        (status)        │
│                                                                  │
│  Estrutura de pastas:                                             │
│    /storage/{cnpj_cpf}/fotos|docs|avatars|recibos|contratos/     │
│    /storage/superadmin/...   (homepage, login-config do sistema) │
│    /storage/suporte/...      (uploads do perfil suporte s/ loja) │
└─────────────────────────────────────────────────────────────────┘
```

## Performance

| Métrica | Antes (Railway + Vercel) | Agora (Magalu SP) |
|---------|------------------------|-------------------|
| Latência API | ~200ms (EUA→BR) | ~5-20ms (local SP) |
| Build frontend | ~75s (Vercel) | ~75s (Docker) |
| Cold start | 1-3s (serverless) | 0ms (sempre quente) |
| Uptime | 99.9% (Railway SLA) | depende de nós |

## Deploy

```bash
# Produção (branch main)
ssh deploy@201.23.81.50 'cd /opt/lwk-erp && git pull && docker compose -f docker-compose.prod.yml up -d --build'

# Beta (branch staging)
ssh deploy@201.23.81.50 'cd /opt/lwk-erp && ./deploy-beta.sh'
```

## Backup

- Automático: cron diário às 3h (`/opt/lwk-erp/backup.sh`)
- Retenção: 7 dias locais
- Banco: pg_dump com formato custom (comprimido)

## Custo Mensal

| Item | Custo |
|------|-------|
| Magalu BV8-16-150 (sistema) | ~R$ 430 |
| Magalu BV1-2-40 (mídia) | ~R$ 70 |
| Domínio (Registro.br) | ~R$ 4 |
| **Total** | **~R$ 504/mês** |

**Economia vs anterior:** Railway + Vercel Pro = ~R$ 650/mês → **economia de ~R$ 150/mês**
**Ganho adicional:** latência 10x menor, controle total, SSH direto, sem limites de build
