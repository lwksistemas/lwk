"""Montagem de XML para ISSNet padrão Nacional (Ribeirão Preto).

Novo padrão que substituirá o ABRASF 2.04 a partir de 03/08/2026.
Endpoint: https://nfse.issnetonline.com.br/wsnfsenacional/ribeiraopreto/nfse.asmx
Método SOAP: RecepcionarLoteDpsSincrono
Namespace: http://www.sped.fazenda.gov.br/nfse

Estrutura:
  EnviarLoteDpsSincronoEnvio
    └── LoteDps (NumeroLote, Prestador, QuantidadeDPS, ListaDps)
         └── Dps (Id, versao="1.01")
              └── infDPS (Id="DPS{nDPS}", versao="1.01")
                   ├── tpAmb, dhEmi, verAplic, serie, nDPS, dCompet, tpEmit, cLocEmi
                   ├── prest (CNPJ, IM, regTrib)
                   ├── tom (CNPJ/CPF, xNome, end)
                   ├── serv (locPrest, cServ, valores)
                   └── vBC
"""
import logging
import re
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

from lxml import etree

logger = logging.getLogger(__name__)

# Namespace NFS-e Nacional (SPED)
NS_NFSE_NACIONAL = "http://www.sped.fazenda.gov.br/nfse"

# Versão do layout ISSNet Nacional
VERSAO_ISSNET_NACIONAL = "1.01"

# Versão da aplicação emissora
VER_APLIC = "LWK1.0"

# Código IBGE Ribeirão Preto
COD_MUNICIPIO_RP = "3543402"


def _somente_digitos(texto: str) -> str:
    """Remove todos os caracteres não-numéricos."""
    return re.sub(r"\D", "", texto or "")


def _formatar_decimal(valor: Decimal, casas: int = 2) -> str:
    """Formata Decimal para string com casas decimais fixas."""
    return f"{valor:.{casas}f}"


def _el(parent, tag: str, text: str | None = None):
    """Cria subelemento no namespace NFS-e Nacional com texto opcional."""
    el = etree.SubElement(parent, f"{{{NS_NFSE_NACIONAL}}}{tag}")
    if text is not None:
        el.text = str(text)
    return el


def _normalizar_codigo_trib_nac(codigo_servico: str) -> str:
    """Normaliza código de serviço para cTribNac (6 dígitos).

    Exemplos:
        '14.01' -> '140100'
        '1401' -> '140100'
        '140100' -> '140100'
        '14.01.18' -> '140118'
    """
    raw = (codigo_servico or "").strip()
    digits = _somente_digitos(raw)
    if len(digits) == 6:
        return digits
    if len(digits) == 4:
        return digits + "00"
    if len(digits) > 6:
        return digits[:6]
    if len(digits) >= 4:
        return digits[:4] + "00"
    return "140100"


def _normalizar_codigo_trib_mun(codigo: str | None) -> str:
    """Normaliza código de tributação municipal.

    Se vazio/None, retorna string vazia (campo não será incluído).
    """
    digits = _somente_digitos(codigo or "")
    return digits if digits else ""


def _formatar_dhemi(dt: datetime) -> str:
    """Formata data/hora de emissão no formato ISO 8601 UTC.

    Formato: AAAA-MM-DDThh:mm:ss-03:00
    """
    return dt.strftime("%Y-%m-%dT%H:%M:%S-03:00")


# ---------------------------------------------------------------------------
# Emissão: EnviarLoteDpsSincronoEnvio
# ---------------------------------------------------------------------------


def construir_xml_enviar_lote_dps_sincrono(
    *,
    # Lote
    numero_lote: int,
    # Prestador (cabeçalho do lote)
    prestador_cnpj: str,
    prestador_inscricao_municipal: str,
    # DPS - Identificação
    numero_dps: int,
    serie_dps: str = "1",
    data_emissao: datetime | None = None,
    data_competencia: datetime | None = None,
    codigo_municipio_emissor: str = COD_MUNICIPIO_RP,
    ambiente: int = 1,
    # Prestador (dentro da DPS)
    prestador_telefone: str = "",
    prestador_email: str = "",
    optante_simples_nacional: bool = True,
    # Tomador
    tomador_cpf_cnpj: str = "",
    tomador_nome: str = "",
    tomador_endereco: dict[str, str] | None = None,
    tomador_telefone: str = "",
    tomador_email: str = "",
    # Serviço
    codigo_municipio_prestacao: str = "",
    codigo_tributacao_nacional: str = "140100",
    codigo_tributacao_municipal: str | None = None,
    descricao_servico: str = "Serviço prestado",
    codigo_nbs: str = "",
    # Valores
    valor_servicos: Decimal = Decimal("0.00"),
    aliquota_iss: Decimal = Decimal("2.50"),
    valor_iss: Decimal | None = None,
) -> str:
    """Monta o XML EnviarLoteDpsSincronoEnvio para ISSNet Nacional.

    Retorna o XML como string (sem assinatura). A assinatura digital
    deve ser aplicada separadamente via issnet_xml_signer ou
    nacional/xml_signer (Reference URI=#infDPS Id).

    Args:
        numero_lote: Número sequencial do lote.
        prestador_cnpj: CNPJ do prestador (será limpo para apenas dígitos).
        prestador_inscricao_municipal: IM do prestador.
        numero_dps: Número da DPS (inteiro sequencial).
        serie_dps: Série da DPS (max 5 chars).
        data_emissao: Data/hora de emissão (default: agora).
        data_competencia: Data de competência (default: data_emissao).
        codigo_municipio_emissor: Código IBGE 7 dígitos do município emissor.
        ambiente: 1=Produção, 2=Homologação.
        prestador_telefone: Telefone do prestador (opcional).
        prestador_email: Email do prestador (opcional).
        optante_simples_nacional: Se o prestador é optante do Simples Nacional.
        tomador_cpf_cnpj: CPF ou CNPJ do tomador.
        tomador_nome: Razão social / nome do tomador.
        tomador_endereco: Dict com logradouro, numero, complemento, bairro,
                          codigo_municipio, uf, cep.
        tomador_telefone: Telefone do tomador (opcional).
        tomador_email: Email do tomador (opcional).
        codigo_municipio_prestacao: Código IBGE do município de prestação do serviço.
        codigo_tributacao_nacional: cTribNac (6 dígitos, ex: '140100').
        codigo_tributacao_municipal: cTribMun (opcional, ex: '140118').
        descricao_servico: Descrição do serviço prestado.
        codigo_nbs: Código NBS (9 chars, ex: '104033000').
        valor_servicos: Valor total dos serviços.
        aliquota_iss: Alíquota ISS em percentual (ex: 2.50).
        valor_iss: Valor do ISS (se None, calcula automaticamente).

    Returns:
        XML string do EnviarLoteDpsSincronoEnvio.

    """
    if data_emissao is None:
        data_emissao = datetime.now()
    if data_competencia is None:
        data_competencia = data_emissao

    cnpj_prest = _somente_digitos(prestador_cnpj)
    im_prest = (prestador_inscricao_municipal or "").strip()
    doc_tomador = _somente_digitos(tomador_cpf_cnpj)
    valor = Decimal(str(valor_servicos))
    aliquota = Decimal(str(aliquota_iss))

    if valor_iss is None:
        valor_iss_calc = (valor * aliquota / Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP,
        )
    else:
        valor_iss_calc = Decimal(str(valor_iss))

    serie = (serie_dps or "1").strip()[:5]
    cod_mun_prestacao = (codigo_municipio_prestacao or codigo_municipio_emissor).strip()

    nsmap = {None: NS_NFSE_NACIONAL}

    # === Raiz: EnviarLoteDpsSincronoEnvio ===
    root = etree.Element(f"{{{NS_NFSE_NACIONAL}}}EnviarLoteDpsSincronoEnvio", nsmap=nsmap)

    # === LoteDps ===
    lote_dps = _el(root, "LoteDps")
    _el(lote_dps, "NumeroLote", str(numero_lote))

    # Prestador do lote
    prest_lote = _el(lote_dps, "Prestador")
    cpf_cnpj_lote = _el(prest_lote, "CpfCnpj")
    _el(cpf_cnpj_lote, "Cnpj", cnpj_prest)
    _el(prest_lote, "InscricaoMunicipal", im_prest)

    _el(lote_dps, "QuantidadeDPS", "1")

    # === ListaDps ===
    lista_dps = _el(lote_dps, "ListaDps")

    # === Dps ===
    dps_id = f"DPS{numero_dps}"
    dps_el = etree.SubElement(
        lista_dps,
        f"{{{NS_NFSE_NACIONAL}}}Dps",
        Id=dps_id,
        versao=VERSAO_ISSNET_NACIONAL,
    )

    # === infDPS ===
    inf_dps_id = f"DPS{numero_dps}"
    inf_dps = etree.SubElement(
        dps_el,
        f"{{{NS_NFSE_NACIONAL}}}infDPS",
        Id=inf_dps_id,
        versao=VERSAO_ISSNET_NACIONAL,
    )

    # --- Identificação ---
    _el(inf_dps, "tpAmb", str(ambiente))
    _el(inf_dps, "dhEmi", _formatar_dhemi(data_emissao))
    _el(inf_dps, "verAplic", VER_APLIC)
    _el(inf_dps, "serie", serie)
    _el(inf_dps, "nDPS", str(numero_dps))
    _el(inf_dps, "dCompet", data_competencia.strftime("%Y-%m-%d"))
    _el(inf_dps, "tpEmit", "1")  # 1 = Prestador
    _el(inf_dps, "cLocEmi", codigo_municipio_emissor)

    # --- Prestador (prest) ---
    prest = _el(inf_dps, "prest")
    _el(prest, "CNPJ", cnpj_prest)
    _el(prest, "IM", _somente_digitos(im_prest) or im_prest)

    reg_trib = _el(prest, "regTrib")
    _el(reg_trib, "opSN", "1" if optante_simples_nacional else "2")

    if prestador_telefone:
        _el(prest, "fone", _somente_digitos(prestador_telefone)[:11])
    if prestador_email:
        _el(prest, "email", prestador_email[:80])

    # --- Tomador (tom) ---
    if doc_tomador:
        tom = _el(inf_dps, "tom")
        if len(doc_tomador) == 11:
            _el(tom, "CPF", doc_tomador)
        else:
            _el(tom, "CNPJ", doc_tomador)
        if tomador_nome:
            _el(tom, "xNome", tomador_nome[:150])

        # Endereço do tomador
        if tomador_endereco:
            end = _el(tom, "end")
            logradouro = (tomador_endereco.get("logradouro") or "").strip()
            if logradouro:
                _el(end, "xLgr", logradouro[:60])
            numero = (tomador_endereco.get("numero") or "S/N").strip()
            _el(end, "nro", numero[:10])
            complemento = (tomador_endereco.get("complemento") or "").strip()
            if complemento:
                _el(end, "xCpl", complemento[:60])
            bairro = (tomador_endereco.get("bairro") or "").strip()
            if bairro:
                _el(end, "xBairro", bairro[:60])
            cod_mun_tom = (tomador_endereco.get("codigo_municipio") or "").strip()
            if cod_mun_tom:
                _el(end, "cMun", cod_mun_tom[:7])
            uf = (tomador_endereco.get("uf") or "").strip()[:2]
            if uf:
                _el(end, "UF", uf.upper())
            cep = _somente_digitos(tomador_endereco.get("cep", ""))[:8]
            if cep:
                _el(end, "CEP", cep.zfill(8))

        if tomador_telefone:
            _el(tom, "fone", _somente_digitos(tomador_telefone)[:11])
        if tomador_email:
            _el(tom, "email", tomador_email[:80])

    # --- Serviço (serv) ---
    serv = _el(inf_dps, "serv")

    # locPrest
    loc_prest = _el(serv, "locPrest")
    _el(loc_prest, "cLocPrestacao", cod_mun_prestacao)

    # cServ
    c_serv = _el(serv, "cServ")
    c_trib_nac = _normalizar_codigo_trib_nac(codigo_tributacao_nacional)
    _el(c_serv, "cTribNac", c_trib_nac)

    c_trib_mun = _normalizar_codigo_trib_mun(codigo_tributacao_municipal)
    if c_trib_mun:
        _el(c_serv, "cTribMun", c_trib_mun)

    _el(c_serv, "xDescServ", (descricao_servico or "Serviço prestado")[:2000])

    nbs = _somente_digitos(codigo_nbs or "")
    if nbs:
        _el(c_serv, "cNBS", nbs[:9])

    # valores
    valores = _el(serv, "valores")
    _el(valores, "vServPrest", _formatar_decimal(valor))
    _el(valores, "vISS", _formatar_decimal(valor_iss_calc))

    # --- Base de cálculo (vBC) ---
    _el(inf_dps, "vBC", _formatar_decimal(valor))

    # Gerar XML
    xml_str = etree.tostring(root, encoding="unicode", pretty_print=False)
    logger.info(
        "XML EnviarLoteDpsSincronoEnvio construído (ISSNet Nacional): "
        "nDPS=%s, serie=%s, lote=%s, valor=R$%s, ISS=R$%s",
        numero_dps, serie, numero_lote, valor, valor_iss_calc,
    )
    return xml_str


# ---------------------------------------------------------------------------
# Cancelamento: CancelarNfseEnvio (padrão Nacional ISSNet)
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
    """Monta XML de cancelamento de NFS-e no padrão Nacional ISSNet.

    Args:
        numero_nfse: Número da NFS-e a ser cancelada.
        codigo_cancelamento: Código do motivo (1=Erro emissão, 2=Serviço não prestado,
                            3=Duplicidade, 4=Outros).
        motivo_cancelamento: Descrição textual do motivo (opcional).
        prestador_cnpj: CNPJ do prestador.
        prestador_inscricao_municipal: Inscrição municipal do prestador.
        codigo_municipio: Código IBGE do município.
        chave_acesso: Chave de acesso da NFS-e (se disponível).
        ambiente: 1=Produção, 2=Homologação.

    Returns:
        XML string do pedido de cancelamento.

    """
    cnpj_prest = _somente_digitos(prestador_cnpj)
    im_prest = (prestador_inscricao_municipal or "").strip()

    nsmap = {None: NS_NFSE_NACIONAL}
    root = etree.Element(f"{{{NS_NFSE_NACIONAL}}}CancelarNfseEnvio", nsmap=nsmap)

    pedido = _el(root, "Pedido")
    inf_pedido = etree.SubElement(
        pedido,
        f"{{{NS_NFSE_NACIONAL}}}InfPedidoCancelamento",
        Id=f"cancel{numero_nfse}",
    )

    # Identificação da NFS-e
    id_nfse = _el(inf_pedido, "IdentificacaoNfse")
    _el(id_nfse, "Numero", str(numero_nfse))

    cpf_cnpj_el = _el(id_nfse, "CpfCnpj")
    _el(cpf_cnpj_el, "Cnpj", cnpj_prest)

    _el(id_nfse, "InscricaoMunicipal", im_prest)
    _el(id_nfse, "CodigoMunicipio", codigo_municipio)

    if chave_acesso:
        _el(id_nfse, "ChaveAcesso", chave_acesso.strip())

    _el(inf_pedido, "CodigoCancelamento", str(codigo_cancelamento))

    if motivo_cancelamento:
        _el(inf_pedido, "MotivoCancelamento", motivo_cancelamento[:255])

    _el(inf_pedido, "tpAmb", str(ambiente))

    xml_str = etree.tostring(root, encoding="unicode", pretty_print=False)
    logger.info(
        "XML CancelarNfseEnvio (ISSNet Nacional): NFS-e=%s, motivo=%s",
        numero_nfse, codigo_cancelamento,
    )
    return xml_str


# ---------------------------------------------------------------------------
# Consulta: ConsultarNfseDpsEnvio (padrão Nacional ISSNet)
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
    """Monta XML de consulta de NFS-e por DPS no padrão Nacional ISSNet.

    Permite localizar a NFS-e gerada a partir de uma DPS específica.

    Args:
        numero_dps: Número da DPS.
        serie_dps: Série da DPS.
        prestador_cnpj: CNPJ do prestador.
        prestador_inscricao_municipal: Inscrição municipal.
        codigo_municipio: Código IBGE do município.
        ambiente: 1=Produção, 2=Homologação.

    Returns:
        XML string da consulta.

    """
    cnpj_prest = _somente_digitos(prestador_cnpj)
    im_prest = (prestador_inscricao_municipal or "").strip()
    serie = (serie_dps or "1").strip()[:5]

    nsmap = {None: NS_NFSE_NACIONAL}
    root = etree.Element(f"{{{NS_NFSE_NACIONAL}}}ConsultarNfseDpsEnvio", nsmap=nsmap)

    _el(root, "tpAmb", str(ambiente))

    # Prestador
    prest = _el(root, "Prestador")
    cpf_cnpj_el = _el(prest, "CpfCnpj")
    _el(cpf_cnpj_el, "Cnpj", cnpj_prest)
    _el(prest, "InscricaoMunicipal", im_prest)

    # Identificação da DPS
    id_dps = _el(root, "IdentificacaoDps")
    _el(id_dps, "nDPS", str(numero_dps))
    _el(id_dps, "serie", serie)
    _el(id_dps, "cMunEmi", codigo_municipio)

    xml_str = etree.tostring(root, encoding="unicode", pretty_print=False)
    logger.info(
        "XML ConsultarNfseDpsEnvio (ISSNet Nacional): nDPS=%s, serie=%s",
        numero_dps, serie,
    )
    return xml_str


# ---------------------------------------------------------------------------
# Utilitários
# ---------------------------------------------------------------------------


def issnet_nacional_xml_para_raiz_envio(xml_envio: str) -> str:
    """Garante que o XML raiz é EnviarLoteDpsSincronoEnvio.

    Útil para compatibilidade caso o XML seja gerado com tag diferente.
    """
    return (xml_envio or "").strip()


def extrair_chave_acesso_nfse_nacional(xml_resposta: str) -> str | None:
    """Extrai a chave de acesso da NFS-e da resposta do webservice.

    Procura pelo elemento ChaveAcesso ou chNFSe na resposta XML.
    """
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
    """Extrai o número da NFS-e da resposta do webservice."""
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
