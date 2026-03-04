# Backup no Render – CORS, banco único e variáveis

Quando o frontend faz **failover** para o backend de backup no Render (`lwksistemas-backup.onrender.com`), o navegador exige que as respostas tenham cabeçalhos CORS corretos **e** que o Render use o **mesmo banco de dados** que o Heroku para as lojas aparecerem nos dois.

---

## 1. CORS no backup (Render)

### O que foi ajustado no código

- **`config/settings_production.py`**: Se `CORS_ORIGINS` estiver vazio ou não estiver definido no ambiente, o backend usa uma lista padrão que inclui `https://lwksistemas.com.br` e `https://www.lwksistemas.com.br`.  
  Assim o backup no Render passa a aceitar requisições do frontend mesmo sem configurar CORS no painel.

### O que conferir no Render

1. **Variáveis de ambiente** (Dashboard do Render → serviço `lwksistemas-backup` → Environment):
   - **`CORS_ORIGINS`**: pode ficar em branco (o código usa o default) ou ser algo como:
     ```text
     https://lwksistemas.com.br,https://www.lwksistemas.com.br
     ```
   - **`DJANGO_SETTINGS_MODULE`**: deve ser `config.settings_production`.

2. **Redeploy**: depois de alterar variáveis ou o código, faça um **redeploy** do serviço no Render para carregar as novas configurações.

3. **`render.yaml`**: o `render.yaml` do repositório já define `CORS_ORIGINS`; se o serviço foi criado a partir dele, não é obrigatório mudar nada no painel, mas vale conferir se o valor não foi sobrescrito ou apagado.

Depois do redeploy, as chamadas do frontend (`lwksistemas.com.br`) para o backup no Render deixam de gerar erro de CORS.

---

## 2. Banco Único para Heroku e Render (obrigatório)

**Se as lojas somem ao trocar para o Render**, é porque o Render está usando outro banco. Heroku e Render **precisam** usar o **mesmo** `DATABASE_URL` (Postgres do Heroku).

### Passo a passo

1. **Obter o `DATABASE_URL` do Heroku**  
   No terminal, na pasta do projeto:
   ```bash
   heroku config:get DATABASE_URL --app lwksistemas
   ```
   (Se o nome do app Heroku for outro, use `--app SEU_APP_NAME`.)  
   Copie **todo** o valor retornado (começa com `postgres://` ou `postgresql://`).

2. **Definir o mesmo `DATABASE_URL` no Render**  
   - Acesse [Dashboard Render](https://dashboard.render.com) → serviço **lwksistemas-backup** → **Environment**.
   - Se já existir **`DATABASE_URL`**, edite e **substitua** pelo valor copiado do Heroku.
   - Se não existir, clique em **Add Environment Variable**: Key = `DATABASE_URL`, Value = (valor do Heroku).
   - Salve.

3. **Redeploy no Render**  
   - No serviço **lwksistemas-backup**, use **Manual Deploy → Deploy latest commit**.
   - Aguarde o deploy terminar.

Depois disso, **Heroku e Render** usam o mesmo banco e as **lojas aparecem nos dois**.

---

## 3. Failover para lojas (flag no frontend)

Por segurança, o frontend só faz failover automático para **rotas do superadmin** por padrão.  
Para permitir failover também para **rotas de loja** (login, `info_publica`, `auth/loja`, etc.) você precisa:

1. Garantir que **Heroku e Render já estão usando o MESMO `DATABASE_URL`** (seção anterior).
2. No **Vercel** (ou no `.env.production` do frontend), definir:
   ```env
   NEXT_PUBLIC_ENABLE_LOJA_FAILOVER=true
   ```

Com isso:
- Se o **Heroku** cair, o frontend pode repetir também as requisições de loja no Render.
- Como os dois usam o mesmo banco, as lojas veem sempre os mesmos dados (sem divergência).
