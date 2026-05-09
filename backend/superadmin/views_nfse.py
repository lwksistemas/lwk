"""
Views para listagem de NFS-e emitidas pelo superadmin.
GET /api/superadmin/nfse-emitidas/
"""
import logging

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import NFSeEmitida

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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def nfse_cancelar(request, nfse_id):
    """Cancela uma NFS-e emitida via ISSNet."""
    if not request.user.is_superuser:
        return Response({'detail': 'Apenas superadmin.'}, status=403)

    try:
        from django.utils import timezone

        nf = NFSeEmitida.objects.get(id=nfse_id)
        if nf.status == 'cancelada':
            return Response({'success': False, 'error': 'Nota já está cancelada'}, status=400)

        if nf.provedor == 'issnet' and nf.numero_nf:
            # Cancelar via ISSNet
            from asaas_integration.models_nfse_config import SuperadminNFSeConfig
            from nfse_integration.issnet_client import ISSNetClient
            import tempfile, os

            config = SuperadminNFSeConfig.get_config()
            cert_tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pfx')
            cert_tmp.write(bytes(config.issnet_certificado))
            cert_tmp.close()

            try:
                client = ISSNetClient(
                    usuario=config.issnet_usuario,
                    senha=config.issnet_senha,
                    certificado_path=cert_tmp.name,
                    senha_certificado=config.issnet_senha_certificado,
                    ambiente='producao',
                )
                resultado = client.cancelar_nfse(
                    numero_nf=nf.numero_nf,
                    motivo='Cancelamento solicitado pelo administrador',
                    prestador_cnpj=config.prestador_cnpj,
                    inscricao_municipal=config.prestador_inscricao_municipal,
                )
                if resultado.get('success'):
                    nf.status = 'cancelada'
                    nf.data_cancelamento = timezone.now()
                    nf.save()
                    return Response({'success': True, 'message': f'NFS-e {nf.numero_nf} cancelada com sucesso'})
                else:
                    return Response({'success': False, 'error': resultado.get('error', 'Erro ao cancelar')}, status=400)
            finally:
                os.unlink(cert_tmp.name)
        else:
            # Cancelamento manual (marcar como cancelada)
            nf.status = 'cancelada'
            nf.data_cancelamento = timezone.now()
            nf.save()
            return Response({'success': True, 'message': 'NFS-e marcada como cancelada'})

    except NFSeEmitida.DoesNotExist:
        return Response({'success': False, 'error': 'NFS-e não encontrada'}, status=404)
    except Exception as e:
        logger.exception('Erro ao cancelar NFS-e: %s', e)
        return Response({'success': False, 'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def nfse_reenviar(request, nfse_id):
    """Reenvia email da NFS-e para o tomador."""
    if not request.user.is_superuser:
        return Response({'detail': 'Apenas superadmin.'}, status=403)

    try:
        from django.core.mail import EmailMessage
        from django.conf import settings
        from asaas_integration.models_nfse_config import SuperadminNFSeConfig

        nf = NFSeEmitida.objects.get(id=nfse_id)
        if not nf.tomador_email:
            return Response({'success': False, 'error': 'Email do tomador não disponível'}, status=400)

        config = SuperadminNFSeConfig.get_config()
        prestador = config.prestador_razao_social or 'LWK Sistemas'

        assunto = f'Nota Fiscal de Serviço Nº {nf.numero_nf} - {prestador}'
        corpo = (
            f'Olá {nf.tomador_nome}!\n\n'
            f'Segue a nota fiscal referente à sua assinatura.\n\n'
            f'📋 DADOS DA NOTA FISCAL:\n'
            f'• Número: {nf.numero_nf}\n'
            f'• Prestador: {prestador}\n'
            f'• Valor: R$ {nf.valor:.2f}\n'
            f'• Código de Verificação: {nf.codigo_verificacao}\n'
            f'• Descrição: {nf.descricao_servico}\n\n'
            f'Atenciosamente,\n{prestador}'
        )

        email = EmailMessage(
            subject=assunto,
            body=corpo,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[nf.tomador_email],
        )
        if nf.xml_nfse:
            email.attach(f'nfse_{nf.numero_nf}.xml', nf.xml_nfse.encode('utf-8'), 'application/xml')
        email.send(fail_silently=False)

        return Response({'success': True, 'message': f'NFS-e reenviada para {nf.tomador_email}'})
    except NFSeEmitida.DoesNotExist:
        return Response({'success': False, 'error': 'NFS-e não encontrada'}, status=404)
    except Exception as e:
        logger.exception('Erro ao reenviar NFS-e: %s', e)
        return Response({'success': False, 'error': str(e)}, status=500)
