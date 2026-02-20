# Capacidade: 100 lojas × 5 usuários simultâneos

Este documento analisa se o sistema permanece **rápido e seguro** com **100 lojas** e **5 usuários por loja** usando ao mesmo tempo (até ~500 usuários concorrentes).

---

## Segurança: sim, continua segura

A arquitetura garante isolamento **por requisição**, independente do número de lojas ou usuários:

| Camada | Comportamento |
|--------|----------------|
| **Middleware de segurança** | Verifica se o usuário autenticado é dono da loja solicitada (slug na URL/header). Suporta múltiplas lojas por dono. |
| **TenantMiddleware** | Define o schema/banco da loja **só para aquela request**. Ao fim da request, o contexto é **limpo** (`set_current_loja_id(None)`, `set_current_tenant_db('default')`). |
| **Thread-local** | `loja_id` e `current_tenant_db` são por thread; não há vazamento entre requisições ou entre lojas. |
| **LojaIsolationManager** | Todas as queries de modelos por loja são filtradas por `loja_id` do contexto. |
| **Mixins** | No `save()`/`delete()` validam que o `loja_id` do objeto é o do contexto. |

Conclusão: **cada requisição vê apenas os dados da loja daquela request**. Não há compartilhamento de contexto entre usuários ou entre lojas. Com 100 lojas e 5 usuários por loja, a segurança e o isolamento se mantêm.

---

## Desempenho: adequado, com ajustes recomendados

### Configuração atual (ex.: Heroku)

- **Web:** `gunicorn` com **2 workers** e **4 threads** por worker → **8 requisições HTTP simultâneas**.
- **Banco:** PostgreSQL (Heroku Postgres); conexões de tenant com `CONN_MAX_AGE=0` (fecham ao fim da request, evitando esgotar conexões).
- **Cache:** Redis se `REDIS_URL` existir; caso contrário, LocMem (por processo).
- **Tenant:** Cache em memória das lojas (slug → id, database_name) no middleware; schemas criados sob demanda em `settings.DATABASES`.

### O que isso significa na prática

- **“500 usuários ao mesmo tempo”** em geral não são 500 requisições no exato mesmo instante. Muitos estarão navegando (leitura) ou com telas abertas sem chamadas contínuas.
- O que importa é o **pico de requisições simultâneas**. Com 8 concorrentes, se cada request levar ~200–500 ms, o servidor atende dezenas de requisições por segundo.
- Se em picos muitos usuários acessarem ao mesmo tempo, as requisições **enfileiram**; a aplicação continua correta, mas o tempo de resposta pode subir.

### Quando aplicar as recomendações (e custo)

**Não é obrigatório fazer nada agora.** A configuração atual (2 workers, sem Redis obrigatório, plano básico) é suficiente para **menos lojas e menos usuários simultâneos**. O sistema segue **seguro** em qualquer escala.

As recomendações abaixo **aumentam o custo** (Heroku: mais workers/dyno maior/Redis/plano de banco; Vercel: planos maiores se necessário). Só vale aplicá-las quando:

- você se aproximar de **100 lojas** com uso real ao mesmo tempo, ou  
- usuários reclamarem de **lentidão** em picos, ou  
- métricas mostrarem fila de requisições / tempo de resposta alto.

Até lá, manter a configuração atual evita custo desnecessário na Vercel e no Heroku.

### Recomendações (para quando a escala exigir)

1. **Aumentar workers (Procfile)**  
   Para mais concorrência sem mudar código:
   ```text
   web: cd backend && gunicorn config.wsgi --workers 3 --threads 4 ...
   ```
   ou `--workers 4` se o plano do banco e o tamanho do dyno permitirem (cada worker usa conexões).

2. **Usar Redis em produção**  
   Configurar `REDIS_URL` (ex.: Heroku Redis) para cache e sessões. Evita LocMem por processo e melhora desempenho sob carga.

3. **Monitorar conexões com o PostgreSQL**  
   O limite de conexões do Heroku Postgres depende do plano. Com `CONN_MAX_AGE=60` no default e `CONN_MAX_AGE=0` nos tenants, o uso tende a ser estável; mesmo assim, vale acompanhar (ex.: dashboard Heroku, logs).

4. **Dyno e plano de banco**  
   Para 100 lojas e picos de dezenas de usuários simultâneos, um dyno um pouco maior e um plano de banco que suporte o número de conexões dos workers ajudam a manter resposta rápida.

---

## Resumo

| Pergunta | Resposta |
|----------|----------|
| **Continua seguro com 100 lojas e 5 usuários por loja?** | **Sim.** Isolamento por request, limpeza de contexto, checagem de dono da loja e filtros por `loja_id` garantem que cada loja e cada usuário veem só seus dados. |
| **Preciso aplicar as recomendações agora?** | **Não.** Só quando a escala (muitas lojas, picos de uso) ou lentidão justificarem; aplicar agora só sobe o custo na Vercel/Heroku sem necessidade. |
| **Continua rápido?** | **Sim, na maior parte do tempo.** Para picos altos (muitos acessos no mesmo instante), aumentar workers, usar Redis e um plano adequado de dyno/banco mantém o sistema responsivo — e aumenta o custo; faça quando precisar. |

Referências: `docs/SEGURANCA_ENTRE_LOJAS.md`, `backend/config/security_middleware.py`, `backend/tenants/middleware.py`, `backend/core/mixins.py`, `Procfile`.
