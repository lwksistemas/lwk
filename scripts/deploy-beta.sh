#!/usr/bin/env bash
# Deploy completo homologação (beta): push staging + frontend + alias + API + schemas tenant.
#
# Uso:
#   bash scripts/deploy-beta.sh
#   bash scripts/deploy-beta.sh --skip-push    # só Vercel alias/deploy + Railway ensure
#   bash scripts/deploy-beta.sh --skip-railway # sem SSH ensure no backend
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/deploy-common.sh
source "$SCRIPT_DIR/deploy-common.sh"

SKIP_PUSH=false
SKIP_RAILWAY=false
for arg in "$@"; do
  case "$arg" in
    --skip-push) SKIP_PUSH=true ;;
    --skip-railway) SKIP_RAILWAY=true ;;
  esac
done

STAGING_API="https://lwks-backend-staging-staging.up.railway.app/api/superadmin/health/"
RAILWAY_SERVICE="lwks-backend-staging"

cd "$REPO_ROOT"
git_require_clean_or_stash

CURRENT_BRANCH="$(git branch --show-current)"
if [[ "$CURRENT_BRANCH" != "staging" ]]; then
  log "Checkout staging (era: $CURRENT_BRANCH)"
  git checkout staging
fi

if [[ "$SKIP_PUSH" == "false" ]]; then
  if git rev-parse --verify origin/staging >/dev/null 2>&1; then
    AHEAD=$(git rev-list --count origin/staging..HEAD 2>/dev/null || echo 0)
  else
    AHEAD=1
  fi
  if [[ "$AHEAD" -gt 0 ]]; then
    log "Push origin staging ($AHEAD commit(s) à frente)..."
    git push -u origin staging
  else
    log "staging já está em dia com origin/staging"
  fi
fi

EXPECTED_BUILD="$(get_expected_build_id)"
wait_api_health "$STAGING_API" 900 "$EXPECTED_BUILD" || warn "Backend staging pode ainda estar deployando"

log "Deploy frontend (preview) + alias beta..."
DEPLOY_URL="$(vercel_deploy_preview || true)"
if [[ -z "${DEPLOY_URL:-}" ]]; then
  warn "Falha no vercel deploy — tentando script de alias da branch staging"
  bash "$REPO_ROOT/frontend/scripts/vercel-link-beta-staging.sh"
else
  link_beta_domains "$DEPLOY_URL"
fi

verify_beta_csp
log "Beta: https://beta.lwksistemas.com.br"

if [[ "$SKIP_RAILWAY" == "false" ]]; then
  railway_tenant_ensure staging "$RAILWAY_SERVICE"
fi

log "Deploy beta concluído. Teste com Ctrl+Shift+R no navegador."
