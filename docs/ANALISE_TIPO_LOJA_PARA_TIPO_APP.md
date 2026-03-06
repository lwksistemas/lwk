# Análise: nomenclatura "Tipo de Loja" → "Tipo de App"

## Objetivo

Garantir que, após a mudança de nome para **"Tipo de App"**, o código use essa nomenclatura de forma consistente em comentários, docstrings, mensagens e documentação.

## O que foi alterado

### Backend

| Arquivo | Alteração |
|--------|------------|
| `superadmin/models.py` | Docstring `TipoLoja`: "Tipos de loja" → "Tipos de app"; comentário e `help_text` em `PlanoAssinatura.tipos_loja`: "Tipos de loja" → "Tipos de app" |
| `superadmin/backup_service.py` | Comentários e constantes: "tipo da loja" / "tipo de loja" → "tipo de app"; renomeadas `BACKUP_TIPO_LOJA_*` → `BACKUP_TIPO_APP_*` |
| `superadmin/services/database_schema_service.py` | Comentários: "Apps por tipo de app" |
| `superadmin/views.py` | Docstring do ViewSet: removido "(anteriormente Tipos de Loja)" |
| `superadmin/api_docs.py` | Comentário "# Tipos de Loja" → "# Tipos de App"; descrição do schema simplificada |
| `superadmin/management/commands/setup_initial_data.py` | `help`, docstrings e mensagens: "tipos de loja" → "tipos de app" |
| `config/urls.py` | Comentário: "tipos de loja" → "tipos de app" |
| `core/models.py` | Docstring `HistoricoAcao`: "tipos de loja" → "tipos de app" |

### Frontend

| Arquivo | Alteração |
|--------|------------|
| `lib/loja-tipo.ts` | Comentário: "tipo de loja" → "tipo de app" |
| `app/(dashboard)/superadmin/tipos-app/page.tsx` | Comentário: removido "(anteriormente Tipos de Loja)" |

## O que não foi alterado (de propósito)

- **Nomes de campo e de modelo:** `tipo_loja`, `tipo_loja_nome`, `TipoLoja`, `tipos_loja` continuam iguais para não quebrar API, banco e contratos existentes.
- **Migrations antigas:** `0001_initial.py`, `0003_planoassinatura_tipos_loja.py` etc. mantêm os textos originais (histórico).
- **Scripts pontuais:** `scripts_arquivo_clinica_beleza/`, `scripts/criar_tipo_loja_*.py` e comandos como `verificar_clinica_beleza.py` ainda podem usar "tipo de loja" em mensagens; podem ser alinhados depois se desejado.

## Já estavam corretos

- `TipoLoja.Meta`: `verbose_name = 'Tipo de App'`, `verbose_name_plural = 'Tipos de App'`.
- Migrations recentes (ex.: `0030_add_backup_models.py`) e rotas do frontend já usam "Tipos de App" / "tipos-app".
- Modal e páginas do superadmin já exibem "Tipo de App" na interface.

## Resumo

A nomenclatura **"Tipo de App"** está aplicada de forma consistente em:

- Model e Meta do `TipoLoja`
- Comentários e docstrings do backup e do `DatabaseSchemaService`
- Comandos de setup e documentação da API
- Frontend (comentários e tela de Tipos de App)

Os identificadores de código (`tipo_loja`, `TipoLoja`, etc.) foram mantidos para compatibilidade com API e banco.
