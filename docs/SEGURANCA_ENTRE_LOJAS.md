# Segurança e isolamento entre lojas

Este documento descreve como o sistema garante que **uma loja nunca acesse dados de outra** e as boas práticas aplicadas.

---

## Camadas de proteção

### 1. Middleware de segurança (`config.security_middleware.SecurityIsolationMiddleware`)

- **Rotas por grupo:** Super Admin (`/api/superadmin/`), Suporte (`/api/suporte/`), Lojas (APIs por tipo: clinica, crm, etc.).
- **Isolamento de loja:** Para rotas de loja, o middleware:
  - Extrai o slug da loja da requisição (headers **`X-Store-Slug`**, **`X-Tenant-Slug`** — enviados pelo frontend —, **`X-Loja-ID`** — resolvido para slug —, query `store`/`tenant` ou path `/api/.../loja/{slug}/...`).
  - Verifica se o **usuário autenticado é dono dessa loja** (`Loja.objects.filter(owner=request.user, is_active=True, slug=requested_store_slug).exists()`).
  - **Suporta múltiplas lojas por dono:** o usuário pode acessar qualquer uma das suas lojas; tentativa de acessar slug de loja que não é dele retorna `403 CROSS_STORE_ACCESS_DENIED`.
- Super Admin **não** pode acessar rotas de loja (uso apenas do painel superadmin).

### 2. Isolamento por tenant (banco/schema)

- **TenantMiddleware** (`tenants.middleware`): identifica a loja pela URL/header e configura o **schema PostgreSQL** (ou banco) daquela loja, de forma que as queries da request já rodem no contexto correto.
- **LojaIsolationManager** (`core.mixins`): em modelos que usam `LojaIsolationMixin`, todas as queries são filtradas por `loja_id` do contexto (defesa em profundidade mesmo com schemas separados).

### 3. Validação nos models

- **LojaIsolationMixin:** no `save()` e `delete()` garante que `loja_id` do objeto seja o do contexto; caso contrário, levanta `ValidationError`.

---

## Boas práticas

- **Nunca** confiar apenas no frontend (slug na URL/header): a verificação é sempre no backend.
- **Sempre** usar modelos com `LojaIsolationMixin` + `LojaIsolationManager` para dados por loja.
- **Logs:** tentativas de acesso cruzado são registradas como críticas (`logger.critical`) para auditoria.

---

## Referências

- `backend/config/security_middleware.py` – regras de rota e verificação de dono da loja.
- `backend/tenants/middleware.py` – definição do tenant (schema/banco) por request.
- `backend/core/mixins.py` – `LojaIsolationMixin`, `LojaIsolationManager`.
- `backend/GUIA_ISOLAMENTO_DADOS.md` – uso dos mixins nos models.
