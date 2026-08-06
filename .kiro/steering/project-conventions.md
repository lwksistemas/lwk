---
inclusion: always
---

# LWK Sistemas — Convenções do Projeto

## Arquitetura

- **Backend**: Django 6.0.8 + DRF 3.17, multi-tenant com schemas PostgreSQL por loja
- **Frontend**: Next.js 16.2 (App Router), TypeScript 7, Tailwind CSS 4
- **Deploy**: Magalu Cloud SP (Docker Compose) — `ssh deploy@201.23.81.50`
- **Banco**: PostgreSQL 18 (Docker local) + Redis 7 (cache/filas)
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

## Fluxo de Deploy (Magalu Cloud SP)

1. Verificar backend: `python3 manage.py check`
2. Verificar frontend: `getDiagnostics` nos arquivos alterados
3. Git: `git add` apenas arquivos relevantes → `git commit` com mensagem descritiva → `git push`
4. Deploy produção: `ssh deploy@201.23.81.50 'cd /opt/lwk-erp && git pull && docker compose -f docker-compose.prod.yml up -d --build'`
5. Deploy beta: `ssh deploy@201.23.81.50 'cd /opt/lwk-erp && ./deploy-beta.sh'`
6. Se criou tabela nova: `ssh deploy@201.23.81.50 'cd /opt/lwk-erp && docker compose -f docker-compose.prod.yml exec backend python manage.py migrate'`

### Regra de ambientes

- **Padrão**: desenvolver no branch `staging`, testar no beta (beta.lwksistemas.com.br), depois fazer merge para `main` e deploy em produção
- **Correções urgentes em produção**: corrigir direto no `main` e deployar em produção, depois sincronizar o beta: `git checkout staging && git merge main --no-edit && git push origin staging` + deploy beta

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
