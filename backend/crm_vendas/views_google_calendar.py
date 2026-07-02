"""
Views para OAuth e sincronização com Google Calendar.
"""
import logging

from django.conf import settings
from django.core.cache import cache
from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from superadmin.models import GoogleCalendarConnection
from tenants.middleware import get_current_loja_id, set_current_loja_id

from .utils import get_current_vendedor_id

from .google_calendar_service import (
    build_calendar_service,
    get_flow,
    pull_events_from_google,
    push_atividade_to_google,
)
from .google_calendar_helpers import (
    MAX_SYNC_ERRORS_RETURNED,
    SYNC_DIRECTION_BOTH,
    SYNC_DIRECTION_PULL,
    SYNC_DIRECTION_PUSH_ONLY,
    VALID_SYNC_DIRECTIONS,
    extract_email_from_credentials,
    get_connection_for_loja_and_vendedor,
    get_loja_slug_by_id,
    get_redirect_uri,
    normalize_token_expiry,
    parse_google_event_start,
    pull_events_time_range,
    redirect_calendario,
)
from .models import Atividade
from core.oauth_state import encode_oauth_state, parse_oauth_state

logger = logging.getLogger(__name__)


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
    vendedor_id = get_current_vendedor_id(request)
    try:
        redirect_uri = get_redirect_uri(request)
        flow = get_flow(redirect_uri)
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            prompt='consent',
            state=encode_oauth_state(loja_id, vendedor_id),
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
        loja_id, _ = parse_oauth_state(state)
        slug = get_loja_slug_by_id(loja_id)
        return redirect_calendario(slug, success=False)

    code = request.GET.get('code')
    if not code:
        return Response(
            {'detail': 'Código de autorização não recebido.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    loja_id, vendedor_id = parse_oauth_state(request.GET.get('state'))
    if not loja_id:
        return Response(
            {'detail': 'Estado inválido (loja).'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    set_current_loja_id(loja_id)
    try:
        redirect_uri = get_redirect_uri(request)
        flow = get_flow(redirect_uri)
        flow.fetch_token(code=code)
        credentials = flow.credentials
        email = extract_email_from_credentials(credentials)
        token_expiry = normalize_token_expiry(credentials.expiry)
        defaults = {
            'access_token': credentials.token,
            'refresh_token': credentials.refresh_token or '',
            'token_expiry': token_expiry,
            'calendar_id': 'primary',
            'email': email,
        }
        lookup = {'loja_id': loja_id}
        if vendedor_id is not None:
            lookup['vendedor_id'] = vendedor_id
        else:
            lookup['vendedor_id__isnull'] = True
        conn, created = GoogleCalendarConnection.objects.using('default').get_or_create(
            defaults=defaults,
            **lookup,
        )
        if not created:
            conn.access_token = credentials.token
            conn.token_expiry = token_expiry
            conn.calendar_id = 'primary'
            conn.email = email
            update_fields = ['access_token', 'token_expiry', 'calendar_id', 'email', 'updated_at']
            if credentials.refresh_token:
                conn.refresh_token = credentials.refresh_token
                update_fields.append('refresh_token')
            conn.save(update_fields=update_fields)
        slug = get_loja_slug_by_id(loja_id)
        cache.delete(f'gcal_status:{loja_id}:owner')
        if vendedor_id is not None:
            cache.delete(f'gcal_status:{loja_id}:{vendedor_id}')
        return redirect_calendario(slug, success=True)
    except Exception as e:
        logger.exception('Erro no callback Google Calendar: %s', e)
        slug = get_loja_slug_by_id(loja_id)
        return redirect_calendario(slug, success=False)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def google_calendar_status(request):
    """Retorna se a loja (ou vendedor) tem conexão com Google Calendar e email (se houver)."""
    loja_id = get_current_loja_id()
    if not loja_id:
        return Response({'connected': False, 'email': None})
    vendedor_id = get_current_vendedor_id(request)
    cache_key = f'gcal_status:{loja_id}:{vendedor_id or "owner"}'
    cached = cache.get(cache_key)
    if cached is not None:
        return Response(cached)
    conn = get_connection_for_loja_and_vendedor(loja_id, vendedor_id)
    if not conn:
        payload = {'connected': False, 'email': None}
    else:
        payload = {
            'connected': True,
            'email': conn.email or None,
            'calendar_id': conn.calendar_id,
        }
    cache.set(cache_key, payload, 120)
    return Response(payload)


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
        logger.warning(
            'google_calendar_sync: contexto de loja ausente. Headers: X-Loja-ID=%s, X-Tenant-Slug=%s',
            request.headers.get('X-Loja-ID'),
            request.headers.get('X-Tenant-Slug'),
        )
        return Response(
            {'detail': 'Contexto de loja não identificado. Atualize a página e tente novamente.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    vendedor_id = get_current_vendedor_id(request)
    conn = get_connection_for_loja_and_vendedor(loja_id, vendedor_id)
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
        atividades_qs = Atividade.objects.filter(loja_id=loja_id).order_by('data')
        if vendedor_id is not None:
            atividades_qs = atividades_qs.filter(
                Q(oportunidade__vendedor_id=vendedor_id) | Q(lead__oportunidades__vendedor_id=vendedor_id)
            ).distinct()
        for at in atividades_qs:
            event_id = push_atividade_to_google(conn, at)
            if event_id:
                at.google_event_id = event_id
                at.save(update_fields=['google_event_id'])
                pushed += 1
            else:
                errors.append(at.titulo)

    pulled = 0
    if direction in (SYNC_DIRECTION_PULL, SYNC_DIRECTION_BOTH):
        time_min, time_max = pull_events_time_range()
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
            dt = parse_google_event_start(ev)
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
                criado_por_vendedor_id=vendedor_id,
            )
            pulled += 1
            existing_ids.add(gid)

    return Response({
        'pushed': pushed,
        'pulled': pulled,
        'errors': errors[:MAX_SYNC_ERRORS_RETURNED],
    })


@api_view(['DELETE', 'POST'])
@permission_classes([IsAuthenticated])
def google_calendar_disconnect(request):
    """Remove a conexão com o Google Calendar da loja (ou do vendedor). Não remove eventos já criados no Google."""
    loja_id = get_current_loja_id()
    if not loja_id:
        return Response(
            {'detail': 'Contexto de loja não identificado.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    vendedor_id = get_current_vendedor_id(request)
    qs = GoogleCalendarConnection.objects.using('default').filter(loja_id=loja_id)
    if vendedor_id is None:
        qs = qs.filter(vendedor_id__isnull=True)
    else:
        qs = qs.filter(vendedor_id=vendedor_id)
    deleted, _ = qs.delete()
    if deleted:
        cache.delete(f'gcal_status:{loja_id}:owner')
        if vendedor_id is not None:
            cache.delete(f'gcal_status:{loja_id}:{vendedor_id}')
    return Response({'disconnected': deleted > 0})
