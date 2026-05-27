"""
Views para listagem e emissão manual de NFS-e pelo superadmin.
GET  /api/superadmin/nfse-emitidas/
POST /api/superadmin/nfse-emitidas/emitir-manual/
"""
import logging

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.audit import audit_log
from core.rate_limit import rate_limit
from .models import NFSeEmitida, Loja

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def listar_nfse_emitidas(request):
    """Lista todas as NFS-e emitidas pela LWK para as lojas."""
    if not request.user.is_superuser:
        return Response({'detail': 'Apenas superadmin.'}, status=403)

    # Filtros
    status_filtro = request.query_params.get('status', '')
    loja_id = request.query_params.get('loja_id', '')
    provedor = request.query_params.get('provedor', '')

    qs = NFSeEmitida.objects.select_related('loja', 'pagamento').all()

    if status_filtro:
        qs = qs.filter(status=status_filtro)
    if loja_id:
        qs = qs.filter(loja_id=loja_id)
    if provedor:
        qs = qs.filter(provedor=provedor)

    # Limitar a 100 registros
    notas = qs[:100]

    data = []
    for nf in notas:
        data.append({
            'id': nf.id,
            'numero_nf': nf.numero_nf,
            'codigo_verificacao': nf.codigo_verificacao,
            'numero_rps': nf.numero_rps,
            'serie_rps': nf.serie_rps,
            'provedor': nf.provedor,
            'status': nf.status,
            'valor': str(nf.valor),
            'aliquota_iss': str(nf.aliquota_iss),
            'valor_iss': str(nf.valor_iss),
            'tomador_nome': nf.tomador_nome,
            'tomador_cpf_cnpj': nf.tomador_cpf_cnpj,
            'tomador_email': nf.tomador_email,
            'descricao_servico': nf.descricao_servico,
            'loja_nome': nf.loja.nome if nf.loja else '',
            'loja_slug': nf.loja.slug if nf.loja else '',
            'asaas_payment_id': nf.asaas_payment_id,
            'data_emissao': nf.data_emissao.isoformat() if nf.data_emissao else None,
            'data_cancelamento': nf.data_cancelamento.isoformat() if nf.data_cancelamento else None,
            'created_at': nf.created_at.isoformat() if nf.created_at else None,
            'tem_xml': bool(nf.xml_nfse),
            'pdf_url': nf.pdf_url,
            'erro_mensagem': nf.erro_mensagem,
        })

    return Response({
        'notas': data,
        'total': qs.count(),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def nfse_xml(request, nfse_id):
    """Retorna XML de uma NFS-e específica."""
    if not request.user.is_superuser:
        return Response({'detail': 'Apenas superadmin.'}, status=403)

    try:
        nf = NFSeEmitida.objects.get(id=nfse_id)
        if not nf.xml_nfse:
            return Response({'success': False, 'error': 'XML não disponível'}, status=404)
        return Response({'success': True, 'xml': nf.xml_nfse, 'numero_nf': nf.numero_nf})
    except NFSeEmitida.DoesNotExist:
        return Response({'success': False, 'error': 'NFS-e não encontrada'}, status=404)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def nfse_debug(request, nfse_id):
    """
    Retorna dados de debug de uma NFS-e: XML DPS assinado + resposta ADN.
    Útil para validar manualmente o XML enviado ao ADN.
    """
    if not request.user.is_superuser:
        return Response({'detail': 'Apenas superadmin.'}, status=403)

    try:
        nf = NFSeEmitida.objects.get(id=nfse_id)
        return Response({
            'success': True,
            'nfse_id': nf.id,
            'numero_rps': nf.numero_rps,
            'status': nf.status,
            'erro_mensagem': nf.erro_mensagem,
            'xml_dps_assinado': nf.xml_dps_assinado or nf.xml_nfse or '',
            'resposta_adn': nf.resposta_adn or '',
            'created_at': nf.created_at.isoformat() if nf.created_at else '',
        })
    except NFSeEmitida.DoesNotExist:
        return Response({'success': False, 'error': 'NFS-e não encontrada'}, status=404)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@rate_limit(max_requests=5, window_seconds=60)
@audit_log('nfse_cancelar', 'Cancelamento de NFS-e via superadmin')
def nfse_cancelar(request, nfse_id):
    if not request.user.is_superuser:
        return Response({'detail': 'Apenas superadmin.'}, status=403)

    try:
        from asaas_integration.models_nfse_config import SuperadminNFSeConfig
        from nfse_integration.issnet_superadmin import cancelar_nfse_emitida_superadmin

        nf = NFSeEmitida.objects.get(id=nfse_id)
        if nf.status == 'cancelada':
            return Response({'success': False, 'error': 'Nota já está cancelada'}, status=400)

        config = SuperadminNFSeConfig.get_config()
        resultado = cancelar_nfse_emitida_superadmin(
            nf,
            config,
            request.data.get('codigo_cancelamento', '1'),
            request.data.get('motivo', ''),
        )
        if resultado.get('success'):
            return Response(resultado)
        return Response(resultado, status=400)

    except NFSeEmitida.DoesNotExist:
        return Response({'success': False, 'error': 'NFS-e não encontrada'}, status=404)
    except Exception as e:
        logger.exception('Erro ao cancelar NFS-e: %s', e)
        return Response({'success': False, 'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def nfse_download_pdf(request, nfse_id):
    """
    Gera e retorna PDF da NFS-e.
    Para ISSNet: tenta buscar URL real via ConsultarUrlNfse primeiro.
    Fallback: gera PDF internamente com os dados da nota.
    """
    from django.http import HttpResponse
    from nfse_integration.pdf_download import resolver_download_pdf_superadmin

    if not request.user.is_superuser:
        return Response({'detail': 'Apenas superadmin.'}, status=403)

    try:
        nfse = NFSeEmitida.objects.select_related('loja').get(id=nfse_id)
        resultado = resolver_download_pdf_superadmin(nfse)

        if resultado.tipo == 'url':
            return Response({'url': resultado.url})

        response = HttpResponse(resultado.conteudo_pdf, content_type='application/pdf')
        response['Content-Disposition'] = (
            f'{resultado.content_disposition}; filename="{resultado.nome_arquivo}"'
        )
        return response

    except NFSeEmitida.DoesNotExist:
        return Response({'error': 'NFS-e não encontrada'}, status=404)
    except Exception as e:
        logger.exception('Erro ao gerar PDF da NFS-e: %s', e)
        return Response({'error': f'Erro ao gerar PDF: {str(e)}'}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@audit_log('nfse_reenviar', 'Reenvio de NFS-e por email via superadmin')
def nfse_reenviar(request, nfse_id):
    if not request.user.is_superuser:
        return Response({'detail': 'Apenas superadmin.'}, status=403)

    try:
        from asaas_integration.models_nfse_config import SuperadminNFSeConfig
        from nfse_integration.danfe import buscar_url_danfe_issnet_superadmin
        from nfse_integration.email_nfse import enviar_email_nfse_tomador
        from types import SimpleNamespace

        nf = NFSeEmitida.objects.select_related('loja').get(id=nfse_id)
        if not nf.tomador_email:
            return Response({'success': False, 'error': 'Email do tomador não disponível'}, status=400)

        config = SuperadminNFSeConfig.get_config()
        prestador = config.prestador_razao_social or 'LWK Sistemas'

        url_danfe = nf.pdf_url or ''
        if not url_danfe and nf.provedor == 'issnet' and nf.numero_nf:
            url_danfe = buscar_url_danfe_issnet_superadmin(nf, config)

        loja = nf.loja or SimpleNamespace(nome=prestador, cpf_cnpj=config.prestador_cnpj or '')

        enviar_email_nfse_tomador(
            loja=loja,
            tomador_email=nf.tomador_email,
            tomador_nome=nf.tomador_nome,
            numero_nf=nf.numero_nf,
            valor=nf.valor,
            descricao=nf.descricao_servico,
            url_danfe=url_danfe,
            codigo_verificacao=nf.codigo_verificacao,
            xml_content=nf.xml_nfse or '',
            fail_silently=False,
            intro='Segue a nota fiscal referente à sua assinatura.',
            prestador_nome=prestador,
            rodape_simples=True,
            assunto_prestador=prestador,
            incluir_cnpj_prestador=False,
        )

        return Response({'success': True, 'message': f'NFS-e reenviada para {nf.tomador_email}'})
    except NFSeEmitida.DoesNotExist:
        return Response({'success': False, 'error': 'NFS-e não encontrada'}, status=404)
    except Exception as e:
        logger.exception('Erro ao reenviar NFS-e: %s', e)
        return Response({'success': False, 'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def nfse_debug_url(request, nfse_id):
    """Debug: chama ConsultarUrlNfse e retorna resposta bruta para diagnóstico."""
    if not request.user.is_superuser:
        return Response({'detail': 'Apenas superadmin.'}, status=403)
    try:
        from asaas_integration.models_nfse_config import SuperadminNFSeConfig
        from nfse_integration.issnet_superadmin import (
            certificado_configurado,
            consultar_url_nfse_superadmin,
            senha_certificado_configurada,
        )

        nfse = NFSeEmitida.objects.get(id=nfse_id)
        config = SuperadminNFSeConfig.get_config()
        if not certificado_configurado(config) or not senha_certificado_configurada(config):
            return Response({'error': 'Certificado não configurado'}, status=400)

        resultado = consultar_url_nfse_superadmin(nfse, config)
        return Response({
            'nfse_id': nfse_id,
            'numero_nf': nfse.numero_nf,
            'resultado': resultado,
        })
    except NFSeEmitida.DoesNotExist:
        return Response({'error': 'NFS-e não encontrada'}, status=404)
    except Exception as e:
        logger.exception('Erro debug URL NFS-e: %s', e)
        return Response({'error': str(e)}, status=500)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def nfse_excluir(request, nfse_id):
    """Exclui registro de NFS-e do banco (apenas notas com erro ou pendentes — emitidas só podem ser canceladas)."""
    if not request.user.is_superuser:
        return Response({'detail': 'Apenas superadmin.'}, status=403)

    try:
        nf = NFSeEmitida.objects.get(id=nfse_id)
        if nf.status == 'emitida':
            return Response({'success': False, 'error': 'Nota fiscal emitida não pode ser excluída. Use a opção Cancelar.'}, status=400)
        if nf.status == 'cancelada':
            return Response({'success': False, 'error': 'Nota fiscal cancelada não pode ser excluída (manter para histórico).'}, status=400)
        numero = nf.numero_nf or f'ID {nf.id}'
        nf.delete()
        logger.info('NFS-e %s excluída pelo superadmin', numero)
        return Response({'success': True, 'message': f'NFS-e {numero} excluída com sucesso'})
    except NFSeEmitida.DoesNotExist:
        return Response({'success': False, 'error': 'NFS-e não encontrada'}, status=404)
    except Exception as e:
        logger.exception('Erro ao excluir NFS-e: %s', e)
        return Response({'success': False, 'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def listar_lojas_para_nfse(request):
    """Lista lojas ativas para o seletor de emissão manual de NFS-e."""
    if not request.user.is_superuser:
        return Response({'detail': 'Apenas superadmin.'}, status=403)

    lojas = Loja.objects.filter(is_active=True).select_related('owner').order_by('nome')[:200]
    data = []
    for loja in lojas:
        data.append({
            'id': loja.id,
            'nome': loja.nome,
            'slug': loja.slug,
            'cpf_cnpj': loja.cpf_cnpj or '',
            'email': loja.owner.email if loja.owner else '',
            'razao_social': loja.nome,
        })
    return Response({'lojas': data})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@rate_limit(max_requests=10, window_seconds=60)
@audit_log('nfse_emitir_manual', 'Emissão manual de NFS-e via superadmin')
def emitir_nfse_manual(request):
    """
    Emite NFS-e manualmente via ISSNet direto.
    Aceita dois modos:
    - Com loja_id: preenche tomador a partir dos dados da loja
    - Sem loja_id: usa dados do tomador informados manualmente
    """
    if not request.user.is_superuser:
        return Response({'detail': 'Apenas superadmin.'}, status=403)

    from asaas_integration.models_nfse_config import SuperadminNFSeConfig
    from nfse_integration.emissao_manual_superadmin import (
        EmissaoManualValidationError,
        emitir_nfse_manual_superadmin,
        preparar_emissao_manual,
        validar_config_emissao,
    )

    try:
        payload = preparar_emissao_manual(request.data)
    except EmissaoManualValidationError as exc:
        return Response({'success': False, 'error': exc.message}, status=exc.status)

    config = SuperadminNFSeConfig.get_config()
    config_err = validar_config_emissao(config)
    if config_err:
        return Response({'success': False, 'error': config_err.message}, status=config_err.status)

    try:
        resultado = emitir_nfse_manual_superadmin(config, payload)
        return Response(resultado.as_response_dict(), status=resultado.http_status)
    except Exception as e:
        logger.exception('Erro ao emitir NFS-e manual: %s', e)
        return Response({'success': False, 'error': str(e)}, status=500)
