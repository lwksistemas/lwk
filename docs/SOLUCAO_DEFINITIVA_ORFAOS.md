# Solução definitiva: não criar órfãos (dados e usuários sem vínculo com loja)

## Objetivo

Garantir que, ao excluir uma loja (ou todas), **nunca** fiquem:
- usuários órfãos (ex-dono sem loja);
- registros órfãos (linhas com `loja_id` de loja inexistente);
- schemas PostgreSQL órfãos (`loja_*` sem loja);
- arquivos órfãos (quando houver upload por loja).

## 1. Prevenção no código (já implementado)

### 1.1 Exclusão de loja (API e signal)

- **`LojaViewSet.destroy()`** (views): remove chamados, banco/schema, Asaas, loja; depois remove o **owner** se não for dono de mais nenhuma loja.
- **Signal `pre_delete` (Loja)** (`signals.delete_all_loja_data`):
  - Remove por **tipo de loja** (Clínica, CRM, Restaurante, etc.) os modelos no schema (tenant).
  - Remove **LojaAssinatura** por `loja_slug`.
  - Remove **schema PostgreSQL** da loja.
  - **Rede de segurança:** percorre `TABELAS_LOJA_ID` e faz `DELETE ... WHERE loja_id = <id>` em cada tabela no banco default (ordem da lista respeita FKs quando possível).
- **Signal `post_delete` (Loja)** (`remove_owner_if_orphan`): se o owner não tiver mais lojas, remove UserSession, ProfissionalUsuario, groups e o User.

Assim, ao excluir uma loja pela API (ou por outro meio que dispare o signal), dados e owner são limpos e não viram órfãos.

### 1.2 Lista única: `orfaos_config.py`

- **`TABELAS_LOJA_ID`**: lista `(tabela, coluna)` de **todas** as tabelas no banco **default** que têm `loja_id` (ou equivalente) referenciando Loja.
  - Usada no **signal** (rede de segurança) e no comando **verificar_dados_orfaos**.
  - **Regra:** ao criar **qualquer** modelo novo no default com `loja_id`, **obrigatório** adicionar em `TABELAS_LOJA_ID` (e, se for tabela pai de outras por FK, em `LIMPAR_REFERENCIAS_ANTES` quando aplicável).

- **`LIMPAR_REFERENCIAS_ANTES`**: dicionário `{ tabela_pai: [ (tabela_filha, coluna_fk), ... ] }`.
  - Usado **só** em `verificar_dados_orfaos --remover`: antes de deletar órfãos na tabela pai, o comando remove referências nas tabelas filhas (evita violação de FK).
  - Ex.: antes de `clinica_procedimentos`, limpar `clinica_anamneses_templates`, `clinica_protocolos`, etc., por `procedimento_id`.

### 1.3 Validação para não esquecer novas tabelas

- **Comando:** `python manage.py validar_config_orfaos`
  - Consulta o banco (public) por tabelas que tenham coluna `loja_id`.
  - Compara com `TABELAS_LOJA_ID`.
  - Se existir tabela com `loja_id` **fora** da lista, o comando **falha** e mostra o que falta.
- **Recomendação:** rodar no CI ou antes do deploy (ou periodicamente), para garantir que nenhuma tabela nova com `loja_id` fique de fora e vire órfã.

## 2. Limpeza corretiva (quando órfãos já existem)

Quando lojas foram excluídas por outro caminho ou houve falha no signal, use:

| Comando | O que faz |
|--------|-----------|
| `verificar_dados_orfaos` | Lista registros com `loja_id` (ou `loja_slug`) inexistente. |
| `verificar_dados_orfaos --remover` | Remove esses registros (respeitando `LIMPAR_REFERENCIAS_ANTES`). |
| `limpar_usuarios_orfaos` | Lista usuários órfãos. |
| `limpar_usuarios_orfaos --confirmar` | Remove usuários órfãos (sessões, vínculos, user). |
| `cleanup_orphan_schemas --dry-run` | Lista schemas `loja_*` órfãos. |
| `cleanup_orphan_schemas --force` | Remove esses schemas. |
| `limpar_todos_orfaos --tudo` | Dados órfãos + usuários órfãos (não mexe em schemas). |

## 3. Arquivos (upload por loja)

- Se houver **upload de arquivos** por loja (ex.: em `media/` ou S3 com prefixo por loja):
  - No **signal** de exclusão da loja (ou em serviço chamado por ele), incluir a lógica de apagar/mover arquivos daquela loja (por exemplo por `loja_id` ou `loja_slug` no path).
- Os comandos de órfãos acima **não** apagam arquivos; a prevenção de “arquivos órfãos” é **sempre** no fluxo de exclusão da loja (signal/serviço).

## 4. Checklist para novos desenvolvimentos

1. **Novo modelo no banco default com `loja_id`:**
   - Adicionar `('nome_da_tabela', 'loja_id')` em `TABELAS_LOJA_ID` em `superadmin/orfaos_config.py`.
   - Se esse modelo for **referenciado por outro** (FK de outra tabela para ele), adicionar em `LIMPAR_REFERENCIAS_ANTES` a tabela filha e a coluna FK antes da tabela pai.
2. **Rodar:** `python manage.py validar_config_orfaos` (e no CI se possível).
3. **Exclusão de loja:** garantir que o signal (e a rede de segurança com `TABELAS_LOJA_ID`) continua cobrindo todas as tabelas por tipo de loja e no default; se criar novo tipo de loja ou novo app com `loja_id`, atualizar o signal e o `orfaos_config`.

Seguindo essa regra e a validação, o sistema deixa de criar órfãos de forma sustentável.
