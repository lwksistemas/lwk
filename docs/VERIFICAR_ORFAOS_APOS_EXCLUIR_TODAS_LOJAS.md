# Verificar órfãos após excluir todas as lojas

Quando você exclui **todas** as lojas do sistema, é importante verificar se não ficaram:

1. **Usuários órfãos** – usuários que eram donos de loja e não foram removidos
2. **Registros órfãos** – linhas em tabelas com `loja_id` apontando para loja inexistente
3. **Schemas PostgreSQL órfãos** – schemas `loja_*` no banco sem loja correspondente
4. **Assinaturas Asaas órfãs** – `LojaAssinatura` com `loja_slug` de loja que não existe mais

---

## 1. Verificar (só listar) – produção Heroku

Rode estes comandos **sem** `--remover` / `--confirmar` para apenas **listar** o que está órfão:

```bash
# 1) Usuários órfãos (não superuser e que não são donos de nenhuma loja)
heroku run "cd backend && python manage.py limpar_usuarios_orfaos" -a lwksistemas

# 2) Registros em tabelas com loja_id de loja inexistente + assinaturas (loja_slug órfão)
heroku run "cd backend && python manage.py verificar_dados_orfaos" -a lwksistemas

# 3) Schemas PostgreSQL órfãos (loja_* sem loja correspondente)
heroku run "cd backend && python manage.py cleanup_orphan_schemas --dry-run" -a lwksistemas
```

Se algum comando mostrar órfãos, anote o que apareceu antes de remover.

---

## 2. Limpar órfãos – produção Heroku

Depois de conferir, use os comandos abaixo para **remover** (na ordem sugerida):

```bash
# A) Remover registros órfãos (tabelas com loja_id inexistente e assinaturas órfãs)
heroku run "cd backend && python manage.py verificar_dados_orfaos --remover" -a lwksistemas

# B) Remover usuários órfãos
heroku run "cd backend && python manage.py limpar_usuarios_orfaos --confirmar" -a lwksistemas

# C) Remover schemas PostgreSQL órfãos (vai pedir digitar CONFIRMAR)
heroku run "cd backend && python manage.py cleanup_orphan_schemas --force" -a lwksistemas
```

**Ou** fazer dados + usuários de uma vez:

```bash
heroku run "cd backend && python manage.py limpar_todos_orfaos --tudo" -a lwksistemas
```

Depois, rodar o `cleanup_orphan_schemas` separadamente (ele não está incluído no `limpar_todos_orfaos`).

---

## 3. Resumo do que cada comando faz

| Comando | O que verifica/remove |
|--------|------------------------|
| `limpar_usuarios_orfaos` | Usuários que não são superuser e não têm nenhuma loja (owner). Remove tokens, UserSession, ProfissionalUsuario, groups e o User. |
| `verificar_dados_orfaos` | Tabelas em `orfaos_config.TABELAS_LOJA_ID` + `loja_assinatura` (por `loja_slug`). Remove linhas com loja_id/loja_slug inexistente. |
| `cleanup_orphan_schemas` | Schemas no PostgreSQL que começam com `loja_` e não têm loja ativa correspondente. Faz DROP SCHEMA ... CASCADE. |
| `limpar_todos_orfaos --tudo` | Equivalente a verificar_dados_orfaos --remover + limpar_usuarios_orfaos --confirmar (não mexe em schemas). |

---

## 4. Arquivos / storage

O sistema **não** mantém arquivos de loja em disco por loja de forma que exija limpeza manual: mídia/upload costumam ir para storage (ex.: S3). Se você usa apenas arquivos locais em `media/`, pode inspecionar pastas por slug de loja e apagar manualmente se existirem. Os comandos acima **não** apagam arquivos em disco.

---

## 5. Ordem recomendada após excluir todas as lojas

1. Rodar os **três** comandos de **verificação** (item 1).
2. Se houver órfãos: rodar **verificar_dados_orfaos --remover** e **limpar_usuarios_orfaos --confirmar** (ou **limpar_todos_orfaos --tudo**).
3. Por último: **cleanup_orphan_schemas** (com `--force` no Heroku para não pedir confirmação interativa, ou sem `--force` se tiver como digitar CONFIRMAR).

Isso deixa o sistema sem usuários, registros nem schemas órfãos após excluir todas as lojas.
