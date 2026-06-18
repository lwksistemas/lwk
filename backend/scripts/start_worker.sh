#!/usr/bin/env sh
# Worker Railway: django-q em background + Gunicorn mínimo para healthcheck HTTP.
set -eu

echo ">> Iniciando django-q qcluster (background)..."
python manage.py qcluster &
QPID=$!

cleanup() {
  kill "$QPID" 2>/dev/null || true
}
trap cleanup INT TERM EXIT

echo ">> Healthcheck HTTP na porta ${PORT:-8080} (1 worker)..."
exec gunicorn config.wsgi \
  --bind "0.0.0.0:${PORT:-8080}" \
  --workers 1 \
  --threads 1 \
  --worker-class sync \
  --timeout 60 \
  --log-file - \
  --access-logfile - \
  --error-logfile -
