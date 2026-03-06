"""
Settings mínimo para rodar makemigrations quando o ambiente não tem todas as deps (ex: django_q).
Importa settings e remove apps opcionais que podem falhar ao importar.
"""
from config.settings import *  # noqa: F401, F403

# Remover django_q para evitar ModuleNotFoundError: pkg_resources no venv
INSTALLED_APPS = [a for a in INSTALLED_APPS if a != 'django_q']
