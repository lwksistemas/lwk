---
inclusion: always
---

# LWK Sistemas — Convenções do Projeto

## Arquitetura

- **Backend**: Django 5 + DRF, multi-tenant com schemas PostgreSQL por loja
- **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS
- **Deploy**: Backend no Railway (`npx railway up --detach`), Frontend no Vercel (`npx vercel --prod --yes`)
- **Banco**: PostgreSQL (Railway) + Redis (cache)
- **Apps por tipo de loja**: clinica_beleza, crm_vendas, cabeleireiro, hotel, restaurante

## Estrutura Multi-Tenant

- Cada loja tem um schema PostgreSQL próprio (`loja_<cpf_cnpj>`)
- Models com `LojaIsolationMixin` + `LojaIsolationManager`
- Após criar tabelas novas, rodar SQL em todos os schemas ativos
- Migration no schema `public` + `migrate_all_lojas` para os tenants

## Padrões de Código — Backend

- Views: usar `APIView` com `GetObjectMixin` (de `views_base.py`) para eliminar try/except repetido
- Service layer: lógica de negócio em `*_service.py`, não dentro de views ou serializers
- Mapeamento de campos: usar `map_field_names()` de `views_base.py`
- Resolução de loja: usar `resolve_loja_id_from_request()` de `views_base.py`
- Paginação: usar `paginate_queryset()` de `pagination.py` (retrocompatível)
- Sempre rodar `python3 manage.py check` antes de considerar pronto

## Padrões de Código — Frontend

- Componentes: `"use client"` no topo de páginas interativas
- Formulários grandes: usar página dedicada (não modal) — ex: `/profissionais/novo`
- Modais: apenas para ações simples (confirmação, seleção rápida)
- Busca em listas longas: campo de input + resultados como botões clicáveis
- Cores: usar cor temática do tipo de loja (não hardcoded)
- Sempre verificar `getDiagnostics` antes de commit

## Fluxo de Deploy

1. Verificar backend: `python3 manage.py check`
2. Verificar frontend: `getDiagnostics` nos arquivos alterados
3. Git: `git add` apenas arquivos relevantes → `git commit` com mensagem descritiva → `git push`
4. Backend: `npx railway up --detach` (a partir da raiz do projeto)
5. Frontend: `npx vercel --prod --yes` (a partir de /frontend)
6. Se criou tabela nova: rodar SQL `CREATE TABLE IF NOT EXISTS` em todos os schemas via `npx railway run python3 -c "..."`

## Convenções de Commit

- feat(modulo): nova funcionalidade
- fix(modulo): correção de bug
- refactor(modulo): refatoração sem mudança de comportamento
- perf(modulo): otimização de performance

## Validação

- Backend compila: `python3 manage.py check` (0 issues)
- Imports OK: importar todos os módulos modificados
- Frontend compila: `getDiagnostics` sem erros
- URLs carregam: verificar contagem de urlpatterns
- Deploy saudável: healthcheck Railway + Vercel Ready
