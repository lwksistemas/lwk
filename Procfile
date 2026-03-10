# Workers: 4 × 4 threads = 16 req simultâneas. Para 120 lojas × 5 func (PROJECAO_CRESCIMENTO_120_LOJAS.md), considerar --workers 6 e PostgreSQL Standard.
web: cd backend && gunicorn config.wsgi --workers 4 --threads 4 --worker-class gthread --worker-connections 1000 --max-requests 1000 --max-requests-jitter 50 --timeout 30 --keep-alive 5 --log-file - --access-logfile - --error-logfile -
# release: cd backend && python manage.py migrate --noinput
