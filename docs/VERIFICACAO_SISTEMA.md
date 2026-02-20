# Verificação do Sistema (Produção)

Script e critérios para conferir se frontend (Vercel) e backend (Heroku) estão respondendo corretamente.

## Executar verificação

Na raiz do projeto:

```bash
./scripts/verificar-sistema.sh
```

Variáveis opcionais (se usar outros domínios):

```bash
BACKEND_URL=https://sua-api.herokuapp.com FRONTEND_URL=https://seu-dominio.com ./scripts/verificar-sistema.sh
```

## O que é verificado

| Check | Descrição |
|-------|-----------|
| **API Root** | `GET /api/` — resposta JSON com `"status": "online"` |
| **Schema OpenAPI** | `GET /api/schema/` — opcional; 500 em alguns ambientes não falha o script |
| **API Superadmin** | `GET /api/superadmin/violacoes-seguranca/` — esperado 401 (exige autenticação) |
| **Página inicial** | Frontend raiz (200) |
| **Login Superadmin** | `/superadmin/login` (200) |
| **Login Suporte** | `/suporte/login` (200) |
| **Limpar cache** | `/limpar-cache.html` (200) |

## Após o deploy

Recomendado rodar a verificação depois de cada deploy:

```bash
./scripts/deploy-vercel-heroku.sh all
./scripts/verificar-sistema.sh
```

## Schema OpenAPI retornando 500

Se o Schema OpenAPI (`/api/schema/`) retornar 500 no Heroku, o script marca como aviso (⚠) e não falha. Possíveis causas: configuração de arquivos estáticos (DRF Spectacular) ou dependência de ambiente. Os endpoints da API e o frontend continuam funcionando.
