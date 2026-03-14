# Relatório de Verificação de Órfãos - Sistema LWKSistemas

**Data:** 2026-03-14

## Resumo Executivo

Foram identificados e corrigidos órfãos em três áreas: **backend** (configuração de banco), **frontend** (componentes não utilizados) e **banco de dados** (tabelas incorretas no config).

---

## 1. BACKEND - Correções Aplicadas

### 1.1 `orfaos_config.py` - Tabelas Corrigidas

**Problema:** O arquivo referenciava tabelas inexistentes ou com estrutura incorreta.

| Removido/Corrigido | Motivo |
|--------------------|--------|
| `asaas_integration_lojaassinatura` | Tabela real é `loja_assinatura`; usa `loja_slug`, não `loja_id`. Tratada separadamente no signal e em `verificar_dados_orfaos` |
| `notificacoes_notificacao` | Modelo `Notification` não possui `loja_id` |
| `whatsapp_mensagemwhatsapp` | Modelo não existe |
| `whatsapp_templatewhatsapp` | Modelo não existe |
| `rules_regra` | Modelo `RegraAutomatica` não possui `loja_id` |
| `rules_execucaoregra` | Modelo não existe |
| `whatsapp_whatsapplog` | **Adicionado** - modelo `WhatsAppLog` existe e tem `loja_id` |

### 1.2 Comandos de Verificação Disponíveis

```bash
# Listar órfãos (sem remover)
cd backend && python manage.py limpar_orfaos --dry-run

# Executar limpeza
cd backend && python manage.py limpar_orfaos --execute

# Verificar dados com loja_id inválido
cd backend && python manage.py verificar_dados_orfaos

# Remover órfãos de loja_id
cd backend && python manage.py verificar_dados_orfaos --remover

# Validar configuração (verifica se todas tabelas com loja_id estão no config)
cd backend && python manage.py validar_config_orfaos
```

### 1.3 No Heroku

```bash
heroku run "cd backend && python manage.py limpar_orfaos --dry-run" --app lwksistemas
heroku run "cd backend && python manage.py verificar_dados_orfaos" --app lwksistemas
```

---

## 2. FRONTEND - Componentes Órfãos (Removidos em 2026-03-14)

| Arquivo | Status |
|---------|--------|
| `components/superadmin/financeiro/LojaFinanceiroCard.tsx` | ✅ Removido |
| `components/suporte/BotaoSuporte.tsx` | ✅ Removido |
| `components/tenant/store-selector.tsx` (StoreSelector) | ✅ Removido |
| `components/crm-vendas/KPICard.tsx` | ✅ Removido |
| `app/(dashboard)/loja/[slug]/dashboard/templates/servicos-modals-all.tsx` | ✅ Removido |

---

## 3. BANCO DE DADOS

### 3.1 Schemas PostgreSQL Órfãos

Schemas `loja_*` no banco sem loja correspondente em `superadmin_loja` são detectados por:

- `python manage.py limpar_orfaos --dry-run` (item 2)
- `backend/analisar_schemas_heroku.py`
- `backend/limpar_schemas_orfaos.py`

### 3.2 Tabelas que Podem Não Existir no Heroku

Algumas tabelas em `TABELAS_LOJA_ID_DEFAULT` podem não existir no schema `public` do Heroku (ex.: CRM em schemas tenant). O safety net no signal usa `try/except` por tabela, então falhas são apenas logadas e não interrompem a exclusão.

### 3.3 LojaAssinatura (loja_slug)

A tabela `loja_assinatura` usa `loja_slug`, não `loja_id`. É tratada por:

- **Signal:** `LojaAssinatura.objects.filter(loja_slug=instance.slug).delete()`
- **verificar_dados_orfaos:** bloco específico para `loja_assinatura` com `loja_slug`

---

## 4. Arquivos de Backup/Media Órfãos

O signal `delete_all_loja_data` chama `_limpar_arquivos_orfaos_loja()` que remove:

- `backups/{slug}/` - diretório de backups da loja
- `media/nfe_restaurante/loja_{id}_*` - arquivos NF-e

---

## 5. Próximos Passos Recomendados

1. **Backend:** Rodar `limpar_orfaos --dry-run` e `verificar_dados_orfaos` no Heroku para validar o estado atual
2. **Frontend:** ✅ 5 componentes órfãos removidos
3. **Validação:** Executar `validar_config_orfaos` após migrations para garantir que novas tabelas com `loja_id` sejam incluídas no config
