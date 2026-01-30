# Workers: 2 × 4 threads = 8 req simultâneas. Para >30 lojas (ANALISE_SEGURANCA_DESEMPENHO_CAPACIDADE.md), considerar --workers 3 ou 4 e monitorar conexões PostgreSQL.
web: cd backend && gunicorn config.wsgi --workers 2 --threads 4 --worker-class gthread --worker-connections 1000 --max-requests 1000 --max-requests-jitter 50 --timeout 30 --keep-alive 5 --log-file - --access-logfile - --error-logfile -
release: cd backend && python manage.py migrate --noinput
