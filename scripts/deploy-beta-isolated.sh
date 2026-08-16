#!/usr/bin/env bash
# Deploy no servidorbeta isolado (201.54.18.213), branch staging.
set -euo pipefail
cd /home/deploy/lwk-beta
echo "=== Deploy BETA isolado $(date) ==="
git fetch origin
git checkout staging
git pull --ff-only origin staging
docker compose -f docker-compose.beta.yml up -d --build backend worker frontend evolution orthanc media
docker compose -f docker-compose.beta.yml exec -T backend python manage.py migrate --noinput
docker compose -f docker-compose.beta.yml exec -T backend python manage.py migrate_all_lojas
docker compose -f docker-compose.beta.yml exec -T backend python manage.py ensure_all
echo "=== Beta isolado atualizado ==="
docker compose -f docker-compose.beta.yml ps
