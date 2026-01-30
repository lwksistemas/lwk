# Análise da Estrutura do Sistema – Boas Práticas

Este documento analisa a estrutura do projeto **lwksistemas** (backend Django + frontend Next.js) em relação a boas práticas de programação.

---

## 1. Visão geral da arquitetura

- **Backend:** Django + DRF, multi-database (superadmin, suporte, lojas), multi-tenant por loja.
- **Frontend:** Next.js 15, App Router, chamadas à API com axios e interceptors.
- **Organização:** Separação clara entre `backend/` e `frontend/`, configuração por ambiente (decouple, `.env`).

---

## 2. Pontos positivos (já aderentes a boas práticas)

### 2.1 Backend

- **Reuso e DRY:** Uso de modelos base em `core/models.py` (`BaseCategoria`, `BaseCliente`, `BasePedido`, `BaseFuncionario`), evitando duplicação entre apps (restaurante, servicos, ecommerce).
- **Isolamento por loja:** `LojaIsolationMixin` e `LojaIsolationManager` em `core/mixins.py` centralizam filtro e validação por `loja_id`, com validação em `save()` e `delete()`.
- **Segurança:** Middleware de isolamento (`SecurityIsolationMiddleware`) separa rotas por tipo de usuário (superadmin, suporte, lojas). JWT + blacklist para sessão.
- **Configuração:** Uso de `python-decouple` para `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`; múltiplos settings (base, production).
- **APIs REST:** ViewSets e serializers por recurso, uso de `select_related`/`prefetch_related` onde faz sentido (ex.: restaurante).
- **Migrations:** Migrations versionadas por app, nomes descritivos.

### 2.2 Frontend

- **Cliente HTTP único:** `api-client.ts` e `clinicaApiClient` com baseURL, timeout e headers padronizados.
- **Interceptors:** Tratamento centralizado de 401, refresh de token e redirecionamento para login; tratamento de 507 (limite de armazenamento).
- **Autenticação e tenant:** Headers `X-Loja-ID` e `X-Tenant-Slug` e token JWT aplicados nos interceptors.
- **Componentes reutilizáveis:** `components/ui/` (Button, Input, Modal, etc.), uso de hooks em alguns fluxos (ex.: clinica).
- **Tipagem:** TypeScript com interfaces para modelos (ex.: `ItemCardapio`, `LojaInfo`).
- **Roteamento:** App Router com `[slug]` para loja, agrupamento `(auth)` e `(dashboard)`.

### 2.3 Geral

- **Documentação operacional:** Vários `.md` de deploy, correções e testes (incl. `DEPLOY_RESTAURANTE.md`, `VER_DASHBOARD_RESTAURANTE.md`).
- **Versionamento:** Uso de Git; histórico de mudanças refletido em docs e commits.

---

## 3. Pontos a melhorar

### 3.1 Isolamento multi-tenant no app Restaurante

- **Problema:** Em `restaurante/models.py`, `Categoria` herda apenas de `BaseCategoria` e `ItemCardapio` é um `Model` comum. Nenhum dos dois usa `LojaIsolationMixin` nem possui `loja_id`.
- **Risco:** Categorias e itens de cardápio ficam compartilhados entre todas as lojas (mesmo banco) ou dependem de outro mecanismo não explícito no código.
- **Recomendação:** Introduzir `loja_id` e `LojaIsolationMixin` (ou equivalente) em `Categoria` e `ItemCardapio`, com migration e filtro por loja nas views/querysets, para que cada loja veja apenas seu próprio cardápio.

### 3.2 Testes automatizados

- **Situação:** Não há testes unitários/integração visíveis (busca por `def test_` / `class Test` no backend não retorna uso efetivo).
- **Recomendação:** Criar testes para:
  - Serializers (validação de payloads válidos e inválidos).
  - ViewSets críticos (listagem filtrada por loja, criação com/sem `loja_id`).
  - Middleware de segurança e isolamento (acesso indevido a rotas de outro grupo).
  - Comandos de management que alteram dados.

### 3.3 Tamanho e responsabilidade do template Restaurante

- **Problema:** `restaurante.tsx` tem cerca de **1.780 linhas**, com vários modais e fluxos no mesmo arquivo (Cardápio, Mesas, Pedidos, Delivery, PDV, Nota Fiscal, Estoque, Balança, Funcionários, Clientes).
- **Impacto:** Dificulta leitura, manutenção, testes e reuso.
- **Recomendação:** Quebrar em componentes por domínio (ex.: `ModalCardapio.tsx`, `ModalPedidos.tsx`, `ModalEstoque.tsx`, hooks `useCardapio`, `usePedidos`) e manter o template principal apenas como orquestração e layout.

### 3.4 Serializers com `fields = '__all__'`

- **Situação:** Vários serializers usam `fields = '__all__'` (ex.: `ItemCardapioSerializer`, `ClienteSerializer`).
- **Risco:** Exposição acidental de campos internos ou sensíveis em respostas e em escritas (e.g. `created_at`/`updated_at` editáveis, se não forem `read_only`).
- **Recomendação:** Definir listas explícitas `fields` (ou `exclude`) e marcar como `read_only_fields` os que não devem ser enviados pelo cliente.

### 3.5 Tratamento de erros 4xx no frontend

- **Situação:** Em vários pontos o código faz apenas `toast.error(err.response?.data?.detail || 'Erro ao salvar')`. Em 400 de validação, o DRF costuma devolver um dicionário por campo (ex.: `{ "preco": ["Campo obrigatório."] }`), não só `detail`.
- **Recomendação:** Criar um helper que formate `err.response?.data` (detail + campos) e exiba no toast ou em lista; em formulários, mostrar erros por campo quando possível.

### 3.6 Validação e formato de dados no frontend

- **Problema:** No cadastro de itens do cardápio, o payload envia `preco: formItem.preco` como string. Se o usuário deixar o campo vazio, envia `""`, o que gera **400 Bad Request** no backend (DecimalField não aceita string vazia).
- **Recomendação:** Garantir que `preco` seja enviado como número ou string numérica válida (ex.: `parseFloat` ou `"0.00"` quando vazio); e, se possível, validação mínima no frontend (required, min 0) antes do POST.

### 3.7 Duplicação de lógica entre `apiClient` e `clinicaApiClient`

- **Situação:** Dois clientes axios com interceptors muito parecidos (token, refresh, sessão, headers de loja).
- **Recomendação:** Extrair a lógica comum (headers, refresh, tratamento de 401/507) para funções/hooks reutilizáveis e configurar um único cliente ou dois clientes que compartilhem a mesma configuração base.

### 3.8 Documentação da API

- **Situação:** Não há referência a Swagger/OpenAPI ou documentação explícita dos endpoints.
- **Recomendação:** Adicionar `drf-spectacular` (ou similar) e expor um schema JSON e uma UI (ex.: `/api/schema/swagger-ui/`) para facilitar integração e onboarding.

---

## 4. Resumo

| Aspecto                    | Situação        | Ação sugerida                          |
|---------------------------|-----------------|----------------------------------------|
| Arquitetura geral         | Boa             | Manter                                |
| Isolamento por loja       | Parcial         | Incluir loja_id em Categoria/ItemCardapio |
| Segurança (middleware/JWT)| Boa             | Manter; reforçar com testes            |
| Testes automatizados      | Ausentes        | Introduzir testes backend (e depois front) |
| Tamanho do template       | Muito grande    | Dividir em componentes e hooks        |
| Serializers               | Expostos demais | Campos explícitos e read_only         |
| Erro 400 / validação      | Genérico        | Tratar body de validação e preco       |
| Documentação da API       | Ausente         | Swagger/OpenAPI                       |

---

## 5. Ação imediata sugerida (erro ao salvar item do cardápio)

O **POST /api/restaurante/cardapio/ 400** costuma ocorrer quando:

1. **Preço vazio ou inválido:** o backend espera um decimal; string vazia `""` é rejeitada.
2. **Descrição vazia:** o modelo tem `descricao = models.TextField()` sem `blank=True`, então é obrigatória.

**Ajustes recomendados no frontend:**

- Normalizar `preco` antes de enviar: por exemplo `preco: formItem.preco ? String(Number(formItem.preco)) : "0"` ou validar e bloquear envio se estiver vazio.
- Garantir que `descricao` não seja enviada vazia (valor padrão ou validação no formulário).
- Exibir erros de validação retornados em `err.response.data` (por campo) no toast ou nos labels dos campos.

Com isso, o sistema continua evoluindo de forma alinhada a boas práticas, com foco em isolamento por loja, testes, componentes menores e API e erros mais claros.

---

## 6. Implementações realizadas (resumo)

- **3.1 Isolamento multi-tenant:** `Categoria`, `ItemCardapio`, `Mesa`, `Cliente`, `Reserva` e `Pedido` passaram a usar `LojaIsolationMixin` e `LojaIsolationManager`; migration `0008_add_loja_id_...` criada.
- **3.2 Testes:** Testes em `restaurante/tests.py` para serializers (Categoria, ItemCardapio, Mesa) e para `LojaIsolationManager`.
- **3.3 Template Restaurante:** Criada pasta `restaurante/modals/` com `ModalClientes.tsx` e `index.ts`; o modal de Clientes foi extraído do `restaurante.tsx`. Os demais modais podem ser extraídos seguindo o mesmo padrão.
- **3.4 Serializers:** Campos explícitos e `read_only_fields` definidos nos serializers do app `restaurante`.
- **3.5 Erros 4xx:** Helper `formatApiError` em `lib/api-errors.ts`; uso em `restaurante.tsx` (e em `ModalClientes.tsx`) para exibir erros de validação.
- **3.6 Validação cardápio:** Preço e descrição normalizados no frontend antes do POST; validação de preço ≥ 0.
- **3.7 apiClient:** Lógica unificada em `lib/api-client.ts` (`createApiInstance`, `applyLojaInterceptors`, `addLojaAuthHeaders`, `handle401`, `handle507`); `apiClient` e `clinicaApiClient` compartilham a mesma base.
- **3.8 Documentação API:** `drf-spectacular` configurado; schema em `/api/schema/` e Swagger UI em `/api/schema/swagger-ui/`.
