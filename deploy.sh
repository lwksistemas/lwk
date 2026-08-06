#!/bin/bash
set -e
cd /opt/lwk-erp
echo "=== LWK Deploy $(date) ==="
git pull origin main
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml exec -T backend python manage.py collectstatic --noinput 2>/dev/null || true
docker compose -f docker-compose.prod.yml exec -T backend python manage.py migrate --noinput 2>/dev/null || true
echo "=== Deploy complete ==="
docker compose -f docker-compose.prod.yml ps
