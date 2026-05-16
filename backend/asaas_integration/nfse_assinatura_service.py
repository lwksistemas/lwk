"""
Serviço de emissão de NFS-e para assinaturas das lojas.
Emite nota fiscal quando o pagamento da assinatura é confirmado.
Provedor: Nacional (ADN - Padrão Nacional NFS-e).
"""
import logging
from decimal import Decimal
from typing import Dict, Any

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

    # Proteção contra emissão duplicada
    from superadmin.models import NFSeEmitida
    if NFSeEmitida.objects.filter(pagamento=pagamento, status='emitida').exists():
        logger.info(
            'NFS-e assinatura: já existe nota emitida para pagamento %s — ignorando duplicata',
            pagamento.id,
        )
        return {'success': True, 'message': 'NFS-e já emitida anteriormente para este pagamento'}

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

    if config.provedor_nfse == 'nacional':
        return _emitir_via_nacional(pagamento, config, tomador_cpf_cnpj, tomador_nome, tomador_email, tomador_endereco, descricao, valor)
    else:
        return {'success': False, 'error': f'Provedor desconhecido: {config.provedor_nfse}'}


def _emitir_via_nacional(
    pagamento,
    config,
    tomador_cpf_cnpj: str,
    tomador_nome: str,
    tomador_email: str,
    tomador_endereco: Dict[str, str],
    descricao: str,
    valor: Decimal,
) -> Dict[str, Any]:
    """Emite NFS-e via ADN Nacional usando certificado do superadmin."""
    try:
        from nfse_integration.nacional import NacionalClient

        # Validações
        if not config.nacional_certificado:
            return {'success': False, 'error': 'Certificado digital Nacional não configurado'}
        if not config.nacional_senha_certificado:
            return {'success': False, 'error': 'Senha do certificado Nacional não configurada'}
        if not config.prestador_cnpj:
            return {'success': False, 'error': 'CNPJ do prestador não configurado'}
        if not config.nacional_codigo_municipio:
            return {'success': False, 'error': 'Código IBGE do município não configurado'}

        # Número DPS
        numero_dps = config.proximo_dps()

        # Cliente Nacional
        client = NacionalClient(
            pfx_bytes=bytes(config.nacional_certificado),
            senha_pfx=config.nacional_senha_certificado,
            ambiente=config.nacional_ambiente or 'homologacao',
        )

        # Emitir
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
            codigo_servico=config.codigo_servico_municipal or '14.01',
            descricao_servico=descricao,
            codigo_cnae=(config.codigo_cnae or '').strip() or '',
            codigo_municipio_incidencia=config.nacional_codigo_municipio,
            valor_servicos=valor,
            aliquota_iss=config.aliquota_iss,
            iss_retido=False,
            optante_simples_nacional=config.optante_simples_nacional,
            incentivador_cultural=config.incentivador_cultural,
        )

        if resultado.get('success'):
            logger.info(
                'NFS-e Nacional emitida: ChaveAcesso=%s, tomador=%s, valor=R$%s',
                resultado.get('chave_acesso'),
                tomador_nome,
                valor,
            )
            resultado_padrao = {
                'success': True,
                'numero_nf': resultado.get('chave_acesso', ''),
                'codigo_verificacao': resultado.get('nsu_recepcao', ''),
                'numero_rps': numero_dps,
                'xml_nfse': resultado.get('xml_dps', ''),
                'xml_dps_assinado': resultado.get('xml_dps', ''),
                'resposta_adn': resultado.get('resposta_adn_raw', ''),
                'data_emissao': None,
            }
            _salvar_nfse_emitida(pagamento, config, resultado_padrao, tomador_nome, tomador_cpf_cnpj, tomador_email, descricao, valor)
            _enviar_email_nfse(config, tomador_email, tomador_nome, resultado_padrao, valor, descricao)
            return resultado_padrao
        else:
            error_msg = resultado.get('error', 'Erro desconhecido')
            erros = resultado.get('erros', [])
            if erros:
                error_msg += ' | ' + '; '.join(
                    f"[{e.get('Codigo', '')}] {e.get('Descricao', '')}" if isinstance(e, dict) else str(e)
                    for e in erros
                )
            logger.warning('NFS-e Nacional falhou: %s', error_msg)
            return {'success': False, 'error': error_msg}

    except Exception as e:
        logger.exception('Erro ao emitir NFS-e assinatura via Nacional: %s', e)
        return {'success': False, 'error': str(e)}


def _salvar_nfse_emitida(pagamento, config, resultado, tomador_nome, tomador_cpf_cnpj, tomador_email, descricao, valor):
    """Salva registro da NFS-e emitida no banco."""
    try:
        from superadmin.models import NFSeEmitida

        valor_dec = Decimal(str(valor))
        aliquota = Decimal(str(config.aliquota_iss))
        valor_iss = (valor_dec * aliquota / 100).quantize(Decimal('0.01'))

        NFSeEmitida.objects.create(
            loja=pagamento.loja,
            pagamento=pagamento,
            numero_nf=resultado.get('numero_nf', ''),
            codigo_verificacao=resultado.get('codigo_verificacao', ''),
            numero_rps=resultado.get('numero_rps', 0),
            serie_rps=config.nacional_serie_dps or '900',
            provedor='nacional',
            status='emitida',
            valor=valor_dec,
            aliquota_iss=aliquota,
            valor_iss=valor_iss,
            tomador_nome=tomador_nome,
            tomador_cpf_cnpj=tomador_cpf_cnpj,
            tomador_email=tomador_email,
            descricao_servico=descricao[:500],
            xml_nfse=resultado.get('xml_nfse', ''),
            xml_dps_assinado=resultado.get('xml_dps_assinado', ''),
            resposta_adn=resultado.get('resposta_adn', ''),
            asaas_payment_id=pagamento.asaas_payment_id or '',
            data_emissao=resultado.get('data_emissao'),
        )
        logger.info('NFSeEmitida salva: %s, loja %s', resultado.get('numero_nf'), pagamento.loja.slug)
    except Exception as e:
        logger.warning('Erro ao salvar NFSeEmitida: %s', e)


def _enviar_email_nfse(config, tomador_email, tomador_nome, resultado, valor, descricao):
    """Envia email com dados da NFS-e emitida para a loja."""
    if not tomador_email:
        return
    try:
        from django.core.mail import EmailMessage
        from django.conf import settings

        numero_nf = resultado.get('numero_nf', '')
        prestador = config.prestador_razao_social or 'LWK Sistemas'

        assunto = f'Nota Fiscal de Serviço - {prestador}'
        corpo = (
            f'Olá {tomador_nome}!\n\n'
            f'A nota fiscal referente à sua assinatura foi emitida.\n\n'
            f'📋 DADOS DA NOTA FISCAL:\n'
            f'• Chave de Acesso: {numero_nf}\n'
            f'• Prestador: {prestador}\n'
            f'• CNPJ: {config.prestador_cnpj}\n'
            f'• Valor: R$ {valor:.2f}\n'
            f'• Descrição: {descricao}\n\n'
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
            email.attach(f'nfse_{numero_nf[:20]}.xml', xml_content.encode('utf-8'), 'application/xml')

        email.send(fail_silently=True)
        logger.info('Email NFS-e enviado para %s', tomador_email)
    except Exception as e:
        logger.warning('Erro ao enviar email NFS-e: %s', e)
