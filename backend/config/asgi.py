import os

from django.core.asgi import get_asgi_application

# Ambientes prod-like (Magalu) devem sempre usar config.settings_production.
if os.environ.get("LWK_ENVIRONMENT") and not os.environ.get("DJANGO_SETTINGS_MODULE"):
    os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings_production"

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_asgi_application()

# Segurança: em produção, DEBUG=True é proibido.
_settings_module = os.environ.get("DJANGO_SETTINGS_MODULE", "")
if "production" in _settings_module:
    from django.conf import settings

    if settings.DEBUG:
        raise RuntimeError(
            "DJANGO_SETTINGS_MODULE aponta para produção mas DEBUG=True. "
            "Defina DEBUG=False ou use config.settings."
        )
