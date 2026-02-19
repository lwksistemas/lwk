# Análise: Conexões de banco e "too many connections"

## Objetivo

Revisar todos os pontos do projeto que configuram ou usam conexões com o Postgres (principalmente em produção/Heroku) para evitar o erro **"too many connections for role ..."** e erros 500 nas rotas da API.

---

## 1. Resumo do que já foi corrigido

- **TenantMiddleware** (`backend/tenants/middleware.py`): ao adicionar o banco do tenant em `settings.DATABASES`, passou a usar `conn_max_age=0` e `CONN_MAX_AGE=0` (e `CONN_HEALTH_CHECKS=False`). A conexão do tenant é fechada ao fim do request, evitando acúmulo por tenant no dyno web.

---

## 2. Configuração do banco `default` (produção)

- **Arquivo:** `backend/config/settings_production.py`
- **Configuração:** `conn_max_age` lido de `CONN_MAX_AGE` (env), padrão **60** segundos; `connect_timeout=10`.
- **Conclusão:** OK. O `default` usa um único valor moderado (60s); não é a principal causa do estouro (o problema era a soma default + muitos tenants com 600s).

---

## 3. Pontos que adicionam bancos de tenant em `DATABASES`

Cada vez que um código adiciona um entry em `settings.DATABASES` com `CONN_MAX_AGE` alto (ex.: 600), essa conexão pode ficar aberta por vários minutos. Em cenários com muitos tenants e vários workers/dynos, isso leva a "too many connections".

### 3.1 TenantMiddleware (já corrigido)

- **Arquivo:** `backend/tenants/middleware.py`
- **Uso:** A cada request, se o tenant ainda não estiver em `DATABASES`, o middleware adiciona.
- **Status:** Usa `CONN_MAX_AGE=0` e `conn_max_age=0`. Nenhum ajuste adicional necessário.

### 3.2 Superadmin – serializers (corrigido nesta análise)

- **Arquivo:** `backend/superadmin/serializers.py`
- **Uso:** No fluxo de criação/configuração de loja (schema), o serializer adiciona o banco do tenant em `DATABASES` com `conn_max_age=600` e `CONN_MAX_AGE=600`.
- **Risco:** Esse fluxo pode ser acionado por request (ex.: superadmin criando loja). Uma conexão por tenant com 600s contribui para o total.
- **Ajuste:** Usar `conn_max_age=0` e `CONN_MAX_AGE=0` (e `CONN_HEALTH_CHECKS=False`) ao adicionar o tenant, alinhado ao middleware.

### 3.3 WhatsApp tasks (corrigido nesta análise)

- **Arquivo:** `backend/whatsapp/tasks.py`
- **Uso:** A função `_ensure_loja_db(loja)` garante que o banco da loja está em `DATABASES` para workers Celery (sem request). Usava `conn_max_age=600` e não definia `CONN_MAX_AGE` no dict.
- **Risco:** Cada worker pode processar várias lojas; cada loja adicionada ficava com conexão reutilizada por 10 min. Vários workers × várias lojas = muitas conexões ativas.
- **Ajuste:** Usar `conn_max_age=0` e `CONN_MAX_AGE=0` em `_ensure_loja_db`, para que a conexão seja fechada após o uso na task.

### 3.4 Superadmin – views (criação de banco SQLite)

- **Arquivo:** `backend/superadmin/views.py`
- **Uso:** Trecho que monta `DATABASES[db_name]` para SQLite com `CONN_MAX_AGE=0`.
- **Conclusão:** Só vale para ambiente com SQLite (ex.: local). Em produção com Postgres não é esse trecho que cria o tenant; não requer alteração.

---

## 4. Comandos de management e scripts

Os comandos abaixo adicionam bancos de tenant com `CONN_MAX_AGE=600` (ou `conn_max_age=600`):

- `migrate_all_lojas.py`
- `popular_loja_clinica_beleza.py`
- `verificar_clinica_beleza.py`
- `limpar_dados_clinica_beleza.py`
- `vincular_owner_profissional_clinica_beleza.py`
- `setup_loja_schema.py`

**Conclusão:** São processos one-off (ex.: `heroku run python manage.py ...`). O processo termina e as conexões são encerradas. O impacto no limite de conexões é temporário durante a execução. Para consistência e menor pico de conexões ao rodar vários comandos em paralelo, pode-se opcionalmente reduzir para `CONN_MAX_AGE=0` nesses comandos; não é prioritário para o erro 500 em produção, que vem do tráfego web e das tasks.

---

## 5. Uso de `connection.cursor()` e conexões brutas

- Vários arquivos usam `with connection.cursor() as cursor:` ou `connection.cursor()`. Isso usa a conexão do Django (do `default` ou do alias passado com `using=...`), respeitando `CONN_MAX_AGE` do respectivo entry em `DATABASES`. Não criam conexões extras além das já configuradas.
- Nenhum uso de pool externo ou abertura de conexão raw fora do Django foi identificado como causa do problema.

---

## 6. Configuração base (settings.py) e local

- **config/settings.py:** Define `CONN_MAX_AGE=600` para SQLite (default, suporte, loja_template, lojas). Usado em desenvolvimento; em produção o que vale é `settings_production.py`.
- **config/settings_local.py:** Usa `conn_max_age=600` para o `default` quando usa Postgres local. Apenas para desenvolvimento.

Nenhum desses altera o comportamento em produção no Heroku.

---

## 7. Recomendações adicionais (opcional)

- **PgBouncer / connection pool:** No Heroku, usar o add-on PgBouncer (ou pooler do Postgres) na URL de conexão reduz o número de conexões reais no Postgres e ajuda em picos. O ajuste de `CONN_MAX_AGE=0` nos tenants já reduz muito o acúmulo; o pool é uma camada extra de proteção.
- **Variável de ambiente:** Em produção, manter `CONN_MAX_AGE=60` (ou menor) para o `default` em `settings_production.py` é suficiente; pode ser controlado por `CONN_MAX_AGE` no env.
- **Monitoramento:** Acompanhar métricas de conexões no Heroku Postgres e o número de dynos/workers para garantir que (dynos × conexões por processo) não se aproxime do limite do plano.

---

## 8. Alterações aplicadas nesta análise

1. **backend/tenants/middleware.py** – Já estava com `CONN_MAX_AGE=0` e `conn_max_age=0` para tenant.
2. **backend/superadmin/serializers.py** – Ajustado para usar `conn_max_age=0`, `CONN_MAX_AGE=0` e `CONN_HEALTH_CHECKS=False` ao adicionar o banco do tenant.
3. **backend/whatsapp/tasks.py** – Ajustado `_ensure_loja_db` para usar `conn_max_age=0` e `CONN_MAX_AGE=0` ao adicionar o banco do tenant.

Com isso, todos os caminhos que adicionam bancos de tenant em tempo de request ou em workers passam a liberar a conexão ao fim do uso, evitando acúmulo e reduzindo o risco de "too many connections".
