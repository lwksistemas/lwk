"""Resolução de XML da NFS-e (consulta ISSNet ou reconstrução a partir do registro)."""
from __future__ import annotations

import logging
import re
from decimal import Decimal
from typing import Any
from xml.sax.saxutils import escape as xml_escape

from nfse_integration.issnet_constants import NS_NFSE
from nfse_integration.issnet_xml_builder import somente_digitos

logger = logging.getLogger(__name__)


def nfse_precisa_buscar_xml(nfse: Any) -> bool:
    """True quando a nota ISSNet emitida não tem XML gravado."""
    if (getattr(nfse, 'xml_nfse', '') or '').strip() or (getattr(nfse, 'xml_rps', '') or '').strip():
        return False
    if (getattr(nfse, 'provedor', '') or '').strip().lower() != 'issnet':
        return False
    return (getattr(nfse, 'status', '') or '') in ('emitida', 'cancelada')


def gerar_xml_nfse_reconstruido(nfse: Any, loja: Any) -> str:
    """Monta CompNfse ABRASF com os dados já salvos no CRM (fallback quando o ISSNet não devolve XML)."""
    cnpj_prest = somente_digitos(getattr(loja, 'cpf_cnpj', '') or '')
    im_prest = somente_digitos(getattr(loja, 'inscricao_municipal', '') or '')
    razao_prest = xml_escape((getattr(loja, 'nome', '') or '')[:200])

    tom_doc = somente_digitos(getattr(nfse, 'tomador_cpf_cnpj', '') or '')
    if len(tom_doc) == 14:
        tom_doc_xml = f'<Cnpj>{tom_doc}</Cnpj>'
    elif len(tom_doc) == 11:
        tom_doc_xml = f'<Cpf>{tom_doc}</Cpf>'
    else:
        tom_doc_xml = ''

    dt = ''
    if getattr(nfse, 'data_emissao', None):
        dt = nfse.data_emissao.isoformat()

    valor = f'{Decimal(str(getattr(nfse, "valor", 0) or 0)):.2f}'
    valor_iss = f'{Decimal(str(getattr(nfse, "valor_iss", 0) or 0)):.2f}'
    aliq = f'{Decimal(str(getattr(nfse, "aliquota_iss", 0) or 0)):.2f}'

    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!-- XML reconstruido pelo LWK Sistemas; webservice ISSNet nao retornou o arquivo -->\n'
        f'<CompNfse xmlns="{NS_NFSE}">\n'
        '  <Nfse>\n'
        '    <InfNfse>\n'
        f'      <Numero>{xml_escape(str(getattr(nfse, "numero_nf", "") or ""))}</Numero>\n'
        f'      <CodigoVerificacao>{xml_escape(str(getattr(nfse, "codigo_verificacao", "") or ""))}</CodigoVerificacao>\n'
        f'      <DataEmissao>{xml_escape(dt)}</DataEmissao>\n'
        '      <IdentificacaoRps>\n'
        f'        <Numero>{int(getattr(nfse, "numero_rps", 0) or 0)}</Numero>\n'
        '      </IdentificacaoRps>\n'
        '      <PrestadorServico>\n'
        '        <IdentificacaoPrestador>\n'
        f'          <CpfCnpj><Cnpj>{cnpj_prest}</Cnpj></CpfCnpj>\n'
        f'          <InscricaoMunicipal>{im_prest}</InscricaoMunicipal>\n'
        '        </IdentificacaoPrestador>\n'
        f'        <RazaoSocial>{razao_prest}</RazaoSocial>\n'
        '      </PrestadorServico>\n'
        '      <Servico>\n'
        '        <Valores>\n'
        f'          <ValorServicos>{valor}</ValorServicos>\n'
        f'          <ValorIss>{valor_iss}</ValorIss>\n'
        f'          <Aliquota>{aliq}</Aliquota>\n'
        '        </Valores>\n'
        f'        <Discriminacao>{xml_escape(str(getattr(nfse, "servico_descricao", "") or "")[:500])}</Discriminacao>\n'
        '      </Servico>\n'
        '      <TomadorServico>\n'
        '        <IdentificacaoTomador>\n'
        f'          <CpfCnpj>{tom_doc_xml}</CpfCnpj>\n'
        '        </IdentificacaoTomador>\n'
        f'        <RazaoSocial>{xml_escape(str(getattr(nfse, "tomador_nome", "") or "")[:200])}</RazaoSocial>\n'
        '      </TomadorServico>\n'
        '    </InfNfse>\n'
        '  </Nfse>\n'
        '</CompNfse>\n'
    )


def _tentar_buscar_xml_issnet(nfse: Any, loja: Any, loja_id: int) -> str:
    from nfse_integration.loja_nfse_api import (
        _consultar_nfse_issnet_por_numero,
        _consultar_nfse_issnet_por_rps,
        _resolver_config_nfse_loja,
    )

    cfg = _resolver_config_nfse_loja(loja_id)
    numero_rps = int(getattr(nfse, 'numero_rps', 0) or 0)
    numero_nf = str(getattr(nfse, 'numero_nf', '') or '').strip()

    if numero_rps > 0:
        parsed, _err = _consultar_nfse_issnet_por_rps(cfg, loja, numero_rps)
        xml = (parsed or {}).get('xml_nfse') or ''
        if xml.strip() and re.search(r'<\s*InfNfse\b', xml, re.I):
            return xml.strip()

    if numero_nf and not numero_nf.startswith('FALHA-'):
        parsed, _err = _consultar_nfse_issnet_por_numero(cfg, loja, numero_nf)
        xml = (parsed or {}).get('xml_nfse') or ''
        if xml.strip() and re.search(r'<\s*InfNfse\b', xml, re.I):
            return xml.strip()

    return ''


def resolver_xml_nfse_loja(
    nfse: Any,
    loja: Any,
    loja_id: int,
    *,
    persistir: bool = True,
) -> str:
    """
    Retorna XML da NFS-e: campo salvo, consulta ISSNet ou reconstrução a partir do registro.
    """
    existente = (getattr(nfse, 'xml_nfse', '') or getattr(nfse, 'xml_rps', '') or '').strip()
    if existente:
        return existente

    xml_issnet = ''
    if nfse_precisa_buscar_xml(nfse):
        try:
            xml_issnet = _tentar_buscar_xml_issnet(nfse, loja, loja_id)
        except Exception:
            logger.exception('Falha ao consultar XML ISSNet nf_id=%s', getattr(nfse, 'id', None))

    xml_final = xml_issnet
    if not xml_final and nfse_precisa_buscar_xml(nfse):
        xml_final = gerar_xml_nfse_reconstruido(nfse, loja)
        logger.info(
            'XML NFS-e reconstruido nf=%s loja_id=%s (ISSNet sem retorno)',
            getattr(nfse, 'numero_nf', ''),
            loja_id,
        )

    if xml_final and persistir and not (getattr(nfse, 'xml_nfse', '') or '').strip():
        nfse.xml_nfse = xml_final
        nfse.save(update_fields=['xml_nfse'])

    return xml_final
