# Backup e restore — validação operacional

Cada loja usa schema PostgreSQL isolado (`loja_*`). Export/import via `BackupService` (CSV em ZIP).

## Verificação (somente leitura)

```bash
# Todas as lojas ativas
python manage.py audit_backup_lojas

# Uma loja
python manage.py audit_backup_lojas --slug novaimagem

# Testa exportação em memória (não grava arquivo)
python manage.py audit_backup_lojas --slug novaimagem --dry-export

# Valida ZIP antes de importar na UI
python manage.py audit_backup_lojas --slug novaimagem --validar-arquivo /caminho/backup.zip
```

Checa: banco criado, tabelas no schema, último backup concluído no histórico.

## Export (produção)

- UI: `/loja/[slug]/configuracoes/backup` ou superadmin
- API: `exportar_backup` no ViewSet da loja
- Automático: `lwks-cron` + `ConfiguracaoBackup`

Arquivos gerados: e-mail ou storage local (`backend/backups/` — gitignored).

## Restore (destrutivo)

- UI/API: `importar_backup` — **substitui dados** do schema da loja
- Só aceita backup da **mesma loja** (id ou slug)
- ZIP deve conter `_metadata.json` + CSVs por tabela

**Checklist antes de importar:**

1. `audit_backup_lojas --validar-arquivo … --slug …`
2. Confirmar ambiente (beta vs produção)
3. Preferir janela de manutenção
4. Ter backup recente **antes** de importar outro ZIP

## Restore de schema PostgreSQL (DR avançado)

Para disaster recovery total (fora do ZIP CSV):

```bash
pg_dump --schema=loja_CNPJ ... > loja.sql
# restore em schema vazio após recriar loja
```

O fluxo CSV/ZIP do LWK é o caminho **suportado pela aplicação**; `pg_dump` por schema é fallback de infra.

## Railway

```bash
railway run python manage.py audit_backup_lojas --slug novaimagem --dry-export
```
