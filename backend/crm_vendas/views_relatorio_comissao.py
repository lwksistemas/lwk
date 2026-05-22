"""
Views para o workflow de Relatório de Comissão.
Endpoints autenticados (admin) e públicos (empresa/vendedor via token).
"""
import logging
from datetime import date as date_type

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from tenants.middleware import get_current_loja_id

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS AUTENTICADOS (admin da loja)
# ═══════════════════════════════════════════════════════════════════════════════

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def criar_relatorio_comissao_view(request):
    """
    POST /crm-vendas/relatorios-comissao/criar/
    Cria relatório e envia para empresa aprovar.
    """
    from .services_relatorio_comissao import (
        criar_relatorio_comissao, enviar_relatorio_para_empresa,
    )
    from .relatorios import calcular_periodo
    from superadmin.models import Loja

    loja_id = get_current_loja_id()
    if not loja_id:
        return Response({'detail': 'Loja não identificada.'}, status=400)

    data = request.data
    empresa_prestadora_id = data.get('empresa_prestadora_id')
    vendedor_id = data.get('vendedor_id')
    periodo = data.get('periodo', 'mes_atual')
    data_inicio_str = data.get('data_inicio')
    data_fim_str = data.get('data_fim')
    observacoes = data.get('observacoes', '')

    if not empresa_prestadora_id:
        return Response({'detail': 'empresa_prestadora_id é obrigatório.'}, status=400)

    # Calcular período
    if data_inicio_str and data_fim_str:
        try:
            periodo_inicio = date_type.fromisoformat(data_inicio_str)
            periodo_fim = date_type.fromisoformat(data_fim_str)
        except ValueError:
            return Response({'detail': 'Datas inválidas.'}, status=400)
        periodo_descricao = f'{periodo_inicio.strftime("%d/%m/%Y")} a {periodo_fim.strftime("%d/%m/%Y")}'
    else:
        periodo_inicio, periodo_fim = calcular_periodo(periodo)
        periodo_descricao = periodo.replace('_', ' ').title()

    relatorio, erro = criar_relatorio_comissao(
        loja_id=loja_id,
        empresa_prestadora_id=int(empresa_prestadora_id),
        vendedor_id=int(vendedor_id) if vendedor_id else None,
        periodo_inicio=periodo_inicio,
        periodo_fim=periodo_fim,
        periodo_descricao=periodo_descricao,
        observacoes=observacoes,
    )

    if not relatorio:
        return Response({'detail': erro}, status=400)

    # Enviar para empresa aprovar
    loja = Loja.objects.using('default').filter(id=loja_id).first()
    ok, err = enviar_relatorio_para_empresa(relatorio, loja)

    return Response({
        'success': True,
        'id': relatorio.id,
        'numero': relatorio.numero,
        'status': relatorio.status,
        'enviado_email': ok,
        'erro_email': err,
        'message': f'Relatório {relatorio.numero} criado e enviado para aprovação.',
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def preview_relatorio_comissao_view(request):
    """
    POST /crm-vendas/relatorios-comissao/preview/
    Gera PDF de preview sem salvar. Retorna blob PDF para visualização.
    """
    from .models import Oportunidade, Vendedor, Conta
    from .relatorios import calcular_periodo, _filtro_datas_fechamento_ganho
    from .pdf_relatorio_comissao import gerar_pdf_relatorio_comissao
    from .models_relatorio_comissao import RelatorioComissao
    from superadmin.models import Loja
    from django.db.models import Sum, Count, Q
    from decimal import Decimal

    loja_id = get_current_loja_id()
    if not loja_id:
        return Response({'detail': 'Loja não identificada.'}, status=400)

    data = request.data
    empresa_prestadora_id = data.get('empresa_prestadora_id')
    vendedor_id = data.get('vendedor_id')
    periodo = data.get('periodo', 'mes_atual')
    data_inicio_str = data.get('data_inicio')
    data_fim_str = data.get('data_fim')

    if not empresa_prestadora_id:
        return Response({'detail': 'empresa_prestadora_id é obrigatório.'}, status=400)

    ep = Conta.objects.filter(id=int(empresa_prestadora_id), loja_id=loja_id).first()
    if not ep:
        return Response({'detail': 'Empresa prestadora não encontrada.'}, status=400)

    if data_inicio_str and data_fim_str:
        try:
            periodo_inicio = date_type.fromisoformat(data_inicio_str)
            periodo_fim = date_type.fromisoformat(data_fim_str)
        except ValueError:
            return Response({'detail': 'Datas inválidas.'}, status=400)
        periodo_descricao = f'{periodo_inicio.strftime("%d/%m/%Y")} a {periodo_fim.strftime("%d/%m/%Y")}'
    else:
        periodo_inicio, periodo_fim = calcular_periodo(periodo)
        periodo_descricao = periodo.replace('_', ' ').title()

    # Inclui vendas sem empresa prestadora definida
    filtro_ep = Q(empresa_prestadora_id=int(empresa_prestadora_id)) | Q(empresa_prestadora_id__isnull=True)

    qs = Oportunidade.objects.filter(
        loja_id=loja_id, etapa='closed_won',
    ).filter(filtro_ep).filter(_filtro_datas_fechamento_ganho(periodo_inicio, periodo_fim)).select_related('lead', 'lead__conta', 'vendedor')

    if vendedor_id:
        # Incluir vendas de vendedores inativos mescladas neste vendedor (mesmo critério do dashboard)
        from .utils import get_vendedor_destino_merge_loja
        destino = get_vendedor_destino_merge_loja(loja_id)
        vid = int(vendedor_id)
        if destino and destino.id == vid:
            qs = qs.filter(
                Q(vendedor_id=vid)
                | Q(vendedor_id__isnull=True)
                | Q(vendedor__is_active=False)
            )
        else:
            qs = qs.filter(vendedor_id=vid)

    totais = qs.aggregate(total_vendas=Sum('valor'), total_comissao=Sum('valor_comissao'), qtd=Count('id'))
    if not totais['qtd']:
        return Response({'detail': 'Nenhuma venda encontrada no período para esta empresa.'}, status=400)

    dados_ops = []
    for op in qs.order_by('-data_fechamento_ganho', '-data_fechamento'):
        dt = op.data_fechamento_ganho or op.data_fechamento
        cliente = ''
        if op.lead:
            cliente = op.lead.conta.nome if op.lead.conta_id else op.lead.nome
        dados_ops.append({
            'data': dt.strftime('%d/%m/%Y') if dt else '—',
            'cliente': cliente or op.titulo,
            'valor': float(op.valor or 0),
            'comissao': float(op.valor_comissao or 0),
        })

    vendedor = Vendedor.objects.filter(id=int(vendedor_id), loja_id=loja_id).first() if vendedor_id else None

    fake_relatorio = RelatorioComissao(
        loja_id=loja_id, numero='PREVIEW',
        titulo=f'Comissões {periodo_descricao} — {ep.nome}',
        empresa_prestadora=ep, vendedor=vendedor,
        periodo_inicio=periodo_inicio, periodo_fim=periodo_fim,
        periodo_descricao=periodo_descricao,
        valor_total_vendas=Decimal(str(totais['total_vendas'] or 0)),
        valor_total_comissao=Decimal(str(totais['total_comissao'] or 0)),
        quantidade_vendas=totais['qtd'] or 0,
        dados_oportunidades=dados_ops,
    )

    loja = Loja.objects.using('default').filter(id=loja_id).first()
    pdf_buffer = gerar_pdf_relatorio_comissao(fake_relatorio, loja)

    response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="preview_relatorio_comissao.pdf"'
    return response


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def enviar_relatorio_comissao_view(request, relatorio_id):
    """
    POST /crm-vendas/relatorios-comissao/<id>/enviar/
    Envia relatório já criado para a empresa prestadora aprovar.
    """
    from .models_relatorio_comissao import RelatorioComissao
    from .services_relatorio_comissao import enviar_relatorio_para_empresa
    from superadmin.models import Loja

    loja_id = get_current_loja_id()
    if not loja_id:
        return Response({'detail': 'Loja não identificada.'}, status=400)

    try:
        r = RelatorioComissao.objects.get(id=relatorio_id, loja_id=loja_id)
    except RelatorioComissao.DoesNotExist:
        return Response({'detail': 'Relatório não encontrado.'}, status=404)

    if r.status != 'pendente_aprovacao':
        return Response({'detail': 'Relatório já foi enviado ou processado.'}, status=400)

    loja = Loja.objects.using('default').filter(id=loja_id).first()
    ok, err = enviar_relatorio_para_empresa(r, loja)
    if not ok:
        return Response({'detail': err or 'Erro ao enviar email.'}, status=400)

    return Response({'success': True, 'message': f'Relatório {r.numero} enviado para {r.empresa_prestadora.email}.'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def listar_relatorios_comissao_view(request):
    """
    GET /crm-vendas/relatorios-comissao/
    Lista relatórios de comissão da loja.
    """
    from .models_relatorio_comissao import RelatorioComissao

    loja_id = get_current_loja_id()
    if not loja_id:
        return Response({'detail': 'Loja não identificada.'}, status=400)

    qs = RelatorioComissao.objects.filter(loja_id=loja_id).select_related(
        'empresa_prestadora', 'vendedor'
    )[:50]

    data = []
    try:
        for r in qs:
            data.append({
                'id': r.id,
                'numero': r.numero,
                'titulo': r.titulo,
                'status': r.status,
                'status_display': r.get_status_display(),
                'empresa_prestadora_nome': r.empresa_prestadora.nome if r.empresa_prestadora else '',
                'vendedor_nome': r.vendedor.nome if r.vendedor else '',
                'periodo_descricao': r.periodo_descricao,
                'valor_total_vendas': str(r.valor_total_vendas),
                'valor_total_comissao': str(r.valor_total_comissao),
                'quantidade_vendas': r.quantidade_vendas,
                'boleto_url': r.boleto_url,
                'nfse_numero': r.nfse_numero,
                'created_at': r.created_at.isoformat() if r.created_at else None,
            })
        return Response({'relatorios': data})
    except Exception:
        # Tabela não existe — criar e retornar lista vazia
        from .models_relatorio_comissao import RelatorioComissao as RC
        from tenants.middleware import get_current_tenant_db
        RC._criar_tabela_se_necessario(using=get_current_tenant_db() or 'default')
        return Response({'relatorios': []})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_pdf_relatorio_comissao_view(request, relatorio_id):
    """
    GET /crm-vendas/relatorios-comissao/<id>/pdf/
    Baixa PDF do relatório.
    """
    from .models_relatorio_comissao import RelatorioComissao
    from .pdf_relatorio_comissao import gerar_pdf_relatorio_comissao
    from superadmin.models import Loja

    loja_id = get_current_loja_id()
    if not loja_id:
        return Response({'detail': 'Loja não identificada.'}, status=400)

    try:
        r = RelatorioComissao.objects.get(id=relatorio_id, loja_id=loja_id)
    except RelatorioComissao.DoesNotExist:
        return Response({'detail': 'Relatório não encontrado.'}, status=404)

    loja = Loja.objects.using('default').filter(id=loja_id).first()
    incluir_assin = r.status not in ('pendente_aprovacao', 'reprovado')
    pdf_buffer = gerar_pdf_relatorio_comissao(r, loja, incluir_assinaturas=incluir_assin)

    response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="relatorio_{r.numero}.pdf"'
    return response


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def excluir_relatorio_comissao_view(request, relatorio_id):
    """
    DELETE /crm-vendas/relatorios-comissao/<id>/excluir/
    Exclui relatório (apenas pendentes ou reprovados).
    """
    from .models_relatorio_comissao import RelatorioComissao

    loja_id = get_current_loja_id()
    if not loja_id:
        return Response({'detail': 'Loja não identificada.'}, status=400)

    try:
        r = RelatorioComissao.objects.get(id=relatorio_id, loja_id=loja_id)
    except RelatorioComissao.DoesNotExist:
        return Response({'detail': 'Relatório não encontrado.'}, status=404)

    if r.status in ('concluido', 'nfse_emitida'):
        return Response({'detail': 'Não é possível excluir relatórios com NFS-e emitida ou concluídos.'}, status=400)

    # Cancelar boleto no Asaas se existir
    if r.asaas_payment_id:
        try:
            from .models_config import CRMConfig
            from asaas_integration.client import AsaasClient
            config = CRMConfig.get_or_create_for_loja(r.loja_id)
            if config.asaas_api_key:
                client = AsaasClient(api_key=config.asaas_api_key, sandbox=config.asaas_sandbox)
                client.delete_payment(r.asaas_payment_id)
                logger.info('Boleto %s cancelado no Asaas', r.asaas_payment_id)
        except Exception as e:
            logger.warning('Erro ao cancelar boleto %s no Asaas: %s', r.asaas_payment_id, e)

    numero = r.numero
    r.delete()
    return Response({'success': True, 'message': f'Relatório {numero} excluído.'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirmar_pagamento_manual_view(request, relatorio_id):
    """
    POST /crm-vendas/relatorios-comissao/<id>/confirmar-pagamento/
    Confirma pagamento manualmente e dispara emissão de NFS-e.
    Usar quando o webhook Asaas não está configurado.
    """
    from .models_relatorio_comissao import RelatorioComissao
    from .services_relatorio_comissao import processar_pagamento_comissao

    loja_id = get_current_loja_id()
    if not loja_id:
        return Response({'detail': 'Loja não identificada.'}, status=400)

    try:
        r = RelatorioComissao.objects.get(id=relatorio_id, loja_id=loja_id)
    except RelatorioComissao.DoesNotExist:
        return Response({'detail': 'Relatório não encontrado.'}, status=404)

    if r.status != 'aguardando_pagamento':
        return Response({'detail': f'Status atual: {r.get_status_display()}. Só é possível confirmar pagamento quando está aguardando.'}, status=400)

    processar_pagamento_comissao(r)

    return Response({
        'success': True,
        'message': f'Pagamento confirmado! NFS-e {"emitida" if r.nfse_numero else "em processamento"}.',
        'status': r.status,
        'nfse_numero': r.nfse_numero,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reemitir_nfse_view(request, relatorio_id):
    """
    POST /crm-vendas/relatorios-comissao/<id>/reemitir-nfse/
    Tenta emitir NFS-e para relatório já pago (retry manual).
    """
    from .models_relatorio_comissao import RelatorioComissao
    from .services_relatorio_comissao import processar_pagamento_comissao

    loja_id = get_current_loja_id()
    if not loja_id:
        return Response({'detail': 'Loja não identificada.'}, status=400)

    try:
        r = RelatorioComissao.objects.get(id=relatorio_id, loja_id=loja_id)
    except RelatorioComissao.DoesNotExist:
        return Response({'detail': 'Relatório não encontrado.'}, status=404)

    if r.status not in ('pago', 'aguardando_pagamento'):
        return Response({'detail': f'Status atual: {r.get_status_display()}. Emissão só para relatórios pagos.'}, status=400)

    # Forçar status pago e tentar emitir
    if r.status == 'aguardando_pagamento':
        from django.utils import timezone as tz
        r.status = 'pago'
        r.pago_em = tz.now()
        r.save(update_fields=['status', 'pago_em', 'updated_at'])

    processar_pagamento_comissao(r)

    # Recarregar para pegar status atualizado
    r.refresh_from_db()
    return Response({
        'success': True,
        'message': f'NFS-e {"emitida: " + r.nfse_numero if r.nfse_numero else "falhou — verifique configuração ISSNet."}',
        'status': r.status,
        'nfse_numero': r.nfse_numero,
    })


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS PÚBLICOS (empresa/vendedor via token UUID)
# ═══════════════════════════════════════════════════════════════════════════════

def _buscar_relatorio_por_token(campo_token: str, token_value):
    """Busca RelatorioComissao configurando o tenant correto pela loja_id na URL."""
    pass  # Não mais necessário — loja_id vem na URL


def _configurar_tenant_relatorio(loja_id):
    """Configura tenant para rotas públicas de relatório de comissão."""
    from superadmin.models import Loja
    from core.db_config import ensure_loja_database_config
    from tenants.middleware import set_current_loja_id, set_current_tenant_db
    from django.conf import settings

    set_current_loja_id(loja_id)
    loja = Loja.objects.using('default').filter(id=loja_id).first()
    if not loja:
        return None, 'Link inválido.'

    db_name = getattr(loja, 'database_name', None) or f'loja_{loja.slug}'
    if not ensure_loja_database_config(db_name, conn_max_age=0) or db_name not in settings.DATABASES:
        return None, 'Serviço temporariamente indisponível.'

    set_current_tenant_db(db_name)
    return loja, None


@csrf_exempt
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def empresa_aprovar_view(request, loja_id, token):
    """
    GET  → mostra dados do relatório para aprovação
    POST → registra aprovação (body: {nome})
    """
    from .models_relatorio_comissao import RelatorioComissao
    from .services_relatorio_comissao import aprovar_relatorio

    loja, err = _configurar_tenant_relatorio(int(loja_id))
    if err:
        return Response({'detail': err}, status=404)

    r = RelatorioComissao.objects.select_related(
        'empresa_prestadora', 'vendedor'
    ).filter(token_empresa=token).first()
    if not r:
        return Response({'detail': 'Link inválido ou expirado.'}, status=404)

    if request.method == 'GET':
        return Response({
            'numero': r.numero,
            'titulo': r.titulo,
            'status': r.status,
            'empresa': r.empresa_prestadora.nome,
            'periodo': r.periodo_descricao,
            'valor_total_vendas': str(r.valor_total_vendas),
            'valor_total_comissao': str(r.valor_total_comissao),
            'quantidade_vendas': r.quantidade_vendas,
            'pode_aprovar': r.pode_aprovar,
        })

    # POST — aprovar
    nome = request.data.get('nome', r.empresa_prestadora.nome)
    ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', ''))
    if ',' in ip:
        ip = ip.split(',')[0].strip()

    ok, err = aprovar_relatorio(r, nome, ip)
    if not ok:
        return Response({'detail': err}, status=400)

    return Response({'success': True, 'message': 'Relatório aprovado com sucesso!'})


@csrf_exempt
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def empresa_reprovar_view(request, loja_id, token):
    """
    GET  → mostra dados do relatório
    POST → registra reprovação (body: {motivo})
    """
    from .models_relatorio_comissao import RelatorioComissao
    from .services_relatorio_comissao import reprovar_relatorio

    loja, err = _configurar_tenant_relatorio(int(loja_id))
    if err:
        return Response({'detail': err}, status=404)

    r = RelatorioComissao.objects.select_related(
        'empresa_prestadora',
    ).filter(token_empresa=token).first()
    if not r:
        return Response({'detail': 'Link inválido ou expirado.'}, status=404)

    if request.method == 'GET':
        return Response({
            'numero': r.numero,
            'titulo': r.titulo,
            'status': r.status,
            'empresa': r.empresa_prestadora.nome,
            'periodo': r.periodo_descricao,
            'valor_total_comissao': str(r.valor_total_comissao),
            'pode_reprovar': r.pode_reprovar,
        })

    motivo = request.data.get('motivo', '')
    if not motivo:
        return Response({'detail': 'Informe o motivo da reprovação.'}, status=400)

    ok, err = reprovar_relatorio(r, motivo)
    if not ok:
        return Response({'detail': err}, status=400)

    return Response({'success': True, 'message': 'Relatório reprovado. O prestador será notificado.'})


@csrf_exempt
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def vendedor_assinar_view(request, loja_id, token):
    """
    GET  → mostra dados do relatório para assinatura
    POST → registra assinatura do vendedor (body: {nome})
    """
    from .models_relatorio_comissao import RelatorioComissao
    from .services_relatorio_comissao import vendedor_assinar_relatorio

    loja, err = _configurar_tenant_relatorio(int(loja_id))
    if err:
        return Response({'detail': err}, status=404)

    r = RelatorioComissao.objects.select_related(
        'empresa_prestadora', 'vendedor',
    ).filter(token_vendedor=token).first()
    if not r:
        return Response({'detail': 'Link inválido ou expirado.'}, status=404)

    if request.method == 'GET':
        return Response({
            'numero': r.numero,
            'titulo': r.titulo,
            'status': r.status,
            'empresa': r.empresa_prestadora.nome,
            'vendedor': r.vendedor.nome if r.vendedor else '',
            'periodo': r.periodo_descricao,
            'valor_total_comissao': str(r.valor_total_comissao),
            'pode_assinar': r.pode_vendedor_assinar,
            'empresa_aprovado_em': r.empresa_aprovado_em.isoformat() if r.empresa_aprovado_em else None,
        })

    nome = request.data.get('nome', '')
    if not nome:
        # Tentar obter nome do vendedor vinculado ao relatório
        if r.vendedor:
            nome = r.vendedor.nome
        else:
            # Fallback: buscar Vendedor do owner da loja
            try:
                from superadmin.models import VendedorUsuario
                from .models import Vendedor
                vu = VendedorUsuario.objects.using('default').filter(loja=loja).first()
                if vu:
                    vend = Vendedor.objects.filter(id=vu.vendedor_id, loja_id=loja.id).first()
                    if vend:
                        nome = vend.nome
            except Exception:
                pass
        if not nome:
            nome = loja.nome
    ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', ''))
    if ',' in ip:
        ip = ip.split(',')[0].strip()

    ok, err = vendedor_assinar_relatorio(r, nome, ip)
    if not ok:
        return Response({'detail': err}, status=400)

    return Response({
        'success': True,
        'message': 'Relatório assinado! Boleto gerado para pagamento.',
        'boleto_url': r.boleto_url,
    })
