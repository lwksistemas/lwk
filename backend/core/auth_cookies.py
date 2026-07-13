"""Cookies httpOnly para JWT e sessão (opcional via JWT_USE_HTTPONLY_COOKIES).
Compatível com Authorization Bearer (transição gradual).
"""
from __future__ import annotations

from django.conf import settings
from django.http import HttpResponse

ACCESS_COOKIE = "lwk_access"
REFRESH_COOKIE = "lwk_refresh"
SESSION_COOKIE = "lwk_session"


def use_httponly_jwt_cookies() -> bool:
    return bool(getattr(settings, "JWT_USE_HTTPONLY_COOKIES", False))


def _cookie_domain():
    return getattr(settings, "JWT_COOKIE_DOMAIN", None) or None


def _base_cookie_kwargs(max_age: int) -> dict:
    secure = not settings.DEBUG
    kwargs = {
        "max_age": max_age,
        "httponly": True,
        "secure": secure,
        "samesite": "Lax",
        "path": "/",
    }
    domain = _cookie_domain()
    if domain:
        kwargs["domain"] = domain
    return kwargs


def attach_auth_cookies(
    response: HttpResponse,
    *,
    access: str,
    refresh: str,
    session_id: str | None = None,
) -> HttpResponse:
    if not use_httponly_jwt_cookies():
        return response

    access_lifetime = int(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds())
    refresh_lifetime = int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds())

    response.set_cookie(ACCESS_COOKIE, access, **_base_cookie_kwargs(access_lifetime))
    response.set_cookie(REFRESH_COOKIE, refresh, **_base_cookie_kwargs(refresh_lifetime))
    if session_id:
        response.set_cookie(
            SESSION_COOKIE,
            session_id,
            **_base_cookie_kwargs(refresh_lifetime),
        )
    return response


def clear_auth_cookies(response: HttpResponse) -> HttpResponse:
    if not use_httponly_jwt_cookies():
        return response
    for name in (ACCESS_COOKIE, REFRESH_COOKIE, SESSION_COOKIE):
        response.delete_cookie(name, path="/", domain=_cookie_domain())
    return response


def inject_bearer_from_cookie(request) -> None:
    """Preenche Authorization a partir do cookie httpOnly, se ausente."""
    if request.META.get("HTTP_AUTHORIZATION"):
        return
    token = request.COOKIES.get(ACCESS_COOKIE)
    if token:
        request.META["HTTP_AUTHORIZATION"] = f"Bearer {token}"


def get_session_id_from_request(request) -> str:
    return (
        (request.headers.get("X-Session-ID") or "").strip()
        or (request.COOKIES.get(SESSION_COOKIE) or "").strip()
        or (request.GET.get("sid") or "").strip()
    )


def get_refresh_from_request(request) -> str | None:
    body = getattr(request, "data", None) or {}
    if isinstance(body, dict) and body.get("refresh"):
        return str(body["refresh"])
    return request.COOKIES.get(REFRESH_COOKIE)
