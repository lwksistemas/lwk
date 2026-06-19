"""
Serviço de emissão de NFS-e para assinaturas das lojas.
Emite nota fiscal quando o pagamento da assinatura é confirmado.
Provedor: Nacional (ADN - Padrão Nacional NFS-e).
"""
import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any

from django.utils import timezone

logger = logging.getLogger(__name__)


def _data_emissao_resultado(resultado: dict) -> datetime:
    """Data/hora da emissão a partir da resposta do provedor ou agora."""
    dt = resultado.get('data_emissao')
    return dt if dt else timezone.now()


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

    # Endereço do tomador — cidade/UF/IBGE devem bater com o CEP (ISSNet E058/E061)
    from nfse_integration.nfse_geo import enriquecer_endereco_por_cep

    from nfse_integration.nfse_geo import normalizar_numero_complemento_endereco

    numero_norm, compl_norm = normalizar_numero_complemento_endereco(
        getattr(loja, 'numero', '') or '',
        getattr(loja, 'complemento', '') or '',
    )
    tomador_endereco = {
        'logradouro': getattr(loja, 'logradouro', '') or '',
        'numero': numero_norm or 'S/N',
        'complemento': compl_norm,
        'bairro': getattr(loja, 'bairro', '') or '',
        'cidade': getattr(loja, 'cidade', '') or '',
        'uf': getattr(loja, 'uf', '') or '',
        'cep': getattr(loja, 'cep', '') or '',
        'email': tomador_email,
        'telefone': getattr(loja, 'owner_telefone', '') or '',
    }
    from core.cep_utils import normalizar_cep
    cep_norm = normalizar_cep(tomador_endereco['cep'])
    if cep_norm:
        tomador_endereco['cep'] = cep_norm
        if cep_norm != (getattr(loja, 'cep', '') or ''):
            loja.cep = cep_norm
            loja.save(update_fields=['cep', 'updated_at'])
    if not enriquecer_endereco_por_cep(tomador_endereco):
        msg = (
            f'CEP do tomador inválido ou não localizado ({tomador_endereco.get("cep") or "vazio"}). '
            'Corrija o endereço da loja antes de emitir a NFS-e.'
        )
        logger.warning('NFS-e assinatura: %s (loja=%s)', msg, loja.slug)
        return {'success': False, 'error': msg}

    # Descrição do serviço
    referencia = pagamento.referencia_mes.strftime('%m/%Y') if pagamento.referencia_mes else ''
    descricao = config.descricao_servico_padrao or 'Licenciamento de uso de software SaaS'
    if referencia:
        descricao = f'{descricao} - Ref. {referencia}'
    if loja.nome:
        descricao = f'{descricao} - {loja.nome}'

    if config.provedor_nfse == 'nacional':
        return _emitir_via_nacional(pagamento, config, tomador_cpf_cnpj, tomador_nome, tomador_email, tomador_endereco, descricao, valor)
    elif config.provedor_nfse == 'issnet':
        return _emitir_via_issnet(pagamento, config, tomador_cpf_cnpj, tomador_nome, tomador_email, tomador_endereco, descricao, valor)
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
                'data_emissao': _data_emissao_resultado(resultado),
            }
            nf = _salvar_nfse_emitida(pagamento, config, resultado_padrao, tomador_nome, tomador_cpf_cnpj, tomador_email, descricao, valor)
            _enviar_email_nfse_assinatura(nf, config)
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


def _emitir_via_issnet(
    pagamento,
    config,
    tomador_cpf_cnpj: str,
    tomador_nome: str,
    tomador_email: str,
    tomador_endereco: Dict[str, str],
    descricao: str,
    valor: Decimal,
) -> Dict[str, Any]:
    """Emite NFS-e via WebService ISSNet (municipal)."""
    try:
        from nfse_integration.issnet_client import ISSNetClient
        import re
        import tempfile
        import os

        cert_data = config.issnet_certificado or config.nacional_certificado
        senha_cert = config.issnet_senha_certificado or config.nacional_senha_certificado
        if not cert_data:
            return {'success': False, 'error': 'Certificado digital não configurado'}
        if not senha_cert:
            return {'success': False, 'error': 'Senha do certificado não configurada'}
        if not config.prestador_cnpj:
            return {'success': False, 'error': 'CNPJ do prestador não configurado'}

        from core.encryption import decrypt_value
        senha_cert_plain = decrypt_value(senha_cert)
        senha_ws_plain = decrypt_value(config.issnet_senha or '')

        cnpj_digits = re.sub(r'\D', '', config.prestador_cnpj)
        im = config.prestador_inscricao_municipal or ''

        from nfse_integration.persistencia_nfse_superadmin import (
            gerar_proximo_numero_rps_superadmin,
            sincronizar_contadores_rps_superadmin,
        )
        from nfse_integration.issnet_fiscal_superadmin import fiscal_codes_issnet_superadmin

        numero_rps = gerar_proximo_numero_rps_superadmin(config)
        item_lista, cod_tributacao, cod_cnae, servico_codigo = fiscal_codes_issnet_superadmin(config)

        # Salvar certificado em arquivo temporário (ISSNetClient precisa de path)
        cert_tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pfx', prefix='issnet_auto_')
        cert_tmp.write(bytes(cert_data))
        cert_tmp.close()

        try:
            client = ISSNetClient(
                usuario=decrypt_value(config.issnet_usuario or ''),
                senha=senha_ws_plain,
                certificado_path=cert_tmp.name,
                senha_certificado=senha_cert_plain,
                ambiente=config.nacional_ambiente or 'producao',
            )

            # Configurar flags
            client._optante_simples = config.optante_simples_nacional
            client._incentivador_cultural = getattr(config, 'incentivador_cultural', False)
            regime = str(getattr(config, 'regime_especial_tributacao', '0') or '0').strip()
            client._regime_especial = regime

            resultado = client.emitir_nfse(
                prestador_cnpj=cnpj_digits,
                prestador_inscricao_municipal=im,
                prestador_razao_social=config.prestador_razao_social or '',
                tomador_cpf_cnpj=tomador_cpf_cnpj,
                tomador_nome=tomador_nome,
                tomador_endereco=tomador_endereco,
                servico_codigo=servico_codigo,
                servico_descricao=descricao,
                valor_servicos=float(valor),
                aliquota_iss=float(config.aliquota_iss),
                numero_rps=numero_rps,
                serie_rps=config.serie_rps or 'E',
                codigo_cnae=cod_cnae,
                item_lista_servico=item_lista,
                codigo_tributacao_municipio=cod_tributacao,
            )
        finally:
            try:
                os.unlink(cert_tmp.name)
            except OSError:
                pass

        if resultado.get('success'):
            logger.info(
                'NFS-e ISSNet emitida: NF=%s, tomador=%s, valor=R$%s',
                resultado.get('numero_nf'), tomador_nome, valor,
            )
            resultado_padrao = {
                'success': True,
                'numero_nf': resultado.get('numero_nf', ''),
                'codigo_verificacao': resultado.get('codigo_verificacao', ''),
                'numero_rps': numero_rps,
                'xml_nfse': resultado.get('xml_nfse', ''),
                'data_emissao': _data_emissao_resultado(resultado),
            }
            sincronizar_contadores_rps_superadmin(config, numero_rps)
            nf = _salvar_nfse_emitida_issnet(pagamento, config, resultado_padrao, tomador_nome, tomador_cpf_cnpj, tomador_email, descricao, valor)
            _enviar_email_nfse_assinatura(nf, config)
            return resultado_padrao
        else:
            error_msg = resultado.get('error', 'Erro desconhecido ISSNet')
            sincronizar_contadores_rps_superadmin(config, numero_rps)
            logger.warning('NFS-e ISSNet falhou: %s', error_msg)
            return {'success': False, 'error': error_msg}

    except Exception as e:
        logger.exception('Erro ao emitir NFS-e assinatura via ISSNet: %s', e)
        return {'success': False, 'error': str(e)}


def _salvar_nfse_emitida_issnet(pagamento, config, resultado, tomador_nome, tomador_cpf_cnpj, tomador_email, descricao, valor):
    """Salva registro da NFS-e emitida via ISSNet."""
    try:
        from superadmin.models import NFSeEmitida

        valor_dec = Decimal(str(valor))
        aliquota = Decimal(str(config.aliquota_iss))
        valor_iss = (valor_dec * aliquota / 100).quantize(Decimal('0.01'))

        nf = NFSeEmitida.objects.create(
            loja=pagamento.loja,
            pagamento=pagamento,
            numero_nf=resultado.get('numero_nf', ''),
            codigo_verificacao=resultado.get('codigo_verificacao', ''),
            numero_rps=resultado.get('numero_rps', 0),
            serie_rps=config.serie_rps or 'E',
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
            pdf_url=(resultado.get('pdf_url') or '').strip(),
            asaas_payment_id=pagamento.asaas_payment_id or '',
            data_emissao=_data_emissao_resultado(resultado),
        )
        logger.info('NFSeEmitida ISSNet salva: %s, loja %s', resultado.get('numero_nf'), pagamento.loja.slug)
        return nf
    except Exception as e:
        logger.warning('Erro ao salvar NFSeEmitida ISSNet: %s', e)
        return None


def _salvar_nfse_emitida(pagamento, config, resultado, tomador_nome, tomador_cpf_cnpj, tomador_email, descricao, valor):
    """Salva registro da NFS-e emitida no banco."""
    try:
        from superadmin.models import NFSeEmitida

        valor_dec = Decimal(str(valor))
        aliquota = Decimal(str(config.aliquota_iss))
        valor_iss = (valor_dec * aliquota / 100).quantize(Decimal('0.01'))

        nf = NFSeEmitida.objects.create(
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
            pdf_url=(resultado.get('pdf_url') or '').strip(),
            asaas_payment_id=pagamento.asaas_payment_id or '',
            data_emissao=_data_emissao_resultado(resultado),
        )
        logger.info('NFSeEmitida salva: %s, loja %s', resultado.get('numero_nf'), pagamento.loja.slug)
        return nf
    except Exception as e:
        logger.warning('Erro ao salvar NFSeEmitida: %s', e)
        return None


def _enviar_email_nfse_assinatura(nf, config) -> None:
    """Envia e-mail da NFS-e com link DANFE (mesmo fluxo do reenvio manual)."""
    if not nf or not getattr(nf, 'tomador_email', None):
        return
    try:
        from nfse_integration.superadmin_nfse_api import (
            ReenvioNFSeError,
            reenviar_email_nfse_superadmin,
        )

        reenviar_email_nfse_superadmin(nf, config)
        logger.info('Email NFS-e assinatura enviado para %s (NF %s)', nf.tomador_email, nf.numero_nf)
    except ReenvioNFSeError as e:
        logger.warning('NFS-e assinatura: email não enviado: %s', e.message)
    except Exception as e:
        logger.warning('Erro ao enviar email NFS-e assinatura: %s', e)
