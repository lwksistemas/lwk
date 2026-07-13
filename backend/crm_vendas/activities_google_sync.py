"""Serviço de sincronização de atividades com Google Calendar.
Extrai a lógica de sync do AtividadeViewSet para centralizar e evitar duplicação.
"""
import logging

from tenants.middleware import get_current_loja_id

from .google_calendar_service import delete_google_event, push_atividade_to_google
from .utils import get_current_vendedor_id

logger = logging.getLogger(__name__)


def _get_connection(loja_id: int, vendedor_id=None):
    """Busca a conexão do Google Calendar para a loja (owner ou vendedor).
    Retorna None se não houver conexão.
    """
    from superadmin.models import GoogleCalendarConnection

    if not loja_id:
        return None

    qs = GoogleCalendarConnection.objects.using("default").filter(loja_id=loja_id)
    if vendedor_id is None:
        qs = qs.filter(vendedor_id__isnull=True)
    else:
        qs = qs.filter(vendedor_id=vendedor_id)
    return qs.first()


def _get_connection_for_request(request):
    """Wrapper legado — usa loja/vendedor do request."""
    loja_id = get_current_loja_id()
    if not loja_id:
        return None
    vendedor_id = get_current_vendedor_id(request) if request else None
    return _get_connection(loja_id, vendedor_id)


def sync_atividade_create_for_context(atividade, *, vendedor_id=None):
    """Sincroniza atividade criada (worker ou chamada direta com contexto explícito)."""
    if not atividade or not getattr(atividade, "loja_id", None):
        return

    try:
        connection = _get_connection(atividade.loja_id, vendedor_id)
        if not connection:
            return

        event_id = push_atividade_to_google(connection, atividade)
        if event_id:
            atividade.google_event_id = event_id
            atividade.save(update_fields=["google_event_id"])
            logger.info("✅ Atividade %s sincronizada com Google Calendar: %s", atividade.id, event_id)
    except Exception as e:
        logger.warning("⚠️ Erro ao sincronizar atividade com Google Calendar: %s", e)


def sync_atividade_update_for_context(atividade, *, vendedor_id=None):
    """Sincroniza atividade atualizada (worker ou chamada direta com contexto explícito)."""
    if not atividade or not getattr(atividade, "loja_id", None):
        return

    try:
        connection = _get_connection(atividade.loja_id, vendedor_id)
        if not connection:
            return

        event_id = push_atividade_to_google(connection, atividade)
        if event_id and not atividade.google_event_id:
            atividade.google_event_id = event_id
            atividade.save(update_fields=["google_event_id"])
        logger.info("✅ Atividade %s atualizada no Google Calendar: %s", atividade.id, event_id)
    except Exception as e:
        logger.warning("⚠️ Erro ao atualizar atividade no Google Calendar: %s", e)


def sync_atividade_delete_event(loja_id, google_event_id, *, vendedor_id=None):
    """Remove evento do Google Calendar pelo ID (usado no worker após destroy)."""
    if not google_event_id:
        return

    try:
        from superadmin.models import GoogleCalendarConnection

        connection = _get_connection(loja_id, vendedor_id)
        if not connection or not connection.access_token:
            connection = (
                GoogleCalendarConnection.objects.filter(loja_id=loja_id)
                .exclude(access_token="")
                .first()
            )
        if not connection:
            return

        success = delete_google_event(connection, google_event_id)
        if success:
            logger.info("✅ Evento deletado do Google Calendar: %s", google_event_id)
        else:
            logger.warning("⚠️ Falha ao deletar evento do Google Calendar: %s", google_event_id)
    except Exception as e:
        logger.warning("⚠️ Erro ao deletar evento do Google Calendar: %s", e)


def sync_atividade_create(request, atividade):
    """Sincroniza uma atividade recém-criada com o Google Calendar.
    Atualiza atividade.google_event_id se a sincronização for bem-sucedida.
    """
    vendedor_id = get_current_vendedor_id(request) if request else None
    sync_atividade_create_for_context(atividade, vendedor_id=vendedor_id)


def sync_atividade_update(request, atividade):
    """Sincroniza uma atividade atualizada com o Google Calendar.
    Cria evento no Google se ainda não existir (google_event_id vazio).
    """
    vendedor_id = get_current_vendedor_id(request) if request else None
    sync_atividade_update_for_context(atividade, vendedor_id=vendedor_id)


def sync_atividade_delete(loja_id, atividade):
    """Remove o evento do Google Calendar ao excluir uma atividade.
    Usa loja_id pois o request pode não estar disponível no perform_destroy.
    """
    if not atividade or not atividade.google_event_id:
        return
    sync_atividade_delete_event(loja_id, atividade.google_event_id)
