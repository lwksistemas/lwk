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

Etapa de schema (migrate/ensure):
  Por padrão, é PULADA quando o deploy só mudou código de aplicação (sem
  migration/ensure novo desde o último deploy) — deploy mais rápido.
  FORCE_SCHEMA=1  força rodar a etapa de schema.
  SKIP_SCHEMA=1   força pular a etapa de schema.
EOF
}

lwk_compose_up_build() {
  local compose_file="$1"
  shift
  # BuildKit acelera o rebuild reaproveitando camadas em cache (ex.: pip/npm install
  # quando só o código mudou). Separar build do restart reduz o tempo em que o
  # container fica indisponível: builda a imagem nova (com cache) e só então recria.
  export DOCKER_BUILDKIT="${DOCKER_BUILDKIT:-1}"
  export COMPOSE_DOCKER_CLI_BUILD="${COMPOSE_DOCKER_CLI_BUILD:-1}"
  docker compose -f "$compose_file" build "$@"
  docker compose -f "$compose_file" up -d --no-build "$@"
}

# Arquivo onde gravamos o SHA do último deploy de backend bem-sucedido.
LWK_LAST_SHA_FILE="${LWK_LAST_SHA_FILE:-.last_deployed_backend_sha}"

# Padrões de caminho que, se mudarem entre o último deploy e o HEAD atual,
# exigem rodar a etapa de schema (migrations Django + ensures SQL idempotentes).
# Só código de aplicação (views, services, serializers, frontend) NÃO exige schema.
lwk_schema_paths_regex() {
  echo -E '(/migrations/|/management/commands/ensure_|/management/commands/normalizar_|/management/commands/fix_.*_column|/management/commands/migrate_all_lojas|/management/commands/deploy_app|superadmin/tenant_deploy\.py|management/commands/ensure_all\.py|services/database_schema_service\.py)'
}

# Decide se a etapa de schema (migrate_all_lojas/ensure_all/deploy_app) deve rodar.
# Retorna 0 (rodar) ou 1 (pular). Fail-safe: em qualquer dúvida, roda.
lwk_deve_rodar_schema() {
  # Override manual: FORCE_SCHEMA=1 sempre roda; SKIP_SCHEMA=1 sempre pula.
  if [[ "${FORCE_SCHEMA:-0}" == "1" ]]; then
    echo "  (FORCE_SCHEMA=1) schema será executado"
    return 0
  fi
  if [[ "${SKIP_SCHEMA:-0}" == "1" ]]; then
    echo "  (SKIP_SCHEMA=1) schema será pulado"
    return 1
  fi
  # Sem git disponível → roda por segurança.
  if ! command -v git >/dev/null 2>&1 || ! git rev-parse --git-dir >/dev/null 2>&1; then
    echo "  (git indisponível) schema será executado por segurança"
    return 0
  fi
  local head_sha last_sha
  head_sha="$(git rev-parse HEAD 2>/dev/null || echo '')"
  last_sha=""
  [[ -f "$LWK_LAST_SHA_FILE" ]] && last_sha="$(cat "$LWK_LAST_SHA_FILE" 2>/dev/null || echo '')"
  # Primeiro deploy (sem SHA salvo) ou SHA inválido → roda por segurança.
  if [[ -z "$last_sha" ]] || ! git cat-file -e "${last_sha}^{commit}" 2>/dev/null; then
    echo "  (sem SHA anterior confiável) schema será executado por segurança"
    return 0
  fi
  if [[ "$last_sha" == "$head_sha" ]]; then
    echo "  (nenhum commit novo desde o último deploy) schema será pulado"
    return 1
  fi
  # Há arquivos de schema no diff entre o último deploy e agora?
  if git diff --name-only "$last_sha" "$head_sha" 2>/dev/null | grep -Eq "$(lwk_schema_paths_regex)"; then
    echo "  (mudanças de migration/ensure detectadas) schema será executado"
    return 0
  fi
  echo "  (só código de aplicação desde $last_sha) schema será pulado — deploy rápido"
  return 1
}

# Grava o SHA atual como o último deploy de backend bem-sucedido.
lwk_gravar_sha_deploy() {
  if command -v git >/dev/null 2>&1 && git rev-parse --git-dir >/dev/null 2>&1; then
    git rev-parse HEAD > "$LWK_LAST_SHA_FILE" 2>/dev/null || true
  fi
}

lwk_backend_migrate() {
  local compose_file="$1"
  shift
  local apps=("$@")

  if ! lwk_deve_rodar_schema; then
    echo "=== Etapa de schema pulada (código puro). Use FORCE_SCHEMA=1 para forçar. ==="
    lwk_gravar_sha_deploy
    return 0
  fi

  docker compose -f "$compose_file" exec -T backend python manage.py migrate --noinput
  if [[ ${#apps[@]} -gt 0 ]]; then
    echo "=== Schema pontual: ${apps[*]} ==="
    docker compose -f "$compose_file" exec -T backend python manage.py deploy_app "${apps[@]}"
  else
    echo "=== Schema completo (todas as lojas / apps) ==="
    docker compose -f "$compose_file" exec -T backend python manage.py migrate_all_lojas
    docker compose -f "$compose_file" exec -T backend python manage.py ensure_all
  fi
  lwk_gravar_sha_deploy
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
