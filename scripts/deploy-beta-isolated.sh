#!/usr/bin/env bash
# Deploy no servidorbeta isolado (201.54.18.213), branch staging.
#
# Padrão: só o que mudou.
#   bash scripts/deploy-beta-isolated.sh frontend
#   bash scripts/deploy-beta-isolated.sh backend clinica_beleza
#   bash scripts/deploy-beta-isolated.sh all
#   bash scripts/deploy-beta-isolated.sh infra
#
# Sem argumentos = all (frontend+backend+worker, sem Evolution/Orthanc).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/deploy-scoped-lib.sh
source "$SCRIPT_DIR/deploy-scoped-lib.sh"

cd /home/deploy/lwk-beta
INFRA_SERVICES="${INFRA_SERVICES:-evolution orthanc media}"

TARGET="${1:-all}"
shift || true
APPS=()
if [[ $# -gt 0 ]]; then
  APPS=("$@")
elif [[ -n "${MIGRATE_APPS:-}" ]]; then
  IFS=',' read -ra APPS <<< "$MIGRATE_APPS"
fi

echo "=== Deploy BETA isolado $(date) target=$TARGET apps=${APPS[*]:-todos} ==="
git fetch origin
git checkout staging
git pull --ff-only origin staging

lwk_deploy_target docker-compose.beta.yml "$TARGET" "${APPS[@]}"

echo "=== Beta isolado atualizado ==="
docker compose -f docker-compose.beta.yml ps
