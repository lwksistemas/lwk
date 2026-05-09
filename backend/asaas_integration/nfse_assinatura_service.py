"""
Serviço de emissão de NFS-e para assinaturas das lojas.
Emite nota fiscal quando o pagamento da assinatura é confirmado.
Suporta ISSNet direto (sem taxa) ou Asaas (intermediário).
"""
import logging
import tempfile
import os
from decimal import Decimal
from typing import Dict, Any, Optional

from django.utils import timezone

logger = logging.getLogger(__name__)


def _buscar_codigo_ibge(cep: str, cidade: str) -> str:
    """
    Busca código IBGE do município pelo CEP (via API ViaCEP).
    Fallback: retorna código de Ribeirão Preto se não encontrar.
    """
    import re
    cep_digits = re.sub(r'\D', '', cep or '')
    if len(cep_digits) == 8:
        try:
            import requests
            resp = requests.get(f'https://viacep.com.br/ws/{cep_digits}/json/', timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                ibge = data.get('ibge', '')
                if ibge:
                    return str(ibge)
        except Exception as e:
            logger.warning(f'Erro ao buscar IBGE pelo CEP {cep_digits}: {e}')
    # Fallback: Ribeirão Preto
    return '3543402'


def emitir_nfse_assinatura(pagamento) -> Dict[str, Any]:
    """
    Emite NFS-e para um pagamento de assinatura confirmado.
    
    Args:
        pagamento: instância de PagamentoLoja (superadmin)
    
    Returns:
        dict com resultado: {'success': bool, 'numero_nf': str, ...}
    """
    from .models_nfse_config import SuperadminNFSeConfig

    config = SuperadminNFSeConfig.get_config()

    if config.provedor_nfse == 'desabilitado':
        logger.info('NFS-e assinatura: emissão desabilitada')
        return {'success': False, 'error': 'Emissão de NFS-e desabilitada'}

    if not config.emitir_automaticamente:
        logger.info('NFS-e assinatura: emissão automática desativada')
        return {'success': False, 'error': 'Emissão automática desativada'}

    loja = pagamento.loja
    valor = Decimal(str(pagamento.valor))

    # Dados do tomador (a loja que pagou a assinatura)
    tomador_cpf_cnpj = getattr(loja, 'cpf_cnpj', '') or ''
    tomador_nome = loja.nome or ''
    tomador_email = getattr(loja, 'owner', None) and getattr(loja.owner, 'email', '') or ''

    # Endereço do tomador
    tomador_endereco = {
        'logradouro': getattr(loja, 'logradouro', '') or '',
        'numero': getattr(loja, 'numero', '') or 'S/N',
        'complemento': getattr(loja, 'complemento', '') or '',
        'bairro': getattr(loja, 'bairro', '') or '',
        'cidade': getattr(loja, 'cidade', '') or '',
        'uf': getattr(loja, 'uf', '') or '',
        'cep': getattr(loja, 'cep', '') or '',
        'codigo_municipio': _buscar_codigo_ibge(getattr(loja, 'cep', '') or '', getattr(loja, 'cidade', '') or ''),
        'email': tomador_email,
        'telefone': getattr(loja, 'owner_telefone', '') or '',
    }

    # Descrição do serviço
    referencia = pagamento.referencia_mes.strftime('%m/%Y') if pagamento.referencia_mes else ''
    descricao = config.descricao_servico_padrao or 'Licenciamento de uso de software SaaS'
    if referencia:
        descricao = f'{descricao} - Ref. {referencia}'
    if loja.nome:
        descricao = f'{descricao} - {loja.nome}'

    if config.provedor_nfse == 'issnet':
        return _emitir_via_issnet(config, tomador_cpf_cnpj, tomador_nome, tomador_email, tomador_endereco, descricao, valor)
    elif config.provedor_nfse == 'asaas':
        # Asaas emite automaticamente via webhook — não precisa fazer nada aqui
        logger.info('NFS-e assinatura: provedor Asaas (emissão automática pelo Asaas)')
        return {'success': True, 'message': 'Emissão delegada ao Asaas'}
    else:
        return {'success': False, 'error': f'Provedor desconhecido: {config.provedor_nfse}'}


def _emitir_via_issnet(
    config,
    tomador_cpf_cnpj: str,
    tomador_nome: str,
    tomador_email: str,
    tomador_endereco: Dict[str, str],
    descricao: str,
    valor: Decimal,
) -> Dict[str, Any]:
    """Emite NFS-e via ISSNet direto usando certificado do superadmin."""
    cert_path = None
    try:
        from nfse_integration.issnet_client import ISSNetClient

        # Validações
        if not config.issnet_usuario:
            return {'success': False, 'error': 'Usuário ISSNet não configurado no superadmin'}
        if not config.issnet_senha:
            return {'success': False, 'error': 'Senha ISSNet não configurada no superadmin'}
        if not config.issnet_certificado:
            return {'success': False, 'error': 'Certificado digital não configurado no superadmin'}
        if not config.issnet_senha_certificado:
            return {'success': False, 'error': 'Senha do certificado não configurada no superadmin'}
        if not config.prestador_cnpj:
            return {'success': False, 'error': 'CNPJ do prestador não configurado no superadmin'}

        # Certificado temporário
        cert_tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pfx')
        cert_tmp.write(bytes(config.issnet_certificado))
        cert_tmp.close()
        cert_path = cert_tmp.name

        # Número RPS
        numero_rps = config.proximo_rps()

        # Cliente ISSNet
        client = ISSNetClient(
            usuario=config.issnet_usuario,
            senha=config.issnet_senha,
            certificado_path=cert_path,
            senha_certificado=config.issnet_senha_certificado,
            ambiente='producao',
        )
        client._regime_especial = config.regime_especial_tributacao or '0'
        client._optante_simples = config.optante_simples_nacional
        client._incentivador_cultural = config.incentivador_cultural

        serie_rps = (config.serie_rps or 'E').strip()

        # Emitir
        resultado = client.emitir_nfse(
            prestador_cnpj=config.prestador_cnpj,
            prestador_inscricao_municipal=config.prestador_inscricao_municipal,
            prestador_razao_social=config.prestador_razao_social,
            tomador_cpf_cnpj=tomador_cpf_cnpj,
            tomador_nome=tomador_nome,
            tomador_endereco=tomador_endereco,
            servico_codigo=config.codigo_servico_municipal or '1401',
            servico_descricao=descricao,
            valor_servicos=valor,
            aliquota_iss=config.aliquota_iss,
            numero_rps=numero_rps,
            serie_rps=serie_rps,
            codigo_cnae=(config.codigo_cnae or '').strip() or None,
        )

        if resultado.get('success'):
            logger.info(
                'NFS-e assinatura emitida: NF %s, tomador=%s, valor=R$%s',
                resultado.get('numero_nf'),
                tomador_nome,
                valor,
            )
            # Salvar registro no banco
            _salvar_nfse_emitida(pagamento, config, resultado, tomador_nome, tomador_cpf_cnpj, tomador_email, descricao, valor)
            # Enviar email para o tomador
            _enviar_email_nfse_assinatura(config, tomador_email, tomador_nome, resultado, valor, descricao)

        return resultado

    except Exception as e:
        logger.exception('Erro ao emitir NFS-e assinatura via ISSNet: %s', e)
        return {'success': False, 'error': str(e)}
    finally:
        if cert_path:
            try:
                os.unlink(cert_path)
            except OSError:
                pass


def _salvar_nfse_emitida(pagamento, config, resultado, tomador_nome, tomador_cpf_cnpj, tomador_email, descricao, valor):
    """Salva registro da NFS-e emitida no banco."""
    try:
        from superadmin.models import NFSeEmitida
        from decimal import Decimal

        valor_dec = Decimal(str(valor))
        aliquota = Decimal(str(config.aliquota_iss))
        valor_iss = (valor_dec * aliquota / 100).quantize(Decimal('0.01'))

        NFSeEmitida.objects.create(
            loja=pagamento.loja,
            pagamento=pagamento,
            numero_nf=resultado.get('numero_nf', ''),
            codigo_verificacao=resultado.get('codigo_verificacao', ''),
            numero_rps=resultado.get('numero_rps', 0),
            serie_rps=config.serie_rps or '',
            provedor='issnet',
            status='emitida',
            valor=valor_dec,
            aliquota_iss=aliquota,
            valor_iss=valor_iss,
            tomador_nome=tomador_nome,
            tomador_cpf_cnpj=tomador_cpf_cnpj,
            tomador_email=tomador_email,
            descricao_servico=descricao[:500],
            xml_nfse=resultado.get('xml_nfse', ''),
            asaas_payment_id=pagamento.asaas_payment_id or '',
            data_emissao=resultado.get('data_emissao'),
        )
        logger.info('NFSeEmitida salva: NF %s, loja %s', resultado.get('numero_nf'), pagamento.loja.slug)
    except Exception as e:
        logger.warning('Erro ao salvar NFSeEmitida: %s', e)


def _enviar_email_nfse_assinatura(config, tomador_email, tomador_nome, resultado, valor, descricao):
    """Envia email com dados da NFS-e emitida para a loja."""
    if not tomador_email:
        return
    try:
        from django.core.mail import EmailMessage
        from django.conf import settings

        numero_nf = resultado.get('numero_nf', '')
        codigo_verificacao = resultado.get('codigo_verificacao', '')
        prestador = config.prestador_razao_social or 'LWK Sistemas'

        assunto = f'Nota Fiscal de Serviço Nº {numero_nf} - {prestador}'
        corpo = (
            f'Olá {tomador_nome}!\n\n'
            f'A nota fiscal referente à sua assinatura foi emitida.\n\n'
            f'📋 DADOS DA NOTA FISCAL:\n'
            f'• Número: {numero_nf}\n'
            f'• Prestador: {prestador}\n'
            f'• CNPJ: {config.prestador_cnpj}\n'
            f'• Valor: R$ {valor:.2f}\n'
            f'• Código de Verificação: {codigo_verificacao}\n'
            f'• Descrição: {descricao}\n\n'
            f'📄 O arquivo XML da nota fiscal está em anexo.\n\n'
            f'📩 Você também receberá um e-mail automático do sistema da Prefeitura (ISS.NET) '
            f'com o link para visualizar e imprimir a nota fiscal oficial.\n\n'
            f'---\n'
            f'Atenciosamente,\n'
            f'{prestador}'
        )

        email = EmailMessage(
            subject=assunto,
            body=corpo,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[tomador_email],
        )

        # Anexar XML se disponível
        xml_content = resultado.get('xml_nfse', '')
        if xml_content:
            email.attach(f'nfse_{numero_nf}.xml', xml_content.encode('utf-8'), 'application/xml')

        email.send(fail_silently=True)
        logger.info('Email NFS-e assinatura enviado para %s', tomador_email)
    except Exception as e:
        logger.warning('Erro ao enviar email NFS-e assinatura: %s', e)
