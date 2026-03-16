# Deploy Frontend no Vercel (Monorepo)

O Next.js está na pasta `frontend/`. Para o deploy funcionar:

## 1. Configurar Root Directory no Vercel

1. Acesse [Vercel Dashboard](https://vercel.com/dashboard) → projeto **lwksistemas**
2. **Settings** → **General** → **Root Directory**
3. Clique em **Edit** e defina: `frontend`
4. Salve

## 2. Variáveis de Ambiente

Em **Settings** → **Environment Variables**, confira:

| Variável | Valor (Produção) |
|----------|------------------|
| `NEXT_PUBLIC_API_URL` | `https://lwksistemas-38ad47519238.herokuapp.com/api` |

## 3. Deploy via CLI

```bash
# Na raiz do projeto (não dentro de frontend)
vercel --prod
```

## 4. Forçar novo deploy (limpar cache)

No Dashboard: **Deployments** → último deploy → **⋯** → **Redeploy** → marque **Use existing Build Cache** como **desmarcado**
