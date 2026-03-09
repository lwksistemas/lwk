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
