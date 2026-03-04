# Render: usar o mesmo banco do Heroku (lojas aparecerem no backup)

Para o serviço **lwksistemas-backup** no Render mostrar as mesmas lojas do Heroku, ele precisa usar o **mesmo PostgreSQL**. Isso é feito pela variável de ambiente `DATABASE_URL`.

## Passo a passo

### 1. Obter o valor atual do Heroku

No terminal (com [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli) instalado e logado):

```bash
heroku config:get DATABASE_URL -a lwksistemas
```

Copie a URL que aparecer (começa com `postgres://` ou `postgresql://`).

### 2. Definir no Render

1. Acesse o [Dashboard do Render](https://dashboard.render.com).
2. Abra o serviço **lwksistemas-backup**.
3. No menu lateral, clique em **Environment**.
4. Localize a variável **DATABASE_URL**:
   - Se existir, clique em **Edit** e cole o valor copiado do Heroku.
   - Se não existir, clique em **Add Environment Variable**, nome `DATABASE_URL` e valor igual ao do Heroku.
5. Salve (**Save Changes**).
6. Faça um **Manual Deploy** (ou aguarde o próximo deploy) para o serviço reiniciar com a nova variável.

### 3. Conferir

- Abra: https://lwksistemas-backup.onrender.com/api/superadmin/health/  
  Na resposta JSON deve aparecer `"lojas_count"` com o número de lojas (não 0).
- No frontend, com o seletor em **lwksistemas-backup**, o dashboard do superadmin deve listar as mesmas lojas do Heroku.

## Observação

O `render.yaml` do repositório pode conter um `DATABASE_URL` de exemplo ou antigo. As variáveis definidas no **Environment** do Dashboard do Render têm prioridade. Por isso, sempre sincronize o valor com o Heroku pelo Dashboard quando quiser que o backup use o mesmo banco.
