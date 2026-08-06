# LWK Sistemas — Stack Tecnológica

**Atualizado em 06/08/2026**

## Infraestrutura

| Camada | Tecnologia | Versão Atual | Última Disponível | Status |
|--------|-----------|-------------|-------------------|--------|
| Servidor | Magalu Cloud SP (VM BV8-16-150) | Ubuntu 24.04 | Ubuntu 24.04 | ✅ Atual |
| Container | Docker + Compose | 29.1.3 / 2.40.3 | ~29.x | ✅ Atual |
| Proxy/SSL | Nginx + Certbot | 1.24 / Let's Encrypt | 1.26 | ⚠️ Atualizar |
| Backend runtime | Python | 3.12.13 | 3.14 | ⚠️ 3.12 OK (LTS suportado) |
| Frontend runtime | Node.js | 20.20.2 | 22 LTS | ⚠️ 20 OK (LTS até 04/2026) |

## Backend

| Tecnologia | Versão Atual | Última Disponível | Status |
|-----------|-------------|-------------------|--------|
| Django | 6.0.7 | 6.1 (ago/2026) + 6.0.8 (segurança) | ⚠️ Atualizar para 6.0.8 |
| Django REST Framework | 3.17.1 | 3.17.x | ✅ Atual |
| PostgreSQL | 16.14 | 18.x | ⚠️ Pode atualizar (Railway usava 18) |
| Redis | 7.4.10 | 7.4.x | ✅ Atual |
| django-q2 | 1.10.0 | 1.10.x | ✅ Atual |
| Gunicorn | 23.0.0 | 23.x | ✅ Atual |
| lxml | 6.1.0 | 6.x | ✅ Atual |
| xmlsec | 1.3.17 | 1.3.x | ✅ Atual |
| cryptography | 45+ | 46.x | ✅ Atual |

## Frontend

| Tecnologia | Versão Atual | Última Disponível | Status |
|-----------|-------------|-------------------|--------|
| Next.js | 16.2.10 | 16.2.x | ✅ Atual |
| React | 19.2.0 | 19.2.x | ✅ Atual |
| TypeScript | 6.0.3 | 6.x | ✅ Atual |
| Tailwind CSS | 4.3.2 | 4.x | ✅ Atual |

## Integrações

| Serviço | Função | Hospedagem |
|---------|--------|-----------|
| Asaas | Cobranças, boletos, PIX | API externa (asaas.com) |
| Evolution API | WhatsApp (mensagens, notificações) | **Magalu SP** (v2.3.7) |
| Resend | Email transacional | API externa (resend.com) |
| Cloudinary | Upload de imagens | API externa (cloudinary.com) |
| Memed | Prescrições médicas | API externa (memed.com.br) |
| ISSNet Nacional | NFS-e (Ribeirão Preto) | Webservice prefeitura |

## Arquitetura (pós-migração 06/08/2026)

```
                    ┌─────────────────────────────────────────┐
                    │        Magalu Cloud SP (201.23.81.50)    │
                    │        Ubuntu 24.04 · 8vCPU · 16GB      │
                    │                                         │
  Internet ──443──► │  Nginx (SSL Let's Encrypt)              │
                    │    ├── lwksistemas.com.br → Next.js:3000 │
                    │    ├── api.lwksistemas.com.br → Django:8080 │
                    │    ├── beta.lwksistemas.com.br → Next.js │
                    │    └── evolution.lwksistemas.com.br → Evo:8081 │
                    │                                         │
                    │  Docker Compose:                         │
                    │    ├── frontend (Next.js 16 standalone)  │
                    │    ├── backend (Django 6 + Gunicorn)     │
                    │    ├── worker (django-q2, 4 workers)     │
                    │    ├── evolution (WhatsApp API v2.3.7)   │
                    │    ├── postgres (16-alpine)              │
                    │    └── redis (7-alpine)                  │
                    └─────────────────────────────────────────┘
```

## Deploy

```bash
ssh deploy@201.23.81.50
cd /opt/lwk-erp
git pull origin main
docker compose -f docker-compose.prod.yml up -d --build
```

## Backup

- Automático: cron diário às 3h (`backup.sh`)
- Retenção: 7 dias locais
- Manual: `./backup.sh`

## Custo Mensal

| Item | Custo |
|------|-------|
| Magalu BV8-16-150 | ~R$ 430/mês |
| Domínio + DNS | ~R$ 40/ano |
| **Total** | **~R$ 450/mês** |

Anterior: Railway (~R$ 200-300) + Vercel Pro (~$40-100/mês) = R$ 500-800/mês
