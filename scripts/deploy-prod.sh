#!/usr/bin/env bash
# Deploy produção: merge staging→main, push, Vercel prod, API, schemas, realinhar beta.
#
# Uso:
#   bash scripts/deploy-prod.sh
#   bash scripts/deploy-prod.sh --skip-merge   # não faz merge staging→main (main já pronta)
#   bash scripts/deploy-prod.sh --skip-beta-sync  # não faz merge main→staging no final
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/deploy-common.sh
source "$SCRIPT_DIR/deploy-common.sh"

SKIP_MERGE=false
SKIP_BETA_SYNC=false
for arg in "$@"; do
  case "$arg" in
    --skip-merge) SKIP_MERGE=true ;;
    --skip-beta-sync) SKIP_BETA_SYNC=true ;;
  esac
done

PROD_API="https://api.lwksistemas.com.br/api/superadmin/health/"
RAILWAY_SERVICE="lwks-backend"

cd "$REPO_ROOT"
git_require_clean_or_stash

if [[ "$SKIP_MERGE" == "false" ]]; then
  log "Merge staging → main..."
  git checkout main
  git pull origin main
  git merge staging -m "merge staging → main (deploy produção)"
else
  git checkout main
  git pull origin main 2>/dev/null || true
fi

EXPECTED_BUILD="$(get_expected_build_id)"
log "Build esperado (Dockerfile.railway): $EXPECTED_BUILD"

log "Push origin main..."
git push origin main

wait_api_health "$PROD_API" 900 "$EXPECTED_BUILD" || warn "Backend produção pode ainda estar deployando"

log "Vercel deploy --prod (garante frontend mesmo se último commit foi só backend)..."
vercel_deploy_production || warn "vercel deploy --prod falhou — verificar painel Vercel"

if railway whoami >/dev/null 2>&1; then
  railway_tenant_ensure production "$RAILWAY_SERVICE"
else
  warn "railway CLI não logado — pulando ensure tenant (rode: cd backend && railway login)"
fi

if [[ "$SKIP_BETA_SYNC" == "false" ]]; then
  log "Alinhar beta: merge main → staging..."
  git checkout staging
  git pull origin staging 2>/dev/null || true
  git merge main -m "merge main → staging (pós deploy produção)"
  git push origin staging
  git checkout main
  log "Para atualizar domínio beta: bash scripts/deploy-beta.sh --skip-push"
fi

log "Produção: https://lwksistemas.com.br"
log "Deploy produção concluído."
