#!/usr/bin/env bash
# Liga beta.lwksistemas.com.br (e staging.lwksistemas.com.br) ao deploy mais
# recente da branch Git "staging" na Vercel.
#
# IMPORTANTE: apontar o domínio para frontend-git-staging-....vercel.app nem sempre
# atualiza beta (fica preso em deploy antigo). Este script resolve o deploy real
# atrás da URL da branch e aponta os domínios customizados diretamente para ele.
#
# Uso:
#   cd frontend && bash scripts/vercel-link-beta-staging.sh
#   cd frontend && bash scripts/vercel-link-beta-staging.sh --deploy
#     → força novo build na branch atual e aponta beta para esse deploy
#
# Deploy completo recomendado: bash scripts/deploy-beta.sh (na raiz do repo)
#
# Configuração permanente (painel): Domains → beta → Preview → branch staging
# Requer: vercel login (conta lwksistemas@gmail.com)

set -euo pipefail

export PATH="${HOME}/.local/npm-global/bin:${PATH}"

STAGING_BRANCH_HOST="frontend-git-staging-lwks-projects-48afd555.vercel.app"
DOMAINS=(
  "beta.lwksistemas.com.br"
  "staging.lwksistemas.com.br"
)
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

FORCE_DEPLOY=false
for arg in "$@"; do
  [[ "$arg" == "--deploy" ]] && FORCE_DEPLOY=true
done

resolve_staging_deploy_url() {
  if [[ "$FORCE_DEPLOY" == "true" ]]; then
    echo ">> Forçando novo deploy Vercel (preview)..." >&2
    cd "$REPO_ROOT"
    npx vercel deploy --yes 2>&1 | tee /tmp/lwk-vercel-link-deploy.out >&2
    local url
    url=$(grep -oE 'https://frontend-[a-z0-9]+-lwks-projects[^ "'\''[:space:]]*' /tmp/lwk-vercel-link-deploy.out | tail -1)
    if [[ -n "$url" ]]; then
      echo "$url"
      return 0
    fi
    echo ">> Deploy falhou — usando alias da branch" >&2
  fi

  echo ">> Resolvendo deploy atual da branch staging..." >&2
  local deploy_host
  deploy_host=$(npx vercel alias ls 2>/dev/null | awk -v branch="$STAGING_BRANCH_HOST" '$2 == branch {print $1; exit}')

  if [[ -z "$deploy_host" ]]; then
    # Fallback: último preview Ready na listagem
    deploy_host=$(npx vercel ls frontend 2>/dev/null | awk '/Preview/ && /Ready/ {print $2; exit}')
  fi

  if [[ -z "$deploy_host" ]]; then
    echo "https://${STAGING_BRANCH_HOST}"
  else
    echo "https://${deploy_host}"
  fi
}

TARGET="$(resolve_staging_deploy_url)"
echo ">> Deploy staging alvo: $TARGET"

for domain in "${DOMAINS[@]}"; do
  echo ">> Apontando $domain → $TARGET"
  npx vercel alias set "$TARGET" "$domain"
done

echo ">> Verificando CSP (deve incluir API staging):"
curl -sI "https://beta.lwksistemas.com.br/superadmin/login" | tr '\r' '\n' | grep -i connect-src || true
echo ">> OK"
