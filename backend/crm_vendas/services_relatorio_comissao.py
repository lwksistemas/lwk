"""
Serviço de Relatório de Comissão — lógica de negócio do workflow.
"""
import logging
from datetime import timedelta
from decimal import Decimal

from django.utils import timezone
from django.db.models import Sum, Count, Q
from django.core.mail import EmailMessage
from django.conf import settings
from core.logging_utils import mask_email

logger = logging.getLogger(__name__)


def _fmt_cpf_cnpj(valor: str) -> str:
    """Formata CPF (000.000.000-00) ou CNPJ (00.000.000/0001-00) a partir de string com ou sem máscara."""
    digits = ''.join(c for c in (valor or '') if c.isdigit())
    if len(digits) == 11:
        return f'{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}'
    if len(digits) == 14:
        return f'{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}'
    return valor  # retorna original se não reconhecer


def criar_relatorio_comissao(
    loja_id: int,
    empresa_prestadora_id: int,
    vendedor_id: int = None,
    periodo_inicio=None,
    periodo_fim=None,
    periodo_descricao: str = '',
    observacoes: str = '',
):
    """
    Cria um RelatorioComissao com snapshot das oportunidades.
    """
    from .models import Oportunidade, Vendedor, Conta
    from .models_relatorio_comissao import RelatorioComissao
    from .relatorios import _filtro_datas_fechamento_ganho

    ep = Conta.objects.filter(id=empresa_prestadora_id, loja_id=loja_id).first()
    if not ep:
        return None, 'Empresa prestadora não encontrada.'

    vendedor = None
    if vendedor_id:
        vendedor = Vendedor.objects.filter(id=vendedor_id, loja_id=loja_id).first()

    # Buscar oportunidades fechadas no período (apenas com empresa prestadora definida)
    qs = Oportunidade.objects.filter(
        loja_id=loja_id,
        etapa='closed_won',
        empresa_prestadora_id=empresa_prestadora_id,
    ).filter(
        _filtro_datas_fechamento_ganho(periodo_inicio, periodo_fim)
    ).select_related('lead', 'lead__conta', 'vendedor')

    if vendedor_id:
        # Incluir vendas de vendedores inativos que seriam mescladas neste vendedor
        from .utils import get_vendedor_destino_merge_loja
        destino = get_vendedor_destino_merge_loja(loja_id)
        if destino and destino.id == vendedor_id:
            # Este vendedor é o destino de merge: incluir vendas sem vendedor ou com vendedor inativo
            qs = qs.filter(
                Q(vendedor_id=vendedor_id)
                | Q(vendedor_id__isnull=True)
                | Q(vendedor__is_active=False)
            )
        else:
            qs = qs.filter(vendedor_id=vendedor_id)

    # Calcular totais
    totais = qs.aggregate(
        total_vendas=Sum('valor'),
        total_comissao=Sum('valor_comissao'),
        qtd=Count('id'),
    )

    if not totais['qtd']:
        return None, 'Nenhuma venda encontrada no período para esta empresa.'

    # Snapshot das oportunidades para o PDF
    dados_ops = []
    for op in qs.order_by('-data_fechamento_ganho', '-data_fechamento'):
        data = op.data_fechamento_ganho or op.data_fechamento
        cliente = ''
        cpf_cnpj = ''
        if op.lead:
            if op.lead.conta_id:
                cliente = op.lead.conta.nome
                cpf_cnpj = op.lead.conta.cnpj or ''
            else:
                cliente = op.lead.nome
                cpf_cnpj = op.lead.cpf_cnpj or ''
        dados_ops.append({
            'id': op.id,
            'data': data.strftime('%d/%m/%Y') if data else '—',
            'cliente': f"{_fmt_cpf_cnpj(cpf_cnpj)} {cliente}".strip() if cpf_cnpj else (cliente or op.titulo),
            'valor': float(op.valor or 0),
            'comissao': float(op.valor_comissao or 0),
            'titulo': op.titulo,
        })

    # Criar relatório
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
    """
    Envia PDF do relatório por email para a empresa prestadora aprovar.
    Inclui link de aprovação/reprovação.
    """
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
        email = EmailMessage(
            subject=f'Relatório de Comissão {relatorio.numero} — {loja.nome}',
            body=corpo,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[ep.email],
        )
        filename = f'relatorio_comissao_{relatorio.numero}.pdf'
        email.attach(filename, pdf_bytes, 'application/pdf')
        email.send(fail_silently=False)
        logger.info('Relatório %s enviado para empresa_prestadora_email=%s', relatorio.numero, mask_email(ep.email))
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

    # Enviar email ao vendedor para assinar
    _enviar_email_vendedor_assinar(relatorio)

    return True, None


def _enviar_email_vendedor_assinar(relatorio):
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

        email = EmailMessage(
            subject=f'✅ Relatório {relatorio.numero} aprovado — assine para gerar boleto',
            body=corpo,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[vendedor.email],
        )
        email.send(fail_silently=False)
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

    # Enviar PDF com assinaturas para ambos
    _enviar_pdf_assinado(relatorio)

    # Gerar boleto automaticamente
    ok, err = gerar_boleto_comissao(relatorio)
    if not ok:
        logger.warning('Falha ao gerar boleto para %s: %s', relatorio.numero, err)

    return True, None


def _enviar_pdf_assinado(relatorio):
    """Envia PDF com assinaturas para empresa e vendedor."""
    from .pdf_relatorio_comissao import gerar_pdf_relatorio_comissao
    from superadmin.models import Loja

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

        email = EmailMessage(
            subject=f'Relatório de Comissão {relatorio.numero} — Assinado',
            body=(
                f'O relatório de comissão {relatorio.numero} foi assinado por ambas as partes.\n'
                f'Segue em anexo o PDF com os registros de assinatura.\n\n'
                f'Atenciosamente,\n{loja.nome}'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=destinatarios,
        )
        email.attach(
            f'relatorio_comissao_{relatorio.numero}_assinado.pdf',
            pdf_bytes,
            'application/pdf',
        )
        email.send(fail_silently=True)
        logger.info('PDF assinado enviado para %s', destinatarios)
    except Exception as e:
        logger.warning('Erro ao enviar PDF assinado: %s', e)


def gerar_boleto_comissao(relatorio):
    """
    Gera boleto no Asaas para pagamento da comissão.
    Usa a API Key da loja (CRMConfig.asaas_api_key).
    """
    from .models_config import CRMConfig
    from asaas_integration.client import AsaasClient

    try:
        config = CRMConfig.get_or_create_for_loja(relatorio.loja_id)
        api_key = config.asaas_api_key
        if not api_key:
            return False, 'API Key Asaas não configurada na loja.'

        client = AsaasClient(api_key=api_key, sandbox=config.asaas_sandbox)
        ep = relatorio.empresa_prestadora

        # Criar ou buscar customer
        import re
        cnpj_digits = re.sub(r'\D', '', ep.cnpj or '')
        if not cnpj_digits:
            return False, 'Empresa prestadora não possui CNPJ cadastrado.'

        customer_data = {
            'name': ep.nome,
            'cpfCnpj': cnpj_digits,
            'email': ep.email or '',
        }
        customer = client.create_customer(customer_data)
        customer_id = customer.get('id')
        if not customer_id:
            return False, 'Falha ao criar cliente no Asaas.'

        # Criar cobrança (boleto)
        vencimento = (timezone.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        payment_data = {
            'customer': customer_id,
            'billingType': 'BOLETO',
            'value': float(relatorio.valor_total_comissao),
            'dueDate': vencimento,
            'description': f'Comissão {relatorio.numero} — {relatorio.periodo_descricao}',
            'externalReference': f'rc_{relatorio.id}',
        }
        payment = client.create_payment(payment_data)
        payment_id = payment.get('id')
        if not payment_id:
            return False, 'Falha ao criar cobrança no Asaas.'

        relatorio.asaas_payment_id = payment_id
        relatorio.asaas_customer_id = customer_id
        relatorio.boleto_url = payment.get('bankSlipUrl', '') or payment.get('invoiceUrl', '')
        relatorio.boleto_vencimento = timezone.now().date() + timedelta(days=7)
        relatorio.save(update_fields=[
            'asaas_payment_id', 'asaas_customer_id',
            'boleto_url', 'boleto_vencimento', 'updated_at',
        ])

        logger.info(
            'Boleto gerado para relatório %s: payment_id=%s',
            relatorio.numero, payment_id,
        )
        return True, None

    except Exception as e:
        logger.exception('Erro ao gerar boleto: %s', e)
        return False, str(e)


def processar_pagamento_comissao(relatorio):
    """
    Chamado quando o pagamento do boleto é confirmado (via webhook Asaas).
    Emite NFS-e automaticamente.
    """
    from nfse_integration.service import NFSeService
    from superadmin.models import Loja

    relatorio.status = 'pago'
    relatorio.pago_em = timezone.now()
    relatorio.save(update_fields=['status', 'pago_em', 'updated_at'])
    logger.info('Relatório %s marcado como pago.', relatorio.numero)

    # Emitir NFS-e automaticamente
    try:
        loja = Loja.objects.using('default').filter(id=relatorio.loja_id).first()
        if not loja:
            logger.warning('Loja não encontrada para emissão de NFS-e: loja_id=%s', relatorio.loja_id)
            return

        # Configurar tenant para que NFSeService acesse CRMConfig corretamente
        from tenants.middleware import set_current_loja_id, set_current_tenant_db
        from core.db_config import ensure_loja_database_config
        set_current_loja_id(loja.id)
        db_name = getattr(loja, 'database_name', None) or f'loja_{loja.slug}'
        ensure_loja_database_config(db_name, conn_max_age=0)
        set_current_tenant_db(db_name)

        ep = relatorio.empresa_prestadora
        import re
        cnpj_digits = re.sub(r'\D', '', ep.cnpj or '')

        service = NFSeService(loja)
        resultado = service.emitir_nfse(
            tomador_cpf_cnpj=cnpj_digits,
            tomador_nome=ep.nome,
            tomador_email=ep.email or '',
            tomador_endereco={
                'logradouro': ep.logradouro or '',
                'numero': ep.numero or 'S/N',
                'complemento': ep.complemento or '',
                'bairro': ep.bairro or '',
                'cidade': ep.cidade or '',
                'uf': ep.uf or '',
                'cep': ep.cep or '',
            },
            servico_descricao=(
                f'Comissão de vendas ref. {relatorio.periodo_descricao} '
                f'— Relatório {relatorio.numero}'
            ),
            valor_servicos=relatorio.valor_total_comissao,
            enviar_email=True,
        )

        if resultado.get('success'):
            relatorio.status = 'nfse_emitida'
            relatorio.nfse_numero = resultado.get('numero_nf', '')
            relatorio.nfse_emitida_em = timezone.now()
            relatorio.save(update_fields=[
                'status', 'nfse_numero', 'nfse_emitida_em', 'updated_at',
            ])
            logger.info(
                'NFS-e emitida para relatório %s: %s',
                relatorio.numero, relatorio.nfse_numero,
            )
        else:
            logger.warning(
                'Falha ao emitir NFS-e para relatório %s: %s',
                relatorio.numero, resultado.get('error'),
            )
    except Exception as e:
        logger.exception('Erro ao emitir NFS-e para relatório %s: %s', relatorio.numero, e)
