"""Montagem de XML para ISSNet padrão Nacional (Ribeirão Preto).

Reutiliza o `nacional.xml_builder.construir_xml_dps` que já gera o XML da DPS
conforme o XSD oficial (http://www.sped.fazenda.gov.br/nfse).

O ISSNet Nacional recebe via SOAP com o XML DPS dentro de:
  - GerarNfseEnvio > DPS (para emissão síncrona de 1 DPS)
  - EnviarLoteDpsSincronoEnvio > LoteDps > DPS (para lote síncrono)

Endpoint: https://nfse.issnetonline.com.br/wsnfsenacional/ribeiraopreto/nfse.asmx
"""
import json
import logging
import re
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from lxml import etree

from nfse_integration.nacional.constants import NS_NFSE, VERSAO_DPS
from nfse_integration.nacional.xml_builder import construir_xml_dps

logger = logging.getLogger(__name__)

NS_NFSE_NACIONAL = NS_NFSE  # Re-export
# Ribeirão Preto (produção) valida o leiaute v1.01 padrão Nacional.
VERSAO_ISSNET_NACIONAL = "1.01"
# Adiciona cTribMun e cNBS no cServ apenas quando forem informados via parâmetro.
ADICIONAR_EXTRAS_ISSNET = True
INCLUIR_IBSCBS = True
COD_MUNICIPIO_RP = "3543402"


def _carregar_mapeamento() -> tuple[dict[str, str], dict[str, str]]:
    """Carrega mapas cNBS e cIndOp por cTribNac da tabela de correlação nacional."""
    try:
        caminho = Path(__file__).parent / "data" / "nbs_indop_map.json"
        with caminho.open("r", encoding="utf-8") as f:
            dados = json.load(f)
        return dados.get("nbs", {}), dados.get("indop", {})
    except Exception as e:
        logger.warning("Não foi possível carregar nbs_indop_map.json: %s", e)
        return {}, {}


_NBS_POR_CTRIBNAC, _INDOP_POR_CTRIBNAC = _carregar_mapeamento()


def _somente_digitos(texto: str) -> str:
    return re.sub(r"\D", "", texto or "")


def _nbs_por_ctrib_nacional(codigo_tributacao_nacional: str, codigo_nbs: str) -> str:
    """Retorna cNBS válido.

    Quando não informado ou com valor genérico (114011100/104033000),
    busca no mapeamento por cTribNac. O cNBS é opcional, mas passa a
    ser obrigatório quando o bloco IBSCBS está habilitado.
    """
    nbs_informado = _somente_digitos(codigo_nbs or "")
    chave = _somente_digitos(codigo_tributacao_nacional or "")[:6]
    nbs_mapeado = _NBS_POR_CTRIBNAC.get(chave)

    if not nbs_informado:
        return nbs_mapeado or ""
    if nbs_informado in ("114011100", "104033000") and nbs_mapeado:
        return nbs_mapeado
    if len(nbs_informado) == 9:
        return nbs_informado
    return nbs_mapeado or ""


def _indicador_operacao_por_ctrib_nacional(codigo_tributacao_nacional: str, indicador_operacao: str | None) -> str:
    """Retorna cIndOp padrão quando não informado ou genérico."""
    ind_informado = _somente_digitos(indicador_operacao or "")
    if ind_informado and ind_informado != "100301":
        return ind_informado
    chave = _somente_digitos(codigo_tributacao_nacional or "")[:6]
    ind_mapeado = _INDOP_POR_CTRIBNAC.get(chave)
    return ind_mapeado or ind_informado or "100301"


def _construir_dps_issnet(
    *,
    numero_dps: int,
    serie_dps: str,
    codigo_municipio_emissor: str,
    ambiente_str: str,
    cnpj_prest: str,
    im_prest: str,
    prestador_cnpj: str,
    prestador_inscricao_municipal: str,
    prestador_telefone: str,
    prestador_email: str,
    optante_simples_nacional: bool,
    tomador_cpf_cnpj: str,
    tomador_nome: str,
    tomador_endereco: dict[str, str] | None,
    tomador_telefone: str,
    tomador_email: str,
    codigo_municipio_prestacao: str,
    codigo_tributacao_nacional: str,
    codigo_tributacao_municipal: str | None,
    descricao_servico: str,
    codigo_nbs: str,
    valor_servicos: Decimal,
    aliquota_iss: Decimal,
    data_emissao: datetime,
    p_tot_trib_sn: Decimal | None,
    indicador_operacao: str,
    ind_final_ibscbs: str,
    ind_dest_ibscbs: str,
    cst_ibscbs: str,
    cclass_trib_ibscbs: str,
) -> etree._Element:
    """Constrói o elemento <DPS> estendido com os campos exigidos pelo ISSNet Nacional."""
    # O leiaute v1.00 aceito por Ribeirão Preto inclui fone/e-mail no <prest>;
    # o leiaute v1.01 (RT) não os aceita.
    incluir_fone_email_prest = not ADICIONAR_EXTRAS_ISSNET

    xml_dps = construir_xml_dps(
        numero_dps=numero_dps,
        serie_dps=serie_dps,
        codigo_municipio_prestador=codigo_municipio_emissor,
        ambiente=ambiente_str,
        prestador_cnpj=prestador_cnpj,
        prestador_inscricao_municipal=prestador_inscricao_municipal,
        prestador_telefone=prestador_telefone if incluir_fone_email_prest else "",
        prestador_email=prestador_email if incluir_fone_email_prest else "",
        tomador_cpf_cnpj=tomador_cpf_cnpj,
        tomador_nome=tomador_nome,
        tomador_endereco=tomador_endereco,
        tomador_telefone=tomador_telefone,
        tomador_email=tomador_email,
        codigo_servico=codigo_tributacao_nacional or "140100",
        descricao_servico=descricao_servico,
        codigo_municipio_incidencia=codigo_municipio_prestacao or codigo_municipio_emissor,
        valor_servicos=valor_servicos,
        aliquota_iss=aliquota_iss,
        optante_simples_nacional=optante_simples_nacional,
        p_tot_trib_sn=p_tot_trib_sn,
        data_competencia=data_emissao,
        versao_dps=VERSAO_ISSNET_NACIONAL,
        prefixo_nfse=False,
    )

    dps_element = etree.fromstring(xml_dps.encode("utf-8"))

    # Resolve cIndOp padrão pelo mapa nacional quando genérico
    indicador_operacao = _indicador_operacao_por_ctrib_nacional(
        codigo_tributacao_nacional, indicador_operacao
    )

    c_serv = dps_element.find(f".//{{{NS_NFSE}}}cServ")
    if c_serv is not None and ADICIONAR_EXTRAS_ISSNET:
        x_desc = c_serv.find(f"{{{NS_NFSE}}}xDescServ")

        # cTribMun é opcional no XSD, mas alguns municípios/mediadores
        # o exigem. Quando informado pelo usuário, inclui-o após cTribNac
        # e antes de xDescServ; nunca gera valor de fallback.
        cod_trib_mun = _somente_digitos(codigo_tributacao_municipal or "")
        if len(cod_trib_mun) == 3:
            c_trib_mun_el = etree.Element(f"{{{NS_NFSE}}}cTribMun")
            c_trib_mun_el.text = cod_trib_mun
            idx = list(c_serv).index(x_desc) if x_desc is not None else 0
            c_serv.insert(idx, c_trib_mun_el)

        # cNBS faz parte do leiaute v1.01 (RT), sempre após xDescServ (XSD TCCServ).
        c_nbs = _nbs_por_ctrib_nacional(codigo_tributacao_nacional, codigo_nbs)
        if c_nbs:
            c_nbs_el = etree.Element(f"{{{NS_NFSE}}}cNBS")
            c_nbs_el.text = c_nbs
            if x_desc is not None:
                x_desc.addnext(c_nbs_el)
            else:
                c_serv.append(c_nbs_el)

    # IBSCBS é obrigatório para emissão a partir da Reforma Tributária.
    if INCLUIR_IBSCBS and ADICIONAR_EXTRAS_ISSNET:
        inf_dps = dps_element.find(f"{{{NS_NFSE}}}infDPS")
        if inf_dps is not None:
            ibscbs = etree.SubElement(inf_dps, f"{{{NS_NFSE}}}IBSCBS")
            etree.SubElement(ibscbs, f"{{{NS_NFSE}}}finNFSe").text = "0"
            etree.SubElement(ibscbs, f"{{{NS_NFSE}}}indFinal").text = ind_final_ibscbs
            etree.SubElement(ibscbs, f"{{{NS_NFSE}}}cIndOp").text = indicador_operacao
            etree.SubElement(ibscbs, f"{{{NS_NFSE}}}indDest").text = ind_dest_ibscbs

            valores_ibscbs = etree.SubElement(ibscbs, f"{{{NS_NFSE}}}valores")
            trib_ibscbs = etree.SubElement(valores_ibscbs, f"{{{NS_NFSE}}}trib")
            g_ibscbs = etree.SubElement(trib_ibscbs, f"{{{NS_NFSE}}}gIBSCBS")
            etree.SubElement(g_ibscbs, f"{{{NS_NFSE}}}CST").text = cst_ibscbs
            etree.SubElement(g_ibscbs, f"{{{NS_NFSE}}}cClassTrib").text = cclass_trib_ibscbs

    return dps_element


def construir_xml_gerar_nfse_envio(
    *,
    prestador_cnpj: str,
    prestador_inscricao_municipal: str,
    numero_dps: int,
    serie_dps: str = "1",
    data_emissao: datetime | None = None,
    data_competencia: datetime | None = None,
    codigo_municipio_emissor: str = COD_MUNICIPIO_RP,
    ambiente: int = 1,
    prestador_telefone: str = "",
    prestador_email: str = "",
    optante_simples_nacional: bool = True,
    tomador_cpf_cnpj: str = "",
    tomador_nome: str = "",
    tomador_endereco: dict[str, str] | None = None,
    tomador_telefone: str = "",
    tomador_email: str = "",
    codigo_municipio_prestacao: str = "",
    codigo_tributacao_nacional: str = "140100",
    codigo_tributacao_municipal: str | None = None,
    descricao_servico: str = "Serviço prestado",
    codigo_nbs: str = "114011100",
    valor_servicos: Decimal = Decimal("0.00"),
    aliquota_iss: Decimal = Decimal("2.50"),
    valor_iss: Decimal | None = None,
    p_tot_trib_sn: Decimal = Decimal("0.00"),
    # IBSCBS / Reforma Tributária
    indicador_operacao: str = "100301",
    ind_final_ibscbs: str = "0",
    ind_dest_ibscbs: str = "0",
    cst_ibscbs: str = "000",
    cclass_trib_ibscbs: str = "000001",
) -> str:
    """Monta GerarNfseEnvio contendo o DPS estendido para emissão via ISSNet Nacional."""
    if data_emissao is None:
        data_emissao = datetime.now()

    ambiente_str = "homologacao" if ambiente == 2 else "producao"
    cnpj_prest = _somente_digitos(prestador_cnpj)
    im_prest = (prestador_inscricao_municipal or "").strip()

    dps_element = _construir_dps_issnet(
        numero_dps=numero_dps,
        serie_dps=serie_dps,
        codigo_municipio_emissor=codigo_municipio_emissor,
        ambiente_str=ambiente_str,
        cnpj_prest=cnpj_prest,
        im_prest=im_prest,
        prestador_cnpj=prestador_cnpj,
        prestador_inscricao_municipal=prestador_inscricao_municipal,
        prestador_telefone=prestador_telefone,
        prestador_email=prestador_email,
        optante_simples_nacional=optante_simples_nacional,
        tomador_cpf_cnpj=tomador_cpf_cnpj,
        tomador_nome=tomador_nome,
        tomador_endereco=tomador_endereco,
        tomador_telefone=tomador_telefone,
        tomador_email=tomador_email,
        codigo_municipio_prestacao=codigo_municipio_prestacao,
        codigo_tributacao_nacional=codigo_tributacao_nacional,
        codigo_tributacao_municipal=codigo_tributacao_municipal,
        descricao_servico=descricao_servico,
        codigo_nbs=codigo_nbs,
        valor_servicos=valor_servicos,
        aliquota_iss=aliquota_iss,
        data_emissao=data_emissao,
        p_tot_trib_sn=p_tot_trib_sn,
        indicador_operacao=indicador_operacao,
        ind_final_ibscbs=ind_final_ibscbs,
        ind_dest_ibscbs=ind_dest_ibscbs,
        cst_ibscbs=cst_ibscbs,
        cclass_trib_ibscbs=cclass_trib_ibscbs,
    )

    nsmap = {None: NS_NFSE}
    root = etree.Element(f"{{{NS_NFSE}}}GerarNfseEnvio", nsmap=nsmap)
    root.append(dps_element)

    xml_str = etree.tostring(root, encoding="unicode", xml_declaration=False)
    logger.info(
        "XML GerarNfseEnvio (ISSNet Nacional): nDPS=%s, serie=%s, valor=R$%s",
        numero_dps, serie_dps, valor_servicos,
    )
    return xml_str


def construir_xml_enviar_lote_dps_sincrono(
    *,
    numero_lote: int,
    prestador_cnpj: str,
    prestador_inscricao_municipal: str,
    numero_dps: int,
    serie_dps: str = "1",
    data_emissao: datetime | None = None,
    data_competencia: datetime | None = None,
    codigo_municipio_emissor: str = COD_MUNICIPIO_RP,
    ambiente: int = 1,
    prestador_telefone: str = "",
    prestador_email: str = "",
    optante_simples_nacional: bool = True,
    tomador_cpf_cnpj: str = "",
    tomador_nome: str = "",
    tomador_endereco: dict[str, str] | None = None,
    tomador_telefone: str = "",
    tomador_email: str = "",
    codigo_municipio_prestacao: str = "",
    codigo_tributacao_nacional: str = "140100",
    codigo_tributacao_municipal: str | None = None,
    descricao_servico: str = "Serviço prestado",
    codigo_nbs: str = "114011100",
    valor_servicos: Decimal = Decimal("0.00"),
    aliquota_iss: Decimal = Decimal("2.50"),
    valor_iss: Decimal | None = None,
    p_tot_trib_sn: Decimal = Decimal("0.00"),
    # IBSCBS / Reforma Tributária
    indicador_operacao: str = "100301",
    ind_final_ibscbs: str = "0",
    ind_dest_ibscbs: str = "0",
    cst_ibscbs: str = "000",
    cclass_trib_ibscbs: str = "000001",
) -> str:
    """Monta EnviarLoteDpsSincronoEnvio para ISSNet Nacional.

    Usa `nacional.xml_builder.construir_xml_dps` para gerar o DPS e envolve
    no formato de lote conforme XSD v1.01.
    """
    if data_emissao is None:
        data_emissao = datetime.now()

    ambiente_str = "homologacao" if ambiente == 2 else "producao"
    cnpj_prest = _somente_digitos(prestador_cnpj)
    im_prest = (prestador_inscricao_municipal or "").strip()

    dps_element = _construir_dps_issnet(
        numero_dps=numero_dps,
        serie_dps=serie_dps,
        codigo_municipio_emissor=codigo_municipio_emissor,
        ambiente_str=ambiente_str,
        cnpj_prest=cnpj_prest,
        im_prest=im_prest,
        prestador_cnpj=prestador_cnpj,
        prestador_inscricao_municipal=prestador_inscricao_municipal,
        prestador_telefone=prestador_telefone,
        prestador_email=prestador_email,
        optante_simples_nacional=optante_simples_nacional,
        tomador_cpf_cnpj=tomador_cpf_cnpj,
        tomador_nome=tomador_nome,
        tomador_endereco=tomador_endereco,
        tomador_telefone=tomador_telefone,
        tomador_email=tomador_email,
        codigo_municipio_prestacao=codigo_municipio_prestacao,
        codigo_tributacao_nacional=codigo_tributacao_nacional,
        codigo_tributacao_municipal=codigo_tributacao_municipal,
        descricao_servico=descricao_servico,
        codigo_nbs=codigo_nbs,
        valor_servicos=valor_servicos,
        aliquota_iss=aliquota_iss,
        data_emissao=data_emissao,
        p_tot_trib_sn=p_tot_trib_sn,
        indicador_operacao=indicador_operacao,
        ind_final_ibscbs=ind_final_ibscbs,
        ind_dest_ibscbs=ind_dest_ibscbs,
        cst_ibscbs=cst_ibscbs,
        cclass_trib_ibscbs=cclass_trib_ibscbs,
    )

    # Envolver em EnviarLoteDpsSincronoEnvio > LoteDps (Id=Lote{n} — exigido p/ assinatura)
    # Namespace padrão (sem prefixo), alinhado ao exemplo oficial .NET.
    nsmap = {None: NS_NFSE}
    root = etree.Element(f"{{{NS_NFSE}}}EnviarLoteDpsSincronoEnvio", nsmap=nsmap)
    lote = etree.SubElement(
        root,
        f"{{{NS_NFSE}}}LoteDps",
        versao=VERSAO_ISSNET_NACIONAL,
        Id=f"Lote{numero_lote}",
    )
    etree.SubElement(lote, f"{{{NS_NFSE}}}NumeroLote").text = str(numero_lote)
    prest_lote = etree.SubElement(lote, f"{{{NS_NFSE}}}Prestador")
    etree.SubElement(prest_lote, f"{{{NS_NFSE}}}CNPJ").text = cnpj_prest
    im_lote = _somente_digitos(im_prest) or im_prest
    if im_lote:
        etree.SubElement(prest_lote, f"{{{NS_NFSE}}}IM").text = im_lote
    etree.SubElement(lote, f"{{{NS_NFSE}}}QuantidadeDps").text = "1"
    lista_dps = etree.SubElement(lote, f"{{{NS_NFSE}}}ListaDps")
    lista_dps.append(dps_element)

    xml_str = etree.tostring(root, encoding="unicode", xml_declaration=False)
    logger.info(
        "XML EnviarLoteDpsSincronoEnvio (ISSNet Nacional): nDPS=%s, serie=%s, lote=%s, valor=R$%s",
        numero_dps, serie_dps, numero_lote, valor_servicos,
    )
    return xml_str


# ---------------------------------------------------------------------------
# Cancelamento
# ---------------------------------------------------------------------------

def construir_xml_cancelar_nfse_nacional(
    *,
    numero_nfse: str,
    codigo_cancelamento: str = "1",
    motivo_cancelamento: str = "",
    prestador_cnpj: str,
    prestador_inscricao_municipal: str,
    codigo_municipio: str = COD_MUNICIPIO_RP,
    chave_acesso: str = "",
    ambiente: int = 1,
) -> str:
    """Monta XML de cancelamento de NFS-e no padrão Nacional ISSNet."""
    cnpj_prest = _somente_digitos(prestador_cnpj)
    im_prest = (prestador_inscricao_municipal or "").strip()

    nsmap = {None: NS_NFSE}
    root = etree.Element(f"{{{NS_NFSE}}}CancelarNfseEnvio", nsmap=nsmap)

    pedido = etree.SubElement(root, f"{{{NS_NFSE}}}Pedido")
    inf_pedido = etree.SubElement(
        pedido, f"{{{NS_NFSE}}}InfPedidoCancelamento",
        Id=f"cancel{numero_nfse}",
    )

    id_nfse = etree.SubElement(inf_pedido, f"{{{NS_NFSE}}}IdentificacaoNfse")
    etree.SubElement(id_nfse, f"{{{NS_NFSE}}}Numero").text = str(numero_nfse)
    cpf_cnpj_el = etree.SubElement(id_nfse, f"{{{NS_NFSE}}}CpfCnpj")
    etree.SubElement(cpf_cnpj_el, f"{{{NS_NFSE}}}Cnpj").text = cnpj_prest
    etree.SubElement(id_nfse, f"{{{NS_NFSE}}}InscricaoMunicipal").text = im_prest
    etree.SubElement(id_nfse, f"{{{NS_NFSE}}}CodigoMunicipio").text = codigo_municipio

    etree.SubElement(inf_pedido, f"{{{NS_NFSE}}}CodigoCancelamento").text = str(codigo_cancelamento)

    xml_str = etree.tostring(root, encoding="unicode")
    logger.info("XML CancelarNfseEnvio (ISSNet Nacional): NFS-e=%s", numero_nfse)
    return xml_str


# ---------------------------------------------------------------------------
# Consulta
# ---------------------------------------------------------------------------

def construir_xml_consultar_nfse_por_dps(
    *,
    numero_dps: int,
    serie_dps: str = "1",
    prestador_cnpj: str,
    prestador_inscricao_municipal: str,
    codigo_municipio: str = COD_MUNICIPIO_RP,
    ambiente: int = 1,
) -> str:
    """Monta XML de consulta de NFS-e por DPS."""
    cnpj_prest = _somente_digitos(prestador_cnpj)
    im_prest = (prestador_inscricao_municipal or "").strip()

    nsmap = {None: NS_NFSE}
    root = etree.Element(f"{{{NS_NFSE}}}ConsultarNfseDpsEnvio", nsmap=nsmap)

    prest = etree.SubElement(root, f"{{{NS_NFSE}}}Prestador")
    cpf_cnpj_el = etree.SubElement(prest, f"{{{NS_NFSE}}}CpfCnpj")
    etree.SubElement(cpf_cnpj_el, f"{{{NS_NFSE}}}Cnpj").text = cnpj_prest
    etree.SubElement(prest, f"{{{NS_NFSE}}}InscricaoMunicipal").text = im_prest

    id_dps = etree.SubElement(root, f"{{{NS_NFSE}}}IdentificacaoDps")
    etree.SubElement(id_dps, f"{{{NS_NFSE}}}nDPS").text = str(numero_dps)
    etree.SubElement(id_dps, f"{{{NS_NFSE}}}serie").text = (serie_dps or "1").strip()[:5]
    etree.SubElement(id_dps, f"{{{NS_NFSE}}}cMunEmi").text = codigo_municipio

    xml_str = etree.tostring(root, encoding="unicode")
    logger.info("XML ConsultarNfseDpsEnvio (ISSNet Nacional): nDPS=%s", numero_dps)
    return xml_str


# ---------------------------------------------------------------------------
# Utilitários
# ---------------------------------------------------------------------------

def extrair_chave_acesso_nfse_nacional(xml_resposta: str) -> str | None:
    """Extrai a chave de acesso da NFS-e da resposta."""
    if not (xml_resposta or "").strip():
        return None
    try:
        root = etree.fromstring(
            xml_resposta.encode("utf-8") if isinstance(xml_resposta, str) else xml_resposta,
        )
        for el in root.iter():
            local = etree.QName(el.tag).localname
            if local in ("ChaveAcesso", "chNFSe", "chaveAcesso"):
                t = (el.text or "").strip()
                if t:
                    return t
    except Exception:
        return None
    return None


def extrair_numero_nfse_nacional(xml_resposta: str) -> str | None:
    """Extrai o número da NFS-e da resposta."""
    if not (xml_resposta or "").strip():
        return None
    try:
        root = etree.fromstring(
            xml_resposta.encode("utf-8") if isinstance(xml_resposta, str) else xml_resposta,
        )
        for el in root.iter():
            local = etree.QName(el.tag).localname
            if local in ("NumeroNfse", "nNFSe", "Numero"):
                t = (el.text or "").strip()
                if t and t.isdigit():
                    return t
    except Exception:
        return None
    return None
