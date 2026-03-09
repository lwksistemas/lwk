"""
Patch para google-auth: utcnow() deve retornar datetime timezone-aware.
Evita TypeError: can't compare offset-naive and offset-aware datetimes
ao verificar expiração do token (credentials.expired).
"""
import logging

try:
    from datetime import datetime, timezone
    import google.auth._helpers as _helpers

    def _utcnow_aware():
        return datetime.now(timezone.utc)

    _helpers.utcnow = _utcnow_aware
except Exception:
    pass  # ignora se google-auth não estiver instalado

# Suprimir aviso "file_cache is only supported with oauth2client<4.0.0" do Google API
import warnings
for _name in ('oauth2client', 'oauth2client.contrib', 'oauth2client.contrib.locked_file',
              'googleapiclient.discovery_cache', 'httplib2'):
    try:
        logging.getLogger(_name).setLevel(logging.ERROR)
    except Exception:
        pass
warnings.filterwarnings('ignore', message='.*file_cache.*oauth2client.*')
