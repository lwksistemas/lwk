#!/bin/bash
# Legado: subia só o frontend-beta na VM de produção.
# O beta isolado é 201.54.18.213 — use scripts/deploy-beta-isolated.sh
set -e
cd /opt/lwk-erp
echo "=== Deploy BETA (staging) $(date) ==="

git fetch origin

# Usar origin/staging (ref atualizada pelo fetch); local staging pode estar atrasado
git checkout origin/staging -- frontend/

docker compose -f docker-compose.prod.yml build frontend-beta
docker compose -f docker-compose.prod.yml up -d frontend-beta

# Restaurar frontend da main no working tree
git checkout origin/main -- frontend/ 2>/dev/null || git checkout main -- frontend/ 2>/dev/null || true

echo "=== Beta deploy complete ==="
docker compose -f docker-compose.prod.yml ps frontend-beta
