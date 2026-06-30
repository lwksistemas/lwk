"""Montagem de XML ABRASF 2.04 para operações ISSNet."""
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional
from xml.sax.saxutils import escape as xml_escape

from lxml import etree

from nfse_integration.issnet_constants import COD_MUNICIPIO_RP, NS_NFSE

logger = logging.getLogger(__name__)


@dataclass
class IssnetEmissaoOpts:
    """Flags de tributação usadas na montagem do EnviarLoteRpsEnvio."""

    numero_lote_config: int = 0
    regime_especial: str = '0'
    optante_simples: bool = True
    incentivador_cultural: bool = False


def somente_digitos(texto: str) -> str:
    return re.sub(r'\D', '', texto or '')


def normalizar_item_lista_servico_abrasf(codigo: Optional[str]) -> str:
    raw = (codigo or '').strip()
    if re.fullmatch(r'\d{2}\.\d{2}', raw):
        return raw
    digits = somente_digitos(raw)
    if len(digits) >= 4:
        return f'{digits[0:2]}.{digits[2:4]}'
    return '14.01'


def codigo_tributacao_municipio_xml(
    raw_codigo: Optional[str], item_lista_abrasf: str
) -> str:
    raw = (raw_codigo or '').strip()
    digits = somente_digitos(raw)
    if len(digits) >= 5:
        return digits[:20]
    if len(digits) == 4:
        return digits
    if re.fullmatch(r'\d{2}\.\d{2}', raw):
        return digits[:20] if digits else raw.replace('.', '')
    fb = somente_digitos(item_lista_abrasf)
    return (fb[:20] if fb else '1401')


def xml_envio_para_raiz_sincrono_sem_assinar(xml_envio: str) -> str:
    s = (xml_envio or '').strip()
    if 'EnviarLoteRpsSincronoEnvio' in s:
        return s
    s = s.replace(
        f'<EnviarLoteRpsEnvio xmlns="{NS_NFSE}">',
        f'<EnviarLoteRpsSincronoEnvio xmlns="{NS_NFSE}">',
        1,
    )
    s = s.replace('</EnviarLoteRpsEnvio>', '</EnviarLoteRpsSincronoEnvio>', 1)
    return s


def issnet_erro_parece_negocio_abrasf(erro: str) -> bool:
    err = (erro or '').strip()
    if re.search(r'\[[A-Za-z]?\d+\]', err):
        return True
    if 'NFS-e nao encontrada na resposta' in err:
        return True
    return False


def extrair_protocolo_lote(xml_abrasf: str) -> Optional[str]:
    if not (xml_abrasf or '').strip():
        return None
    try:
        root = etree.fromstring(
            xml_abrasf.encode('utf-8') if isinstance(xml_abrasf, str) else xml_abrasf
        )
        for el in root.iter():
            if etree.QName(el.tag).localname == 'Protocolo':
                t = (el.text or '').strip()
                if t:
                    return t
    except Exception:
        return None
    return None


def construir_xml_enviar_lote_rps(
    *,
    prestador_cnpj: str,
    prestador_inscricao_municipal: str,
    tomador_cpf_cnpj: str,
    tomador_nome: str,
    tomador_endereco: Dict[str, str],
    servico_codigo: str,
    servico_descricao: str,
    valor_servicos: Decimal,
    aliquota_iss: Decimal,
    numero_rps: int,
    serie_rps: str,
    tipo_rps: int,
    data_emissao: datetime,
    codigo_cnae: Optional[str] = None,
    item_lista_servico: Optional[str] = None,
    codigo_tributacao_municipio: Optional[str] = None,
    opts: Optional[IssnetEmissaoOpts] = None,
) -> str:
    """Monta EnviarLoteRpsEnvio (ABRASF 2.04) para RecepcionarLoteRps."""
    cfg = opts or IssnetEmissaoOpts()
    cnpj_prest = somente_digitos(prestador_cnpj)
    doc_tomador = somente_digitos(tomador_cpf_cnpj)

    valor = Decimal(str(valor_servicos))
    aliquota = Decimal(str(aliquota_iss))
    valor_iss = (valor * aliquota / 100).quantize(Decimal('0.01'))

    ns = NS_NFSE
    root = etree.Element('{%s}EnviarLoteRpsEnvio' % ns, nsmap={None: ns})

    lote = etree.SubElement(root, '{%s}LoteRps' % ns, versao='2.04')
    nlote_cfg = int(cfg.numero_lote_config or 0)
    numero_lote = nlote_cfg if nlote_cfg > 0 else int(numero_rps)
    etree.SubElement(lote, '{%s}NumeroLote' % ns).text = str(numero_lote)

    prest_lote = etree.SubElement(lote, '{%s}Prestador' % ns)
    cpf_cnpj_pl = etree.SubElement(prest_lote, '{%s}CpfCnpj' % ns)
    etree.SubElement(cpf_cnpj_pl, '{%s}Cnpj' % ns).text = cnpj_prest
    etree.SubElement(prest_lote, '{%s}InscricaoMunicipal' % ns).text = prestador_inscricao_municipal

    etree.SubElement(lote, '{%s}QuantidadeRps' % ns).text = '1'

    lista = etree.SubElement(lote, '{%s}ListaRps' % ns)
    rps_el = etree.SubElement(lista, '{%s}Rps' % ns)
    inf = etree.SubElement(
        rps_el, '{%s}InfDeclaracaoPrestacaoServico' % ns, Id=f'rps{numero_rps}'
    )

    rps_inner = etree.SubElement(inf, '{%s}Rps' % ns)
    id_rps = etree.SubElement(rps_inner, '{%s}IdentificacaoRps' % ns)
    etree.SubElement(id_rps, '{%s}Numero' % ns).text = str(numero_rps)
    etree.SubElement(id_rps, '{%s}Serie' % ns).text = serie_rps
    etree.SubElement(id_rps, '{%s}Tipo' % ns).text = str(tipo_rps)
    etree.SubElement(rps_inner, '{%s}DataEmissao' % ns).text = data_emissao.strftime('%Y-%m-%d')
    etree.SubElement(rps_inner, '{%s}Status' % ns).text = '1'

    etree.SubElement(inf, '{%s}Competencia' % ns).text = data_emissao.strftime('%Y-%m-%d')

    servico = etree.SubElement(inf, '{%s}Servico' % ns)
    valores = etree.SubElement(servico, '{%s}Valores' % ns)
    etree.SubElement(valores, '{%s}ValorServicos' % ns).text = f'{valor:.2f}'
    etree.SubElement(valores, '{%s}ValorDeducoes' % ns).text = '0.00'
    etree.SubElement(valores, '{%s}ValorPis' % ns).text = '0.00'
    etree.SubElement(valores, '{%s}ValorCofins' % ns).text = '0.00'
    etree.SubElement(valores, '{%s}ValorInss' % ns).text = '0.00'
    etree.SubElement(valores, '{%s}ValorIr' % ns).text = '0.00'
    etree.SubElement(valores, '{%s}ValorCsll' % ns).text = '0.00'
    etree.SubElement(valores, '{%s}OutrasRetencoes' % ns).text = '0.00'
    etree.SubElement(valores, '{%s}ValTotTributos' % ns).text = '0.00'
    etree.SubElement(valores, '{%s}ValorIss' % ns).text = f'{valor_iss:.2f}'
    etree.SubElement(valores, '{%s}Aliquota' % ns).text = f'{aliquota:.2f}'
    etree.SubElement(valores, '{%s}DescontoIncondicionado' % ns).text = '0.00'
    etree.SubElement(valores, '{%s}DescontoCondicionado' % ns).text = '0.00'

    etree.SubElement(servico, '{%s}IssRetido' % ns).text = '2'
    if item_lista_servico and str(item_lista_servico).strip():
        item_lista = normalizar_item_lista_servico_abrasf(item_lista_servico)
    else:
        item_lista = normalizar_item_lista_servico_abrasf(servico_codigo)
    trib_override = somente_digitos(codigo_tributacao_municipio or '')
    if trib_override:
        cod_tributacao = trib_override[:20]
    else:
        cod_tributacao = codigo_tributacao_municipio_xml(servico_codigo, item_lista)
    if (servico_codigo or '').strip() and (
        (servico_codigo or '').strip() != item_lista
        or somente_digitos(servico_codigo or '') != cod_tributacao
    ):
        logger.info(
            'ISSNet codigo servico: config %r -> ItemListaServico %r, '
            'CodigoTributacaoMunicipio %r',
            servico_codigo,
            item_lista,
            cod_tributacao,
        )
    etree.SubElement(servico, '{%s}ItemListaServico' % ns).text = item_lista
    cnae_digits = somente_digitos(codigo_cnae or '')
    if cnae_digits:
        etree.SubElement(servico, '{%s}CodigoCnae' % ns).text = cnae_digits
    etree.SubElement(servico, '{%s}CodigoTributacaoMunicipio' % ns).text = cod_tributacao
    etree.SubElement(servico, '{%s}Discriminacao' % ns).text = servico_descricao
    etree.SubElement(servico, '{%s}CodigoMunicipio' % ns).text = COD_MUNICIPIO_RP
    etree.SubElement(servico, '{%s}ExigibilidadeISS' % ns).text = '1'
    etree.SubElement(servico, '{%s}MunicipioIncidencia' % ns).text = COD_MUNICIPIO_RP

    prestador = etree.SubElement(inf, '{%s}Prestador' % ns)
    cpf_cnpj_prest = etree.SubElement(prestador, '{%s}CpfCnpj' % ns)
    etree.SubElement(cpf_cnpj_prest, '{%s}Cnpj' % ns).text = cnpj_prest
    etree.SubElement(prestador, '{%s}InscricaoMunicipal' % ns).text = prestador_inscricao_municipal

    tomador = etree.SubElement(inf, '{%s}TomadorServico' % ns)
    id_tom = etree.SubElement(tomador, '{%s}IdentificacaoTomador' % ns)
    cpf_cnpj_tom = etree.SubElement(id_tom, '{%s}CpfCnpj' % ns)
    if len(doc_tomador) == 11:
        etree.SubElement(cpf_cnpj_tom, '{%s}Cpf' % ns).text = doc_tomador
    else:
        etree.SubElement(cpf_cnpj_tom, '{%s}Cnpj' % ns).text = doc_tomador
    etree.SubElement(tomador, '{%s}RazaoSocial' % ns).text = tomador_nome

    end = etree.SubElement(tomador, '{%s}Endereco' % ns)
    etree.SubElement(end, '{%s}Endereco' % ns).text = (
        (tomador_endereco.get('logradouro') or '').strip() or 'Nao informado'
    )
    from nfse_integration.nfse_geo import normalizar_numero_complemento_endereco

    numero_tomador, _ = normalizar_numero_complemento_endereco(
        (tomador_endereco.get('numero') or '').strip(),
    )
    etree.SubElement(end, '{%s}Numero' % ns).text = numero_tomador or 'S/N'
    compl = (tomador_endereco.get('complemento') or '').strip()
    if compl:
        etree.SubElement(end, '{%s}Complemento' % ns).text = compl
    bairro = (tomador_endereco.get('bairro') or '').strip() or 'Nao informado'
    etree.SubElement(end, '{%s}Bairro' % ns).text = bairro[:60]
    cod_mun_tomador = (tomador_endereco.get('codigo_municipio') or '').strip()
    if not cod_mun_tomador:
        from nfse_integration.nfse_geo import buscar_codigo_ibge_por_cep

        cod_mun_tomador = buscar_codigo_ibge_por_cep(tomador_endereco.get('cep', ''))
    if not cod_mun_tomador:
        cod_mun_tomador = COD_MUNICIPIO_RP
    etree.SubElement(end, '{%s}CodigoMunicipio' % ns).text = cod_mun_tomador
    etree.SubElement(end, '{%s}Uf' % ns).text = (
        (tomador_endereco.get('uf') or 'SP').strip()[:2] or 'SP'
    )
    cep = somente_digitos(tomador_endereco.get('cep', ''))[:8]
    if len(cep) != 8:
        cep = '00000000'
    etree.SubElement(end, '{%s}Cep' % ns).text = cep

    tomador_email = (tomador_endereco.get('email') or '').strip()
    tomador_telefone = somente_digitos(tomador_endereco.get('telefone', ''))[:11]
    if tomador_email or tomador_telefone:
        contato = etree.SubElement(tomador, '{%s}Contato' % ns)
        if tomador_telefone:
            etree.SubElement(contato, '{%s}Telefone' % ns).text = tomador_telefone
        if tomador_email:
            etree.SubElement(contato, '{%s}Email' % ns).text = tomador_email[:80]

    regime = (cfg.regime_especial or '').strip()
    if regime and regime != '0':
        etree.SubElement(inf, '{%s}RegimeEspecialTributacao' % ns).text = regime
    optante = '1' if cfg.optante_simples else '2'
    etree.SubElement(inf, '{%s}OptanteSimplesNacional' % ns).text = optante
    incentivo = '1' if cfg.incentivador_cultural else '2'
    etree.SubElement(inf, '{%s}IncentivoFiscal' % ns).text = incentivo

    xml_str = etree.tostring(root, encoding='unicode', pretty_print=False)
    logger.info(
        'XML EnviarLoteRpsEnvio construido: RPS %s serie %r lote %s, Valor R$ %s',
        numero_rps,
        serie_rps,
        numero_lote,
        valor,
    )
    return xml_str


def construir_xml_consultar_lote_rps(
    protocolo: str,
    prestador_cnpj: str,
    prestador_inscricao_municipal: str,
) -> str:
    cnpj = somente_digitos(prestador_cnpj)
    im = (prestador_inscricao_municipal or '').strip()
    return (
        f'<ConsultarLoteRpsEnvio xmlns="{NS_NFSE}">'
        f'<Prestador><CpfCnpj><Cnpj>{cnpj}</Cnpj></CpfCnpj>'
        f'<InscricaoMunicipal>{xml_escape(im)}</InscricaoMunicipal></Prestador>'
        f'<Protocolo>{xml_escape((protocolo or "").strip())}</Protocolo>'
        f'</ConsultarLoteRpsEnvio>'
    )


def construir_xml_consultar_url_nfse(
    numero_nf: str,
    prestador_cnpj: str,
    inscricao_municipal: str,
) -> str:
    cnpj = somente_digitos(prestador_cnpj)
    im = (inscricao_municipal or '').strip()
    return (
        f'<ConsultarUrlNfseEnvio xmlns="{NS_NFSE}">'
        f'<Pedido>'
        f'<Prestador>'
        f'<CpfCnpj><Cnpj>{cnpj}</Cnpj></CpfCnpj>'
        f'<InscricaoMunicipal>{xml_escape(im)}</InscricaoMunicipal>'
        f'</Prestador>'
        f'<NumeroNfse>{xml_escape(str(numero_nf))}</NumeroNfse>'
        f'<Pagina>1</Pagina>'
        f'</Pedido>'
        f'</ConsultarUrlNfseEnvio>'
    )


def construir_xml_consultar_nfse_por_rps(
    *,
    numero_rps: int,
    serie_rps: str,
    tipo_rps: str,
    prestador_cnpj: str,
    inscricao_municipal: str,
) -> str:
    cnpj_digits = somente_digitos(prestador_cnpj)
    im = (inscricao_municipal or '').strip()
    serie = (serie_rps or '').strip() or '1'
    ns = NS_NFSE
    root = etree.Element('{%s}ConsultarNfseRpsEnvio' % ns, nsmap={None: ns})
    id_rps = etree.SubElement(root, '{%s}IdentificacaoRps' % ns)
    etree.SubElement(id_rps, '{%s}Numero' % ns).text = str(int(numero_rps))
    etree.SubElement(id_rps, '{%s}Serie' % ns).text = serie
    etree.SubElement(id_rps, '{%s}Tipo' % ns).text = str(int(tipo_rps or 1))
    prest = etree.SubElement(root, '{%s}Prestador' % ns)
    cpf_cnpj = etree.SubElement(prest, '{%s}CpfCnpj' % ns)
    etree.SubElement(cpf_cnpj, '{%s}Cnpj' % ns).text = cnpj_digits
    if im:
        etree.SubElement(prest, '{%s}InscricaoMunicipal' % ns).text = im
    return etree.tostring(root, encoding='unicode')


def _prestador_element(parent, ns: str, cnpj_digits: str, im: str):
    prest = etree.SubElement(parent, '{%s}Prestador' % ns)
    cpf_cnpj = etree.SubElement(prest, '{%s}CpfCnpj' % ns)
    etree.SubElement(cpf_cnpj, '{%s}Cnpj' % ns).text = cnpj_digits
    if (im or '').strip():
        etree.SubElement(prest, '{%s}InscricaoMunicipal' % ns).text = im.strip()


def construir_xml_consultar_nfse_servico_prestado(
    numero_nf: str,
    prestador_cnpj: str,
    inscricao_municipal: str,
) -> str:
    cnpj_digits = somente_digitos(prestador_cnpj)
    im = (inscricao_municipal or '').strip()
    ns = NS_NFSE
    root = etree.Element('{%s}ConsultarNfseServicoPrestadoEnvio' % ns, nsmap={None: ns})
    _prestador_element(root, ns, cnpj_digits, im)
    etree.SubElement(root, '{%s}NumeroNfse' % ns).text = str(int(numero_nf))
    etree.SubElement(root, '{%s}Pagina' % ns).text = '1'
    return etree.tostring(root, encoding='unicode')


def construir_xml_consultar_nfse_por_faixa(
    numero_nf: str,
    prestador_cnpj: str,
    inscricao_municipal: str,
) -> str:
    cnpj_digits = somente_digitos(prestador_cnpj)
    im = (inscricao_municipal or '').strip()
    ns = NS_NFSE
    root = etree.Element('{%s}ConsultarNfsePorFaixaEnvio' % ns, nsmap={None: ns})
    _prestador_element(root, ns, cnpj_digits, im)
    faixa = etree.SubElement(root, '{%s}Faixa' % ns)
    n = str(int(numero_nf))
    etree.SubElement(faixa, '{%s}NumeroNfseInicial' % ns).text = n
    etree.SubElement(faixa, '{%s}NumeroNfseFinal' % ns).text = n
    etree.SubElement(root, '{%s}Pagina' % ns).text = '1'
    return etree.tostring(root, encoding='unicode')


def construir_xml_consultar_nfse_por_rps_legado(numero_nf: str, prestador_cnpj: str) -> str:
    return (
        f'<ConsultarNfseRpsEnvio xmlns="{NS_NFSE}">'
        f'<IdentificacaoRps>'
        f'<Numero>{numero_nf}</Numero>'
        f'<Serie>E</Serie>'
        f'<Tipo>1</Tipo>'
        f'</IdentificacaoRps>'
        f'<Prestador>'
        f'<CpfCnpj><Cnpj>{prestador_cnpj}</Cnpj></CpfCnpj>'
        f'</Prestador>'
        f'</ConsultarNfseRpsEnvio>'
    )


def construir_xml_cancelar_nfse(
    numero_nf: str,
    prestador_cnpj: str,
    inscricao_municipal: str,
    codigo_cancelamento: str = '1',
    *,
    inf_pedido_id: Optional[str] = None,
) -> str:
    """
    Monta CancelarNfseEnvio.
    Sem inf_pedido_id: InfPedidoCancelamento Id=s01 (assinatura no Pedido).
    Com inf_pedido_id: assinatura no InfPedidoCancelamento (ex. cancel144).
    """
    cnpj_digits = somente_digitos(prestador_cnpj)
    im = (inscricao_municipal or '').strip()
    inf_id = (inf_pedido_id or 's01').strip()
    return (
        f'<CancelarNfseEnvio xmlns="{NS_NFSE}">'
        f'<Pedido>'
        f'<InfPedidoCancelamento Id="{xml_escape(inf_id)}">'
        f'<IdentificacaoNfse>'
        f'<Numero>{numero_nf}</Numero>'
        f'<CpfCnpj><Cnpj>{cnpj_digits}</Cnpj></CpfCnpj>'
        f'<InscricaoMunicipal>{im}</InscricaoMunicipal>'
        f'<CodigoMunicipio>{COD_MUNICIPIO_RP}</CodigoMunicipio>'
        f'</IdentificacaoNfse>'
        f'<CodigoCancelamento>{codigo_cancelamento}</CodigoCancelamento>'
        f'</InfPedidoCancelamento>'
        f'</Pedido>'
        f'</CancelarNfseEnvio>'
    )
