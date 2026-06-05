import os
import sys

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
application = get_wsgi_application()


def _run_startup_ensures():
    """Garante schema de estoque nas lojas ao subir o worker (idempotente)."""
    if os.environ.get('LWK_SKIP_STARTUP_ENSURE') == '1':
        return
    settings_module = os.environ.get('DJANGO_SETTINGS_MODULE', '')
    if 'production' not in settings_module:
        return
    try:
        from django.core.management import call_command
        call_command('ensure_estoque_produto_fields', verbosity=1)
    except Exception as exc:
        print(f'[wsgi] ensure_estoque_produto_fields falhou: {exc}', file=sys.stderr)


_run_startup_ensures()
