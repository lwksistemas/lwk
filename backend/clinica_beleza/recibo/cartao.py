"""Conta do comprovante, lida pelo HTML e pelo PDF.

Cada saída continua com o próprio desenho. Os números, títulos e formas
de pagamento saem daqui para os dois não divergirem.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .context import (
    _linha_documento_loja,
    _linha_tel_cep,
    _linhas_descontos_recibo,
    _linhas_taxa_consulta_recibo,
    comprovante_sem_cobranca,
    conta_com_saldo_recibo,
    cor_primaria_recibo,
    custeado_pela_clinica,
    formas_detalhadas_recibo,
    linha_valor_com_desconto_recibo,
    linha_vencimento_recibo,
    linhas_local_convenio_recibo,
    linhas_protocolo_informativo,
    procedimentos_exibidos_recibo,
    produtos_exibidos_recibo,
    recebido_a_maior_recibo,
    rotulo_forma_recibo,
    rotulo_numero_recibo,
    rotulo_situacao_recibo,
    rotulo_total_recibo,
    rotulo_valor_conta_recibo,
    situacao_recibo,
    tinta_recibo,
    titulo_recibo,
    aviso_exibido_recibo,
    nota_documento_recibo,
)
from .moeda import formatar_moeda_recibo


def hora_recibo(valor: str) -> str:
    texto = (valor or "").strip()
    if re.fullmatch(r"\d{2}/\d{2}/\d{4} \d{2}:\d{2}", texto):
        return texto.replace(" ", " às ", 1)
    return texto


def saldo_recibo(ctx: dict) -> float:
    valor_pago = ctx.get("valor_pago", 0) or 0
    valor_total = ctx.get("valor_total", 0) or 0
    return float(ctx.get("saldo_devedor", max(valor_total - valor_pago, 0)) or 0)


@dataclass(frozen=True)
class CartaoRecibo:
    titulo: str
    subtitulo: str
    situacao: str
    cor: str
    fundo: str
    fundo_tabela: str
    doc_line: str
    tel_cep: str
    data_emissao: str
    data_atendimento: str
    somente_produtos: bool
    custeio: bool
    comprovante: bool
    conta_pendente: bool
    saldo: float
    valor_pago: float
    valor_total: float
    subtotal: float
    rotulo_conta: str
    rotulo_pessoa: str
    taxas: tuple[tuple[str, float], ...]
    procedimentos: tuple[tuple[str, float, str], ...]
    convenios: tuple[tuple[str, str], ...]
    produtos: tuple[dict, ...]
    titulo_tabela_html: str
    titulo_tabela_pdf: str
    descontos: tuple[tuple[str, float], ...]
    protocolo: tuple[tuple[str, float], ...]
    valor_com_desconto: tuple[str, float] | None
    rotulo_destaque: str
    valor_destaque: float
    detalhes: tuple[dict, ...]
    varios_recebimentos: bool
    total_recebido: float
    formas_texto: str
    rotulo_forma: str
    mostrar_pago: bool
    extra: float
    mostrar_saldo: bool
    texto_vencimento: str
    aviso_vencimento: str
    vencido: bool
    aviso: str
    nota: str
    numero: object
    rotulo_numero: str
    rotulo_situacao: str


def _titulo_tabela_html(ctx: dict, qtd_linhas: int, qtd_produtos: int) -> str:
    if ctx.get("somente_produtos"):
        return "Produtos"
    if qtd_produtos and qtd_linhas > qtd_produtos:
        return "Procedimentos, serviços e produtos"
    if qtd_produtos:
        return "Produtos"
    return "Serviços / procedimentos"


def _titulo_tabela_pdf(ctx: dict, tem_servicos: bool, tem_produtos: bool) -> str:
    if ctx.get("somente_produtos") or (tem_produtos and not tem_servicos):
        return "Produtos"
    if tem_produtos and tem_servicos:
        return "Procedimentos, serviços e produtos"
    return "Serviços / procedimentos"


def montar_cartao(ctx: dict) -> CartaoRecibo:
    """ctx já reconciliado pelo HTML ou pelo PDF."""
    titulo, subtitulo = titulo_recibo(ctx)
    situacao = situacao_recibo(ctx)
    cor = cor_primaria_recibo(ctx.get("cor_primaria") or "")
    somente = bool(ctx.get("somente_produtos"))
    custeio = situacao == "quitado" and custeado_pela_clinica(ctx)
    comprovante = comprovante_sem_cobranca(ctx)
    conta_pendente = conta_com_saldo_recibo(ctx)
    saldo = saldo_recibo(ctx)
    valor_pago = float(ctx.get("valor_pago") or 0)
    valor_total = float(ctx.get("valor_total") or 0)
    subtotal = float(ctx.get("subtotal", ctx.get("valor_total") or 0))
    taxas = tuple(_linhas_taxa_consulta_recibo(ctx))
    procedimentos = tuple(
        (nome, valor, "1" if valor > 0.009 else "—")
        for nome, valor in procedimentos_exibidos_recibo(ctx)
    )
    convenios = tuple(linhas_local_convenio_recibo(ctx))
    produtos = tuple(produtos_exibidos_recibo(ctx))
    qtd_linhas = len(taxas) + len(procedimentos) + len(convenios) + len(produtos)
    descontos = tuple(_linhas_descontos_recibo(ctx))
    protocolo = tuple(linhas_protocolo_informativo(ctx))
    valor_com_desconto = linha_valor_com_desconto_recibo(ctx)
    rotulo = rotulo_total_recibo(ctx)
    if comprovante:
        rotulo_destaque = "Valor pago pelo paciente"
        valor_destaque = 0
    elif situacao == "quitado" and not custeio and rotulo == "Total":
        rotulo_destaque = "TOTAL PAGO"
        valor_destaque = valor_total
    elif rotulo == "Total":
        rotulo_destaque = "TOTAL"
        valor_destaque = valor_total
    else:
        rotulo_destaque = rotulo
        valor_destaque = valor_total

    detalhes = list(formas_detalhadas_recibo(ctx))
    if not detalhes and valor_pago > 0.009 and not custeio:
        detalhes = [{
            "data": "",
            "forma": rotulo_forma_recibo(ctx.get("metodo") or "Pagamento"),
            "valor": valor_pago,
        }]
    varios = len(detalhes) > 1
    if varios:
        formas_texto = ""
        total_recebido = round(sum(item["valor"] for item in detalhes), 2)
    elif detalhes:
        item = detalhes[0]
        quando = f' ({item["data"]})' if item["data"] else ""
        formas_texto = f'{item["forma"]}{quando} — {formatar_moeda_recibo(item["valor"])}'
        total_recebido = 0.0
    else:
        formas_texto = (ctx.get("condicao_cobranca") or "").strip()
        total_recebido = 0.0

    texto_vencimento = linha_vencimento_recibo(ctx)
    aviso_venc = texto_vencimento if conta_pendente else ""
    return CartaoRecibo(
        titulo=titulo,
        subtitulo=subtitulo,
        situacao=situacao,
        cor=cor,
        fundo=tinta_recibo(cor, 0.9),
        fundo_tabela=tinta_recibo(cor, 0.82),
        doc_line=_linha_documento_loja(ctx),
        tel_cep=ctx.get("loja_tel_cep") or _linha_tel_cep(ctx.get("loja_telefone", ""), ctx.get("loja_cep", "")),
        data_emissao=hora_recibo(ctx.get("data_emissao") or ctx.get("data") or "—"),
        data_atendimento=hora_recibo(ctx.get("data_atendimento") or ""),
        somente_produtos=somente,
        custeio=custeio,
        comprovante=comprovante,
        conta_pendente=conta_pendente,
        saldo=saldo,
        valor_pago=valor_pago,
        valor_total=valor_total,
        subtotal=subtotal,
        rotulo_conta=rotulo_valor_conta_recibo(ctx),
        rotulo_pessoa="Cliente" if somente else "Paciente",
        taxas=taxas,
        procedimentos=procedimentos,
        convenios=convenios,
        produtos=produtos,
        titulo_tabela_html=_titulo_tabela_html(ctx, qtd_linhas, len(produtos)),
        titulo_tabela_pdf=_titulo_tabela_pdf(ctx, bool(taxas or procedimentos), bool(produtos)),
        descontos=descontos,
        protocolo=protocolo,
        valor_com_desconto=valor_com_desconto,
        rotulo_destaque=rotulo_destaque,
        valor_destaque=float(valor_destaque or 0),
        detalhes=tuple(detalhes),
        varios_recebimentos=varios,
        total_recebido=total_recebido,
        formas_texto=formas_texto,
        rotulo_forma="Forma de pagamento",
        mostrar_pago=situacao == "parcial" and valor_pago > 0.009 and not conta_pendente,
        extra=recebido_a_maior_recibo(ctx),
        mostrar_saldo=not custeio and saldo > 0.009 and not conta_pendente,
        texto_vencimento=texto_vencimento,
        aviso_vencimento=aviso_venc,
        vencido=aviso_venc.startswith("Vencido"),
        aviso=aviso_exibido_recibo(ctx),
        nota=nota_documento_recibo(ctx),
        numero=ctx.get("recibo_numero"),
        rotulo_numero=rotulo_numero_recibo(ctx),
        rotulo_situacao=rotulo_situacao_recibo(ctx),
    )
