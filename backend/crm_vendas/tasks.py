"""
Tarefas agendadas do CRM Vendas.
"""
from django.core.management import call_command


def notificar_tarefas_crm():
    """
    Cria notificações in-app para tarefas do CRM que estão próximas (próximas 24h).
    Chamado pelo Django-Q Schedule.
    """
    call_command('notificar_tarefas_crm', verbosity=1)


def lembretes_atividade_crm_24h():
    from crm_vendas.atividade_lembrete_tasks import send_lembretes_atividade_crm_24h
    return send_lembretes_atividade_crm_24h()


def lembretes_atividade_crm_2h():
    from crm_vendas.atividade_lembrete_tasks import send_lembretes_atividade_crm_2h
    return send_lembretes_atividade_crm_2h()
