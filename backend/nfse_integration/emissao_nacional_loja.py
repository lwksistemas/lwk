"""Emissao de NFS-e via ADN Nacional (loja/CRM)."""
import logging
import re
from decimal import Decimal
from decimal import ROUND_HALF_UP
from typing import Any, Callable, Dict, Optional

from django.utils import timezone

from nfse_integration.nfse_geo import buscar_codigo_ibge_por_cep
from nfse_integration.persistencia_nfse_loja import gerar_proximo_numero_rps, salvar_nfse_emitida

logger = logging.getLogger(__name__)


def emitir_via_nacional_loja(
    loja: Any,
    config: Any,
    *,
    tomador_cpf_cnpj: str,
    tomador_nome: str,
    tomador_email: str,
    tomador_endereco: Dict[str, str],
    servico_descricao: str,
    valor_servicos: Decimal,
    enviar_email: bool,
    enviar_email_fn: Callable[..., None],
    codigo_cnae_override: Optional[str] = None,
    codigo_servico_override: Optional[str] = None,
) -> Dict[str, Any]:
    """Emite NFS-e via ADN Nacional usando certificado da loja."""
    try:
        from nfse_integration.nacional import NacionalClient

        cert_data = (
            getattr(config, 'nacional_certificado', None)
            or getattr(config, 'issnet_certificado', None)
        )
        senha_cert = (
            getattr(config, 'nacional_senha_certificado', '')
            or getattr(config, 'issnet_senha_certificado', '')
        )
        codigo_municipio = getattr(config, 'nacional_codigo_municipio', '') or ''

        if not cert_data:
            return {'success': False, 'error': 'Certificado digital não configurado'}
        if not senha_cert:
            return {'success': False, 'error': 'Senha do certificado não configurada'}
        if not codigo_municipio:
            cep_loja = getattr(loja, 'cep', '') or ''
            codigo_municipio = buscar_codigo_ibge_por_cep(cep_loja)
            if not codigo_municipio:
                return {'success': False, 'error': 'Código IBGE do município não configurado'}

        numero_dps = gerar_proximo_numero_rps(loja.id, config)
        ambiente = getattr(config, 'nacional_ambiente', 'homologacao') or 'homologacao'
        client = NacionalClient(
            pfx_bytes=bytes(cert_data),
            senha_pfx=senha_cert,
            ambiente=ambiente,
        )

        cep_tomador = (tomador_endereco.get('cep') or '').strip()
        codigo_municipio_tomador = (tomador_endereco.get('codigo_municipio') or '').strip()
        if not codigo_municipio_tomador and cep_tomador:
            codigo_municipio_tomador = buscar_codigo_ibge_por_cep(cep_tomador)
        tomador_endereco_final = {**tomador_endereco, 'codigo_municipio': codigo_municipio_tomador}

        cnpj_prestador = re.sub(r'\D', '', loja.cpf_cnpj or '')
        im_prestador = (
            getattr(config, 'inscricao_municipal', '')
            or getattr(loja, 'inscricao_municipal', '')
            or ''
        )
        codigo_servico_final = (
            codigo_servico_override
            or getattr(config, 'codigo_servico_municipal', '14.01')
            or '14.01'
        )
        codigo_cnae_final = codigo_cnae_override or (getattr(config, 'codigo_cnae', '') or '').strip()
        aliquota = Decimal(str(getattr(config, 'aliquota_iss', Decimal('2.00')) or 0))
        valor_iss = (Decimal(str(valor_servicos)) * aliquota / Decimal('100')).quantize(
            Decimal('0.01'),
            rounding=ROUND_HALF_UP,
        )
        serie_dps = getattr(config, 'nacional_serie_dps', '900') or '900'

        resultado = client.emitir_nfse(
            numero_dps=numero_dps,
            serie_dps=serie_dps,
            codigo_municipio_prestador=codigo_municipio,
            prestador_cnpj=cnpj_prestador,
            prestador_inscricao_municipal=im_prestador,
            prestador_razao_social=loja.nome or '',
            prestador_email=getattr(loja, 'email', '') or '',
            tomador_cpf_cnpj=tomador_cpf_cnpj,
            tomador_nome=tomador_nome,
            tomador_endereco=tomador_endereco_final,
            tomador_email=tomador_email,
            codigo_servico=codigo_servico_final,
            descricao_servico=(
                servico_descricao
                or getattr(config, 'descricao_servico_padrao', '')
                or 'Serviço prestado'
            ),
            codigo_cnae=codigo_cnae_final,
            codigo_municipio_incidencia=codigo_municipio,
            valor_servicos=valor_servicos,
            aliquota_iss=aliquota,
            iss_retido=False,
            optante_simples_nacional=getattr(config, 'optante_simples_nacional', True),
            incentivador_cultural=getattr(config, 'incentivador_cultural', False),
        )

        if resultado.get('success'):
            resultado_final = {
                'success': True,
                'numero_nf': resultado.get('chave_acesso', ''),
                'codigo_verificacao': resultado.get('nsu_recepcao', ''),
                'numero_rps': numero_dps,
                'data_emissao': timezone.now(),
                'valor': float(valor_servicos),
                'aliquota_iss': float(aliquota),
                'valor_iss': float(valor_iss),
                'xml_nfse': resultado.get('xml_dps', ''),
                'pdf_url': '',
                'tomador_nome': tomador_nome,
                'tomador_cpf_cnpj': tomador_cpf_cnpj,
                'servico_descricao': servico_descricao,
            }
            salvar_nfse_emitida(loja.id, resultado_final, tomador_email, provedor='nacional')
            if enviar_email and tomador_email:
                enviar_email_fn(
                    tomador_email=tomador_email,
                    tomador_nome=tomador_nome,
                    numero_nf=resultado_final['numero_nf'],
                    valor=valor_servicos,
                    descricao=servico_descricao,
                )
            return resultado_final

        error_msg = resultado.get('error', 'Erro desconhecido')
        erros = resultado.get('erros', [])
        if erros:
            error_msg += ' | ' + '; '.join(
                f"[{e.get('Codigo', '')}] {e.get('Descricao', '')}" if isinstance(e, dict) else str(e)
                for e in erros
            )
        return {'success': False, 'error': error_msg, 'numero_rps': numero_dps}
    except Exception as exc:
        logger.exception('Erro ao emitir via Nacional: %s', exc)
        return {'success': False, 'error': str(exc)}
