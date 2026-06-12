"""
Termo de consentimento esclarecido — Clínica da Beleza.

Monta o texto do termo e verifica se a consulta exige assinatura digital.
"""
from __future__ import annotations

from django.utils import timezone

from .models import ConsultaTermoProcedimento, Procedure

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


def nomes_procedimentos_termo(consulta) -> str:
    """Nomes dos procedimentos com termo ativo, para título do e-mail e tela de assinatura."""
    nomes = [p.nome for p in _procedimentos_com_termo_ativo(consulta)]
    return ', '.join(nomes) if nomes else 'Procedimento clínico'


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


def _ctx_base_termo(consulta) -> dict:
    loja = _dados_loja(consulta.loja_id)
    paciente = consulta.patient
    prof = consulta.professional
    data_str = timezone.localtime().strftime('%d/%m/%Y')
    if consulta.data_inicio:
        data_str = timezone.localtime(consulta.data_inicio).strftime('%d/%m/%Y')
    return {
        'paciente_nome': paciente.nome if paciente else '',
        'paciente_cpf': getattr(paciente, 'cpf', '') or '',
        'paciente_email': getattr(paciente, 'email', '') or '',
        'paciente_telefone': getattr(paciente, 'telefone', '') or '',
        'profissional_nome': prof.nome if prof else '',
        'profissional_conselho': prof.formatar_conselho() if prof else '',
        'profissional_cpf': getattr(prof, 'cpf', '') or '',
        'clinica_nome': loja['nome'],
        'clinica_cnpj': loja['cnpj'],
        'clinica_endereco': loja['endereco'],
        'clinica_telefone': loja['telefone'],
        'clinica_email': loja['email'],
        'data': data_str,
    }


def limpar_conteudo_termo_exibicao(conteudo: str) -> str:
    """Remove cabeçalho legado com metadados duplicados (já exibidos no PDF/tela)."""
    texto = (conteudo or '').strip()
    if not texto:
        return ''
    if 'Clínica:' in texto and 'Paciente:' in texto and 'Procedimento:' in texto:
        sep = '—' * 40
        if sep in texto:
            _, resto = texto.split(sep, 1)
            resto = resto.strip()
            if resto:
                return resto
    return texto


def montar_conteudo_termo_procedimento(consulta, procedure: Procedure) -> str:
    """Gera o texto jurídico do procedimento (metadados ficam no layout do PDF)."""
    tpl = (procedure.termo_consentimento or '').strip()
    if not tpl:
        return ''

    ctx_base = _ctx_base_termo(consulta)
    ctx = {**ctx_base, 'procedimento': procedure.nome, 'procedimentos': procedure.nome}
    return _renderizar_bloco_termo(tpl, ctx)


def montar_conteudo_termo_consentimento(consulta) -> str:
    """Legado — concatena todos os procedimentos (preferir termos por procedimento)."""
    procs = _procedimentos_com_termo_ativo(consulta)
    blocos = [montar_conteudo_termo_procedimento(consulta, p) for p in procs]
    blocos = [b for b in blocos if b]
    return '\n\n'.join(blocos) if blocos else ''


def sincronizar_status_consulta(consulta) -> None:
    """Atualiza status agregado da consulta a partir dos termos por procedimento."""
    termos = list(
        ConsultaTermoProcedimento.objects.filter(consulta=consulta).values_list(
            'status_assinatura_termo', flat=True,
        ),
    )
    if not termos:
        return
    if all(s == 'concluido' for s in termos):
        novo = 'concluido'
    elif any(s == 'aguardando_profissional' for s in termos):
        novo = 'aguardando_profissional'
    elif any(s == 'aguardando_paciente' for s in termos):
        novo = 'aguardando_paciente'
    else:
        novo = 'rascunho'
    if consulta.status_assinatura_termo != novo:
        consulta.status_assinatura_termo = novo
        consulta.save(update_fields=['status_assinatura_termo', 'updated_at'])


def garantir_termos_procedimento(consulta) -> list[ConsultaTermoProcedimento]:
    """Cria/atualiza um registro de termo por procedimento com termo ativo."""
    procs = _procedimentos_com_termo_ativo(consulta)
    resultado: list[ConsultaTermoProcedimento] = []
    for proc in procs:
        termo, _created = ConsultaTermoProcedimento.objects.get_or_create(
            consulta=consulta,
            procedure=proc,
            defaults={
                'loja_id': consulta.loja_id,
                'conteudo_termo': '',
                'status_assinatura_termo': 'rascunho',
            },
        )
        if termo.status_assinatura_termo == 'concluido':
            pass
        elif termo.status_assinatura_termo == 'aguardando_profissional':
            limpo = limpar_conteudo_termo_exibicao(termo.conteudo_termo)
            if limpo and limpo != termo.conteudo_termo:
                termo.conteudo_termo = limpo
                termo.save(update_fields=['conteudo_termo', 'updated_at'])
        else:
            conteudo = montar_conteudo_termo_procedimento(consulta, proc)
            if conteudo and termo.conteudo_termo != conteudo:
                termo.conteudo_termo = conteudo
                termo.save(update_fields=['conteudo_termo', 'updated_at'])
        resultado.append(termo)
    sincronizar_status_consulta(consulta)
    return list(
        ConsultaTermoProcedimento.objects.filter(consulta=consulta)
        .select_related('procedure')
        .order_by('procedure__nome'),
    )


STATUS_TERMO_DISPLAY = {
    'rascunho': 'Não enviado',
    'aguardando_paciente': 'Aguardando paciente',
    'aguardando_profissional': 'Aguardando profissional',
    'concluido': 'Assinado',
}


def serializar_termos_procedimento(consulta) -> list[dict]:
    """Lista termos por procedimento para a API."""
    termos = garantir_termos_procedimento(consulta)
    return [
        {
            'id': t.id,
            'procedure_id': t.procedure_id,
            'procedure_nome': t.procedure.nome,
            'status': t.status_assinatura_termo,
            'status_display': STATUS_TERMO_DISPLAY.get(
                t.status_assinatura_termo, t.status_assinatura_termo,
            ),
            'tem_conteudo': bool((t.conteudo_termo or '').strip()),
        }
        for t in termos
    ]
