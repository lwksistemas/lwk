"""Helpers para montar e enviar e-mails de NFS-e."""
import logging
from decimal import Decimal
from typing import Any

from django.conf import settings
from django.core.mail import EmailMessage

from core.logging_utils import mask_email

logger = logging.getLogger(__name__)


def montar_corpo_email_nfse(
    *,
    loja: Any,
    tomador_nome: str,
    numero_nf: str,
    valor: Decimal | float | str,
    descricao: str,
    url_danfe: str = '',
    intro: str = 'Segue as informações da Nota Fiscal de Serviço Eletrônica.',
    codigo_verificacao: str = '',
    incluir_codigo_verificacao: bool = True,
    prestador_nome: str | None = None,
    prestador_cnpj: str | None = None,
    rodape_simples: bool = False,
    incluir_cnpj_prestador: bool = True,
) -> str:
    """Monta o corpo do e-mail mantendo o formato usado no produto."""
    nome_prestador = prestador_nome if prestador_nome is not None else loja.nome
    cnpj_prestador = prestador_cnpj if prestador_cnpj is not None else getattr(loja, 'cpf_cnpj', '')

    corpo = (
        f'Olá {tomador_nome}!\n\n'
        f'{intro}\n\n'
        f'📋 DADOS DA NOTA FISCAL:\n'
        f'• Número: {numero_nf}\n'
        f'• Prestador: {nome_prestador}\n'
    )
    if incluir_cnpj_prestador:
        corpo += f'• CNPJ: {cnpj_prestador}\n'
    corpo += f'• Valor: R$ {float(valor):.2f}\n'

    if incluir_codigo_verificacao:
        corpo += f'• Código de Verificação: {codigo_verificacao or "—"}\n'

    corpo += f'• Descrição: {descricao}\n\n'

    if url_danfe:
        corpo += (
            f'📄 VISUALIZAR NOTA FISCAL (DANFE):\n'
            f'{url_danfe}\n\n'
        )

    if rodape_simples:
        return corpo + f'Atenciosamente,\n{nome_prestador}'

    return corpo + (
        f'---\n'
        f'Atenciosamente,\n'
        f'{nome_prestador}'
    )


def enviar_email_nfse_tomador(
    *,
    loja: Any,
    tomador_email: str,
    tomador_nome: str,
    numero_nf: str,
    valor: Decimal | float | str,
    descricao: str,
    url_danfe: str = '',
    codigo_verificacao: str = '',
    xml_content: str = '',
    fail_silently: bool = False,
    intro: str = 'Segue as informações da Nota Fiscal de Serviço Eletrônica.',
    incluir_codigo_verificacao: bool = True,
    xml_filename: str | None = None,
    prestador_nome: str | None = None,
    prestador_cnpj: str | None = None,
    rodape_simples: bool = False,
    assunto_prestador: str | None = None,
    incluir_cnpj_prestador: bool = True,
) -> None:
    """Envia e-mail de NFS-e ao tomador e anexa XML quando disponível."""
    nome_assunto = assunto_prestador or prestador_nome or loja.nome
    assunto = f'Nota Fiscal de Serviço Nº {numero_nf} - {nome_assunto}'
    corpo = montar_corpo_email_nfse(
        loja=loja,
        tomador_nome=tomador_nome,
        numero_nf=numero_nf,
        valor=valor,
        descricao=descricao,
        url_danfe=url_danfe,
        intro=intro,
        codigo_verificacao=codigo_verificacao,
        incluir_codigo_verificacao=incluir_codigo_verificacao,
        prestador_nome=prestador_nome,
        prestador_cnpj=prestador_cnpj,
        rodape_simples=rodape_simples,
        incluir_cnpj_prestador=incluir_cnpj_prestador,
    )

    email = EmailMessage(
        subject=assunto,
        body=corpo,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[tomador_email],
    )

    if xml_content:
        email.attach(
            xml_filename or f'nfse_{numero_nf}.xml',
            xml_content.encode('utf-8'),
            'application/xml',
        )

    email.send(fail_silently=fail_silently)
    logger.info(
        'Email NFS-e enviado para tomador_email=%s (url_danfe=%s)',
        mask_email(tomador_email),
        bool(url_danfe),
    )


def enviar_email_nfse_cancelada_tomador(
    *,
    loja: Any,
    tomador_email: str,
    tomador_nome: str,
    numero_nf: str,
    valor: Decimal | float | str,
    descricao: str,
    url_danfe: str = '',
    xml_content: str = '',
    fail_silently: bool = True,
    prestador_nome: str | None = None,
    prestador_cnpj: str | None = None,
) -> None:
    """Envia e-mail informando o cancelamento da NFS-e ao tomador."""
    enviar_email_nfse_tomador(
        loja=loja,
        tomador_email=tomador_email,
        tomador_nome=tomador_nome,
        numero_nf=numero_nf,
        valor=valor,
        descricao=descricao,
        url_danfe=url_danfe,
        xml_content=xml_content,
        fail_silently=fail_silently,
        intro='A nota fiscal de serviço foi cancelada.',
        incluir_codigo_verificacao=False,
        prestador_nome=prestador_nome,
        prestador_cnpj=prestador_cnpj,
    )
