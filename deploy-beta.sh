#!/bin/bash
set -e
cd /opt/lwk-erp
echo "=== Deploy BETA (staging) $(date) ==="

# Mudar para branch staging, buildar, voltar para main
git fetch origin
git checkout staging -- frontend/ 2>/dev/null || git stash

# Build do frontend-beta com código do staging
docker compose -f docker-compose.prod.yml build frontend-beta
docker compose -f docker-compose.prod.yml up -d frontend-beta

# Restaurar branch main
git checkout main -- frontend/ 2>/dev/null || true
git stash pop 2>/dev/null || true

echo "=== Beta deploy complete ==="
docker compose -f docker-compose.prod.yml ps frontend-beta
