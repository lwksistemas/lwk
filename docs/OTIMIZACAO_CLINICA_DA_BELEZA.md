# Otimização – Tipo de loja Clínica da Beleza

Sistema completo para gestão de clínicas de estética e beleza: agendamentos, procedimentos, pacientes e pagamentos.

## O que foi feito

### Frontend
- **Dashboard** (`dashboard/page.tsx`): removidos `console.log` de produção e comentários de versão (v577, v561).
- **Template** (`dashboard/templates/clinica-beleza.tsx`): comentário do cabeçalho atualizado (sem v579); descrição alinhada ao produto.

### Backend – Scripts e commands
- **Scripts obsoletos/debug removidos** da raiz do `backend/`: `force_load_clinica_beleza.py`, `test_clinica_beleza_import.py`, `create_clinica_beleza_tables.py`, `apply_clinica_beleza_migrations.py`, `limpar_dados_clinica_beleza.py`, `popular_loja_clinica_beleza.py`, `verificar_clinica_beleza_producao.py` (lógica coberta pelos management commands).
- **Scripts one-off** movidos para `backend/scripts_arquivo_clinica_beleza/`: `criar_tipo_loja_clinica_beleza.py`, `criar_planos_clinica_beleza.py`, `criar_dados_clinica_beleza.py`, `setup_clinica_beleza_producao.py`, `fix_clinica_beleza_schema.py`. Duplicatas na raiz do backend foram removidas.
- **globals.css**: revisado; não há classes com prefixo `clinica-` obsoletas (apenas comentário e estilos FullCalendar em uso para a agenda).

### Separação de tipos (não remover)
- **Clínica da Beleza** usa:
  - API: `/api/clinica-beleza/`
  - Páginas: `loja/[slug]/clinica-beleza/*` (pacientes, profissionais, procedimentos, campanhas, financeiro)
  - Agenda: `loja/[slug]/agenda` (FullCalendar + bloqueios)
  - Componentes: `components/clinica-beleza/`, `lib/clinica-beleza-api.ts`, `lib/offline-db.ts`
- **Clínica de Estética** (outro tipo de loja) usa:
  - API: `/api/clinica/` (clinica_estetica no backend)
  - Dashboard: `templates/clinica-estetica.tsx` e `components/clinica/` (modais, GerenciadorConsultas, CalendarioAgendamentos)

Não remover `clinica-estetica.tsx` nem `components/clinica/*` — são do tipo **Clínica de Estética**, não da Clínica da Beleza.

## Scripts e commands (estado atual)

### Management commands (usar no dia a dia)

Executar a partir da pasta **backend** (`python manage.py <command>`):

| Command | Uso |
|--------|-----|
| `verificar_clinica_beleza [--slug SLUG]` | Verifica tipo de loja, planos e opcionalmente dados de uma loja. |
| `limpar_dados_clinica_beleza --slug SLUG` | Limpa pacientes, profissionais, procedimentos, agendamentos e pagamentos da loja. |
| `popular_loja_clinica_beleza --slug SLUG` | Popula uma loja com dados de exemplo. |
| `vincular_owner_profissional_clinica_beleza --slug SLUG` | Vincula o owner da loja como profissional (administrador) na lista de Profissionais. |
| `verificar_loja_clinica_beleza --slug SLUG` | Verificação específica da loja. |

### Scripts one-off (arquivo)

Em `backend/scripts_arquivo_clinica_beleza/`. Ver **README** dentro da pasta para como executar.

| Script | Uso |
|--------|-----|
| `criar_tipo_loja_clinica_beleza.py` | Setup inicial: cria o tipo de loja "Clínica da Beleza". |
| `criar_planos_clinica_beleza.py` | Cria planos de assinatura para o tipo. |
| `criar_dados_clinica_beleza.py` | Dados de exemplo no banco default (evitar em produção). |
| `setup_clinica_beleza_producao.py` | Setup produção (criação manual de tabelas; fluxo normal é via migrations). |
| `fix_clinica_beleza_schema.py` | Correção one-off de schema (ex.: loja_id). |

## Próximos passos opcionais

1. Se precisar de um único entry point de setup, criar um command `setup_clinica_beleza` que chame os scripts de tipo + planos (ou documentar a ordem no README do arquivo).
2. Manter apenas os commands e o arquivo de scripts; não recriar scripts na raiz do backend.
