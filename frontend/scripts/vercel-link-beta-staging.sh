#!/usr/bin/env bash
# Liga beta.lwksistemas.com.br (e staging.lwksistemas.com.br) ao deploy mais
# recente da branch Git "staging" na Vercel.
#
# IMPORTANTE: apontar o domínio para frontend-git-staging-....vercel.app nem sempre
# atualiza beta (fica preso em deploy antigo). Este script resolve o deploy real
# atrás da URL da branch e aponta os domínios customizados diretamente para ele.
#
# Uso (após push na staging ou se o beta não refletir mudanças):
#   cd frontend && bash scripts/vercel-link-beta-staging.sh
#
# Configuração permanente (painel): Domains → beta → Preview → branch staging
# Requer: vercel login (conta lwksistemas@gmail.com)

set -euo pipefail

STAGING_BRANCH_HOST="frontend-git-staging-lwks-projects-48afd555.vercel.app"
DOMAINS=(
  "beta.lwksistemas.com.br"
  "staging.lwksistemas.com.br"
)

echo ">> Resolvendo deploy atual da branch staging..."
DEPLOY_HOST=$(npx vercel alias ls 2>/dev/null | awk -v branch="$STAGING_BRANCH_HOST" '$2 == branch {print $1; exit}')

if [[ -z "$DEPLOY_HOST" ]]; then
  echo ">> Alias da branch não encontrado — usando URL estável da branch"
  TARGET="https://${STAGING_BRANCH_HOST}"
else
  echo ">> Deploy staging: $DEPLOY_HOST"
  TARGET="https://${DEPLOY_HOST}"
fi

for domain in "${DOMAINS[@]}"; do
  echo ">> Apontando $domain → $TARGET"
  npx vercel alias set "$TARGET" "$domain"
done

echo ">> Verificando CSP (deve incluir API staging):"
curl -sI "https://beta.lwksistemas.com.br/superadmin/login" | tr '\r' '\n' | grep -i connect-src || true
echo ">> OK"
