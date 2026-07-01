"""
Workflow de aprovação e assinatura do Relatório de Comissão (CRM).
"""
import logging

from django.conf import settings
from django.utils import timezone

from core.email_delivery import create_email_message, send_prepared
from core.logging_utils import mask_email

from .relatorio_comissao_data import (
    agregar_totais_oportunidades,
    montar_dados_oportunidades_snapshot,
    queryset_oportunidades_comissao,
)
from .relatorio_comissao_pagamento import gerar_boleto_comissao

logger = logging.getLogger(__name__)


def configurar_tenant_relatorio_publico(loja_id: int):
    """Configura tenant para rotas públicas. Retorna (loja, erro)."""
    from django.conf import settings as django_settings

    from core.db_config import ensure_loja_database_config
    from superadmin.models import Loja
    from tenants.middleware import set_current_loja_id, set_current_tenant_db

    set_current_loja_id(loja_id)
    loja = Loja.objects.using('default').filter(id=loja_id).first()
    if not loja:
        return None, 'Link inválido.'

    db_name = getattr(loja, 'database_name', None) or f'loja_{loja.slug}'
    if not ensure_loja_database_config(db_name, conn_max_age=0) or db_name not in django_settings.DATABASES:
        return None, 'Serviço temporariamente indisponível.'

    set_current_tenant_db(db_name)
    return loja, None


def extrair_ip_cliente(request) -> str:
    ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', ''))
    if ',' in ip:
        ip = ip.split(',')[0].strip()
    return ip


def criar_relatorio_comissao(
    loja_id: int,
    empresa_prestadora_id: int,
    vendedor_id: int = None,
    periodo_inicio=None,
    periodo_fim=None,
    periodo_descricao: str = '',
    observacoes: str = '',
):
    """Cria um RelatorioComissao com snapshot das oportunidades."""
    from decimal import Decimal

    from .models import Conta, Vendedor
    from .models_relatorio_comissao import RelatorioComissao

    ep = Conta.objects.filter(id=empresa_prestadora_id, loja_id=loja_id).first()
    if not ep:
        return None, 'Empresa prestadora não encontrada.'

    vendedor = None
    if vendedor_id:
        vendedor = Vendedor.objects.filter(id=vendedor_id, loja_id=loja_id).first()

    qs = queryset_oportunidades_comissao(
        loja_id, empresa_prestadora_id, vendedor_id, periodo_inicio, periodo_fim
    )
    totais = agregar_totais_oportunidades(qs)
    if not totais['qtd']:
        return None, 'Nenhuma venda encontrada no período para esta empresa.'

    dados_ops = montar_dados_oportunidades_snapshot(qs, incluir_id=True)

    relatorio = RelatorioComissao.objects.create(
        loja_id=loja_id,
        titulo=f'Comissões {periodo_descricao} — {ep.nome}',
        empresa_prestadora=ep,
        vendedor=vendedor,
        periodo_inicio=periodo_inicio,
        periodo_fim=periodo_fim,
        periodo_descricao=periodo_descricao,
        valor_total_vendas=Decimal(str(totais['total_vendas'] or 0)),
        valor_total_comissao=Decimal(str(totais['total_comissao'] or 0)),
        quantidade_vendas=totais['qtd'] or 0,
        dados_oportunidades=dados_ops,
        observacoes=observacoes,
        status='pendente_aprovacao',
    )

    return relatorio, None


def enviar_relatorio_para_empresa(relatorio, loja):
    """Envia PDF do relatório por email para a empresa prestadora aprovar."""
    from .pdf_relatorio_comissao import gerar_pdf_relatorio_comissao

    ep = relatorio.empresa_prestadora
    if not ep.email:
        return False, 'Empresa prestadora não possui email cadastrado.'

    pdf_buffer = gerar_pdf_relatorio_comissao(relatorio, loja)
    pdf_bytes = pdf_buffer.read()

    frontend_url = getattr(settings, 'FRONTEND_URL', 'https://lwksistemas.com.br')
    link_aprovar = f'{frontend_url}/relatorio-comissao/{relatorio.loja_id}/{relatorio.token_empresa}/aprovar'
    link_reprovar = f'{frontend_url}/relatorio-comissao/{relatorio.loja_id}/{relatorio.token_empresa}/reprovar'

    corpo = (
        f'Olá {ep.nome},\n\n'
        f'Segue o relatório de comissão referente ao período '
        f'{relatorio.periodo_descricao}.\n\n'
        f'📋 RESUMO:\n'
        f'• Vendas: {relatorio.quantidade_vendas}\n'
        f'• Total Vendas: R$ {relatorio.valor_total_vendas:.2f}\n'
        f'• Total Comissão: R$ {relatorio.valor_total_comissao:.2f}\n\n'
        f'Para APROVAR o relatório, acesse:\n{link_aprovar}\n\n'
        f'Para REPROVAR (informar divergência), acesse:\n{link_reprovar}\n\n'
        f'Atenciosamente,\n{loja.nome}'
    )

    try:
        email = create_email_message(
            subject=f'Relatório de Comissão {relatorio.numero} — {loja.nome}',
            body=corpo,
            to=[ep.email],
        )
        filename = f'relatorio_comissao_{relatorio.numero}.pdf'
        email.attach(filename, pdf_bytes, 'application/pdf')
        send_prepared(email, fail_silently=False)
        logger.info(
            'Relatório %s enviado para empresa_prestadora_email=%s',
            relatorio.numero,
            mask_email(ep.email),
        )
        return True, None
    except Exception as e:
        logger.exception('Erro ao enviar relatório: %s', e)
        return False, str(e)


def aprovar_relatorio(relatorio, nome_aprovador: str, ip: str):
    """Empresa prestadora aprova o relatório. Envia email ao vendedor para assinar."""
    if not relatorio.pode_aprovar:
        return False, 'Relatório não pode ser aprovado neste status.'

    relatorio.status = 'aprovado'
    relatorio.empresa_aprovado_em = timezone.now()
    relatorio.empresa_aprovado_ip = ip
    relatorio.empresa_aprovado_nome = nome_aprovador
    relatorio.save(update_fields=[
        'status', 'empresa_aprovado_em', 'empresa_aprovado_ip',
        'empresa_aprovado_nome', 'updated_at',
    ])
    logger.info('Relatório %s aprovado por %s', relatorio.numero, nome_aprovador)

    enviar_email_vendedor_assinar(relatorio)

    return True, None


def enviar_email_vendedor_assinar(relatorio):
    """Envia email ao vendedor com link para assinar o relatório aprovado."""
    try:
        vendedor = relatorio.vendedor
        if not vendedor or not vendedor.email:
            logger.warning('Vendedor sem email para relatório %s', relatorio.numero)
            return

        frontend_url = getattr(settings, 'FRONTEND_URL', 'https://lwksistemas.com.br')
        link_assinar = (
            f'{frontend_url}/relatorio-comissao/{relatorio.loja_id}/'
            f'{relatorio.token_vendedor}/assinar'
        )

        corpo = (
            f'Olá {vendedor.nome},\n\n'
            f'O relatório de comissão {relatorio.numero} foi APROVADO pela empresa '
            f'{relatorio.empresa_prestadora.nome}.\n\n'
            f'📋 RESUMO:\n'
            f'• Período: {relatorio.periodo_descricao}\n'
            f'• Total Comissão: R$ {relatorio.valor_total_comissao:.2f}\n'
            f'• Aprovado por: {relatorio.empresa_aprovado_nome}\n\n'
            f'Para ASSINAR o relatório, acesse:\n{link_assinar}\n\n'
            f'Após sua assinatura, o boleto será gerado automaticamente.\n\n'
            f'Atenciosamente,\nSistema LWK'
        )

        email = create_email_message(
            subject=f'✅ Relatório {relatorio.numero} aprovado — assine para gerar boleto',
            body=corpo,
            to=[vendedor.email],
        )
        send_prepared(email, fail_silently=False)
        logger.info('Email de assinatura enviado para vendedor_email=%s', mask_email(vendedor.email))
    except Exception as e:
        logger.warning('Erro ao enviar email ao vendedor: %s', e)


def reprovar_relatorio(relatorio, motivo: str):
    """Empresa prestadora reprova o relatório."""
    if not relatorio.pode_reprovar:
        return False, 'Relatório não pode ser reprovado neste status.'

    relatorio.status = 'reprovado'
    relatorio.empresa_reprovado_em = timezone.now()
    relatorio.empresa_reprovado_motivo = motivo
    relatorio.save(update_fields=[
        'status', 'empresa_reprovado_em', 'empresa_reprovado_motivo', 'updated_at',
    ])
    logger.info('Relatório %s reprovado: %s', relatorio.numero, motivo[:100])
    return True, None


def vendedor_assinar_relatorio(relatorio, nome_vendedor: str, ip: str):
    """
    Vendedor assina o relatório após aprovação da empresa.
    Após assinatura, gera boleto automaticamente.
    """
    if not relatorio.pode_vendedor_assinar:
        return False, 'Relatório não está pronto para assinatura do vendedor.'

    relatorio.vendedor_assinado_em = timezone.now()
    relatorio.vendedor_assinado_ip = ip
    relatorio.vendedor_assinado_nome = nome_vendedor
    relatorio.status = 'aguardando_pagamento'
    relatorio.save(update_fields=[
        'vendedor_assinado_em', 'vendedor_assinado_ip',
        'vendedor_assinado_nome', 'status', 'updated_at',
    ])
    logger.info('Relatório %s assinado por vendedor %s', relatorio.numero, nome_vendedor)

    enviar_pdf_assinado(relatorio)

    ok, err = gerar_boleto_comissao(relatorio)
    if not ok:
        logger.warning('Falha ao gerar boleto para %s: %s', relatorio.numero, err)

    return True, None


def enviar_pdf_assinado(relatorio):
    """Envia PDF com assinaturas para empresa e vendedor."""
    from superadmin.models import Loja

    from .pdf_relatorio_comissao import gerar_pdf_relatorio_comissao

    try:
        loja = Loja.objects.using('default').filter(id=relatorio.loja_id).first()
        if not loja:
            return

        pdf_buffer = gerar_pdf_relatorio_comissao(relatorio, loja, incluir_assinaturas=True)
        pdf_bytes = pdf_buffer.read()

        destinatarios = []
        ep = relatorio.empresa_prestadora
        if ep.email:
            destinatarios.append(ep.email)
        if relatorio.vendedor and relatorio.vendedor.email:
            destinatarios.append(relatorio.vendedor.email)

        if not destinatarios:
            return

        email = create_email_message(
            subject=f'Relatório de Comissão {relatorio.numero} — Assinado',
            body=(
                f'O relatório de comissão {relatorio.numero} foi assinado por ambas as partes.\n'
                f'Segue em anexo o PDF com os registros de assinatura.\n\n'
                f'Atenciosamente,\n{loja.nome}'
            ),
            to=destinatarios,
        )
        email.attach(
            f'relatorio_comissao_{relatorio.numero}_assinado.pdf',
            pdf_bytes,
            'application/pdf',
        )
        send_prepared(email, fail_silently=True)
        logger.info('PDF assinado enviado para %s', destinatarios)
    except Exception as e:
        logger.warning('Erro ao enviar PDF assinado: %s', e)
