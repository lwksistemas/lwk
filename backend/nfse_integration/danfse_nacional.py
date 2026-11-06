"""DANFSe da NFS-e Nacional a partir do XML autorizado.

A API do ADN que gerava o PDF foi desligada em agosto de 2026. O portal
só entrega o arquivo depois de um captcha. A Nota Técnica 008 manda o
sistema emissor montar o DANFSe com os dados do XML.

O miolo segue a grade do DANFSe v2.0: identificação com a chave e o QR,
prestador, tomador, serviço, ISSQN, tributos federais, IBS/CBS e valor.
Campo que o XML não traz fica com traço.
"""
from __future__ import annotations

import logging
from datetime import datetime
from io import BytesIO
from pathlib import Path

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
    Table,
    TableStyle,
)
from xml.sax.saxutils import escape

from nfse_integration.numero_exibicao import PORTAL_CONSULTA_NACIONAL

logger = logging.getLogger(__name__)

_LOGO = Path(__file__).resolve().parent / "assets" / "logo-nfse-horizontal.png"
_LARGURA = 19.6 * cm

_OP_SIMPLES = {
    "1": "Não optante",
    "2": "Optante — MEI",
    "3": "Optante — ME/EPP",
}
_OP_SIMPLES_LONGO = {
    "1": "Não Optante",
    "2": "Optante - Microempreendedor Individual (MEI)",
    "3": "Optante - Microempresa ou Empresa de Pequeno Porte (ME/EPP)",
}
_REG_APURACAO = {
    "1": "Federais e municipal pelo Simples Nacional",
    "2": "Federais pelo Simples Nacional e ISSQN fora do Simples",
    "3": "Federais e municipal fora do Simples Nacional",
}
_REG_APURACAO_LONGO = {
    "1": "Regime de apuração dos tributos federais e municipal pelo Simples Nacional",
    "2": "Regime de apuração dos tributos federais pelo Simples Nacional e o ISSQN por fora",
    "3": "Regime de apuração dos tributos federais e municipal por fora do Simples Nacional",
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
_RET_ISS_LONGO = {
    "1": "Não Retido",
    "2": "Retido pelo Tomador",
    "3": "Retido pelo Intermediário",
}
_REG_ESPECIAL = {
    "0": "Nenhum",
    "1": "Ato Cooperado (Cooperativa)",
    "2": "Estimativa",
    "3": "Microempresa Municipal",
    "4": "Notário ou Registrador",
    "5": "Profissional Autônomo",
    "6": "Sociedade de Profissionais",
}
_EMITENTE = {"1": "Prestador", "2": "Tomador", "3": "Intermediário"}
_AMBIENTE = {"1": "Produção", "2": "Homologação"}
_GERADOR = {"1": "Município", "2": "Emissor Nacional"}
_SITUACAO = {"100": "NFS-e Gerada", "101": "NFS-e Cancelada", "102": "NFS-e Substituída"}

_BORDA = colors.HexColor("#222222")
_CINZA = colors.HexColor("#555555")


def _texto(el, nome: str) -> str:
    if el is None:
        return ""
    for filho in el.iter():
        if etree.QName(filho.tag).localname == nome and (filho.text or "").strip():
            return filho.text.strip()
    return ""


def _primeiro(root, nome: str):
    if root is None:
        return None
    for el in root.iter():
        if etree.QName(el.tag).localname == nome:
            return el
    return None


def _filho(el, nome: str):
    if el is None:
        return None
    for filho in el:
        if etree.QName(filho.tag).localname == nome:
            return filho
    return None


def _data(valor: str) -> str:
    bruto = (valor or "").strip()
    if not bruto:
        return ""
    try:
        momento = datetime.fromisoformat(bruto)
    except ValueError:
        return bruto[:19].replace("T", " ")
    return momento.strftime("%d/%m/%Y %H:%M:%S")


def _data_curta(valor: str) -> str:
    bruto = (valor or "").strip()
    if len(bruto) >= 10 and bruto[4] == "-":
        ano, mes, dia = bruto[:10].split("-")
        return f"{dia}/{mes}/{ano}"
    return bruto


def _moeda(valor: str) -> str:
    bruto = (valor or "").strip().replace(",", ".")
    if not bruto:
        return ""
    try:
        numero = float(bruto)
    except ValueError:
        return bruto
    texto = f"{numero:,.2f}"
    return "R$ " + texto.replace(",", "X").replace(".", ",").replace("X", ".")


def _digitos(valor: str) -> str:
    return "".join(c for c in (valor or "") if c.isdigit())


def _documento(valor: str) -> str:
    digitos = _digitos(valor)
    if len(digitos) == 14:
        return f"{digitos[:2]}.{digitos[2:5]}.{digitos[5:8]}/{digitos[8:12]}-{digitos[12:]}"
    if len(digitos) == 11:
        return f"{digitos[:3]}.{digitos[3:6]}.{digitos[6:9]}-{digitos[9:]}"
    return valor


def _fone(valor: str) -> str:
    digitos = _digitos(valor)
    if len(digitos) == 10:
        return f"({digitos[:2]}) {digitos[2:6]}-{digitos[6:]}"
    if len(digitos) == 11:
        return f"({digitos[:2]}) {digitos[2:7]}-{digitos[7:]}"
    return valor


def _cep(valor: str) -> str:
    digitos = _digitos(valor)
    if len(digitos) == 8:
        return f"{digitos[:5]}-{digitos[5:]}"
    return valor


def _codigo_nacional(valor: str) -> str:
    digitos = _digitos(valor)
    if len(digitos) == 6:
        return f"{digitos[:2]}.{digitos[2:4]}.{digitos[4:]}"
    return valor


def _codigo_nbs(valor: str) -> str:
    digitos = _digitos(valor)
    if len(digitos) == 9:
        return f"{digitos[0]}.{digitos[1:5]}.{digitos[5:7]}.{digitos[7:]}"
    return valor


def _endereco_linha(bloco) -> str:
    if bloco is None:
        return ""
    partes = [
        _texto(bloco, "xLgr"),
        _texto(bloco, "nro"),
        _texto(bloco, "xCpl"),
        _texto(bloco, "xBairro"),
    ]
    return ", ".join(p for p in partes if p)


def _cidade_uf(cidade: str, uf: str) -> str:
    cidade = (cidade or "").strip()
    uf = (uf or "").strip()
    if cidade and uf:
        return f"{cidade} / {uf}"
    return cidade or uf


def _local_pais(cidade: str, uf: str) -> str:
    base = _cidade_uf(cidade, uf)
    if not base:
        return ""
    return f"{base} / BR"


def _rotulo(mapa: dict[str, str], valor: str) -> str:
    codigo = (valor or "").strip()
    if not codigo:
        return ""
    return mapa.get(codigo, codigo)


def _traco(valor: str) -> str:
    texto = (valor or "").strip()
    return texto or "-"


def ler_dados_danfse(xml_nfse: str, *, chave: str = "") -> dict[str, str]:
    """Lê do XML o que a DANFSe imprime. Ausência vira string vazia."""
    root = etree.fromstring(xml_nfse.encode("utf-8") if isinstance(xml_nfse, str) else xml_nfse)
    inf = _primeiro(root, "infNFSe")
    if inf is None:
        inf = root
    dps = _primeiro(root, "infDPS")
    emit = _primeiro(inf, "emit")
    prest = _primeiro(dps, "prest") if dps is not None else None
    toma = _primeiro(dps, "toma") if dps is not None else None
    serv = _primeiro(dps, "serv") if dps is not None else None
    valores_nf = _filho(inf, "valores")
    end_prest = _primeiro(emit, "enderNac") if emit is not None else None
    end_toma = _primeiro(toma, "endNac") if toma is not None else None
    uf_prest = _texto(end_prest, "UF")
    cidade_prest = _texto(end_prest, "xMun") or _texto(inf, "xLocEmi")
    numero = _texto(inf, "nNFSe")
    c_trib = _texto(serv, "cTribNac") if serv is not None else ""
    c_mun = _texto(serv, "cTribMun") if serv is not None else ""
    codigo_fmt = _codigo_nacional(c_trib)
    if c_mun and c_mun not in {"0", "000"}:
        codigo_fmt = " / ".join(p for p in (codigo_fmt, c_mun) if p)
    aliquota = _texto(dps, "pAliq") if dps is not None else ""
    p_sn = _texto(dps, "pTotTribSN") if dps is not None else ""
    info = _texto(inf, "xInfComp") or (_texto(dps, "xInfComp") if dps is not None else "")
    if p_sn and "Simples Nacional" not in info:
        extra = f"Percentual aproximado dos tributos do Simples Nacional: {p_sn.replace('.', ',')}%."
        info = f"{info} {extra}".strip() if info else extra
    return {
        "chave": (chave or "").strip(),
        "numero": str(int(numero)) if numero.isdigit() else numero,
        "municipio": _texto(inf, "xLocEmi"),
        "municipio_uf": _cidade_uf(_texto(inf, "xLocEmi"), uf_prest),
        "competencia": _data_curta(_texto(dps, "dCompet") if dps is not None else ""),
        "emissao_nfse": _data(_texto(inf, "dhProc")),
        "numero_dps": _texto(dps, "nDPS") if dps is not None else "",
        "serie_dps": _texto(dps, "serie") if dps is not None else "",
        "emissao_dps": _data(_texto(dps, "dhEmi") if dps is not None else ""),
        "emitente": _rotulo(_EMITENTE, _texto(dps, "tpEmit") if dps is not None else "") or "Prestador",
        "situacao": _rotulo(_SITUACAO, _texto(inf, "cStat")),
        "finalidade": _texto(inf, "finNFSe") or (_texto(dps, "finNFSe") if dps is not None else ""),
        "ambiente": _rotulo(_AMBIENTE, _texto(dps, "tpAmb") if dps is not None else ""),
        "gerador": _rotulo(_GERADOR, _texto(inf, "ambGer")),
        "amb_ger_cod": _texto(inf, "ambGer"),
        "tp_amb_cod": _texto(dps, "tpAmb") if dps is not None else "",
        "prestador_doc": _documento(_texto(emit, "CNPJ") or _texto(emit, "CPF")),
        "prestador_nome": _texto(emit, "xNome"),
        "prestador_endereco": _endereco_linha(end_prest),
        "prestador_fone": _fone(_texto(emit, "fone")),
        "prestador_email": _texto(emit, "email"),
        "prestador_im": _texto(emit, "IM"),
        "prestador_municipio": cidade_prest,
        "prestador_mun_uf": _cidade_uf(cidade_prest, uf_prest),
        "prestador_ibge_cep": " / ".join(
            p for p in (_texto(end_prest, "cMun"), _cep(_texto(end_prest, "CEP"))) if p
        ),
        "simples": _rotulo(_OP_SIMPLES, _texto(prest, "opSimpNac") if prest is not None else ""),
        "simples_longo": _rotulo(_OP_SIMPLES_LONGO, _texto(prest, "opSimpNac") if prest is not None else ""),
        "regime_sn": _rotulo(_REG_APURACAO, _texto(prest, "regApTribSN") if prest is not None else ""),
        "regime_longo": _rotulo(_REG_APURACAO_LONGO, _texto(prest, "regApTribSN") if prest is not None else ""),
        "regime_especial": _rotulo(_REG_ESPECIAL, _texto(prest, "regEspTrib") if prest is not None else "") or "Nenhum",
        "tomador_doc": _documento(_texto(toma, "CNPJ") or _texto(toma, "CPF")) if toma is not None else "",
        "tomador_nome": _texto(toma, "xNome") if toma is not None else "",
        "tomador_endereco": _endereco_linha(end_toma),
        "tomador_fone": _fone(_texto(toma, "fone")) if toma is not None else "",
        "tomador_email": _texto(toma, "email") if toma is not None else "",
        "tomador_im": _texto(toma, "IM") if toma is not None else "",
        "tomador_mun_uf": _cidade_uf(_texto(end_toma, "xMun"), _texto(end_toma, "UF")),
        "tomador_ibge_cep": " / ".join(
            p for p in (_texto(end_toma, "cMun"), _cep(_texto(end_toma, "CEP"))) if p
        ),
        "codigo_servico": c_trib,
        "codigo_fmt": codigo_fmt,
        "nbs": _codigo_nbs(_texto(serv, "cNBS") if serv is not None else ""),
        "descricao_codigo": _texto(inf, "xTribNac"),
        "local_prestacao": _texto(inf, "xLocPrestacao"),
        "local_fmt": _local_pais(_texto(inf, "xLocPrestacao"), uf_prest),
        "descricao": _texto(serv, "xDescServ") if serv is not None else "",
        "tributacao_iss": _rotulo(_TRIB_ISS, _texto(dps, "tribISSQN") if dps is not None else ""),
        "retencao_iss": _rotulo(_RET_ISS, _texto(dps, "tpRetISSQN") if dps is not None else ""),
        "retencao_longa": _rotulo(_RET_ISS_LONGO, _texto(dps, "tpRetISSQN") if dps is not None else ""),
        "incidencia": _texto(inf, "xLocIncid"),
        "incidencia_fmt": _local_pais(_texto(inf, "xLocIncid"), uf_prest),
        "aliquota_sn": (p_sn + "%") if p_sn else "",
        "aliquota_aplicada": (aliquota.replace(".", ",") + "%") if aliquota else "",
        "bc_iss": _moeda(_texto(dps, "vBC") if dps is not None else ""),
        "iss_apurado": _moeda(_texto(inf, "vISSQN") or (_texto(dps, "vISSQN") if dps is not None else "")),
        "valor_servico": _moeda(_texto(dps, "vServ") if dps is not None else ""),
        "valor_liquido": _moeda(_texto(valores_nf, "vLiq") if valores_nf is not None else ""),
        "desconto_incond": _moeda(_texto(dps, "vDescIncond") if dps is not None else ""),
        "desconto_cond": _moeda(_texto(dps, "vDescCond") if dps is not None else ""),
        "info_comp": info,
    }


def _qr(url: str) -> BytesIO:
    imagem = qrcode.make(url)
    buf = BytesIO()
    imagem.save(buf, format="PNG")
    buf.seek(0)
    return buf


def _estilos() -> dict[str, ParagraphStyle]:
    base = ParagraphStyle("DfsBase", fontName="Helvetica", fontSize=7, leading=8.5, textColor=colors.HexColor("#111111"))
    return {
        "base": base,
        "titulo": ParagraphStyle("DfsTitulo", fontName="Helvetica-Bold", fontSize=11, leading=13, alignment=TA_CENTER),
        "sub": ParagraphStyle("DfsSub", fontName="Helvetica-Bold", fontSize=8, leading=10, alignment=TA_CENTER),
        "dir": ParagraphStyle("DfsDir", fontName="Helvetica", fontSize=6.5, leading=8, alignment=TA_RIGHT),
        "secao": ParagraphStyle("DfsSecao", fontName="Helvetica-Bold", fontSize=6.4, leading=8),
        "aviso": ParagraphStyle("DfsAviso", fontName="Helvetica-Bold", fontSize=6.5, leading=8, alignment=TA_CENTER),
        "qr": ParagraphStyle("DfsQr", fontName="Helvetica", fontSize=5.2, leading=6.4, alignment=TA_CENTER, textColor=_CINZA),
        "chave": ParagraphStyle("DfsChave", fontName="Helvetica-Bold", fontSize=8, leading=10),
        "miudo": ParagraphStyle("DfsMiudo", fontName="Helvetica", fontSize=5.5, leading=7, textColor=_CINZA),
        "valor": base,
        "info": ParagraphStyle("DfsInfo", fontName="Helvetica", fontSize=6, leading=7.5),
        "hom": ParagraphStyle(
            "DfsHom", fontName="Helvetica-Bold", fontSize=7, leading=9, alignment=TA_CENTER, textColor=colors.red,
        ),
    }


def _p(texto: str, estilo: ParagraphStyle) -> Paragraph:
    return Paragraph(escape(texto or ""), estilo)


def _campo(rotulo: str, valor: str, *, cor: str = "#111111") -> Paragraph:
    return Paragraph(
        f'<font name="Helvetica" size="5.2" color="#555555">{escape(rotulo)}</font><br/>'
        f'<font name="Helvetica" size="7" color="{cor}">{escape(_traco(valor))}</font>',
        ParagraphStyle("DfsCampo", fontName="Helvetica", fontSize=7, leading=8.2),
    )


def _grade(celulas: list[list], colunas: list[float], spans: list[tuple] | None = None) -> Table:
    tabela = Table(celulas, colWidths=colunas)
    estilo = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, _BORDA),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
    ]
    for inicio, fim in spans or []:
        estilo.append(("SPAN", inicio, fim))
    tabela.setStyle(TableStyle(estilo))
    return tabela


def gerar_danfse_nacional(xml_nfse: str, *, chave: str = "", cancelada: bool = False) -> BytesIO:
    """Monta o PDF do DANFSe v2.0 na grade do documento auxiliar.

    O XML autorizado permanece com a situação da emissão. O cancelamento
    é um evento separado, então a marca de cancelada vem do status da nota.
    """
    dados = ler_dados_danfse(xml_nfse, chave=chave)
    if cancelada:
        dados["situacao"] = "NFS-e Cancelada"
    chave_acesso = dados["chave"]
    consulta = PORTAL_CONSULTA_NACIONAL.format(chave=chave_acesso) if chave_acesso else ""
    est = _estilos()
    quatro = [_LARGURA / 4] * 4

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        title=f"DANFSe v2.0 - NFS-e nº {dados['numero'] or '-'}",
        author=dados["prestador_nome"] or "NFS-e Nacional",
        topMargin=0.4 * cm,
        bottomMargin=0.4 * cm,
        leftMargin=0.7 * cm,
        rightMargin=0.7 * cm,
    )

    cabeca_meio = [
        _p("DANFSe v2.0", est["titulo"]),
        _p("Documento Auxiliar da NFS-e", est["sub"]),
    ]
    if dados["ambiente"] == "Homologação":
        cabeca_meio.append(_p("NFS-e SEM VALIDADE JURÍDICA", est["hom"]))
    if cancelada:
        cabeca_meio.append(_p("NFS-e CANCELADA", est["hom"]))
    direita = [
        _p(f"Município: {_traco(dados['municipio_uf'])}", est["dir"]),
        _p(f"Ambiente Gerador: {_traco(dados['amb_ger_cod'])}", est["dir"]),
        _p(f"Tipo de Ambiente: {_traco(dados['tp_amb_cod'])}", est["dir"]),
    ]
    logo = Image(str(_LOGO), width=4.4 * cm, height=1.05 * cm) if _LOGO.is_file() else _p("NFS-e", est["titulo"])
    cabeca = Table([[logo, cabeca_meio, direita]], colWidths=[4.8 * cm, 9.2 * cm, 5.6 * cm])
    cabeca.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (-1, -1), 0.6, _BORDA),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
    ]))

    qr_celula: list = []
    if consulta:
        imagem_qr = Image(_qr(consulta), width=2.15 * cm, height=2.15 * cm)
        imagem_qr.hAlign = "CENTER"
        qr_celula.append(imagem_qr)
    qr_celula.append(Paragraph(
        "A autenticidade desta NFS-e pode ser verificada pela leitura deste código QR "
        "ou pela consulta da chave de acesso no portal nacional da NFS-e",
        est["qr"],
    ))
    col_id = (_LARGURA - 3.5 * cm) / 3
    identificacao = _grade(
        [
            [_p("CHAVE DE ACESSO DA NFS-E", est["miudo"]), "", "", qr_celula],
            [_p(chave_acesso or "-", est["chave"]), "", "", ""],
            [
                _campo("NÚMERO DA NFS-E", dados["numero"]),
                _campo("COMPETÊNCIA DA NFS-E", dados["competencia"]),
                _campo("DATA E HORA DA EMISSÃO DA NFS-E", dados["emissao_nfse"]),
                "",
            ],
            [
                _campo("NÚMERO DA DPS", dados["numero_dps"]),
                _campo("SÉRIE DA DPS", dados["serie_dps"]),
                _campo("DATA E HORA DA EMISSÃO DA DPS", dados["emissao_dps"]),
                "",
            ],
            [
                _campo("EMITENTE DA NFS-E", dados["emitente"]),
                _campo(
                    "SITUAÇÃO DA NFS-E",
                    dados["situacao"],
                    cor="#c1121f" if cancelada else "#111111",
                ),
                _campo("FINALIDADE", dados["finalidade"]),
                "",
            ],
        ],
        [col_id, col_id, col_id, 3.5 * cm],
        spans=[((0, 0), (2, 0)), ((0, 1), (2, 1)), ((3, 0), (3, 4))],
    )

    def parte(titulo: str) -> Paragraph:
        return _p(titulo, est["secao"])

    prestador = _grade(
        [
            [
                parte("PRESTADOR / FORNECEDOR"),
                _campo("CNPJ / CPF / NIF", dados["prestador_doc"]),
                _campo("Indicador Municipal (Inscrição)", dados["prestador_im"]),
                _campo("Telefone", dados["prestador_fone"]),
            ],
            [
                _campo("Nome / Nome Empresarial", dados["prestador_nome"]),
                "",
                _campo("Município / Sigla UF", dados["prestador_mun_uf"]),
                _campo("Código IBGE / CEP", dados["prestador_ibge_cep"]),
            ],
            [
                _campo("Endereço", dados["prestador_endereco"]),
                "",
                _campo("E-mail", dados["prestador_email"]),
                "",
            ],
            [
                _campo("Simples Nacional na Data de Competência", dados["simples_longo"]),
                "",
                _campo("Regime de Apuração Tributária pelo SN", dados["regime_longo"]),
                "",
            ],
        ],
        quatro,
        spans=[((0, 1), (1, 1)), ((2, 2), (3, 2)), ((0, 3), (1, 3)), ((2, 3), (3, 3))],
    )
    tomador = _grade(
        [
            [
                parte("TOMADOR / ADQUIRENTE"),
                _campo("CNPJ / CPF / NIF", dados["tomador_doc"]),
                _campo("Indicador Municipal (Inscrição)", dados["tomador_im"]),
                _campo("Telefone", dados["tomador_fone"]),
            ],
            [
                _campo("Nome / Nome Empresarial", dados["tomador_nome"]),
                "",
                _campo("Município / Sigla UF", dados["tomador_mun_uf"]),
                _campo("Código IBGE / CEP", dados["tomador_ibge_cep"]),
            ],
            [
                _campo("Endereço", dados["tomador_endereco"]),
                "",
                _campo("E-mail", dados["tomador_email"]),
                "",
            ],
        ],
        quatro,
        spans=[((0, 1), (1, 1)), ((2, 2), (3, 2))],
    )
    avisos = _grade(
        [
            [_p("DESTINATÁRIO DA OPERAÇÃO NÃO IDENTIFICADO NA NFS-e", est["aviso"])],
            [_p("INTERMEDIÁRIO DA OPERAÇÃO NÃO IDENTIFICADO NA NFS-e", est["aviso"])],
        ],
        [_LARGURA],
    )
    servico = _grade(
        [
            [
                [parte("SERVIÇO PRESTADO"), _p(_traco(dados["descricao_codigo"]), est["valor"])],
                _campo("Código de Tributação Nacional / Municipal", dados["codigo_fmt"]),
                _campo("Código da NBS", dados["nbs"]),
                _campo("Local da Prestação / Sigla UF / País", dados["local_fmt"]),
            ],
            [_campo("Descrição do Serviço", dados["descricao"]), "", "", ""],
        ],
        quatro,
        spans=[((0, 1), (3, 1))],
    )
    issqn = _grade(
        [
            [
                parte("TRIBUTAÇÃO MUNICIPAL (ISSQN)"),
                _campo("Tipo de Tributação do ISSQN", dados["tributacao_iss"]),
                _campo("Município / Sigla UF / País de Incidência do ISSQN", dados["incidencia_fmt"]),
                "",
            ],
            [
                _campo("Regime Especial de Tributação do ISSQN", dados["regime_especial"]),
                _campo("Tipo de Imunidade do ISSQN", ""),
                _campo("Suspensão da Exigibilidade do ISSQN", ""),
                _campo("Número Processo Suspensão", ""),
            ],
            [
                _campo("Benefício Municipal", ""),
                _campo("Cálculo do BM", ""),
                _campo("Total Deduções/Reduções", ""),
                _campo("Desconto Incondicionado", dados["desconto_incond"]),
            ],
            [
                _campo("BC ISSQN", dados["bc_iss"]),
                _campo("Alíquota Aplicada", dados["aliquota_aplicada"]),
                _campo("Retenção do ISSQN", dados["retencao_longa"]),
                _campo("ISSQN Apurado", dados["iss_apurado"]),
            ],
        ],
        quatro,
        spans=[((2, 0), (3, 0))],
    )
    federal = _grade(
        [
            [
                parte("TRIBUTAÇÃO FEDERAL (EXCETO CBS)"),
                _campo("IRRF", ""),
                _campo("Contribuição Previdenciária - Retida", ""),
                _campo("Contribuições Sociais - Retidas", ""),
            ],
            [
                _campo("PIS - Débito Apuração Própria", ""),
                _campo("COFINS - Débito Apuração Própria", ""),
                _campo("Descrição Contrib. Sociais - Retidas", ""),
                "",
            ],
        ],
        quatro,
        spans=[((2, 1), (3, 1))],
    )
    ibs = _grade(
        [
            [
                parte("TRIBUTAÇÃO IBS / CBS"),
                _campo("CST / cClassTrib", ""),
                _campo("Indicador de Operação / Código IBGE Incidência / Município Incidência / Sigla UF", ""),
                "",
            ],
            [
                _campo("Exclusões e Reduções da Base de Cálculo", ""),
                _campo("Base de Cálculo Após Exclusões e Reduções", ""),
                _campo("Red. Alíquota IBS / Red. Alíquota CBS", ""),
                _campo("Alíquota - IBS UF / IBS Mun", ""),
            ],
            [
                _campo("Alíq. Efetiva Municipal - IBS", ""),
                _campo("Valor Apurado Municipal - IBS", ""),
                _campo("Alíq. Efetiva Estadual - IBS", ""),
                _campo("Valor Apurado Estadual - IBS", ""),
            ],
            [
                _campo("Valor Total Apurado - IBS", ""),
                _campo("Alíquota - CBS", ""),
                _campo("Alíquota Efetiva - CBS", ""),
                _campo("Valor Total Apurado - CBS", ""),
            ],
        ],
        quatro,
        spans=[((2, 0), (3, 0))],
    )
    totais = _grade(
        [
            [
                parte("VALOR TOTAL DA NFS-E"),
                _campo("VALOR DA OPERAÇÃO / SERVIÇO", dados["valor_servico"]),
                _campo("Desconto Incondicionado", dados["desconto_incond"]),
                _campo("Desconto Condicionado", dados["desconto_cond"]),
            ],
            [
                _campo("Total das Retenções (ISSQN / Federais)", ""),
                _campo("VALOR LÍQUIDO DA NFS-e", dados["valor_liquido"]),
                _campo("Total do IBS/CBS", ""),
                _campo("VALOR LÍQUIDO DA NFS-e + IBS/CBS", ""),
            ],
        ],
        quatro,
    )
    complementares = _grade(
        [[
            [
                parte("INFORMAÇÕES COMPLEMENTARES"),
                Paragraph(escape(_traco(dados["info_comp"])), est["info"]),
                Paragraph(
                    "Totais Aproximados dos Tributos cfe. Lei nº 12.741/2012: "
                    "Federais: - ; Estaduais: - ; Municipais: -",
                    est["info"],
                ),
            ]
        ]],
        [_LARGURA],
    )

    doc.build([
        cabeca,
        identificacao,
        prestador,
        tomador,
        avisos,
        servico,
        issqn,
        federal,
        ibs,
        totais,
        complementares,
    ])
    buf.seek(0)
    return buf
