#!/usr/bin/env bash
# Liga beta.lwksistemas.com.br (e staging.lwksistemas.com.br) ao deploy estável
# da branch Git "staging" na Vercel — atualiza a cada push na branch staging.
#
# Uso (se o domínio voltar a apontar para Production):
#   cd frontend && bash scripts/vercel-link-beta-staging.sh
#
# Requer: vercel login (conta lwksistemas@gmail.com)

set -euo pipefail

STAGING_BRANCH_URL="frontend-git-staging-lwks-projects-48afd555.vercel.app"
DOMAINS=(
  "beta.lwksistemas.com.br"
  "staging.lwksistemas.com.br"
)

for domain in "${DOMAINS[@]}"; do
  echo ">> Apontando $domain → $STAGING_BRANCH_URL"
  npx vercel alias set "$STAGING_BRANCH_URL" "$domain"
done

echo ">> Verificando CSP (deve incluir API staging):"
curl -sI "https://beta.lwksistemas.com.br/superadmin/login" | tr '\r' '\n' | grep -i connect-src || true
echo ">> OK"
