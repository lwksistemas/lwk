"""
Views para listagem e emissão manual de NFS-e pelo superadmin.
GET  /api/superadmin/nfse-emitidas/
POST /api/superadmin/nfse-emitidas/emitir-manual/
"""
import logging
import os
import tempfile
from decimal import Decimal, InvalidOperation

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.audit import audit_log, registrar_audit_manual
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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@rate_limit(max_requests=5, window_seconds=60)
@audit_log('nfse_cancelar', 'Cancelamento de NFS-e via superadmin')
def nfse_cancelar(request, nfse_id):
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
@audit_log('nfse_reenviar', 'Reenvio de NFS-e por email via superadmin')
def nfse_reenviar(request, nfse_id):
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
    from nfse_integration.issnet_client import ISSNetClient

    data = request.data
    loja_id = data.get('loja_id')
    loja = None

    # Dados do tomador
    if loja_id:
        try:
            loja = Loja.objects.select_related('owner').get(id=loja_id, is_active=True)
            tomador_cpf_cnpj = loja.cpf_cnpj or ''
            tomador_nome = loja.nome
            tomador_email = loja.owner.email if loja.owner else ''
            # Endereço da loja para o tomador
            tomador_endereco_loja = {
                'logradouro': getattr(loja, 'logradouro', '') or '',
                'numero': getattr(loja, 'numero', '') or 'S/N',
                'complemento': getattr(loja, 'complemento', '') or '',
                'bairro': getattr(loja, 'bairro', '') or '',
                'cidade': getattr(loja, 'cidade', '') or 'Ribeirão Preto',
                'uf': getattr(loja, 'uf', '') or 'SP',
                'cep': getattr(loja, 'cep', '') or '',
            }
        except Loja.DoesNotExist:
            return Response({'success': False, 'error': 'Loja não encontrada'}, status=404)
    else:
        tomador_cpf_cnpj = (data.get('tomador_cpf_cnpj') or '').strip()
        tomador_nome = (data.get('tomador_nome') or '').strip()
        tomador_email = (data.get('tomador_email') or '').strip()

    # Validações básicas
    if not tomador_cpf_cnpj:
        return Response({'success': False, 'error': 'CPF/CNPJ do tomador é obrigatório'}, status=400)
    if not tomador_nome:
        return Response({'success': False, 'error': 'Nome do tomador é obrigatório'}, status=400)

    # Valor e descrição
    valor_str = data.get('valor_servicos') or data.get('valor') or ''
    try:
        valor = Decimal(str(valor_str).replace(',', '.'))
        if valor <= 0:
            raise InvalidOperation()
    except (InvalidOperation, ValueError):
        return Response({'success': False, 'error': 'Valor dos serviços inválido'}, status=400)

    descricao = (data.get('servico_descricao') or data.get('descricao_servico') or '').strip()
    if not descricao:
        return Response({'success': False, 'error': 'Descrição do serviço é obrigatória'}, status=400)

    # Endereço do tomador
    if loja_id:
        tomador_endereco = tomador_endereco_loja
    else:
        tomador_endereco = {
            'logradouro': data.get('tomador_logradouro', ''),
            'numero': data.get('tomador_numero', ''),
            'complemento': data.get('tomador_complemento', ''),
            'bairro': data.get('tomador_bairro', ''),
            'cidade': data.get('tomador_cidade', '') or 'Ribeirão Preto',
            'uf': data.get('tomador_uf', '') or 'SP',
            'cep': data.get('tomador_cep', ''),
        }

    # Buscar código IBGE do município pelo CEP
    import re, requests as req_http
    cep_digits = re.sub(r'\D', '', tomador_endereco.get('cep') or '')
    if len(cep_digits) == 8:
        try:
            resp = req_http.get(f'https://viacep.com.br/ws/{cep_digits}/json/', timeout=5)
            if resp.status_code == 200:
                viacep = resp.json()
                ibge = viacep.get('ibge', '')
                if ibge:
                    tomador_endereco['codigo_municipio'] = str(ibge)
                # Preencher cidade/UF se vieram vazios
                if not tomador_endereco.get('cidade') or tomador_endereco['cidade'] == 'Ribeirão Preto':
                    tomador_endereco['cidade'] = viacep.get('localidade') or tomador_endereco['cidade']
                if not tomador_endereco.get('uf') or tomador_endereco['uf'] == 'SP':
                    tomador_endereco['uf'] = viacep.get('uf') or tomador_endereco['uf']
        except Exception as e:
            logger.warning('Erro ao buscar IBGE pelo CEP %s: %s', cep_digits, e)

    # Configuração do superadmin
    config = SuperadminNFSeConfig.get_config()

    if config.provedor_nfse == 'desabilitado':
        return Response({'success': False, 'error': 'Emissão de NFS-e está desabilitada nas configurações'}, status=400)

    if not config.issnet_usuario or not config.issnet_senha:
        return Response({'success': False, 'error': 'Credenciais ISSNet não configuradas'}, status=400)
    if not config.issnet_certificado:
        return Response({'success': False, 'error': 'Certificado digital não configurado'}, status=400)
    if not config.prestador_cnpj:
        return Response({'success': False, 'error': 'CNPJ do prestador não configurado'}, status=400)

    # Descriptografar credenciais
    from core.encryption import decrypt_value
    issnet_usuario = decrypt_value(config.issnet_usuario)
    issnet_senha = decrypt_value(config.issnet_senha)
    issnet_senha_cert = decrypt_value(config.issnet_senha_certificado)

    # Certificado temporário
    cert_path = None
    try:
        cert_tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pfx')
        cert_tmp.write(bytes(config.issnet_certificado))
        cert_tmp.close()
        cert_path = cert_tmp.name

        # Número RPS
        numero_rps = config.proximo_rps()

        # Cliente ISSNet
        client = ISSNetClient(
            usuario=issnet_usuario,
            senha=issnet_senha,
            certificado_path=cert_path,
            senha_certificado=issnet_senha_cert,
            ambiente='producao',
        )
        client._regime_especial = config.regime_especial_tributacao or '0'
        client._optante_simples = config.optante_simples_nacional
        client._incentivador_cultural = config.incentivador_cultural

        serie_rps = (config.serie_rps or 'E').strip()

        # Emitir — usar override de CNAE/serviço se informado no request
        codigo_cnae_req = (data.get('codigo_cnae') or '').strip()
        codigo_servico_req = (data.get('codigo_servico') or '').strip()

        resultado = client.emitir_nfse(
            prestador_cnpj=config.prestador_cnpj,
            prestador_inscricao_municipal=config.prestador_inscricao_municipal,
            prestador_razao_social=config.prestador_razao_social,
            tomador_cpf_cnpj=tomador_cpf_cnpj,
            tomador_nome=tomador_nome,
            tomador_endereco=tomador_endereco,
            servico_codigo=codigo_servico_req or config.codigo_servico_municipal or '1401',
            servico_descricao=descricao,
            valor_servicos=valor,
            aliquota_iss=config.aliquota_iss,
            numero_rps=numero_rps,
            serie_rps=serie_rps,
            codigo_cnae=codigo_cnae_req or (config.codigo_cnae or '').strip() or None,
        )

        # Salvar registro
        aliquota = Decimal(str(config.aliquota_iss))
        valor_iss = (valor * aliquota / 100).quantize(Decimal('0.01'))

        nfse_obj = NFSeEmitida.objects.create(
            loja=loja,
            pagamento=None,
            numero_nf=resultado.get('numero_nf', ''),
            codigo_verificacao=resultado.get('codigo_verificacao', ''),
            numero_rps=resultado.get('numero_rps', numero_rps),
            serie_rps=serie_rps,
            provedor='issnet',
            status='emitida' if resultado.get('success') else 'erro',
            valor=valor,
            aliquota_iss=aliquota,
            valor_iss=valor_iss,
            tomador_nome=tomador_nome,
            tomador_cpf_cnpj=tomador_cpf_cnpj,
            tomador_email=tomador_email,
            descricao_servico=descricao[:500],
            xml_nfse=resultado.get('xml_nfse', ''),
            data_emissao=resultado.get('data_emissao'),
            erro_mensagem=resultado.get('error', '') if not resultado.get('success') else '',
        )

        if resultado.get('success'):
            # Enviar email se solicitado
            enviar_email = data.get('enviar_email', True)
            if enviar_email and tomador_email:
                _enviar_email_nfse_manual(config, tomador_email, tomador_nome, resultado, valor, descricao)

            return Response({
                'success': True,
                'message': f'NFS-e {resultado.get("numero_nf", "")} emitida com sucesso!',
                'numero_nf': resultado.get('numero_nf', ''),
                'id': nfse_obj.id,
            })
        else:
            return Response({
                'success': False,
                'error': resultado.get('error', 'Erro desconhecido ao emitir NFS-e'),
                'id': nfse_obj.id,
            }, status=400)

    except Exception as e:
        logger.exception('Erro ao emitir NFS-e manual: %s', e)
        return Response({'success': False, 'error': str(e)}, status=500)
    finally:
        if cert_path:
            try:
                os.unlink(cert_path)
            except OSError:
                pass


def _enviar_email_nfse_manual(config, tomador_email, tomador_nome, resultado, valor, descricao):
    """Envia email com a NFS-e emitida manualmente."""
    try:
        from django.core.mail import EmailMessage
        from django.conf import settings

        prestador = config.prestador_razao_social or 'LWK Sistemas'
        numero_nf = resultado.get('numero_nf', '')

        assunto = f'Nota Fiscal de Serviço Nº {numero_nf} - {prestador}'
        corpo = (
            f'Olá {tomador_nome}!\n\n'
            f'Segue a nota fiscal referente ao serviço prestado.\n\n'
            f'📋 DADOS DA NOTA FISCAL:\n'
            f'• Número: {numero_nf}\n'
            f'• Prestador: {prestador}\n'
            f'• Valor: R$ {valor:.2f}\n'
            f'• Código de Verificação: {resultado.get("codigo_verificacao", "")}\n'
            f'• Descrição: {descricao}\n\n'
            f'Atenciosamente,\n{prestador}'
        )

        email = EmailMessage(
            subject=assunto,
            body=corpo,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[tomador_email],
        )
        xml_nfse = resultado.get('xml_nfse', '')
        if xml_nfse:
            email.attach(f'nfse_{numero_nf}.xml', xml_nfse.encode('utf-8'), 'application/xml')
        email.send(fail_silently=False)
        logger.info('Email NFS-e manual enviado para %s', tomador_email)
    except Exception as e:
        logger.warning('Falha ao enviar email NFS-e manual: %s', e)
