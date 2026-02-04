# Análise de Segurança, Desempenho e Capacidade

**Escopo:** Tipos de loja **Clínica de Estética** e **CRM Vendas**, com melhorias e otimizações já implementadas.  
**Objetivo:** Estimar quantas lojas (com até **5 usuários por loja**) o sistema suporta sem comprometer segurança nem desempenho para o usuário da loja.

---

## 1. Arquitetura em Produção

| Componente | Stack |
|------------|--------|
| **Backend** | Django + DRF, Heroku (Gunicorn) |
| **Banco de dados** | PostgreSQL único (todas as lojas no mesmo DB) |
| **Isolamento de dados** | Por `loja_id` (campo em todas as tabelas de loja), não por banco por tenant |
| **Frontend** | Next.js, Vercel |
| **Autenticação** | JWT (access 1h, refresh 7 dias) + blacklist na rotação |
| **Cache** | LocMemCache (em memória, 10k entradas; não compartilhado entre workers) |

**Procfile (backend):**
- 2 workers Gunicorn
- 4 threads por worker → **8 requisições simultâneas** por instância
- Timeout 30s, keep-alive 5s, max 1000 requests por worker (recycle)

---

## 2. Segurança

### 2.1 Camadas de isolamento

1. **TenantMiddleware** (`tenants/middleware.py`)
   - Define contexto da loja a partir de `X-Loja-ID` ou `X-Tenant-Slug`.
   - **Regra crítica:** usuário autenticado só acessa se for **owner** da loja (ou superuser em rotas de superadmin).
   - Se usuário tentar acessar loja de outro owner → retorno `None` (acesso bloqueado) e log de violação.

2. **SuperAdminSecurityMiddleware** (produção)
   - Isolamento de rotas: Super Admin só em `/api/superadmin/`, Suporte em `/api/suporte/`, Lojas em `/api/clinica/`, `/api/crm/`, etc.
   - Usuário de loja **não** acessa rotas de superadmin/suporte (exceto endpoints públicos/owner permitidos).
   - Verificação de loja: proprietário só acessa **sua** loja (slug/header conferido).

3. **LojaIsolationManager** (`core/mixins.py`)
   - Todo `get_queryset()` filtra por `loja_id` do contexto (thread-local).
   - Se não houver `loja_id` no contexto → retorna queryset **vazio** (nenhum dado exposto).

4. **LojaIsolationMixin** (save/delete)
   - No `save()`: exige `loja_id` igual ao contexto; impede gravar em outra loja.
   - No `delete()`: impede deletar registro de outra loja.
   - Violações geram `ValidationError` e log crítico.

5. **Serializers (Clínica + CRM)**
   - `loja_id` em `read_only_fields` e preenchido no `create()` via `get_current_loja_id()` (contexto do request).
   - Cliente não envia `loja_id`; backend define pelo header/contexto.

6. **CORS**
   - Origens restritas (ex.: `lwksistemas.com.br`); credentials habilitado.
   - Headers permitidos incluem `x-loja-id` e `x-tenant-slug`.

7. **HTTPS e headers**
   - HSTS, X-Frame-Options DENY, XSS filter, etc. (produção).

**Resumo segurança:** Múltiplas camadas (rota, owner, contexto, queryset, save/delete) garantem que uma loja não acesse dados de outra e que apenas o owner (e usuários daquela loja, quando houver modelo de permissão por loja) acesse seus dados. Com 5 usuários por loja, hoje o modelo é “uma loja = um owner”; se no futuro houver “funcionários” por loja, a mesma lógica de contexto por request (X-Loja-ID) mantém o isolamento.

---

## 3. Desempenho e otimizações

### 3.1 Backend

- **Clínica de Estética**
  - `Agendamento`, `EvolucaoPaciente`, `Anamnese`, `BloqueioAgenda`, `Consulta`: uso de `select_related` para evitar N+1.
  - Dashboard: **1 request** (`/clinica/agendamentos/dashboard/`) retornando estatísticas + próximos agendamentos.
  - Modais carregados sob demanda (lazy) no frontend.

- **CRM Vendas**
  - `Venda`: `select_related('cliente', 'vendedor', 'produto')`.
  - Dashboard: **2 requests em paralelo** (`/crm/vendas/estatisticas/` e `/crm/leads/recentes/`).
  - Índices em `loja_id` (LojaIsolationMixin + migrations).

- **Geral**
  - `CONN_MAX_AGE=600` (PostgreSQL) para reuso de conexões.
  - GZip para respostas.
  - Paginação (ex.: PAGE_SIZE 50) onde aplicável.
  - Limite de tamanho de banco por loja (512 MB) no TenantMiddleware quando em SQLite (dev); em produção (PostgreSQL único) o limite é de uso geral do banco.

### 3.2 Frontend

- **Clínica:** 1 chamada de dashboard; modais em lazy loading; skeleton durante carregamento.
- **CRM:** 2 chamadas em paralelo no load do dashboard; skeleton; componentes reutilizáveis (StatCard, EmptyState, etc.).

### 3.3 Throttling (configuração em desenvolvimento)

- `UserRateThrottle`: 2000 req/h por usuário.
- Com 5 usuários/loja: 10.000 req/h por loja (no limite do throttle).
- **Produção:** em `settings_production.py` não há `DEFAULT_THROTTLE_*` definido; vale a pena replicar throttle em produção para proteção contra abuso.

---

## 4. Capacidade estimada (lojas × 5 usuários/loja)

### 4.1 Fatores limitantes (Heroku típico)

- **Conexões PostgreSQL:** plano Eco ≈ 20 conexões; planos maiores aumentam.
- **Concorrência da app:** 2 workers × 4 threads = **8 requisições simultâneas** por dyno.
- **Throughput aproximado:** com tempo médio de resposta ~200–400 ms, 8 handlers → ~20–40 req/s por dyno em pico.
- **Memória:** 2 workers consomem mais memória; dyno Eco ~512 MB pode ficar no limite com picos.

### 4.2 Cenários de uso

- **Usuário “típico”:** abre o dashboard (1–2 req para Clínica, 2 para CRM), depois fica navegando (poucas req/min).
- **Pico:** vários usuários de lojas diferentes acessando ao mesmo tempo (ex.: início do expediente).

### 4.3 Estimativa conservadora

- **Até 20–30 lojas**, com **até 5 usuários por loja** (100–150 usuários no total).
- Premissas:
  - Em pico, uma fração pequena dos usuários está ativa ao mesmo tempo (ex.: 10–20%).
  - 15–30 usuários concorrentes × 2–3 req cada = 30–90 req em poucos segundos; 8 threads conseguem servir com fila curta e tempo de resposta aceitável (< 1–2 s).
  - Conexões DB: com `conn_max_age=600`, o número de conexões ativas tende a ficar abaixo do limite do plano se a concorrência não for extrema.

### 4.4 Se todas as lojas (5 usuários cada) usarem ao mesmo tempo

- 30 lojas × 5 usuários = 150 usuários; se todos abrirem o dashboard ao mesmo tempo → 150 × 2 ≈ 300 req em poucos segundos.
- 8 threads não dão conta sem fila longa; tempo de resposta sobe muito.
- **Recomendação:** não dimensionar para “todos os usuários ativos ao mesmo tempo”; para esse perfil, aumentar workers/dynos ou considerar mais de uma instância.

### 4.5 Número sugerido para “sem comprometer segurança e desempenho”

- **Meta confortável:** **20 lojas × 5 usuários = 100 usuários**, com uso típico (dashboard + navegação leve).
- **Até 30 lojas (150 usuários)** é possível se:
  - Picos de acesso forem moderados (ex.: não todos os 5 usuários de todas as lojas ao mesmo tempo), e
  - Resposta do dashboard em 1–2 s for aceitável em picos.
- Acima disso, é recomendável:
  - Aumentar workers/dynos (mais concorrência e throughput),
  - Habilitar throttle em produção (ex.: 2000/h por user) e
  - Monitorar conexões DB e tempo de resposta (Heroku Metrics, APM).

---

## 5. Recomendações

### Segurança

- Manter **X-Loja-ID** obrigatório nas chamadas de loja (já feito pelo `clinicaApiClient`).
- Replicar **throttle** em produção (ex.: `UserRateThrottle` 2000/h por usuário) para limitar abuso. ✅ Implementado em `settings_production.py`.
- Se no futuro houver “funcionários” por loja com login próprio, garantir que o contexto da loja (e eventualmente perfil) seja sempre definido a partir do token/sessão e validado no backend.

### Desempenho

- Considerar **Redis** para cache compartilhado entre workers (substituir LocMemCache em produção) para sessões ou respostas muito acessadas.
- Manter **select_related/prefetch_related** em listagens e dashboards; revisar novas views para evitar N+1.
- Em crescimento além de ~30 lojas, considerar **mais workers** (ex.: 3–4) ou **mais dynos** e monitorar conexões do PostgreSQL. ✅ Comentário adicionado no `Procfile`.

### Monitoramento

- Acompanhar no Heroku: uso de memória, tempo de resposta (p50, p95), taxa de erro e número de conexões com o banco.
- Logs de “violação” (TenantMiddleware, LojaIsolationMixin) devem ser monitorados para detectar tentativas de acesso indevido.

#### Checklist de monitoramento (Heroku)

| O que acompanhar | Onde | Ação se crítico |
|------------------|------|------------------|
| Memória do dyno | Heroku Dashboard → Metrics | Aumentar dyno ou reduzir workers |
| Tempo de resposta (p50, p95) | Heroku Dashboard → Metrics / APM | Otimizar queries, mais workers ou dynos |
| Taxa de erro (5xx) | Heroku Dashboard → Metrics / Logs | Corrigir exceções, revisar logs |
| Conexões PostgreSQL | Heroku Dashboard → Datastore / Metrics | Ajustar `conn_max_age` ou plano do DB |
| Logs `VIOLAÇÃO DE SEGURANÇA` / `CROSS_STORE` | Heroku → Logs (filtrar por “violação” ou “CRÍTICA”) | Investigar tentativa de acesso indevido |
| Throttle 429 (Too Many Requests) | Logs / frontend | Aumentar `DEFAULT_THROTTLE_RATES` se legítimo |

---

## 6. Resumo

| Item | Situação |
|------|----------|
| **Segurança** | Isolamento por loja em várias camadas (rota, owner, contexto, queryset, save/delete); adequado para multi-tenant com 5 usuários/loja. |
| **Desempenho** | Otimizações presentes (select_related, dashboard enxuto, lazy loading, GZip, connection pooling). |
| **Capacidade sugerida** | **20–30 lojas** com **5 usuários por loja** (100–150 usuários), com uso típico, sem comprometer segurança nem desempenho. |
| **Acima de 30 lojas** | Aumentar capacidade (workers/dynos), throttle em produção e monitoramento de DB e latência. |

Documento gerado com base no código atual (Clínica de Estética, CRM Vendas, middlewares, serializers e configurações de produção).
