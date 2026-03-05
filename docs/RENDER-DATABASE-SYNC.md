# Render: usar o mesmo banco do Heroku (lojas aparecerem no backup)

Para o serviço **lwksistemas-backup** no Render mostrar as mesmas lojas do Heroku, ele precisa usar o **mesmo PostgreSQL**. Isso é feito pela variável de ambiente **DATABASE_URL** no Dashboard do Render.

---

## Checklist rápido

- [ ] **1.** Rodar no terminal: `heroku config:get DATABASE_URL -a lwksistemas` e copiar a URL inteira
- [ ] **2.** Abrir [Render Dashboard](https://dashboard.render.com) → serviço **lwksistemas-backup** → **Environment**
- [ ] **3.** Editar ou criar a variável **DATABASE_URL** e colar o valor do Heroku (substituir qualquer outro valor que estiver aí)
- [ ] **4.** Clicar em **Save Changes**
- [ ] **5.** Ir em **Manual Deploy** e disparar um novo deploy
- [ ] **6.** Após o deploy, abrir de novo o dashboard com backend Render e conferir se as lojas aparecem

---

## Passo a passo detalhado

### 1. Obter o valor do Heroku

No terminal (com [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli) instalado e logado no app `lwksistemas`):

```bash
heroku config:get DATABASE_URL -a lwksistemas
```

**Copie a URL inteira** que aparecer (começa com `postgres://` ou `postgresql://`). Não apague nenhum caractere.

### 2. Definir no Render

1. Acesse o [Dashboard do Render](https://dashboard.render.com).
2. Clique no serviço **lwksistemas-backup**.
3. No menu lateral esquerdo, clique em **Environment**.
4. Procure a variável **DATABASE_URL**:
   - **Se existir:** clique no lápis (Edit), apague o valor atual e **cole o valor que você copiou do Heroku**.
   - **Se não existir:** clique em **Add Environment Variable**, em **Key** coloque `DATABASE_URL` e em **Value** cole o valor do Heroku.
5. Clique em **Save Changes** (canto superior direito da seção Environment).
6. Vá na aba **Manual Deploy** (ou no topo, botão **Manual Deploy**) e clique para iniciar um novo deploy. Espere terminar.

> **Importante:** Se o Render tiver criado uma `DATABASE_URL` própria (por exemplo ao conectar um banco PostgreSQL do Render), **substitua** por completo pelo valor do Heroku. O backup precisa usar o **mesmo** banco do Heroku, não um banco separado do Render.

### 3. Conferir

- Abra: https://lwksistemas-backup.onrender.com/api/superadmin/health/  
  No JSON deve aparecer `"lojas_count": 4` (ou outro número > 0), não `0`.
- No site https://lwksistemas.com.br/superadmin/dashboard, com o seletor de backend em **Render**, o painel deve mostrar Total de Lojas > 0 e a lista de lojas.

---

## Se ainda mostrar 0 lojas

- Confirme que salvou a variável e fez **Manual Deploy** depois.
- Confirme que colou a URL **inteira** do Heroku, sem espaços no início/fim.
- No Render, em **Environment**, confirme que o **Key** é exatamente `DATABASE_URL` (tudo maiúsculo).

---

## CORS e erro "blocked by CORS policy" / 503

Se ao usar o backend **Render** (no seletor ou no failover) aparecer **CORS** ou **503 (Service Unavailable)**:

### 1. Usar a URL correta do backup (evita CORS + 503)

O serviço do blueprint é **lwksistemas-backup** e a URL correta é:

- **https://lwksistemas-backup.onrender.com**

**Não use** `https://lwksistemas-backup-ewgo.onrender.com` — essa URL antiga/outra instância costuma gerar CORS e 503.

**No Vercel** (onde o frontend é buildado, a variável é aplicada no build):

1. Acesse [Vercel Dashboard](https://vercel.com) → seu projeto (frontend) → **Settings** → **Environment Variables**.
2. Procure **NEXT_PUBLIC_API_BACKUP_URL**.
3. Se existir com valor `...-ewgo.onrender.com`, clique em **Edit** e troque para:  
   **Value:** `https://lwksistemas-backup.onrender.com`  
   Se não existir, **Add New** → Key: `NEXT_PUBLIC_API_BACKUP_URL`, Value: `https://lwksistemas-backup.onrender.com`.
4. Salve e faça um **redeploy** do projeto (Deployments → ⋮ no último deploy → Redeploy), pois variáveis `NEXT_PUBLIC_*` entram no build.

### 2. CORS no Render

O backend precisa enviar `Access-Control-Allow-Origin` para o frontend. No Render → **lwksistemas-backup** → **Environment** deve existir:

- **Key:** `CORS_ORIGINS`
- **Value:** `https://lwksistemas.com.br,https://www.lwksistemas.com.br`

(O `render.yaml` do repositório já inclui isso; ao sincronizar o Blueprint, a variável é aplicada.)

### 3. 503 no plano free (serviço “dormindo”)

No plano **free**, o Render desliga o serviço após inatividade. A primeira requisição depois disso pode receber **503** e a página de erro do Render **não** envia headers CORS, então o navegador mostra erro de CORS.

- **Solução:** espere alguns segundos e tente de novo (o serviço sobe em ~30–60 s) ou abra antes o health: https://lwksistemas-backup.onrender.com/api/superadmin/health/ para “acordar” o serviço.
- Para evitar 503 por inatividade, é necessário um plano pago no Render.
