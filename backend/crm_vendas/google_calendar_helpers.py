"""Helpers puros para OAuth e sincronização com Google Calendar.
Separados de views_google_calendar.py para testes e reuso.
"""
import logging
from datetime import timedelta

from django.conf import settings
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from superadmin.models import GoogleCalendarConnection, Loja

logger = logging.getLogger(__name__)

FRONTEND_BASE = getattr(settings, "FRONTEND_URL", "https://lwksistemas.com.br")
SYNC_DIRECTION_PUSH_ONLY = "push_only"
SYNC_DIRECTION_PULL = "pull"
SYNC_DIRECTION_BOTH = "both"
VALID_SYNC_DIRECTIONS = (SYNC_DIRECTION_PUSH_ONLY, SYNC_DIRECTION_PULL, SYNC_DIRECTION_BOTH)
PULL_EVENTS_DAYS = 365
MAX_SYNC_ERRORS_RETURNED = 10


def normalize_token_expiry(expiry):
    """Normaliza expiry para UTC aware (evita erro naive/aware no refresh)."""
    if not expiry:
        return None
    if timezone.is_naive(expiry):
        return timezone.make_aware(expiry, timezone.utc)
    return expiry.astimezone(timezone.utc)


def get_redirect_uri(request):
    """Monta a URL de callback para OAuth (deve coincidir com a configurada no Google Cloud)."""
    scheme = request.META.get("HTTP_X_FORWARDED_PROTO", request.scheme)
    if not getattr(settings, "DEBUG", False) and scheme != "https":
        scheme = "https"
    host = request.get_host()
    return f"{scheme}://{host}/api/crm-vendas/google-calendar/callback/"


def get_loja_slug_by_id(loja_id):
    """Retorna o slug da loja pelo id (consulta no banco default)."""
    if not loja_id:
        return None
    loja = Loja.objects.using("default").filter(id=loja_id).first()
    return loja.slug if loja else None


def get_connection_for_loja_and_vendedor(loja_id, vendedor_id=None):
    """Retorna a conexão Google Calendar da loja (e vendedor, se houver).
    vendedor_id=None = conexão do proprietário.
    """
    if not loja_id:
        return None
    qs = GoogleCalendarConnection.objects.using("default").filter(loja_id=loja_id)
    if vendedor_id is None:
        qs = qs.filter(vendedor_id__isnull=True)
    else:
        qs = qs.filter(vendedor_id=vendedor_id)
    return qs.first()


def redirect_calendario(slug, success=True):
    """URL de redirecionamento para a página de calendário do CRM."""
    param = "google_connected=1" if success else "google_error=1"
    return redirect(f'{FRONTEND_BASE}/loja/{slug or "unknown"}/crm-vendas/calendario?{param}')


def extract_email_from_credentials(credentials):
    """Extrai email do id_token das credenciais OAuth, se disponível."""
    if not getattr(credentials, "id_token", None):
        return None
    try:
        from google.auth.transport.requests import Request as GoogleRequest
        from google.oauth2 import id_token
        decoded = id_token.verify_oauth2_token(
            credentials.id_token,
            GoogleRequest(),
            settings.GOOGLE_CLIENT_ID,
        )
        return decoded.get("email")
    except Exception as e:
        logger.debug("Não foi possível extrair email do id_token: %s", e)
        return None


def parse_google_event_start(ev):
    """Extrai datetime de início de um evento da API Google Calendar.
    Suporta dateTime (com hora) e date (all-day, usa 09:00 como hora padrão).
    """
    start = ev.get("start") or {}
    dt_str = start.get("dateTime")
    date_str = start.get("date")
    if dt_str:
        dt = parse_datetime(dt_str)
        if dt:
            if timezone.is_naive(dt):
                return timezone.make_aware(dt)
            return dt
    if date_str:
        parsed = parse_datetime(f"{date_str}T09:00:00")
        if parsed:
            return timezone.make_aware(parsed) if timezone.is_naive(parsed) else parsed
    return None


def pull_events_time_range():
    """Intervalo padrão para importação de eventos do Google."""
    time_min = timezone.now()
    time_max = time_min + timedelta(days=PULL_EVENTS_DAYS)
    return time_min, time_max
