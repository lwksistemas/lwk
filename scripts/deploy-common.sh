#!/usr/bin/env bash
# Funções compartilhadas pelos scripts deploy-beta.sh e deploy-prod.sh
set -euo pipefail

export PATH="${HOME}/.local/npm-global/bin:${PATH}"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

log() { echo ">> $*" >&2; }
warn() { echo ">> WARN: $*" >&2; }

get_expected_build_id() {
  grep -m1 '^ARG BUILD_ID=' "$REPO_ROOT/Dockerfile.railway" | sed 's/ARG BUILD_ID=//'
}

wait_api_health() {
  local url="$1"
  local max_wait="${2:-600}"
  local expected_build="${3:-}"
  local elapsed=0

  log "Aguardando API: $url"
  while [[ $elapsed -lt $max_wait ]]; do
    local resp status build
    resp=$(curl -sf "$url" 2>/dev/null) || { sleep 15; elapsed=$((elapsed + 15)); continue; }
    status=$(echo "$resp" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status',''))" 2>/dev/null || echo "")
    build=$(echo "$resp" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('build',''))" 2>/dev/null || echo "")
    if [[ "$status" == "healthy" ]]; then
      if [[ -z "$expected_build" ]] || [[ "$build" == "$expected_build" ]]; then
        log "API OK (build=${build:-?})"
        return 0
      fi
      log "API healthy, build=$build (esperado $expected_build) — aguardando deploy Railway..."
    fi
    sleep 15
    elapsed=$((elapsed + 15))
  done
  warn "Timeout (${max_wait}s) aguardando $url"
  return 1
}

extract_vercel_deploy_url() {
  local file="${1:-/tmp/lwk-vercel-deploy.out}"
  grep -oE 'https://frontend-[a-z0-9]+-lwks-projects[^ "'\''[:space:]]*' "$file" | tail -1
}

vercel_deploy_preview() {
  cd "$REPO_ROOT"
  log "Vercel deploy (preview) a partir da raiz do repo..."
  if ! npx vercel deploy --yes > /tmp/lwk-vercel-deploy.out 2>&1; then
    cat /tmp/lwk-vercel-deploy.out >&2
    return 1
  fi
  cat /tmp/lwk-vercel-deploy.out >&2
  extract_vercel_deploy_url /tmp/lwk-vercel-deploy.out
}

vercel_deploy_production() {
  cd "$REPO_ROOT"
  log "Vercel deploy --prod a partir da raiz do repo..."
  if ! npx vercel deploy --prod --yes > /tmp/lwk-vercel-deploy.out 2>&1; then
    cat /tmp/lwk-vercel-deploy.out >&2
    return 1
  fi
  cat /tmp/lwk-vercel-deploy.out >&2
  extract_vercel_deploy_url /tmp/lwk-vercel-deploy.out
}

link_beta_domains() {
  local target="$1"
  target=$(printf '%s\n' "$target" | grep -oE 'https://frontend-[a-z0-9]+-lwks-projects[^[:space:]]*' | tail -1)
  if [[ -z "$target" ]]; then
    warn "URL de deploy Vercel inválida — não foi possível criar alias beta"
    return 1
  fi
  cd "$REPO_ROOT/frontend"
  for domain in beta.lwksistemas.com.br staging.lwksistemas.com.br; do
    log "Alias $domain → $target"
    npx vercel alias set "$target" "$domain"
  done
}

verify_beta_csp() {
  curl -sI "https://beta.lwksistemas.com.br/superadmin/login" | tr '\r' '\n' | grep -i connect-src || true
}

railway_tenant_ensure() {
  local environment="$1"
  local service="$2"
  cd "$REPO_ROOT/backend"
  railway environment "$environment" >/dev/null 2>&1 || true
  log "Schemas tenant ($service / $environment)..."
  railway ssh --service "$service" python manage.py ensure_all 2>&1 | tail -20 || warn "ensure_all falhou (ver logs Railway)"
  railway ssh --service "$service" python manage.py corrigir_schema_clinica_beleza 2>&1 | tail -15 || warn "corrigir_schema_clinica_beleza falhou"
  railway ssh --service "$service" python manage.py corrigir_schema_crm 2>&1 | tail -15 || warn "corrigir_schema_crm falhou"
  railway ssh --service "$service" python manage.py ensure_crm_financeiro_tabelas 2>&1 | tail -10 || true
}

git_require_clean_or_stash() {
  if ! git diff --quiet || ! git diff --cached --quiet; then
    warn "Working tree com alterações não commitadas — continue por sua conta."
  fi
}
