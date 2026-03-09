"""
Patch para google-auth: utcnow() deve retornar datetime timezone-aware.
Evita TypeError: can't compare offset-naive and offset-aware datetimes
ao verificar expiração do token (credentials.expired).
"""
try:
    from datetime import datetime, timezone
    import google.auth._helpers as _helpers

    def _utcnow_aware():
        return datetime.now(timezone.utc)

    _helpers.utcnow = _utcnow_aware
except Exception:
    pass  # ignora se google-auth não estiver instalado
