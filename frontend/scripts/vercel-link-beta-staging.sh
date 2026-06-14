#!/usr/bin/env bash
# Liga beta.lwksistemas.com.br e staging.lwksistemas.com.br ao deploy estável
# da branch Git "staging" na Vercel (atualiza automaticamente a cada push).
#
# Uso (uma vez, ou se o domínio voltar a apontar para Production):
#   cd frontend && bash scripts/vercel-link-beta-staging.sh
#
# Requer: vercel login (conta lwksistemas@gmail.com)

set -euo pipefail

STAGING_BRANCH_URL="frontend-git-staging-lwks-projects-48afd555.vercel.app"
BETA_DOMAIN="beta.lwksistemas.com.br"
STAGING_DOMAIN="staging.lwksistemas.com.br"

echo ">> Apontando $BETA_DOMAIN → $STAGING_BRANCH_URL"
npx vercel alias set "$STAGING_BRANCH_URL" "$BETA_DOMAIN"

echo ">> Apontando $STAGING_DOMAIN → $STAGING_BRANCH_URL"
npx vercel alias set "$STAGING_BRANCH_URL" "$STAGING_DOMAIN"

echo ">> OK. Teste: curl -sI https://$BETA_DOMAIN/superadmin/login | grep connect-src"
