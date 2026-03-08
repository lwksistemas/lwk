"""
Serviço de integração com Google Calendar API.
OAuth2 + criar/atualizar/listar eventos.
"""
import logging
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

# Scopes necessários para leitura/escrita do calendário
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/calendar.events',
]
# Fuso e duração padrão para eventos
TIMEZONE_DEFAULT = 'America/Sao_Paulo'
EVENT_DURATION_HOURS = 1
TOKEN_URI = 'https://oauth2.googleapis.com/token'


def get_flow(redirect_uri):
    """Retorna o Flow do OAuth2 para uso em auth e callback."""
    from google_auth_oauthlib.flow import Flow

    client_id = getattr(settings, 'GOOGLE_CLIENT_ID', None)
    client_secret = getattr(settings, 'GOOGLE_CLIENT_SECRET', None)
    if not client_id or not client_secret:
        raise ValueError('GOOGLE_CLIENT_ID e GOOGLE_CLIENT_SECRET devem estar configurados.')

    flow = Flow.from_client_config(
        {
            'web': {
                'client_id': client_id,
                'client_secret': client_secret,
                'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
                'token_uri': TOKEN_URI,
                'redirect_uris': [redirect_uri],
            }
        },
        scopes=SCOPES,
        redirect_uri=redirect_uri,
    )
    return flow


def get_credentials(connection):
    """Converte GoogleCalendarConnection em Credentials do google-auth (com refresh)."""
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google.auth.exceptions import RefreshError

    creds = Credentials(
        token=connection.access_token,
        refresh_token=connection.refresh_token,
        token_uri=TOKEN_URI,
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        scopes=SCOPES,
    )
    if connection.token_expiry:
        expiry = connection.token_expiry
        if timezone.is_naive(expiry):
            expiry = timezone.make_aware(expiry, timezone.utc)
        else:
            expiry = expiry.astimezone(timezone.utc)
        creds.expiry = expiry
    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            connection.access_token = creds.token
            expiry = creds.expiry
            if expiry and timezone.is_naive(expiry):
                expiry = timezone.make_aware(expiry, timezone.utc)
            connection.token_expiry = expiry
            connection.save(update_fields=['access_token', 'token_expiry', 'updated_at'])
        except RefreshError as e:
            logger.warning('Refresh token falhou, removendo conexão inválida: %s', e)
            connection.delete()
            raise ValueError(
                'Token expirado ou inválido. Desconecte e conecte o Google Calendar novamente.'
            ) from e
    return creds


def build_calendar_service(connection):
    """Retorna o cliente da API Google Calendar."""
    from googleapiclient.discovery import build

    creds = get_credentials(connection)
    return build('calendar', 'v3', credentials=creds)


def atividade_to_google_event(atividade):
    """Converte uma Atividade do CRM em corpo de evento da API Google Calendar."""
    start_dt = atividade.data
    if start_dt.tzinfo is None:
        start_dt = timezone.make_aware(start_dt)
    end_dt = start_dt + timedelta(hours=EVENT_DURATION_HOURS)
    desc = (atividade.observacoes or '').strip()
    desc = f'[CRM - {atividade.get_tipo_display()}]\n{desc}'.strip() or None
    return {
        'summary': atividade.titulo,
        'description': desc,
        'start': {'dateTime': start_dt.isoformat(), 'timeZone': TIMEZONE_DEFAULT},
        'end': {'dateTime': end_dt.isoformat(), 'timeZone': TIMEZONE_DEFAULT},
    }


def push_atividade_to_google(connection, atividade, calendar_id=None):
    """
    Cria ou atualiza um evento no Google Calendar para a atividade.
    Retorna o event_id do Google ou None em caso de erro.
    """
    cal_id = calendar_id or connection.calendar_id
    try:
        service = build_calendar_service(connection)
        body = atividade_to_google_event(atividade)
        if getattr(atividade, 'google_event_id', None):
            event = service.events().update(
                calendarId=cal_id,
                eventId=atividade.google_event_id,
                body=body,
            ).execute()
        else:
            event = service.events().insert(calendarId=cal_id, body=body).execute()
        return event.get('id')
    except Exception as e:
        logger.exception('Erro ao enviar atividade para Google Calendar: %s', e)
        return None


def pull_events_from_google(connection, time_min, time_max, calendar_id=None):
    """
    Lista eventos do Google Calendar no intervalo.
    Retorna lista de dicts com id, summary, start, end, description.
    """
    cal_id = calendar_id or connection.calendar_id
    try:
        service = build_calendar_service(connection)
        events_result = (
            service.events()
            .list(
                calendarId=cal_id,
                timeMin=time_min.isoformat(),
                timeMax=time_max.isoformat(),
                singleEvents=True,
                orderBy='startTime',
            )
            .execute()
        )
        return events_result.get('items', [])
    except Exception as e:
        logger.exception('Erro ao listar eventos do Google Calendar: %s', e)
        return []


def delete_google_event(connection, event_id, calendar_id=None):
    """Remove evento do Google Calendar (útil ao excluir atividade sincronizada)."""
    cal_id = calendar_id or connection.calendar_id
    try:
        service = build_calendar_service(connection)
        service.events().delete(calendarId=cal_id, eventId=event_id).execute()
        return True
    except Exception as e:
        logger.exception('Erro ao excluir evento do Google Calendar: %s', e)
        return False
