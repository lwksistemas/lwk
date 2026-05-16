#!/bin/bash
set -e

echo "Running migrations..."
python manage.py migrate --noinput

echo "Starting gunicorn..."
exec gunicorn --bind 0.0.0.0:8000 \
     --workers 4 \
     --threads 2 \
     --worker-class gthread \
     --worker-tmp-dir /dev/shm \
     --timeout 120 \
     --graceful-timeout 30 \
     --keep-alive 5 \
     --max-requests 1000 \
     --max-requests-jitter 50 \
     --access-logfile - \
     --error-logfile - \
     --log-level info \
     config.wsgi:application
