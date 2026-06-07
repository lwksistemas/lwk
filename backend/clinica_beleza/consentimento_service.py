"""
Termo de consentimento esclarecido — Clínica da Beleza.

Monta o texto do termo e verifica se a consulta exige assinatura digital.
"""
from __future__ import annotations

from django.utils import timezone

from .models import Procedure

# Domínios com erro de digitação frequente — bloqueia envio e orienta correção no cadastro.
_EMAIL_DOMINIO_TYPO: dict[str, str] = {
    'homail.com': 'hotmail.com',
    'hotmial.com': 'hotmail.com',
    'hotmal.com': 'hotmail.com',
    'gmial.com': 'gmail.com',
    'gmal.com': 'gmail.com',
    'gmai.com': 'gmail.com',
    'outlok.com': 'outlook.com',
    'outllok.com': 'outlook.com',
    'yaho.com': 'yahoo.com',
    'yahooo.com': 'yahoo.com',
}


def aviso_email_paciente_suspeito(email: str) -> str | None:
    """Retorna mensagem de erro se o domínio do e-mail parece digitado errado."""
    email = (email or '').strip().lower()
    if '@' not in email:
        return None
    dominio = email.rsplit('@', 1)[-1]
    sugestao = _EMAIL_DOMINIO_TYPO.get(dominio)
    if not sugestao:
        return None
    corrigido = f'{email.rsplit("@", 1)[0]}@{sugestao}'
    return (
        f'E-mail do paciente parece incorreto ({email}). '
        f'Corrija no cadastro do paciente (sugestão: {corrigido}) e tente novamente.'
    )


def _procedimentos_com_termo_ativo(consulta) -> list[Procedure]:
    """Procedimentos da consulta com termo de consentimento ativo."""
    vistos: set[int] = set()
    resultado: list[Procedure] = []

    def _add(proc: Procedure | None):
        if not proc or proc.id in vistos:
            return
        if proc.termo_consentimento_ativo and (proc.termo_consentimento or '').strip():
            vistos.add(proc.id)
            resultado.append(proc)

    appointment = getattr(consulta, 'appointment', None)
    if appointment:
        for ap in appointment.appointment_procedures.select_related('procedure').all():
            _add(ap.procedure)

    for cpu in consulta.produtos_estoque.select_related('produto__procedure').all():
        prod = cpu.produto
        if prod and prod.procedure_id:
            _add(prod.procedure)

    if consulta.procedure_id:
        _add(consulta.procedure)

    return resultado


def consulta_exige_termo_consentimento(consulta) -> bool:
    """True se há produto/procedimento com termo ativo na consulta."""
    return bool(_procedimentos_com_termo_ativo(consulta))


def _dados_loja(loja_id: int) -> dict:
    from superadmin.models import Loja

    loja = Loja.objects.using('default').filter(id=loja_id).first()
    if not loja:
        return {'nome': 'Clínica', 'cnpj': '', 'endereco': '', 'telefone': '', 'email': ''}
    endereco = ', '.join(
        p for p in [
            getattr(loja, 'endereco', '') or '',
            getattr(loja, 'cidade', '') or '',
            getattr(loja, 'estado', '') or '',
        ] if p
    )
    return {
        'nome': loja.nome or 'Clínica',
        'cnpj': getattr(loja, 'cpf_cnpj', '') or '',
        'endereco': endereco,
        'telefone': getattr(loja, 'telefone', '') or '',
        'email': getattr(loja, 'email', '') or '',
    }


def _renderizar_bloco_termo(template: str, ctx: dict) -> str:
    texto = template or ''
    for chave, valor in ctx.items():
        texto = texto.replace(f'{{{chave}}}', str(valor or ''))
    return texto


def montar_conteudo_termo_consentimento(consulta) -> str:
    """
    Gera o conteúdo final do termo com dados da clínica, profissional, paciente
    e blocos de cada procedimento com termo ativo.
    """
    procs = _procedimentos_com_termo_ativo(consulta)
    if not procs:
        return ''

    loja = _dados_loja(consulta.loja_id)
    paciente = consulta.patient
    prof = consulta.professional
    data_str = timezone.localtime().strftime('%d/%m/%Y')
    if consulta.data_inicio:
        data_str = timezone.localtime(consulta.data_inicio).strftime('%d/%m/%Y')

    ctx_base = {
        'paciente_nome': paciente.nome if paciente else '',
        'paciente_cpf': getattr(paciente, 'cpf', '') or '',
        'paciente_email': getattr(paciente, 'email', '') or '',
        'paciente_telefone': getattr(paciente, 'telefone', '') or '',
        'profissional_nome': prof.nome if prof else '',
        'profissional_conselho': getattr(prof, 'conselho', '') or '',
        'profissional_cpf': getattr(prof, 'cpf', '') or '',
        'clinica_nome': loja['nome'],
        'clinica_cnpj': loja['cnpj'],
        'clinica_endereco': loja['endereco'],
        'clinica_telefone': loja['telefone'],
        'clinica_email': loja['email'],
        'procedimentos': ', '.join(p.nome for p in procs),
        'data': data_str,
    }

    blocos = []
    for proc in procs:
        tpl = (proc.termo_consentimento or '').strip()
        if not tpl:
            continue
        ctx = {**ctx_base, 'procedimento': proc.nome}
        blocos.append(_renderizar_bloco_termo(tpl, ctx))

    if not blocos:
        return ''

    cabecalho = (
        f'TERMO DE CONSENTIMENTO ESCLARECIDO\n\n'
        f'Clínica: {ctx_base["clinica_nome"]}\n'
        f'CNPJ: {ctx_base["clinica_cnpj"]}\n'
        f'Endereço: {ctx_base["clinica_endereco"]}\n\n'
        f'Paciente: {ctx_base["paciente_nome"]}\n'
        f'Profissional: {ctx_base["profissional_nome"]}\n'
        f'Data: {ctx_base["data"]}\n'
        f'Procedimento(s): {ctx_base["procedimentos"]}\n\n'
        f'{"—" * 40}\n\n'
    )
    return cabecalho + '\n\n'.join(blocos)
