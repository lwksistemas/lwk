"""
Retentativas de envio do link de assinatura ao vendedor após assinatura do cliente.
"""
import logging
import threading
import time

from django.conf import settings
from django.db import close_old_connections
from django.utils import timezone

logger = logging.getLogger(__name__)

_RETRY_DELAYS_SEC = (30, 120, 300)


def _configurar_tenant_loja(loja_id):
    from tenants.middleware import set_current_loja_id, set_current_tenant_db
    from superadmin.models import Loja
    from core.db_config import ensure_loja_database_config

    set_current_loja_id(loja_id)
    loja = Loja.objects.using('default').filter(id=loja_id).first()
    if not loja:
        return None
    db_name = getattr(loja, 'database_name', None) or f'loja_{getattr(loja, "slug", "")}'
    if not ensure_loja_database_config(db_name, conn_max_age=0) or db_name not in settings.DATABASES:
        return None
    set_current_tenant_db(db_name)
    return loja


def tentar_envio_vendedor_por_id(assinatura_id, loja_id):
    """
    Carrega assinatura pendente do vendedor e tenta enviar por todos os canais.
    Retorna True se o link foi enviado com sucesso.
    """
    from .models import AssinaturaDigital
    from .assinatura_digital_service import tentar_enviar_link_vendedor

    if not _configurar_tenant_loja(loja_id):
        return False

    assinatura = (
        AssinaturaDigital.objects.filter(
            pk=assinatura_id,
            loja_id=loja_id,
            tipo='vendedor',
            assinado=False,
        )
        .select_related('proposta', 'contrato', 'proposta__oportunidade__vendedor', 'contrato__oportunidade__vendedor')
        .first()
    )
    if not assinatura or assinatura.link_enviado_em:
        return bool(assinatura and assinatura.link_enviado_em)

    documento = assinatura.documento
    if not documento or getattr(documento, 'status_assinatura', None) != 'aguardando_vendedor':
        return False

    ok, _, _ = tentar_enviar_link_vendedor(documento, assinatura, request=None)
    return ok


def agendar_retry_envio_vendedor(assinatura_id, loja_id):
    """Retenta envio em background (30s, 2min, 5min) sem bloquear a assinatura do cliente."""

    def _run():
        for delay in _RETRY_DELAYS_SEC:
            time.sleep(delay)
            try:
                close_old_connections()
                if tentar_envio_vendedor_por_id(assinatura_id, loja_id):
                    logger.info(
                        'Retry envio vendedor OK: assinatura_id=%s loja_id=%s',
                        assinatura_id,
                        loja_id,
                    )
                    return
            except Exception as exc:
                logger.warning(
                    'Retry envio vendedor falhou: assinatura_id=%s loja_id=%s err=%s',
                    assinatura_id,
                    loja_id,
                    exc,
                )

    threading.Thread(
        target=_run,
        daemon=True,
        name=f'crm-vendedor-retry-{assinatura_id}',
    ).start()


def processar_envios_vendedor_pendentes():
    """
    Varre lojas CRM e reenvia links pendentes (aguardando_vendedor, token sem link_enviado_em).
    Chamado pelo scheduler do WSGI como rede de segurança.
    """
    from superadmin.models import Loja
    from .models import AssinaturaDigital

    lojas = Loja.objects.using('default').filter(is_active=True, database_created=True).exclude(database_name='')
    limite = timezone.now() - timezone.timedelta(minutes=1)
    processados = 0

    for loja in lojas.iterator():
        if not _configurar_tenant_loja(loja.id):
            continue
        try:
            pendentes = list(
                AssinaturaDigital.objects.filter(
                    loja_id=loja.id,
                    tipo='vendedor',
                    assinado=False,
                    link_enviado_em__isnull=True,
                    created_at__lt=limite,
                    token_expira_em__gt=timezone.now(),
                ).select_related('proposta', 'contrato')[:20]
            )
        except Exception as exc:
            logger.debug('processar_envios_vendedor_pendentes loja=%s: %s', loja.slug, exc)
            continue

        for assinatura in pendentes:
            documento = assinatura.documento
            if not documento:
                continue
            sa = getattr(documento, 'status_assinatura', None)
            if sa != 'aguardando_vendedor':
                continue
            if tentar_envio_vendedor_por_id(assinatura.id, loja.id):
                processados += 1

    if processados:
        logger.info('processar_envios_vendedor_pendentes: %s envios concluídos', processados)
    return processados
