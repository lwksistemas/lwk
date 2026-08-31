#!/usr/bin/env bash
# Funções de deploy recortado (frontend | backend | all | infra).
# Não rebuildar Evolution/mídia em bug de tela ou API.

lwk_deploy_usage() {
  cat <<'EOF'
Uso: TARGET [app ...]

  frontend              só Next.js (tela / JS / CSS)
  backend [app ...]     API + worker; se informar app, migrate/ensure só dele
  all [app ...]         frontend + backend + worker (sem Evolution/mídia)
  infra                 Evolution e mídia

Apps: clinica_beleza  clinica_geral  crm_vendas  whatsapp  nfse_integration  cabeleireiro  hotel

Exemplos:
  bash scripts/deploy-beta-isolated.sh frontend
  bash scripts/deploy-beta-isolated.sh backend clinica_beleza
  bash scripts/deploy-prod-magalu.sh backend clinica_beleza whatsapp
EOF
}

lwk_compose_up_build() {
  local compose_file="$1"
  shift
  docker compose -f "$compose_file" up -d --build "$@"
}

lwk_backend_migrate() {
  local compose_file="$1"
  shift
  local apps=("$@")
  docker compose -f "$compose_file" exec -T backend python manage.py migrate --noinput
  if [[ ${#apps[@]} -gt 0 ]]; then
    echo "=== Schema pontual: ${apps[*]} ==="
    docker compose -f "$compose_file" exec -T backend python manage.py deploy_app "${apps[@]}"
  else
    echo "=== Schema completo (todas as lojas / apps) ==="
    docker compose -f "$compose_file" exec -T backend python manage.py migrate_all_lojas
    docker compose -f "$compose_file" exec -T backend python manage.py ensure_all
  fi
}

lwk_deploy_target() {
  local compose_file="$1"
  local target="$2"
  shift 2
  local apps=("$@")

  case "$target" in
    frontend)
      echo "=== Rebuild só frontend ==="
      lwk_compose_up_build "$compose_file" frontend
      ;;
    backend)
      echo "=== Rebuild só backend + worker ==="
      lwk_compose_up_build "$compose_file" backend worker
      lwk_backend_migrate "$compose_file" "${apps[@]}"
      ;;
    all)
      echo "=== Rebuild frontend + backend + worker (sem infra) ==="
      lwk_compose_up_build "$compose_file" backend worker frontend
      lwk_backend_migrate "$compose_file" "${apps[@]}"
      ;;
    infra)
      # shellcheck disable=SC2206
      local infra_svcs=(${INFRA_SERVICES:-evolution})
      echo "=== Rebuild infra: ${infra_svcs[*]} ==="
      lwk_compose_up_build "$compose_file" "${infra_svcs[@]}"
      ;;
    -h|--help|help)
      lwk_deploy_usage
      return 0
      ;;
    *)
      echo "Alvo inválido: $target" >&2
      lwk_deploy_usage >&2
      return 1
      ;;
  esac
}
