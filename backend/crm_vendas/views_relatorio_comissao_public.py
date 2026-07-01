"""Endpoints públicos (empresa/vendedor via token) — relatório de comissão."""
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@csrf_exempt
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def empresa_aprovar_view(request, loja_id, token):
    from .models_relatorio_comissao import RelatorioComissao
    from .services_relatorio_comissao import (
        aprovar_relatorio,
        configurar_tenant_relatorio_publico,
        extrair_ip_cliente,
    )

    loja, err = configurar_tenant_relatorio_publico(int(loja_id))
    if err:
        return Response({'detail': err}, status=404)

    relatorio = RelatorioComissao.objects.select_related(
        'empresa_prestadora', 'vendedor'
    ).filter(token_empresa=token).first()
    if not relatorio:
        return Response({'detail': 'Link inválido ou expirado.'}, status=404)

    if request.method == 'GET':
        return Response({
            'numero': relatorio.numero,
            'titulo': relatorio.titulo,
            'status': relatorio.status,
            'empresa': relatorio.empresa_prestadora.nome,
            'periodo': relatorio.periodo_descricao,
            'valor_total_vendas': str(relatorio.valor_total_vendas),
            'valor_total_comissao': str(relatorio.valor_total_comissao),
            'quantidade_vendas': relatorio.quantidade_vendas,
            'pode_aprovar': relatorio.pode_aprovar,
        })

    nome = request.data.get('nome', relatorio.empresa_prestadora.nome)
    ok, err_msg = aprovar_relatorio(relatorio, nome, extrair_ip_cliente(request))
    if not ok:
        return Response({'detail': err_msg}, status=400)

    return Response({'success': True, 'message': 'Relatório aprovado com sucesso!'})


@csrf_exempt
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def empresa_reprovar_view(request, loja_id, token):
    from .models_relatorio_comissao import RelatorioComissao
    from .services_relatorio_comissao import (
        configurar_tenant_relatorio_publico,
        reprovar_relatorio,
    )

    loja, err = configurar_tenant_relatorio_publico(int(loja_id))
    if err:
        return Response({'detail': err}, status=404)

    relatorio = RelatorioComissao.objects.select_related('empresa_prestadora').filter(
        token_empresa=token
    ).first()
    if not relatorio:
        return Response({'detail': 'Link inválido ou expirado.'}, status=404)

    if request.method == 'GET':
        return Response({
            'numero': relatorio.numero,
            'titulo': relatorio.titulo,
            'status': relatorio.status,
            'empresa': relatorio.empresa_prestadora.nome,
            'periodo': relatorio.periodo_descricao,
            'valor_total_comissao': str(relatorio.valor_total_comissao),
            'pode_reprovar': relatorio.pode_reprovar,
        })

    motivo = request.data.get('motivo', '')
    if not motivo:
        return Response({'detail': 'Informe o motivo da reprovação.'}, status=400)

    ok, err_msg = reprovar_relatorio(relatorio, motivo)
    if not ok:
        return Response({'detail': err_msg}, status=400)

    return Response({'success': True, 'message': 'Relatório reprovado. O prestador será notificado.'})


@csrf_exempt
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def vendedor_assinar_view(request, loja_id, token):
    from .models_relatorio_comissao import RelatorioComissao
    from .services_relatorio_comissao import (
        configurar_tenant_relatorio_publico,
        extrair_ip_cliente,
        vendedor_assinar_relatorio,
    )

    loja, err = configurar_tenant_relatorio_publico(int(loja_id))
    if err:
        return Response({'detail': err}, status=404)

    relatorio = RelatorioComissao.objects.select_related(
        'empresa_prestadora', 'vendedor'
    ).filter(token_vendedor=token).first()
    if not relatorio:
        return Response({'detail': 'Link inválido ou expirado.'}, status=404)

    if request.method == 'GET':
        return Response({
            'numero': relatorio.numero,
            'titulo': relatorio.titulo,
            'status': relatorio.status,
            'empresa': relatorio.empresa_prestadora.nome,
            'vendedor': relatorio.vendedor.nome if relatorio.vendedor else '',
            'periodo': relatorio.periodo_descricao,
            'valor_total_comissao': str(relatorio.valor_total_comissao),
            'pode_assinar': relatorio.pode_vendedor_assinar,
            'empresa_aprovado_em': (
                relatorio.empresa_aprovado_em.isoformat() if relatorio.empresa_aprovado_em else None
            ),
        })

    nome = request.data.get('nome', '')
    if not nome:
        if relatorio.vendedor:
            nome = relatorio.vendedor.nome
        else:
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

    ok, err_msg = vendedor_assinar_relatorio(relatorio, nome, extrair_ip_cliente(request))
    if not ok:
        return Response({'detail': err_msg}, status=400)

    return Response({
        'success': True,
        'message': 'Relatório assinado! Boleto gerado para pagamento.',
        'boleto_url': relatorio.boleto_url,
    })
