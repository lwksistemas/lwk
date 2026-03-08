"""
Views para OAuth e sincronização com Google Calendar.
"""
import logging
from datetime import timedelta

from django.conf import settings
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from superadmin.models import GoogleCalendarConnection, Loja
from tenants.middleware import get_current_loja_id, set_current_loja_id

from .google_calendar_service import (
    build_calendar_service,
    get_flow,
    pull_events_from_google,
    push_atividade_to_google,
)
from .models import Atividade

logger = logging.getLogger(__name__)

# Constantes
FRONTEND_BASE = getattr(settings, 'FRONTEND_URL', 'https://lwksistemas.com.br')
SYNC_DIRECTION_PUSH_ONLY = 'push_only'
SYNC_DIRECTION_PULL = 'pull'
SYNC_DIRECTION_BOTH = 'both'
VALID_SYNC_DIRECTIONS = (SYNC_DIRECTION_PUSH_ONLY, SYNC_DIRECTION_PULL, SYNC_DIRECTION_BOTH)
PULL_EVENTS_DAYS = 365
MAX_SYNC_ERRORS_RETURNED = 10


def _get_redirect_uri(request):
    """Monta a URL de callback para OAuth (deve coincidir com a configurada no Google Cloud)."""
    scheme = request.META.get('HTTP_X_FORWARDED_PROTO', request.scheme)
    host = request.get_host()
    return f'{scheme}://{host}/api/crm-vendas/google-calendar/callback/'


def _get_loja_slug_by_id(loja_id):
    """Retorna o slug da loja pelo id (consulta no banco default)."""
    if not loja_id:
        return None
    loja = Loja.objects.using('default').filter(id=loja_id).first()
    return loja.slug if loja else None


def _get_connection_for_loja(loja_id):
    """Retorna a conexão Google Calendar da loja, se existir."""
    if not loja_id:
        return None
    return GoogleCalendarConnection.objects.using('default').filter(loja_id=loja_id).first()


def _redirect_calendario(slug, success=True):
    """URL de redirecionamento para a página de calendário do CRM."""
    param = 'google_connected=1' if success else 'google_error=1'
    return redirect(f'{FRONTEND_BASE}/loja/{slug or "unknown"}/crm-vendas/calendario?{param}')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def google_calendar_auth(request):
    """
    Retorna a URL de autorização OAuth do Google para o frontend redirecionar o usuário.
    Requer contexto de loja (X-Tenant-Slug ou path).
    """
    loja_id = get_current_loja_id()
    if not loja_id:
        return Response(
            {'detail': 'Contexto de loja não identificado.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        redirect_uri = _get_redirect_uri(request)
        flow = get_flow(redirect_uri)
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            prompt='consent',
            state=str(loja_id),
            include_granted_scopes='true',
        )
        return Response({'auth_url': auth_url})
    except ValueError as e:
        return Response({'detail': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        logger.exception('Erro ao iniciar OAuth Google Calendar: %s', e)
        return Response(
            {
                'detail': (
                    'Para usar o Google Calendar, autorize sua conta Google. '
                    'Clique em "Conectar Google Calendar" e faça login na tela do Google quando solicitado. '
                    'Se o erro persistir, entre em contato com o suporte.'
                ),
                'error': str(e) if settings.DEBUG else None,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def google_calendar_callback(request):
    """
    Callback do OAuth: recebe o code do Google, troca por tokens e salva por loja.
    state = loja_id (numérico). Redireciona para o frontend.
    """
    error = request.GET.get('error')
    if error:
        logger.warning('Google OAuth error: %s', error)
        state = request.GET.get('state')
        loja_id = _parse_loja_id_from_state(state)
        slug = _get_loja_slug_by_id(loja_id)
        return _redirect_calendario(slug, success=False)

    code = request.GET.get('code')
    if not code:
        return Response(
            {'detail': 'Código de autorização não recebido.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    loja_id = _parse_loja_id_from_state(request.GET.get('state'))
    if not loja_id:
        return Response(
            {'detail': 'Estado inválido (loja).'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    set_current_loja_id(loja_id)
    try:
        redirect_uri = _get_redirect_uri(request)
        flow = get_flow(redirect_uri)
        flow.fetch_token(code=code)
        credentials = flow.credentials
        email = _extract_email_from_credentials(credentials)
        GoogleCalendarConnection.objects.using('default').update_or_create(
            loja_id=loja_id,
            defaults={
                'access_token': credentials.token,
                'refresh_token': credentials.refresh_token or '',
                'token_expiry': credentials.expiry,
                'calendar_id': 'primary',
                'email': email,
            },
        )
        slug = _get_loja_slug_by_id(loja_id)
        return _redirect_calendario(slug, success=True)
    except Exception as e:
        logger.exception('Erro no callback Google Calendar: %s', e)
        slug = _get_loja_slug_by_id(loja_id)
        return _redirect_calendario(slug, success=False)


def _parse_loja_id_from_state(state):
    """Extrai loja_id do parâmetro state (string numérica)."""
    if not state:
        return None
    try:
        return int(state)
    except (TypeError, ValueError):
        return None


def _extract_email_from_credentials(credentials):
    """Extrai email do id_token das credenciais OAuth, se disponível."""
    if not getattr(credentials, 'id_token', None):
        return None
    try:
        from google.oauth2 import id_token
        from google.auth.transport.requests import Request as GoogleRequest
        decoded = id_token.verify_oauth2_token(
            credentials.id_token,
            GoogleRequest(),
            settings.GOOGLE_CLIENT_ID,
        )
        return decoded.get('email')
    except Exception as e:
        logger.debug('Não foi possível extrair email do id_token: %s', e)
        return None


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def google_calendar_status(request):
    """Retorna se a loja tem conexão com Google Calendar e email (se houver)."""
    loja_id = get_current_loja_id()
    if not loja_id:
        return Response({'connected': False, 'email': None})
    conn = _get_connection_for_loja(loja_id)
    if not conn:
        return Response({'connected': False, 'email': None})
    return Response({
        'connected': True,
        'email': conn.email or None,
        'calendar_id': conn.calendar_id,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def google_calendar_sync(request):
    """
    Sincroniza atividades do CRM com o Google Calendar.
    - Push: envia atividades para o Google (cria ou atualiza por google_event_id).
    - Pull: importa eventos do Google como atividades (direction=push_only | pull | both).
    """
    loja_id = get_current_loja_id()
    if not loja_id:
        return Response(
            {'detail': 'Contexto de loja não identificado.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    conn = _get_connection_for_loja(loja_id)
    if not conn:
        return Response(
            {'detail': 'Conecte o Google Calendar antes de sincronizar.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    direction = (request.data.get('direction') or SYNC_DIRECTION_PUSH_ONLY).strip().lower()
    if direction not in VALID_SYNC_DIRECTIONS:
        direction = SYNC_DIRECTION_PUSH_ONLY

    pushed = 0
    errors = []
    if direction in (SYNC_DIRECTION_PUSH_ONLY, SYNC_DIRECTION_BOTH):
        try:
            build_calendar_service(conn)
        except Exception as e:
            logger.exception('Erro ao obter credenciais Google: %s', e)
            return Response(
                {'detail': 'Token expirado ou inválido. Desconecte e conecte o Google Calendar novamente.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        for at in Atividade.objects.filter(loja_id=loja_id).order_by('data'):
            event_id = push_atividade_to_google(conn, at)
            if event_id:
                at.google_event_id = event_id
                at.save(update_fields=['google_event_id'])
                pushed += 1
            else:
                errors.append(at.titulo)

    pulled = 0
    if direction in (SYNC_DIRECTION_PULL, SYNC_DIRECTION_BOTH):
        time_min = timezone.now()
        time_max = time_min + timedelta(days=PULL_EVENTS_DAYS)
        events = pull_events_from_google(conn, time_min, time_max)
        existing_ids = set(
            Atividade.objects.filter(loja_id=loja_id)
            .exclude(google_event_id__isnull=True)
            .exclude(google_event_id='')
            .values_list('google_event_id', flat=True)
        )
        for ev in events:
            gid = ev.get('id')
            if not gid or gid in existing_ids:
                continue
            dt = _parse_google_event_start(ev)
            if not dt:
                continue
            summary = (ev.get('summary') or 'Evento Google')[:255]
            Atividade.objects.create(
                loja_id=loja_id,
                titulo=summary,
                tipo='task',
                data=dt,
                observacoes=f"Importado do Google Calendar (event_id: {gid})",
                google_event_id=gid,
            )
            pulled += 1
            existing_ids.add(gid)

    return Response({
        'pushed': pushed,
        'pulled': pulled,
        'errors': errors[:MAX_SYNC_ERRORS_RETURNED],
    })


def _parse_google_event_start(ev):
    """
    Extrai datetime de início de um evento da API Google Calendar.
    Suporta dateTime (com hora) e date (all-day, usa 09:00 como hora padrão).
    """
    start = ev.get('start') or {}
    dt_str = start.get('dateTime')
    date_str = start.get('date')
    if dt_str:
        dt = parse_datetime(dt_str)
        if dt:
            if timezone.is_naive(dt):
                return timezone.make_aware(dt)
            return dt
    if date_str:
        parsed = parse_datetime(f'{date_str}T09:00:00')
        if parsed:
            return timezone.make_aware(parsed) if timezone.is_naive(parsed) else parsed
    return None


@api_view(['DELETE', 'POST'])
@permission_classes([IsAuthenticated])
def google_calendar_disconnect(request):
    """Remove a conexão com o Google Calendar da loja. Não remove eventos já criados no Google."""
    loja_id = get_current_loja_id()
    if not loja_id:
        return Response(
            {'detail': 'Contexto de loja não identificado.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    deleted, _ = GoogleCalendarConnection.objects.using('default').filter(loja_id=loja_id).delete()
    return Response({'disconnected': deleted > 0})
