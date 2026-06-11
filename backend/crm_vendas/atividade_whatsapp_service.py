"""Envio de lembrete de atividade do CRM por WhatsApp."""
from __future__ import annotations

from typing import Any

from django.utils import timezone


def montar_mensagem_lembrete_atividade(
    atividade: Any,
    loja_nome: str,
    antecedencia: str,
) -> str:
    """Mensagem de lembrete automático (24h ou 2h antes)."""
    tipo = (
        atividade.get_tipo_display()
        if hasattr(atividade, 'get_tipo_display')
        else getattr(atividade, 'tipo', 'task')
    )
    data_local = timezone.localtime(atividade.data) if atividade.data else None
    data_str = data_local.strftime('%d/%m/%Y às %H:%M') if data_local else ''
    quando = '24 horas' if antecedencia == '24h' else '2 horas'

    linhas = [
        f'🔔 *Lembrete — faltam {quando}*',
        f'📅 *{loja_nome}*',
        '',
        f'*{tipo}:* {atividade.titulo}',
        f'*Quando:* {data_str}',
    ]

    lead = getattr(atividade, 'lead', None)
    if lead:
        lead_nome = (getattr(lead, 'nome', '') or '').strip()
        if lead_nome:
            linhas.append(f'*Cliente:* {lead_nome}')

    linhas.append('')
    linhas.append('_Mensagem automática do calendário CRM._')
    return '\n'.join(linhas)


def montar_mensagem_atividade_whatsapp(atividade: Any, loja_nome: str) -> str:
    tipo = (
        atividade.get_tipo_display()
        if hasattr(atividade, 'get_tipo_display')
        else getattr(atividade, 'tipo', 'task')
    )
    data_local = timezone.localtime(atividade.data) if atividade.data else None
    data_str = data_local.strftime('%d/%m/%Y %H:%M') if data_local else ''
    duracao = int(getattr(atividade, 'duracao_minutos', None) or 60)
    if duracao < 60:
        duracao_str = f'{duracao} min'
    elif duracao % 60 == 0:
        duracao_str = f'{duracao // 60}h'
    else:
        duracao_str = f'{duracao // 60}h {duracao % 60}min'

    linhas = [
        f'📅 *Atividade — {loja_nome}*',
        '',
        f'*{tipo}:* {atividade.titulo}',
        f'*Quando:* {data_str}',
        f'*Duração:* {duracao_str}',
    ]

    lead = getattr(atividade, 'lead', None)
    if lead:
        lead_nome = (getattr(lead, 'nome', '') or '').strip()
        empresa = (getattr(lead, 'empresa', '') or '').strip()
        if lead_nome:
            cliente = f'{lead_nome} — {empresa}' if empresa and empresa.lower() != lead_nome.lower() else lead_nome
            linhas.append(f'*Cliente:* {cliente}')

    obs = (getattr(atividade, 'observacoes', '') or '').strip()
    if obs:
        linhas.extend(['', obs])

    return '\n'.join(linhas)


def enviar_atividade_whatsapp(
    loja_id: int,
    atividade: Any,
    telefone: str,
    *,
    user=None,
) -> tuple[bool, str]:
    from superadmin.models import Loja
    from whatsapp.models import WhatsAppConfig
    from whatsapp.services import send_whatsapp

    telefone = (telefone or '').strip()
    if not telefone:
        return False, 'Informe o número de WhatsApp.'

    config = WhatsAppConfig.objects.filter(loja_id=loja_id).first()
    if not config or not getattr(config, 'whatsapp_ativo', False):
        return False, 'WhatsApp não está ativo. Configure em Configurações → WhatsApp.'

    loja = Loja.objects.using('default').filter(id=loja_id).first()
    loja_nome = (loja.nome if loja else 'CRM') or 'CRM'
    mensagem = montar_mensagem_atividade_whatsapp(atividade, loja_nome)

    ok, err = send_whatsapp(
        telefone=telefone,
        mensagem=mensagem,
        user=user,
        config=config,
    )
    if not ok:
        return False, err or 'Erro ao enviar WhatsApp.'
    return True, telefone


def enviar_lembrete_atividade_whatsapp(
    loja_id: int,
    atividade: Any,
    antecedencia: str,
    *,
    user=None,
) -> tuple[bool, str]:
    """Envia lembrete automático (24h ou 2h) para o número cadastrado na atividade."""
    from superadmin.models import Loja
    from whatsapp.models import WhatsAppConfig
    from whatsapp.services import send_whatsapp

    telefone = (getattr(atividade, 'lembrete_whatsapp_telefone', '') or '').strip()
    if not telefone:
        return False, 'Telefone de lembrete não informado.'

    config = WhatsAppConfig.objects.filter(loja_id=loja_id).first()
    if not config or not getattr(config, 'whatsapp_ativo', False):
        return False, 'WhatsApp não está ativo.'

    if antecedencia == '24h' and not getattr(config, 'enviar_lembrete_24h', True):
        return False, 'Lembrete 24h desabilitado na configuração.'
    if antecedencia == '2h' and not getattr(config, 'enviar_lembrete_2h', True):
        return False, 'Lembrete 2h desabilitado na configuração.'
    if not getattr(config, 'enviar_lembrete_tarefas', True):
        return False, 'Lembretes de tarefas CRM desabilitados.'

    loja = Loja.objects.using('default').filter(id=loja_id).first()
    loja_nome = (loja.nome if loja else 'CRM') or 'CRM'
    mensagem = montar_mensagem_lembrete_atividade(atividade, loja_nome, antecedencia)

    ok, err = send_whatsapp(
        telefone=telefone,
        mensagem=mensagem,
        user=user,
        config=config,
    )
    if not ok:
        return False, err or 'Erro ao enviar WhatsApp.'
    return True, telefone
