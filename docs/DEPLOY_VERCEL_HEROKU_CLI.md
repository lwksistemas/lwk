# Deploy via CLI: Vercel (frontend) e Heroku (backend)

## Pré-requisitos

- **Vercel:** conta em [vercel.com](https://vercel.com) e CLI instalada.
- **Heroku:** conta em [heroku.com](https://heroku.com), CLI instalada e app criado.
- Git com alterações commitadas (recomendado).

---

## 1. Instalar CLIs

```bash
# Vercel CLI
npm i -g vercel

# Heroku CLI (Linux)
# https://devcenter.heroku.com/articles/heroku-cli
# Ou: npm i -g heroku
```

---

## 2. Deploy do **frontend** (Vercel)

```bash
# Na raiz do projeto
cd /home/luiz/Documents/lwksistemas/frontend

# Login (só na primeira vez)
vercel login

# Deploy de produção (usa vercel.json e build do Next.js)
vercel --prod
```

- O primeiro deploy pode pedir para linkar o projeto (escolher projeto existente ou criar um).
- A raiz do app para a Vercel deve ser a pasta **frontend** (onde está `package.json` e `next.config.*`). Se o projeto na Vercel foi criado com a raiz na pasta `frontend`, esses comandos já fazem o deploy correto.
- Se o projeto Vercel estiver na **raiz do repositório**, na Vercel (Dashboard) configure **Root Directory** = `frontend` e **Build Command** = `npm run build` (ou `yarn build`).

**Variáveis de ambiente:** configure no Dashboard da Vercel (Settings → Environment Variables) as que o frontend precisa (ex.: `NEXT_PUBLIC_API_URL`).

---

## 3. Deploy do **backend** (Heroku)

```bash
# Na raiz do repositório (onde está o Procfile)
cd /home/luiz/Documents/lwksistemas

# Ver remoto Heroku (se já existir)
git remote -v

# Se ainda não tiver o remoto heroku:
# heroku git:remote -a NOME_DA_SUA_APP

# Deploy (branch main → Heroku main)
git push heroku main
```

Se sua branch principal for `master`:

```bash
git push heroku master
```

Se estiver em outra branch (ex.: `develop`) e quiser subir como `main` no Heroku:

```bash
git push heroku develop:main
```

O **Procfile** na raiz define:

- `web`: Gunicorn (Django).
- `worker`: Django-Q (quando existir).
- `release`: migrations antes de subir.

**Variáveis e add-ons:** configure no Heroku (Dashboard da app → Settings → Config Vars e add-ons como PostgreSQL, Redis, etc.).

---

## 4. Script único (frontend + backend)

Na raiz do projeto:

```bash
chmod +x scripts/deploy-vercel-heroku.sh
./scripts/deploy-vercel-heroku.sh all
```

Só frontend:

```bash
./scripts/deploy-vercel-heroku.sh frontend
```

Só backend:

```bash
./scripts/deploy-vercel-heroku.sh backend
```

---

## 5. Comandos úteis

**Vercel**

```bash
cd frontend
vercel              # deploy preview
vercel --prod       # deploy produção
vercel env ls       # listar variáveis
vercel logs         # logs do deploy
```

**Heroku**

```bash
heroku logs --tail -a NOME_DA_APP    # logs em tempo real
heroku run bash -a NOME_DA_APP       # shell no dyno
heroku run "cd backend && python manage.py migrate" -a NOME_DA_APP
heroku config -a NOME_DA_APP         # listar config vars
```

Substitua `NOME_DA_APP` pelo nome da aplicação Heroku (ex.: `lwksistemas`).

---

## 6. Verificação pós-deploy

Após deploy, rode a verificação do sistema (frontend + backend em produção):

```bash
./scripts/verificar-sistema.sh
```

Detalhes em **docs/VERIFICACAO_SISTEMA.md**.

---

## 7. Resumo rápido

| Onde   | Comando (na pasta indicada)        |
|--------|------------------------------------|
| Frontend | `cd frontend && vercel --prod`   |
| Backend  | `git push heroku main` (na raiz) |
