"""URLs públicas da API (acessíveis de fora — Evolution, webhooks, links em e-mail)."""


def get_public_api_base_url(request=None) -> str:
    """Base HTTPS da API sem path final.
    Preferir API_BASE_URL/BACKEND_URL em settings; fallback produção LWK.
    """
    from django.conf import settings

    for key in ("API_BASE_URL", "BACKEND_URL"):
        val = (getattr(settings, key, None) or "").strip().rstrip("/")
        if val:
            return val

    site = (getattr(settings, "SITE_URL", None) or "").strip().rstrip("/")
    if site and "api." in site:
        return site
    if site and "lwksistemas.com.br" in site:
        return "https://api.lwksistemas.com.br"

    if request is not None:
        return request.build_absolute_uri("/").rstrip("/")

    return "https://api.lwksistemas.com.br"
