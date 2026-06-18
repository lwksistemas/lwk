# Observabilidade — Sentry (opcional)

O Sentry é **opcional**: sem `SENTRY_DSN` no Railway, nada muda no comportamento atual.

## Backend (Railway)

Variáveis em `lwks-backend` e `lwks-worker`:

```env
SENTRY_DSN=https://xxx@o000.ingest.sentry.io/000
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.05
LWK_BUILD=release-tag-20260618
```

Opcional:

```env
SENTRY_RELEASE=1.0.0
SENTRY_PROFILES_SAMPLE_RATE=0
```

1. Criar projeto **Django** em [sentry.io](https://sentry.io)
2. Copiar DSN → `SENTRY_DSN`
3. Redeploy `lwks-backend` + `lwks-worker`

Erros 500, exceções não tratadas e logs `ERROR` passam a aparecer no Sentry.

## Frontend (futuro)

Quando quiser monitorar o Next.js:

```env
NEXT_PUBLIC_SENTRY_DSN=...
```

Recomendado: `@sentry/nextjs` (wizard oficial). Não é obrigatório para o backend já reportar falhas de API.

## Health check existente

`GET /api/superadmin/health/` continua sendo a primeira linha de monitoramento:

- `status`, `build`, `task_queue`, `evolution_available`

Configure alertas no Sentry para:

- Spike de erros 5xx
- `task_queue.workers_alive == 0` com fila > 0 (via cron externo ou Railway metrics)

## Backup / restore

Ver `docs/BACKUP_RESTORE_VALIDACAO.md` e:

```bash
python manage.py audit_backup_lojas
python manage.py audit_backup_lojas --slug novaimagem --dry-export
```
