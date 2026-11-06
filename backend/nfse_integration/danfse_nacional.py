"""DANFSe da NFS-e Nacional a partir do XML autorizado.

A API do ADN que gerava o PDF foi desligada em agosto de 2026. O portal
só entrega o arquivo depois de um captcha. A Nota Técnica 008 manda o
sistema emissor montar o DANFSe com os dados do XML.
"""
from __future__ import annotations

import logging
from datetime import datetime
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

import qrcode
from lxml import etree
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from nfse_integration.numero_exibicao import PORTAL_CONSULTA_NACIONAL

logger = logging.getLogger(__name__)

_LOGO = Path(__file__).resolve().parent / "assets" / "logo-nfse-horizontal.png"

_OP_SIMPLES = {
    "1": "Não optante",
    "2": "Optante — MEI",
    "3": "Optante — ME/EPP",
}
_REG_APURACAO = {
    "1": "Federais e municipal pelo Simples Nacional",
    "2": "Federais pelo Simples Nacional e ISSQN fora do Simples",
    "3": "Federais e municipal fora do Simples Nacional",
}
_TRIB_ISS = {
    "1": "Operação tributável",
    "2": "Imunidade",
    "3": "Exportação de serviço",
    "4": "Não incidência",
}
_RET_ISS = {
    "1": "Não retido",
    "2": "Retido pelo tomador",
    "3": "Retido pelo intermediário",
}
_AMBIENTE = {"1": "Produção", "2": "Homologação"}
_GERADOR = {"1": "Município", "2": "Emissor Nacional"}
_SITUACAO = {"100": "NFS-e gerada", "101": "NFS-e cancelada", "102": "NFS-e substituída"}


def _texto(el, nome: str) -> str:
    if el is None:
        return ""
    for filho in el.iter():
        if etree.QName(filho.tag).localname == nome and (filho.text or "").strip():
            return filho.text.strip()
    return ""


def _primeiro(root, nome: str):
    for el in root.iter():
        if etree.QName(el.tag).localname == nome:
            return el
    return None


def _data(valor: str) -> str:
    bruto = (valor or "").strip()
    if not bruto:
        return "—"
    try:
        momento = datetime.fromisoformat(bruto)
    except ValueError:
        return bruto[:16].replace("T", " ")
    return momento.strftime("%d/%m/%Y %H:%M")


def _data_curta(valor: str) -> str:
    bruto = (valor or "").strip()
    if len(bruto) >= 10 and bruto[4] == "-":
        ano, mes, dia = bruto[:10].split("-")
        return f"{dia}/{mes}/{ano}"
    return bruto or "—"


def _moeda(valor: str) -> str:
    bruto = (valor or "").strip().replace(",", ".")
    if not bruto:
        return "—"
    try:
        numero = float(bruto)
    except ValueError:
        return bruto
    texto = f"{numero:,.2f}"
    return "R$ " + texto.replace(",", "X").replace(".", ",").replace("X", ".")


def _documento(valor: str) -> str:
    digitos = "".join(c for c in (valor or "") if c.isdigit())
    if len(digitos) == 14:
        return f"{digitos[:2]}.{digitos[2:5]}.{digitos[5:8]}/{digitos[8:12]}-{digitos[12:]}"
    if len(digitos) == 11:
        return f"{digitos[:3]}.{digitos[3:6]}.{digitos[6:9]}-{digitos[9:]}"
    return valor or "—"


def _endereco(bloco) -> str:
    if bloco is None:
        return "—"
    partes = [
        _texto(bloco, "xLgr"),
        _texto(bloco, "nro"),
        _texto(bloco, "xCpl"),
        _texto(bloco, "xBairro"),
    ]
    linha = ", ".join(p for p in partes if p)
    cidade = _texto(bloco, "xMun") or _texto(bloco, "cMun")
    uf = _texto(bloco, "UF")
    cep = _texto(bloco, "CEP")
    if cidade or uf:
        linha = ", ".join(p for p in (linha, f"{cidade}/{uf}".strip("/")) if p)
    if cep:
        linha = f"{linha} — CEP {cep}" if linha else f"CEP {cep}"
    return linha or "—"


def _rotulo(mapa: dict[str, str], valor: str) -> str:
    codigo = (valor or "").strip()
    if not codigo:
        return "—"
    return mapa.get(codigo, codigo)


def ler_dados_danfse(xml_nfse: str, *, chave: str = "") -> dict[str, str]:
    """Lê do XML só o que a DANFSe pode imprimir."""
    root = etree.fromstring(xml_nfse.encode("utf-8") if isinstance(xml_nfse, str) else xml_nfse)
    inf = _primeiro(root, "infNFSe")
    if inf is None:
        inf = root
    dps = _primeiro(root, "infDPS")
    emit = _primeiro(inf, "emit")
    prest = _primeiro(dps, "prest") if dps is not None else None
    toma = _primeiro(dps, "toma") if dps is not None else None
    serv = _primeiro(dps, "serv") if dps is not None else None
    valores_nf = None
    for el in inf:
        if etree.QName(el.tag).localname == "valores":
            valores_nf = el
            break
    numero = _texto(inf, "nNFSe")
    return {
        "chave": (chave or "").strip(),
        "numero": str(int(numero)) if numero.isdigit() else (numero or "—"),
        "municipio": _texto(inf, "xLocEmi") or "—",
        "competencia": _data_curta(_texto(dps, "dCompet") if dps is not None else ""),
        "emissao_nfse": _data(_texto(inf, "dhProc")),
        "numero_dps": _texto(dps, "nDPS") if dps is not None else "—",
        "serie_dps": _texto(dps, "serie") if dps is not None else "—",
        "emissao_dps": _data(_texto(dps, "dhEmi") if dps is not None else ""),
        "situacao": _rotulo(_SITUACAO, _texto(inf, "cStat")),
        "ambiente": _rotulo(_AMBIENTE, _texto(dps, "tpAmb") if dps is not None else ""),
        "gerador": _rotulo(_GERADOR, _texto(inf, "ambGer")),
        "prestador_doc": _documento(_texto(emit, "CNPJ") or _texto(emit, "CPF")),
        "prestador_nome": _texto(emit, "xNome") or "—",
        "prestador_endereco": _endereco(_primeiro(emit, "enderNac") if emit is not None else None),
        "prestador_fone": _texto(emit, "fone") or "—",
        "prestador_email": _texto(emit, "email") or "—",
        "prestador_municipio": _texto(inf, "xLocEmi") or "—",
        "simples": _rotulo(_OP_SIMPLES, _texto(prest, "opSimpNac") if prest is not None else ""),
        "regime_sn": _rotulo(_REG_APURACAO, _texto(prest, "regApTribSN") if prest is not None else ""),
        "tomador_doc": _documento(_texto(toma, "CNPJ") or _texto(toma, "CPF")) if toma is not None else "—",
        "tomador_nome": _texto(toma, "xNome") if toma is not None else "—",
        "tomador_endereco": _endereco(_primeiro(toma, "endNac") if toma is not None else None),
        "tomador_fone": _texto(toma, "fone") if toma is not None else "—",
        "tomador_email": _texto(toma, "email") if toma is not None else "—",
        "codigo_servico": _texto(serv, "cTribNac") if serv is not None else "—",
        "descricao_codigo": _texto(inf, "xTribNac") or "—",
        "local_prestacao": _texto(inf, "xLocPrestacao") or "—",
        "descricao": _texto(serv, "xDescServ") if serv is not None else "—",
        "tributacao_iss": _rotulo(_TRIB_ISS, _texto(dps, "tribISSQN") if dps is not None else ""),
        "retencao_iss": _rotulo(_RET_ISS, _texto(dps, "tpRetISSQN") if dps is not None else ""),
        "incidencia": _texto(inf, "xLocIncid") or "—",
        "aliquota_sn": (p + "%") if (p := (_texto(dps, "pTotTribSN") if dps is not None else "")) else "—",
        "valor_servico": _moeda(_texto(dps, "vServ") if dps is not None else ""),
        "valor_liquido": _moeda(_texto(valores_nf, "vLiq") if valores_nf is not None else ""),
    }


def _qr(url: str) -> BytesIO:
    imagem = qrcode.make(url)
    buf = BytesIO()
    imagem.save(buf, format="PNG")
    buf.seek(0)
    return buf


def _p(texto: str, estilo: ParagraphStyle) -> Paragraph:
    return Paragraph(escape(texto or "—"), estilo)


def gerar_danfse_nacional(xml_nfse: str, *, chave: str = "") -> BytesIO:
    """Monta o PDF do DANFSe v2.0 com os campos do XML."""
    dados = ler_dados_danfse(xml_nfse, chave=chave)
    chave_acesso = dados["chave"]
    consulta = PORTAL_CONSULTA_NACIONAL.format(chave=chave_acesso) if chave_acesso else ""

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        title=f"DANFSe {dados['numero']}",
        author="NFS-e Nacional",
        topMargin=0.8 * cm,
        bottomMargin=0.8 * cm,
        leftMargin=0.9 * cm,
        rightMargin=0.9 * cm,
    )
    normal = ParagraphStyle("Dfs", fontName="Helvetica", fontSize=8, leading=10)
    negrito = ParagraphStyle("DfsB", parent=normal, fontName="Helvetica-Bold")
    miudo = ParagraphStyle("DfsM", parent=normal, fontSize=7, leading=9, textColor=colors.HexColor("#444444"))
    titulo = ParagraphStyle("DfsT", fontName="Helvetica-Bold", fontSize=12, alignment=TA_CENTER, leading=14)
    sub = ParagraphStyle("DfsS", fontName="Helvetica-Bold", fontSize=8, alignment=TA_CENTER, leading=10)
    centro = ParagraphStyle("DfsC", parent=miudo, alignment=TA_CENTER)
    direita = ParagraphStyle("DfsR", parent=negrito, alignment=TA_RIGHT, fontSize=11)
    bloco = ParagraphStyle(
        "DfsBloco",
        fontName="Helvetica-Bold",
        fontSize=8,
        textColor=colors.white,
        leading=10,
    )

    def secao(nome: str):
        tabela = Table([[Paragraph(nome, bloco)]], colWidths=[19.2 * cm])
        tabela.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0B3D91")),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        return tabela

    def grade(linhas: list[list[str]]):
        celulas = [[_p(item, negrito if col % 2 == 0 else normal) for col, item in enumerate(linha)] for linha in linhas]
        tabela = Table(celulas, colWidths=[3.3 * cm, 6.3 * cm, 3.3 * cm, 6.3 * cm])
        tabela.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 2),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ("TOPPADDING", (0, 0), (-1, -1), 1),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ("BOX", (0, 0), (-1, -1), 0.3, colors.HexColor("#cccccc")),
            ("LINEBELOW", (0, 0), (-1, -2), 0.2, colors.HexColor("#eeeeee")),
        ]))
        return tabela

    elementos: list = []
    cabeca = []
    if _LOGO.is_file():
        cabeca.append(Image(str(_LOGO), width=4.6 * cm, height=1.15 * cm))
    else:
        cabeca.append(Paragraph("NFS-e", titulo))
    meio = [
        Paragraph("DANFSe v2.0", titulo),
        Paragraph("Documento Auxiliar da NFS-e", sub),
        Paragraph(dados["municipio"], centro),
        Paragraph(f"{dados['gerador']} — {dados['ambiente']}", centro),
    ]
    if dados["ambiente"] == "Homologação":
        meio.append(Paragraph("NFS-e SEM VALIDADE JURÍDICA", ParagraphStyle(
            "DfsHom", fontName="Helvetica-Bold", fontSize=8, alignment=TA_CENTER, textColor=colors.red,
        )))
    cabeca_tabela = Table([[cabeca[0], meio]], colWidths=[5.2 * cm, 14 * cm])
    cabeca_tabela.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#0B3D91")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elementos.append(cabeca_tabela)
    elementos.append(Spacer(1, 0.2 * cm))

    chave_fmt = " ".join(chave_acesso[i:i + 4] for i in range(0, len(chave_acesso), 4)) or "—"
    coluna_chave = [
        Paragraph("CHAVE DE ACESSO", miudo),
        Paragraph(chave_fmt, ParagraphStyle("DfsChave", fontName="Helvetica-Bold", fontSize=8, leading=11)),
        Spacer(1, 0.15 * cm),
        Paragraph(f"NFS-e nº {dados['numero']}", direita),
    ]
    if consulta:
        qr = _qr(consulta)
        qr.seek(0)
        imagem_qr = Image(qr, width=2.5 * cm, height=2.5 * cm)
        imagem_qr.hAlign = "RIGHT"
        coluna_chave.append(imagem_qr)
    chave_tabela = Table([[coluna_chave]], colWidths=[19.2 * cm])
    chave_tabela.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.4, colors.HexColor("#0B3D91")),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f4f7fb")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elementos.append(chave_tabela)
    elementos.append(Spacer(1, 0.2 * cm))

    elementos.append(secao("IDENTIFICAÇÃO DA NFS-e"))
    elementos.append(grade([
        ["Número da NFS-e", dados["numero"], "Competência", dados["competencia"]],
        ["Data e hora da NFS-e", dados["emissao_nfse"], "Situação", dados["situacao"]],
        ["Número da DPS", dados["numero_dps"], "Série da DPS", dados["serie_dps"]],
        ["Data e hora da DPS", dados["emissao_dps"], "Emitente", "Prestador"],
    ]))
    elementos.append(Spacer(1, 0.15 * cm))

    elementos.append(secao("PRESTADOR DO SERVIÇO"))
    elementos.append(grade([
        ["CNPJ / CPF", dados["prestador_doc"], "Município", dados["prestador_municipio"]],
        ["Nome / Nome empresarial", dados["prestador_nome"], "Telefone", dados["prestador_fone"]],
        ["E-mail", dados["prestador_email"], "Simples Nacional", dados["simples"]],
        ["Endereço", dados["prestador_endereco"], "Regime de apuração", dados["regime_sn"]],
    ]))
    elementos.append(Spacer(1, 0.15 * cm))

    elementos.append(secao("TOMADOR DO SERVIÇO"))
    elementos.append(grade([
        ["CNPJ / CPF", dados["tomador_doc"], "Telefone", dados["tomador_fone"] or "—"],
        ["Nome / Nome empresarial", dados["tomador_nome"], "E-mail", dados["tomador_email"] or "—"],
        ["Endereço", dados["tomador_endereco"], "", ""],
    ]))
    elementos.append(Spacer(1, 0.15 * cm))

    elementos.append(secao("SERVIÇO PRESTADO"))
    elementos.append(grade([
        ["Código de tributação nacional", dados["codigo_servico"], "Local da prestação", dados["local_prestacao"]],
        ["Descrição do código", dados["descricao_codigo"], "Descrição do serviço", dados["descricao"]],
    ]))
    elementos.append(Spacer(1, 0.15 * cm))

    elementos.append(secao("TRIBUTAÇÃO MUNICIPAL — ISSQN"))
    elementos.append(grade([
        ["Tributação do ISSQN", dados["tributacao_iss"], "Município de incidência", dados["incidencia"]],
        ["Retenção do ISSQN", dados["retencao_iss"], "Alíquota aprox. SN", dados["aliquota_sn"]],
    ]))
    elementos.append(Spacer(1, 0.15 * cm))

    elementos.append(secao("VALOR TOTAL DA NFS-e"))
    elementos.append(grade([
        ["Valor do serviço", dados["valor_servico"], "Valor líquido", dados["valor_liquido"]],
    ]))
    elementos.append(Spacer(1, 0.25 * cm))
    if consulta:
        elementos.append(Paragraph(f"Consulte a autenticidade em {consulta}", centro))

    doc.build(elementos)
    buf.seek(0)
    return buf
