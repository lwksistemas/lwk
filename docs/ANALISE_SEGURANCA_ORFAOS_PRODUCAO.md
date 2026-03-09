# Análise de Segurança, Órfãos e Produção

**Ambientes:** Heroku, Render, Vercel  
**Objetivo:** Garantir que não existam arquivos, registros ou nomes órfãos após exclusões.

---

## 1. Resumo das Correções Implementadas

### 1.1 Arquivos órfãos – prevenção

| Tipo | Local | Correção |
|------|-------|----------|
| **Backups** | `backups/{slug}/` | Signal `pre_delete` em `HistoricoBackup` remove arquivo do disco |
| **Backups (diretório)** | `backups/{slug}/` | Signal `pre_delete` em `Loja` remove diretório inteiro via `_limpar_arquivos_orfaos_loja()` |
| **NF-e XML** | `media/nfe_restaurante/` | Signal `post_delete` em `NotaFiscalEntrada` remove arquivo |
| **NF-e órfãos** | `media/nfe_restaurante/` | `_limpar_arquivos_orfaos_loja()` remove arquivos com prefixo `loja_{id}_` |

### 1.2 Banco de dados – órfãos

| Tabela | Status |
|--------|--------|
| `superadmin_historicobackup` | Adicionada em `TABELAS_LOJA_ID_DEFAULT` |
| `superadmin_configuracaobackup` | Adicionada em `TABELAS_LOJA_ID_DEFAULT` |
| Comandos `verificar_dados_orfaos` e `validar_config_orfaos` | Compatibilidade com `TABELAS_LOJA_ID` e `LIMPAR_REFERENCIAS_ANTES` |

### 1.3 Fluxo de exclusão de loja

1. **pre_delete Loja** (`delete_all_loja_data`):
   - Remove dados por tipo (Clínica, CRM, Restaurante, etc.)
   - Remove schema PostgreSQL
   - Rede de segurança: `TABELAS_LOJA_ID_DEFAULT`
   - **`_limpar_arquivos_orfaos_loja()`**: backups, NF-e
2. **CASCADE** deleta `HistoricoBackup`, `ConfiguracaoBackup`
3. **pre_delete HistoricoBackup**: remove arquivo de backup (se ainda existir)
4. **post_delete Loja** (`remove_owner_if_orphan`): remove owner se órfão

---

## 2. Segurança – Pontos de Atenção

### 2.1 Credenciais no `render.yaml`

O arquivo `render.yaml` contém valores sensíveis em texto plano:

- `DATABASE_URL`
- `REDIS_URL`
- `SECRET_KEY`
- `ASAAS_API_KEY`
- `EMAIL_HOST_PASSWORD`
- `GOOGLE_CLIENT_ID`

**Recomendação:** Migrar para variáveis de ambiente do Dashboard do Render.  
Exemplo: `value: ${{DATABASE_URL}}` ou configurar no painel e remover do repositório.

### 2.2 Heroku

- Credenciais em Config Vars (recomendado)
- `SECRET_KEY`, `DATABASE_URL` etc. não devem estar no código

### 2.3 Vercel

- Variáveis em Project Settings → Environment Variables
- `NEXT_PUBLIC_*` são expostas ao cliente (não colocar secrets)

---

## 3. Comandos de Manutenção

| Comando | Uso |
|---------|-----|
| `python manage.py validar_config_orfaos` | Valida se todas as tabelas com `loja_id` estão em `orfaos_config` |
| `python manage.py verificar_dados_orfaos` | Lista registros órfãos |
| `python manage.py verificar_dados_orfaos --remover` | Remove registros órfãos |
| `python manage.py cleanup_orphan_schemas --dry-run` | Lista schemas PostgreSQL órfãos |
| `python manage.py cleanup_orphan_schemas --force` | Remove schemas órfãos |
| `python manage.py limpar_usuarios_orfaos --confirmar` | Remove usuários órfãos |

**Sugestão:** Rodar `validar_config_orfaos` no CI ou antes do deploy.

---

## 4. Arquivos que Geram Órfãos (antes das correções)

| Origem | Situação anterior |
|--------|-------------------|
| Exclusão de loja | Backups em `backups/{slug}/` permaneciam no disco |
| Exclusão de loja (Restaurante) | XMLs em `media/nfe_restaurante/` permaneciam |
| Exclusão de `NotaFiscalEntrada` | Django não remove `FileField` automaticamente |
| Exclusão de `HistoricoBackup` | Arquivo removido em `limpar_backups_antigos`, mas não no CASCADE da loja |

**Situação atual:** Todos os cenários acima passam a remover os arquivos associados.

---

## 5. Projeção de Crescimento

Ver **`docs/PROJECAO_CRESCIMENTO_120_LOJAS.md`** para:

- 120 lojas × 5 funcionários = 600 usuários simultâneos
- Ajustes de workers, PostgreSQL, Redis
- Estimativa de custos e checklist de deploy

---

*Documento gerado para o projeto LWK Sistemas – análise de segurança e órfãos em produção.*
