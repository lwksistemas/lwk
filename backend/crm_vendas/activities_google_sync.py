"""
Serviço de sincronização de atividades com Google Calendar.
Extrai a lógica de sync do AtividadeViewSet para centralizar e evitar duplicação.
"""
import logging

from tenants.middleware import get_current_loja_id
from .utils import get_current_vendedor_id
from .google_calendar_service import push_atividade_to_google, delete_google_event

logger = logging.getLogger(__name__)


def _get_connection_for_request(request):
    """
    Busca a conexão do Google Calendar para o contexto atual (owner ou vendedor).
    Retorna None se não houver conexão.
    """
    from superadmin.models import GoogleCalendarConnection

    loja_id = get_current_loja_id()
    if not loja_id:
        return None

    vendedor_id = get_current_vendedor_id(request) if request else None
    qs = GoogleCalendarConnection.objects.using('default').filter(loja_id=loja_id)
    if vendedor_id is None:
        qs = qs.filter(vendedor_id__isnull=True)
    else:
        qs = qs.filter(vendedor_id=vendedor_id)
    return qs.first()


def sync_atividade_create(request, atividade):
    """
    Sincroniza uma atividade recém-criada com o Google Calendar.
    Atualiza atividade.google_event_id se a sincronização for bem-sucedida.
    """
    if not atividade or not getattr(atividade, 'loja_id', None):
        return

    try:
        connection = _get_connection_for_request(request)
        if not connection:
            return

        event_id = push_atividade_to_google(connection, atividade)
        if event_id:
            atividade.google_event_id = event_id
            atividade.save(update_fields=['google_event_id'])
            logger.info("✅ Atividade %s sincronizada com Google Calendar: %s", atividade.id, event_id)
    except Exception as e:
        logger.warning("⚠️ Erro ao sincronizar atividade com Google Calendar: %s", e)


def sync_atividade_update(request, atividade):
    """
    Sincroniza uma atividade atualizada com o Google Calendar.
    Cria evento no Google se ainda não existir (google_event_id vazio).
    """
    if not atividade or not getattr(atividade, 'loja_id', None):
        return

    try:
        connection = _get_connection_for_request(request)
        if not connection:
            return

        event_id = push_atividade_to_google(connection, atividade)
        if event_id and not atividade.google_event_id:
            atividade.google_event_id = event_id
            atividade.save(update_fields=['google_event_id'])
        logger.info("✅ Atividade %s atualizada no Google Calendar: %s", atividade.id, event_id)
    except Exception as e:
        logger.warning("⚠️ Erro ao atualizar atividade no Google Calendar: %s", e)


def sync_atividade_delete(loja_id, atividade):
    """
    Remove o evento do Google Calendar ao excluir uma atividade.
    Usa loja_id pois o request pode não estar disponível no perform_destroy.
    """
    if not atividade or not atividade.google_event_id:
        return

    try:
        from superadmin.models import GoogleCalendarConnection

        connection = (
            GoogleCalendarConnection.objects.filter(loja_id=loja_id)
            .exclude(access_token='')
            .first()
        )
        if not connection:
            return

        success = delete_google_event(connection, atividade.google_event_id)
        if success:
            logger.info("✅ Evento deletado do Google Calendar: %s", atividade.google_event_id)
        else:
            logger.warning("⚠️ Falha ao deletar evento do Google Calendar: %s", atividade.google_event_id)
    except Exception as e:
        logger.warning("⚠️ Erro ao deletar evento do Google Calendar: %s", e)
