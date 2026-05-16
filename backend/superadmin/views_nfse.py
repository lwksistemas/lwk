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
        from django.utils import timezone

        nf = NFSeEmitida.objects.get(id=nfse_id)
        if nf.status == 'cancelada':
            return Response({'success': False, 'error': 'Nota já está cancelada'}, status=400)

        if nf.provedor == 'issnet' and nf.numero_nf:
            # ISSNet removido — cancelar apenas no sistema
            nf.status = 'cancelada'
            nf.data_cancelamento = timezone.now()
            nf.save()
            return Response({
                'success': True,
                'message': f'NFS-e {nf.numero_nf} marcada como cancelada no sistema.'
            })
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

    # Adicionar email e telefone ao endereço do tomador (usado no XML do ISSNet)
    tomador_endereco['email'] = tomador_email
    tomador_endereco['telefone'] = data.get('tomador_telefone', '') or ''

    # Configuração do superadmin
    config = SuperadminNFSeConfig.get_config()

    if config.provedor_nfse == 'desabilitado':
        return Response({'success': False, 'error': 'Emissão de NFS-e está desabilitada nas configurações'}, status=400)

    if not config.nacional_certificado:
        return Response({'success': False, 'error': 'Certificado digital não configurado'}, status=400)
    if not config.nacional_senha_certificado:
        return Response({'success': False, 'error': 'Senha do certificado não configurada'}, status=400)
    if not config.prestador_cnpj:
        return Response({'success': False, 'error': 'CNPJ do prestador não configurado'}, status=400)
    if not config.nacional_codigo_municipio:
        return Response({'success': False, 'error': 'Código IBGE do município não configurado'}, status=400)

    try:
        from nfse_integration.nacional import NacionalClient

        numero_dps = config.proximo_dps()

        client = NacionalClient(
            pfx_bytes=bytes(config.nacional_certificado),
            senha_pfx=config.nacional_senha_certificado,
            ambiente=config.nacional_ambiente or 'homologacao',
        )

        codigo_cnae_req = (data.get('codigo_cnae') or '').strip()
        codigo_servico_req = (data.get('codigo_servico') or '').strip()

        resultado = client.emitir_nfse(
            numero_dps=numero_dps,
            serie_dps=config.nacional_serie_dps or '900',
            codigo_municipio_prestador=config.nacional_codigo_municipio,
            prestador_cnpj=config.prestador_cnpj,
            prestador_inscricao_municipal=config.prestador_inscricao_municipal or '',
            prestador_razao_social=config.prestador_razao_social or '',
            prestador_email=config.prestador_email or '',
            tomador_cpf_cnpj=tomador_cpf_cnpj,
            tomador_nome=tomador_nome,
            tomador_endereco=tomador_endereco,
            tomador_email=tomador_email,
            codigo_servico=codigo_servico_req or config.codigo_servico_municipal or '14.01',
            descricao_servico=descricao,
            codigo_cnae=codigo_cnae_req or (config.codigo_cnae or '').strip() or '',
            codigo_municipio_incidencia=config.nacional_codigo_municipio,
            valor_servicos=valor,
            aliquota_iss=config.aliquota_iss,
            iss_retido=False,
            optante_simples_nacional=config.optante_simples_nacional,
            incentivador_cultural=config.incentivador_cultural,
        )

        if resultado.get('success'):
            # Salvar registro
            aliquota = Decimal(str(config.aliquota_iss))
            valor_iss = (valor * aliquota / 100).quantize(Decimal('0.01'))

            nfse_obj = NFSeEmitida.objects.create(
                loja=loja,
                pagamento=None,
                numero_nf=resultado.get('chave_acesso', ''),
                codigo_verificacao=resultado.get('nsu_recepcao', ''),
                numero_rps=numero_dps,
                serie_rps=config.nacional_serie_dps or '900',
                provedor='nacional',
                status='emitida',
                valor=valor,
                aliquota_iss=aliquota,
                valor_iss=valor_iss,
                tomador_nome=tomador_nome,
                tomador_cpf_cnpj=tomador_cpf_cnpj,
                tomador_email=tomador_email,
                descricao_servico=descricao[:500],
                xml_nfse=resultado.get('xml_dps', ''),
                xml_dps_assinado=resultado.get('xml_dps', ''),
                resposta_adn=resultado.get('resposta_adn_raw', ''),
            )

            return Response({
                'success': True,
                'message': f'NFS-e emitida com sucesso! Chave: {resultado.get("chave_acesso", "")}',
                'numero_nf': resultado.get('chave_acesso', ''),
                'nfse_id': nfse_obj.id,
            })
        else:
            error_msg = resultado.get('error', 'Erro desconhecido')

            # Salvar registro com erro para debug (XML assinado + resposta ADN)
            nfse_obj = NFSeEmitida.objects.create(
                loja=loja,
                pagamento=None,
                numero_nf='',
                numero_rps=numero_dps,
                serie_rps=config.nacional_serie_dps or '900',
                provedor='nacional',
                status='erro',
                valor=valor,
                aliquota_iss=Decimal(str(config.aliquota_iss)),
                valor_iss=Decimal('0'),
                tomador_nome=tomador_nome,
                tomador_cpf_cnpj=tomador_cpf_cnpj,
                tomador_email=tomador_email,
                descricao_servico=descricao[:500],
                xml_dps_assinado=resultado.get('xml_dps', '') or '',
                resposta_adn=resultado.get('resposta_adn_raw', '') or '',
                erro_mensagem=error_msg[:2000],
            )

            return Response({
                'success': False,
                'error': error_msg,
                'nfse_id': nfse_obj.id,
                'debug_info': 'XML assinado e resposta ADN salvos no registro para análise',
            }, status=400)

    except Exception as e:
        logger.exception('Erro ao emitir NFS-e manual via Nacional: %s', e)
        return Response({'success': False, 'error': str(e)}, status=500)

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
