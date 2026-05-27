"""Emissao de NFS-e via ISSNet (loja/CRM)."""
import logging
import re
from decimal import Decimal
from typing import Any, Callable, Dict, Optional

from django.utils import timezone

from nfse_integration.issnet_loja import (
    certificado_configurado_loja,
    issnet_client_loja,
    senha_certificado_configurada_loja,
)
from nfse_integration.persistencia_nfse_loja import gerar_proximo_numero_rps, salvar_nfse_emitida

logger = logging.getLogger(__name__)


def emitir_via_issnet_loja(
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
    """Emite NFS-e via WebService ISSNet municipal."""
    try:
        if not certificado_configurado_loja(config):
            return {'success': False, 'error': 'Certificado digital não configurado para ISSNet'}
        if not senha_certificado_configurada_loja(config):
            return {'success': False, 'error': 'Senha do certificado não configurada'}

        cnpj_prestador = re.sub(r'\D', '', loja.cpf_cnpj or '')
        im_prestador = (
            getattr(config, 'inscricao_municipal', '')
            or getattr(loja, 'inscricao_municipal', '')
            or ''
        )
        codigo_servico_final = (
            codigo_servico_override
            or getattr(config, 'codigo_servico_municipal', '1401')
            or '1401'
        )
        codigo_cnae_final = codigo_cnae_override or (getattr(config, 'codigo_cnae', '') or '').strip()
        aliquota = float(getattr(config, 'aliquota_iss', 2.00))

        with issnet_client_loja(config) as client:
            numero_rps = gerar_proximo_numero_rps(loja.id, config)
            resultado = client.emitir_nfse(
                prestador_cnpj=cnpj_prestador,
                prestador_inscricao_municipal=im_prestador,
                prestador_razao_social=loja.nome or '',
                tomador_cpf_cnpj=tomador_cpf_cnpj,
                tomador_nome=tomador_nome,
                tomador_endereco=tomador_endereco,
                servico_codigo=codigo_servico_final,
                servico_descricao=servico_descricao or 'Serviço prestado',
                valor_servicos=Decimal(str(valor_servicos)),
                aliquota_iss=Decimal(str(aliquota)),
                numero_rps=numero_rps,
                serie_rps=getattr(config, 'issnet_serie_rps', '1') or '1',
                codigo_cnae=codigo_cnae_final or None,
            )

        if resultado.get('success'):
            resultado_final = {
                'success': True,
                'numero_nf': resultado.get('numero_nf', ''),
                'codigo_verificacao': resultado.get('codigo_verificacao', ''),
                'numero_rps': numero_rps,
                'data_emissao': timezone.now(),
                'valor': float(valor_servicos),
                'xml_nfse': resultado.get('xml_nfse', ''),
                'pdf_url': resultado.get('link_pdf', ''),
                'tomador_nome': tomador_nome,
                'tomador_cpf_cnpj': tomador_cpf_cnpj,
                'servico_descricao': servico_descricao,
            }
            salvar_nfse_emitida(loja.id, resultado_final, tomador_email, provedor='issnet')
            if enviar_email and tomador_email:
                enviar_email_fn(
                    tomador_email=tomador_email,
                    tomador_nome=tomador_nome,
                    numero_nf=resultado_final['numero_nf'],
                    valor=valor_servicos,
                    descricao=servico_descricao,
                )
            return resultado_final

        return {
            'success': False,
            'error': resultado.get('error', 'Erro ISSNet'),
            'numero_rps': numero_rps,
        }
    except Exception as exc:
        logger.exception('Erro ao emitir via ISSNet: %s', exc)
        return {'success': False, 'error': str(exc)}
