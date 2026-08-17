#!/usr/bin/env bash
# Deploy produção no Magalu (201.23.81.50), branch já no disco após git pull.
#
# No servidor:
#   cd /opt/lwk-erp && git pull && bash scripts/deploy-prod-magalu.sh frontend
#   cd /opt/lwk-erp && git pull && bash scripts/deploy-prod-magalu.sh backend clinica_beleza
#   cd /opt/lwk-erp && git pull && bash scripts/deploy-prod-magalu.sh all
#   cd /opt/lwk-erp && git pull && bash scripts/deploy-prod-magalu.sh infra
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
# shellcheck source=scripts/deploy-scoped-lib.sh
source "$SCRIPT_DIR/deploy-scoped-lib.sh"

cd "$REPO_ROOT"
INFRA_SERVICES="${INFRA_SERVICES:-evolution}"

TARGET="${1:-all}"
shift || true
APPS=()
if [[ $# -gt 0 ]]; then
  APPS=("$@")
elif [[ -n "${MIGRATE_APPS:-}" ]]; then
  IFS=',' read -ra APPS <<< "$MIGRATE_APPS"
fi

echo "=== Deploy PRODUÇÃO $(date) target=$TARGET apps=${APPS[*]:-todos} ==="
lwk_deploy_target docker-compose.prod.yml "$TARGET" "${APPS[@]}"
echo "=== Produção atualizada ==="
docker compose -f docker-compose.prod.yml ps
