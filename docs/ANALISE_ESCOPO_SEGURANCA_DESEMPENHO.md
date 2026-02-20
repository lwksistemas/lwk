# Escopo da análise de segurança, desempenho e limpeza de código

Este documento deixa claro **o que foi e o que não foi** analisado nas etapas de segurança, desempenho e remoção de código/templates duplicados ou antigos.

---

## Compatibilidade frontend ↔ backend

| Aspecto | Situação |
|--------|----------|
| **Headers de loja** | Frontend envia `X-Loja-ID` e `X-Tenant-Slug` (api-client, clinica-beleza-api). Backend `SecurityIsolationMiddleware` passou a aceitar também `X-Tenant-Slug` e `X-Loja-ID` (além de `X-Store-Slug` e path), garantindo que o isolamento entre lojas seja aplicado em todas as chamadas de API. |
| **Autenticação** | JWT (Bearer) em todas as requisições de loja; refresh token tratado no frontend (api-client); 401 redireciona para login. |
| **Isolamento** | Backend valida que o usuário é dono da loja (slug/ID) em dois pontos: SecurityIsolationMiddleware e TenantMiddleware. Frontend grava `current_loja_id` e `loja_slug` após login/info_publica e envia nos headers. |

---

## O que foi analisado e feito

### Backend (Heroku / Django)

| Item | Situação |
|------|----------|
| **Segurança entre lojas** | Analisado. Middleware, TenantMiddleware, LojaIsolationManager, mixins. Documentado em `docs/SEGURANCA_ENTRE_LOJAS.md`. Correção para múltiplas lojas por dono no `security_middleware`. |
| **Desempenho / capacidade** | Analisado para 100 lojas × 5 usuários. Documentado em `docs/CAPACIDADE_100_LOJAS.md` (workers, Redis, conexões Postgres). Foco em **Heroku** (web dyno, banco). |
| **Código/templates duplicados ou antigos** | Removidos: `limpar_usuarios_orfaos.py`, `test_app_loading.py`, `debug_installed_apps.py`, `limpar_dados_loja.py`, `verificar_dados_apos_exclusao.py`. Templates de e-mail já usam um único base. |

### Frontend (Vercel / Next.js)

| Item | Situação |
|------|----------|
| **Servidor Vercel** | **Não** foi feita uma análise dedicada de segurança/desempenho do runtime Vercel (serverless, limites, cold start). O `vercel.json` já define headers de segurança (X-Frame-Options, X-Content-Type-Options, Referrer-Policy) e redirect www → domínio canônico. |
| **Código duplicado / redundante** | **Feito.** Formatação de moeda/data consolidada em `lib/financeiro-helpers.ts`; uso de `next/image` onde havia `<img>`; dependências de `useEffect` corrigidas (useCallback ou eslint-disable com comentário). |
| **Templates/páginas antigas** | Não foi feita varredura para páginas ou componentes obsoletos no frontend. O `clear-cache.html` já foi unificado (redirect para `limpar-cache.html`). |

---

## Resumo

- **Backend:** segurança entre lojas, capacidade (Heroku) e remoção de scripts/templates redundantes **foram** analisados e aplicados.
- **Frontend (Vercel):** o **servidor Vercel** não foi objeto de análise específica de segurança/desempenho; apenas o que já está no `vercel.json` (headers, redirect) foi considerado.
- **Frontend (código):** a remoção de **códigos e templates duplicados/redundantes/antigos** **não** foi feita de forma sistemática no frontend; há espaço para consolidar formatação (moeda/data) no `financeiro-helpers` e revisar componentes pouco usados.

---

## Recomendações futuras (opcional)

1. **Vercel:** se quiser aprofundar, revisar no dashboard: variáveis de ambiente (ex.: `NEXT_PUBLIC_*`), limites de função/serverless, e uso de cache/CDN.
2. **Frontend – menos duplicação:** aos poucos, trocar usos de `toLocaleString('pt-BR')` e `formatDate`/`formatMoney` locais por `formatCurrency`, `formatDate` e `formatDateTime` de `@/lib/financeiro-helpers` onde fizer sentido (ex.: `ModalConflitoAgenda.tsx`, `restaurante/ModalsAll.tsx`, componentes de suporte e relatórios).
3. **Frontend – limpeza:** identificar páginas ou componentes não usados (rotas antigas, modais substituídos) e removê-los ou documentar como legado.

Referências: `docs/SEGURANCA_ENTRE_LOJAS.md`, `docs/CAPACIDADE_100_LOJAS.md`, `frontend/vercel.json`, `frontend/lib/financeiro-helpers.ts`.
