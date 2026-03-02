# Backup no Render – CORS, banco único e variáveis

Quando o frontend faz **failover** para o backend de backup no Render (`lwksistemas-backup-ewgo.onrender.com`), o navegador exige que as respostas tenham cabeçalhos CORS corretos **e** que o Render use o **mesmo banco de dados** que o Heroku para não mostrar dados diferentes.

---

## 1. CORS no backup (Render)

### O que foi ajustado no código

- **`config/settings_production.py`**: Se `CORS_ORIGINS` estiver vazio ou não estiver definido no ambiente, o backend usa uma lista padrão que inclui `https://lwksistemas.com.br` e `https://www.lwksistemas.com.br`.  
  Assim o backup no Render passa a aceitar requisições do frontend mesmo sem configurar CORS no painel.

### O que conferir no Render

1. **Variáveis de ambiente** (Dashboard do Render → serviço `lwksistemas-backup-ewgo` → Environment):
   - **`CORS_ORIGINS`**: pode ficar em branco (o código usa o default) ou ser algo como:
     ```text
     https://lwksistemas.com.br,https://www.lwksistemas.com.br
     ```
   - **`DJANGO_SETTINGS_MODULE`**: deve ser `config.settings_production`.

2. **Redeploy**: depois de alterar variáveis ou o código, faça um **redeploy** do serviço no Render para carregar as novas configurações.

3. **`render.yaml`**: o `render.yaml` do repositório já define `CORS_ORIGINS`; se o serviço foi criado a partir dele, não é obrigatório mudar nada no painel, mas vale conferir se o valor não foi sobrescrito ou apagado.

Depois do redeploy, as chamadas do frontend (`lwksistemas.com.br`) para o backup no Render deixam de gerar erro de CORS.

---

## 2. Banco Único para Heroku e Render

Para que o Render seja um **backup real** (com os mesmos dados das lojas), Heroku e Render devem usar o **mesmo banco PostgreSQL**.

### Passo a passo (recomendado: usar o Postgres do Heroku)

1. **Pegar o `DATABASE_URL` do Heroku**  
   No seu computador, na pasta do projeto:
   ```bash
   heroku config:get DATABASE_URL --app lwksistemas
   ```
   Copie o valor retornado (URL completa do Postgres do Heroku).

2. **Configurar o mesmo `DATABASE_URL` no Render**  
   - Acesse o painel do Render → serviço `lwksistemas-backup-ewgo` → **Environment**.
   - Encontre a variável **`DATABASE_URL`**.
   - Substitua o valor atual pela **mesma URL** que você copiou do Heroku.
   - Salve as mudanças.

3. **Redeploy no Render**  
   - Clique em **Manual Deploy → Deploy latest commit** (ou use o hook de deploy).
   - Aguarde o deploy completar.

Depois disso, **Heroku e Render** passam a ler e gravar no **mesmo banco**.

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
