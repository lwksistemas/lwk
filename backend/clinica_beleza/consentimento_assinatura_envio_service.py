"""Envio e reenvio de termos de consentimento para assinatura."""
from __future__ import annotations

from .consentimento_assinatura_publica_service import preencher_termo_se_vazio
from .consentimento_service import aviso_email_paciente_suspeito

CANAIS_ENVIO_VALIDOS = ('email', 'whatsapp')


def normalizar_canal_envio(canal: str | None) -> str | None:
    valor = (canal or 'email').strip().lower()
    return valor if valor in CANAIS_ENVIO_VALIDOS else None


def validar_destino_envio_termo(*, termo_proc, consulta, adapter, canal: str, loja_id: int) -> str | None:
    """Retorna mensagem de erro ou None se o destino é válido."""
    if canal == 'whatsapp':
        from whatsapp.assinatura_whatsapp import whatsapp_envio_permitido
        from whatsapp.models import WhatsAppConfig

        config = WhatsAppConfig.objects.filter(loja_id=loja_id).first()
        ok_cfg, err_cfg = whatsapp_envio_permitido(config, termo=True)
        if not ok_cfg:
            return err_cfg or 'WhatsApp indisponível.'
        telefone = adapter.get_telefone_parte1(termo_proc)
        if not telefone:
            return 'Paciente não possui telefone cadastrado.'
        return None

    paciente = consulta.patient
    email_paciente = (getattr(paciente, 'email', '') or '').strip() if paciente else ''
    if not paciente or not email_paciente:
        return 'Paciente não possui e-mail cadastrado.'
    return aviso_email_paciente_suspeito(email_paciente)


def enviar_um_termo(
    *,
    termo_proc,
    consulta,
    adapter,
    loja_id: int,
    canal: str,
    request,
) -> tuple[bool, str]:
    """Envia um termo por e-mail ou WhatsApp. Retorna (sucesso, nome_proc ou erro)."""
    from core.assinatura_service import criar_assinatura, enviar_email_parte1
    from whatsapp.assinatura_whatsapp import enviar_whatsapp_link_assinatura

    preencher_termo_se_vazio(termo_proc)
    nome_proc = termo_proc.procedure.nome

    if canal == 'whatsapp':
        telefone = adapter.get_telefone_parte1(termo_proc)
        if not telefone:
            return False, 'Paciente não possui telefone cadastrado.'
    else:
        paciente = consulta.patient
        email_paciente = (getattr(paciente, 'email', '') or '').strip() if paciente else ''
        if not paciente or not email_paciente:
            return False, 'Paciente não possui e-mail cadastrado.'
        aviso_email = aviso_email_paciente_suspeito(email_paciente)
        if aviso_email:
            return False, aviso_email

    assinatura = criar_assinatura(adapter, termo_proc, 'paciente', loja_id)
    termo_proc.status_assinatura_termo = 'aguardando_paciente'
    termo_proc.save(update_fields=['status_assinatura_termo', 'updated_at'])

    if canal == 'whatsapp':
        ok, err = enviar_whatsapp_link_assinatura(
            adapter, termo_proc, assinatura, loja_id,
            telefone=adapter.get_telefone_parte1(termo_proc),
            user=request.user,
        )
    else:
        ok, err = enviar_email_parte1(adapter, termo_proc, assinatura, loja_id)
        err = err or 'erro no e-mail'

    if ok:
        return True, nome_proc

    termo_proc.status_assinatura_termo = 'rascunho'
    termo_proc.save(update_fields=['status_assinatura_termo', 'updated_at'])
    assinatura.delete()
    return False, f'{nome_proc}: {err}'


def reenviar_termo_whatsapp(
    *,
    termo_proc,
    adapter,
    loja_id: int,
    request,
) -> tuple[bool, str | None, str | None]:
    """
    Reenvia link por WhatsApp quando o termo já está aguardando paciente.
    Retorna (ok, telefone, erro).
    """
    from core.assinatura_service import criar_assinatura
    from whatsapp.assinatura_whatsapp import enviar_whatsapp_link_assinatura, whatsapp_envio_permitido
    from whatsapp.models import WhatsAppConfig

    from .models import ConsultaAssinaturaTermo

    config = WhatsAppConfig.objects.filter(loja_id=loja_id).first()
    ok_cfg, err_cfg = whatsapp_envio_permitido(config, termo=True)
    if not ok_cfg:
        return False, None, err_cfg

    telefone = adapter.get_telefone_parte1(termo_proc)
    if not telefone:
        return False, None, 'Paciente não possui telefone cadastrado.'

    assinatura = ConsultaAssinaturaTermo.objects.filter(
        termo_procedimento=termo_proc, tipo='paciente', assinado=False,
    ).order_by('-created_at').first()
    if not assinatura:
        adapter.deletar_assinaturas_pendentes(termo_proc, 'paciente')
        assinatura = criar_assinatura(adapter, termo_proc, 'paciente', loja_id)

    ok, err = enviar_whatsapp_link_assinatura(
        adapter, termo_proc, assinatura, loja_id, telefone=telefone, user=request.user,
    )
    if ok:
        return True, telefone, None
    return False, telefone, err or 'Erro ao reenviar.'


def enviar_termo_assinado_whatsapp(
    *,
    termo_proc,
    adapter,
    loja_id: int,
    user=None,
) -> tuple[bool, str]:
    """
    Envia o PDF do termo já assinado (paciente + profissional) via WhatsApp.
    Mesmo padrão do recibo: texto + documento público temporário.
    """
    import hashlib
    import logging
    import time

    from django.conf import settings
    from django.core.cache import cache as django_cache
    from whatsapp.assinatura_whatsapp import whatsapp_envio_permitido
    from whatsapp.models import WhatsAppConfig
    from whatsapp.services import _send_whatsapp_document_evolution, send_whatsapp

    logger = logging.getLogger(__name__)

    if termo_proc.status_assinatura_termo != 'concluido':
        return False, 'O termo ainda não foi assinado pelas duas partes.'

    config = WhatsAppConfig.objects.filter(loja_id=loja_id).first()
    ok_cfg, err_cfg = whatsapp_envio_permitido(config, termo=True)
    if not ok_cfg:
        return False, err_cfg or 'WhatsApp indisponível.'

    telefone = adapter.get_telefone_parte1(termo_proc)
    if not telefone:
        return False, 'Paciente não possui telefone cadastrado.'

    consulta = termo_proc.consulta
    paciente = getattr(consulta, 'patient', None)
    nome_paciente = (getattr(paciente, 'nome', None) or 'cliente').strip()
    nome_proc = (termo_proc.procedure.nome if termo_proc.procedure_id else 'procedimento').strip()
    mensagem = (
        f'Olá {nome_paciente}! Segue o PDF do termo de consentimento assinado '
        f'({nome_proc}).'
    )

    ok, err = send_whatsapp(telefone=telefone, mensagem=mensagem, config=config, user=user)
    if not ok:
        return False, err or 'Erro ao enviar WhatsApp.'

    try:
        pdf = adapter.gerar_pdf(termo_proc, incluir_assinaturas=True)
        pdf_bytes = pdf.getvalue() if hasattr(pdf, 'getvalue') else bytes(pdf)
        ts = str(int(time.time()))
        token_raw = f'termo-{consulta.id}-{termo_proc.procedure_id}-{ts}-{settings.SECRET_KEY[:16]}'
        token = hashlib.sha256(token_raw.encode()).hexdigest()[:32]
        django_cache.set(
            f'termo_pdf_{token}',
            {
                'consulta_id': consulta.id,
                'procedure_id': termo_proc.procedure_id,
                'pdf': pdf_bytes,
            },
            300,
        )
        api_base = getattr(settings, 'API_BASE_URL', '') or 'https://api.lwksistemas.com.br'
        pdf_url = (
            f'{api_base}/api/clinica-beleza/termo-consentimento-pdf/'
            f'{consulta.id}/{termo_proc.procedure_id}/{token}/'
        )
        nome_arquivo = f'termo_{nome_proc.replace(" ", "_")[:40]}_{consulta.id}.pdf'
        _send_whatsapp_document_evolution(
            telefone,
            pdf_url,
            nome_arquivo,
            caption='Termo de Consentimento Assinado',
            config=config,
            user=user,
        )
    except Exception as pdf_err:
        logger.warning(
            'PDF do termo via WhatsApp falhou (texto já enviado) consulta=%s proc=%s: %s',
            consulta.id,
            termo_proc.procedure_id,
            pdf_err,
        )

    return True, f'Termo assinado enviado por WhatsApp para {telefone}'


def resolver_termos_para_envio(consulta, procedure_id) -> tuple[list, str | None]:
    """
    Lista termos a enviar ou mensagem de erro.
    procedure_id None = todos em rascunho.
    """
    from .consentimento_assinatura_publica_service import resolver_termo_procedimento
    from .consentimento_service import garantir_termos_procedimento

    termos = garantir_termos_procedimento(consulta)
    if procedure_id:
        termo_proc = resolver_termo_procedimento(consulta, procedure_id)
        if not termo_proc:
            return [], 'Procedimento não encontrado nesta consulta.'
        if termo_proc.status_assinatura_termo != 'rascunho':
            return [], (
                f'Termo de "{termo_proc.procedure.nome}" já está em processo de assinatura.'
            )
        return [termo_proc], None

    termos_a_enviar = [t for t in termos if t.status_assinatura_termo == 'rascunho']
    if not termos_a_enviar:
        return [], 'Não há termos pendentes de envio. Todos já estão em assinatura ou concluídos.'
    return termos_a_enviar, None
