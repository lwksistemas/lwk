"""
Lembretes automáticos de atividades do CRM por WhatsApp (24h e 2h antes).
"""
import logging
from datetime import timedelta

from django.utils import timezone

logger = logging.getLogger(__name__)


def _janela_antecedencia(antecedencia: str):
    agora = timezone.now()
    if antecedencia == '24h':
        return (
            agora + timedelta(hours=23, minutes=40),
            agora + timedelta(hours=24, minutes=20),
            'lembrete_24h_enviado_em',
            'enviar_lembrete_24h',
        )
    return (
        agora + timedelta(hours=1, minutes=40),
        agora + timedelta(hours=2, minutes=20),
        'lembrete_2h_enviado_em',
        'enviar_lembrete_2h',
    )


def send_lembretes_atividade_crm(antecedencia: str) -> int:
    """
    Envia lembretes WhatsApp para atividades com lembrete_whatsapp=True.
    antecedencia: '24h' ou '2h'
    """
    from crm_vendas.atividade_whatsapp_service import enviar_lembrete_atividade_whatsapp
    from superadmin.models import Loja
    from tenants.middleware import set_current_loja_id, set_current_tenant_db
    from whatsapp.tasks import _ensure_loja_db, _get_whatsapp_config

    inicio, fim, campo_enviado, config_flag = _janela_antecedencia(antecedencia)
    lojas = Loja.objects.filter(
        tipo_loja__slug='crm-vendas',
        database_created=True,
        is_active=True,
    )
    enviados = 0

    for loja in lojas:
        try:
            db_name = _ensure_loja_db(loja)
            set_current_loja_id(loja.id)
            set_current_tenant_db(db_name)

            config = _get_whatsapp_config(loja)
            if not config or not config.whatsapp_ativo:
                continue
            if not getattr(config, 'enviar_lembrete_tarefas', True):
                continue
            if not getattr(config, config_flag, True):
                continue

            filtro = {
                'concluido': False,
                'lembrete_whatsapp': True,
                'data__gte': inicio,
                'data__lte': fim,
                f'{campo_enviado}__isnull': True,
            }
            from crm_vendas.models import Atividade

            qs = (
                Atividade.objects.using(db_name)
                .filter(**filtro)
                .exclude(lembrete_whatsapp_telefone='')
                .select_related('lead')
            )

            for atividade in qs:
                ok, _ = enviar_lembrete_atividade_whatsapp(
                    loja.id,
                    atividade,
                    antecedencia,
                )
                if ok:
                    Atividade.objects.using(db_name).filter(pk=atividade.pk).update(
                        **{campo_enviado: timezone.now()}
                    )
                    enviados += 1
        except Exception as exc:
            logger.exception(
                'Lembrete atividade CRM %s loja %s: %s',
                antecedencia,
                getattr(loja, 'slug', loja.id),
                exc,
            )
        finally:
            set_current_loja_id(None)
            set_current_tenant_db('default')

    logger.info('CRM atividade lembretes %s: %d enviados', antecedencia, enviados)
    return enviados


def send_lembretes_atividade_crm_24h() -> int:
    return send_lembretes_atividade_crm('24h')


def send_lembretes_atividade_crm_2h() -> int:
    return send_lembretes_atividade_crm('2h')
