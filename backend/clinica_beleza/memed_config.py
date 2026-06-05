"""
Configuração e credenciais da integração Memed (sem dependência de views).
"""
from django.conf import settings

MEMED_ENDPOINTS = {
    'integration': {
        'api': 'https://integrations.api.memed.com.br/v1',
        'script': 'https://integrations.memed.com.br/modulos/plataforma.sinapse-prescricao/build/sinapse-prescricao.min.js',
    },
    'production': {
        'api': 'https://api.memed.com.br/v1',
        'script': 'https://memed.com.br/modulos/plataforma.sinapse-prescricao/build/sinapse-prescricao.min.js',
    },
}


def memed_config():
    env = (getattr(settings, 'MEMED_ENVIRONMENT', 'integration') or 'integration').lower()
    if env not in MEMED_ENDPOINTS:
        env = 'integration'
    return env, MEMED_ENDPOINTS[env]


def memed_credentials(env):
    """
    Retorna (api_key, secret_key) conforme o ambiente. Em produção, prioriza as
    chaves *_PROD; se ausentes, faz fallback para as genéricas (homologação).
    """
    if env == 'production':
        api_key = getattr(settings, 'MEMED_API_KEY_PROD', '') or getattr(settings, 'MEMED_API_KEY', '')
        secret_key = getattr(settings, 'MEMED_SECRET_KEY_PROD', '') or getattr(settings, 'MEMED_SECRET_KEY', '')
    else:
        api_key = getattr(settings, 'MEMED_API_KEY', '')
        secret_key = getattr(settings, 'MEMED_SECRET_KEY', '')
    return api_key, secret_key
