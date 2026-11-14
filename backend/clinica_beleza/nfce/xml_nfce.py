"""XML da NFC-e modelo 65. A assinatura cobre só o infNFe."""
from __future__ import annotations

from decimal import Decimal

from lxml import etree

from .chave import (
    CONSULTA_SP,
    FRASE_HOMOLOGACAO_EMITENTE,
    FRASE_HOMOLOGACAO_ITEM,
    MODELO,
    NS_NFE,
    UF_SP,
    dinheiro,
    texto_fiscal,
    unidade_fiscal,
    url_qrcode,
)

NS = f"{{{NS_NFE}}}"


def _el(pai, tag: str, texto=None):
    no = etree.SubElement(pai, f"{NS}{tag}")
    if texto is not None:
        no.text = str(texto)
    return no


def _dinheiro(valor) -> str:
    return f"{dinheiro(valor):.2f}"


def _quantidade(valor) -> str:
    return f"{Decimal(str(valor or 0)).quantize(Decimal('0.0001')):.4f}"


def _preco(valor) -> str:
    return f"{Decimal(str(valor or 0)).quantize(Decimal('0.0000000001')):.10f}"


def assinar_raiz(raiz, key_pem: bytes, cert_pem: bytes):
    """Assina o elemento com Id e coloca a assinatura no final da raiz."""
    from signxml import XMLSigner, methods

    ident = ""
    for filho in raiz:
        ident = filho.get("Id") or ""
        if ident:
            break
    if not ident:
        raise ValueError("O XML fiscal não tem identificador para assinar.")
    signer = XMLSigner(
        method=methods.enveloped,
        signature_algorithm="rsa-sha256",
        digest_algorithm="sha256",
        c14n_algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315",
    )
    assinado = signer.sign(
        raiz,
        key=key_pem,
        cert=cert_pem,
        reference_uri=f"#{ident}",
        id_attribute="Id",
    )
    for no in list(assinado.iter()):
        if no.tag.endswith("KeyValue") and no.getparent() is not None:
            no.getparent().remove(no)
    return assinado


def montar_nfe(dados: dict):
    """Monta a NFe com QR Code. dados traz emitente, itens, pagamento e a chave já fechada."""
    homologacao = bool(dados["homologacao"])
    nfe = etree.Element(f"{NS}NFe", nsmap={None: NS_NFE})
    inf = _el(nfe, "infNFe")
    inf.set("versao", "4.00")
    inf.set("Id", f"NFe{dados['chave']}")
    _ide(inf, dados)
    _emitente(inf, dados, homologacao)
    if dados.get("cpf"):
        _destinatario(inf, dados, homologacao)
    for indice, item in enumerate(dados["itens"], start=1):
        _item(inf, indice, item, dados, homologacao and indice == 1)
    _totais(inf, dados)
    transp = _el(inf, "transp")
    _el(transp, "modFrete", "9")
    _pagamento(inf, dados)
    supl = _el(nfe, "infNFeSupl")
    _el(supl, "qrCode", dados["qrcode"])
    _el(supl, "urlChave", CONSULTA_SP[homologacao])
    return nfe


def envelopar(nfe) -> str:
    envio = etree.Element(f"{NS}enviNFe", nsmap={None: NS_NFE}, versao="4.00")
    _el(envio, "idLote", "1")
    _el(envio, "indSinc", "1")
    envio.append(nfe)
    return etree.tostring(envio, encoding="unicode")


def xml_evento_cancelamento(dados: dict) -> etree._Element:
    evento = etree.Element(f"{NS}evento", nsmap={None: NS_NFE}, versao="1.00")
    inf = _el(evento, "infEvento")
    inf.set("Id", f"ID110111{dados['chave']}01")
    _el(inf, "cOrgao", UF_SP)
    _el(inf, "tpAmb", "2" if dados["homologacao"] else "1")
    if len(dados["documento"]) == 11:
        _el(inf, "CPF", dados["documento"])
    else:
        _el(inf, "CNPJ", dados["documento"])
    _el(inf, "chNFe", dados["chave"])
    _el(inf, "dhEvento", dados["quando"])
    _el(inf, "tpEvento", "110111")
    _el(inf, "nSeqEvento", "1")
    _el(inf, "verEvento", "1.00")
    det = _el(inf, "detEvento")
    det.set("versao", "1.00")
    _el(det, "descEvento", "Cancelamento")
    _el(det, "nProt", dados["protocolo"])
    _el(det, "xJust", texto_fiscal(dados["justificativa"], 255))
    return evento


def xml_inutilizacao(dados: dict) -> etree._Element:
    ano = str(dados["ano"])[-2:]
    serie = f"{int(dados['serie']):03d}"
    numero = f"{int(dados['numero']):09d}"
    documento = str(dados["documento"])
    doc_chave = documento.zfill(14)
    ident = f"ID{UF_SP}{ano}{doc_chave}{MODELO}{serie}{numero}{numero}"
    raiz = etree.Element(f"{NS}inutNFe", nsmap={None: NS_NFE}, versao="4.00")
    inf = _el(raiz, "infInut")
    inf.set("Id", ident)
    _el(inf, "tpAmb", "2" if dados["homologacao"] else "1")
    _el(inf, "xServ", "INUTILIZAR")
    _el(inf, "cUF", UF_SP)
    _el(inf, "ano", ano)
    if len(documento) == 11:
        _el(inf, "CPF", documento)
    else:
        _el(inf, "CNPJ", documento)
    _el(inf, "mod", MODELO)
    _el(inf, "serie", str(int(dados["serie"])))
    _el(inf, "nNFIni", str(int(dados["numero"])))
    _el(inf, "nNFFin", str(int(dados["numero"])))
    _el(inf, "xJust", texto_fiscal(dados["justificativa"], 255))
    return raiz


def _ide(inf, dados: dict) -> None:
    ide = _el(inf, "ide")
    _el(ide, "cUF", UF_SP)
    _el(ide, "cNF", dados["codigo"])
    _el(ide, "natOp", "VENDA")
    _el(ide, "mod", MODELO)
    _el(ide, "serie", str(int(dados["serie"])))
    _el(ide, "nNF", str(int(dados["numero"])))
    _el(ide, "dhEmi", dados["quando"])
    _el(ide, "tpNF", "1")
    _el(ide, "idDest", "1")
    _el(ide, "cMunFG", dados["municipio"])
    _el(ide, "tpImp", "4")
    _el(ide, "tpEmis", "1")
    _el(ide, "cDV", dados["chave"][-1])
    _el(ide, "tpAmb", "2" if dados["homologacao"] else "1")
    _el(ide, "finNFe", "1")
    _el(ide, "indFinal", "1")
    _el(ide, "indPres", "1")
    _el(ide, "procEmi", "0")
    _el(ide, "verProc", "LWK NFC-e 1")


def _emitente(inf, dados: dict, homologacao: bool) -> None:
    emit = _el(inf, "emit")
    if len(dados["documento"]) == 11:
        _el(emit, "CPF", dados["documento"])
    else:
        _el(emit, "CNPJ", dados["documento"])
    nome = FRASE_HOMOLOGACAO_EMITENTE if homologacao else texto_fiscal(dados["nome"], 60)
    _el(emit, "xNome", nome)
    ender = _el(emit, "enderEmit")
    _el(ender, "xLgr", texto_fiscal(dados["logradouro"], 60))
    _el(ender, "nro", texto_fiscal(dados["numero_endereco"], 60))
    _el(ender, "xBairro", texto_fiscal(dados["bairro"], 60))
    _el(ender, "cMun", dados["municipio"])
    _el(ender, "xMun", texto_fiscal(dados["cidade"], 60))
    _el(ender, "UF", "SP")
    _el(ender, "CEP", dados["cep"])
    _el(ender, "cPais", "1058")
    _el(ender, "xPais", "BRASIL")
    _el(emit, "IE", dados["ie"])
    _el(emit, "CRT", "1" if dados["simples"] else "3")


def _destinatario(inf, dados: dict, homologacao: bool) -> None:
    dest = _el(inf, "dest")
    _el(dest, "CPF", dados["cpf"])
    nome = FRASE_HOMOLOGACAO_EMITENTE if homologacao else texto_fiscal(dados["nome_cliente"], 60)
    _el(dest, "xNome", nome)
    _el(dest, "indIEDest", "9")


def _item(inf, indice: int, item: dict, dados: dict, forcar_homologacao: bool) -> None:
    det = _el(inf, "det")
    det.set("nItem", str(indice))
    prod = _el(det, "prod")
    _el(prod, "cProd", str(item["codigo"])[:60])
    _el(prod, "cEAN", "SEM GTIN")
    nome = FRASE_HOMOLOGACAO_ITEM if forcar_homologacao else texto_fiscal(item["nome"], 120)
    _el(prod, "xProd", nome)
    _el(prod, "NCM", item["ncm"])
    _el(prod, "CFOP", "5102")
    unidade = unidade_fiscal(item.get("unidade") or "")
    _el(prod, "uCom", unidade)
    _el(prod, "qCom", _quantidade(item["quantidade"]))
    _el(prod, "vUnCom", _preco(item["preco"]))
    _el(prod, "vProd", _dinheiro(item["bruto"]))
    _el(prod, "cEANTrib", "SEM GTIN")
    _el(prod, "uTrib", unidade)
    _el(prod, "qTrib", _quantidade(item["quantidade"]))
    _el(prod, "vUnTrib", _preco(item["preco"]))
    if dinheiro(item["desconto"]) > 0:
        _el(prod, "vDesc", _dinheiro(item["desconto"]))
    _el(prod, "indTot", "1")
    imposto = _el(det, "imposto")
    icms = _el(imposto, "ICMS")
    if dados["simples"]:
        sn = _el(icms, "ICMSSN102")
        _el(sn, "orig", "0")
        _el(sn, "CSOSN", "102")
    else:
        cheio = _el(icms, "ICMS00")
        _el(cheio, "orig", "0")
        _el(cheio, "CST", "00")
        _el(cheio, "modBC", "3")
        _el(cheio, "vBC", _dinheiro(item["liquido"]))
        _el(cheio, "pICMS", _dinheiro(dados["aliquota_icms"]))
        _el(cheio, "vICMS", _dinheiro(item["icms"]))
    pis = _el(imposto, "PIS")
    if dados["simples"]:
        bloco = _el(pis, "PISOutr")
        _el(bloco, "CST", "49")
        _el(bloco, "vBC", "0.00")
        _el(bloco, "pPIS", "0.00")
        _el(bloco, "vPIS", "0.00")
    else:
        bloco = _el(pis, "PISAliq")
        _el(bloco, "CST", "01")
        _el(bloco, "vBC", _dinheiro(item["liquido"]))
        _el(bloco, "pPIS", "0.65")
        _el(bloco, "vPIS", _dinheiro(item["pis"]))
    cofins = _el(imposto, "COFINS")
    if dados["simples"]:
        bloco = _el(cofins, "COFINSOutr")
        _el(bloco, "CST", "49")
        _el(bloco, "vBC", "0.00")
        _el(bloco, "pCOFINS", "0.00")
        _el(bloco, "vCOFINS", "0.00")
    else:
        bloco = _el(cofins, "COFINSAliq")
        _el(bloco, "CST", "01")
        _el(bloco, "vBC", _dinheiro(item["liquido"]))
        _el(bloco, "pCOFINS", "3.00")
        _el(bloco, "vCOFINS", _dinheiro(item["cofins"]))


def _totais(inf, dados: dict) -> None:
    total = _el(inf, "total")
    icms = _el(total, "ICMSTot")
    for tag, valor in (
        ("vBC", dados["base_icms"]),
        ("vICMS", dados["icms"]),
        ("vICMSDeson", 0),
        ("vFCP", 0),
        ("vBCST", 0),
        ("vST", 0),
        ("vFCPST", 0),
        ("vFCPSTRet", 0),
        ("vProd", dados["bruto"]),
        ("vFrete", 0),
        ("vSeg", 0),
        ("vDesc", dados["desconto"]),
        ("vII", 0),
        ("vIPI", 0),
        ("vIPIDevol", 0),
        ("vPIS", dados["pis"]),
        ("vCOFINS", dados["cofins"]),
        ("vOutro", 0),
        ("vNF", dados["liquido"]),
    ):
        _el(icms, tag, _dinheiro(valor))


def _pagamento(inf, dados: dict) -> None:
    pag = _el(inf, "pag")
    det = _el(pag, "detPag")
    _el(det, "indPag", "1" if dados["tpag"] == "05" else "0")
    _el(det, "tPag", dados["tpag"])
    _el(det, "vPag", _dinheiro(dados["liquido"]))
    if dados["tpag"] in {"03", "04"}:
        card = _el(det, "card")
        _el(card, "tpIntegra", "2")


def qr_do_documento(dados: dict) -> str:
    return url_qrcode(
        chave=dados["chave"],
        homologacao=dados["homologacao"],
        id_csc=dados["id_csc"],
        csc=dados["csc"],
    )
