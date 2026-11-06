"""Recibo HTML — o mesmo visual da venda de produtos e do atendimento."""
from __future__ import annotations

import html
import re

from .context import (
    _linha_documento_loja,
    _linha_tel_cep,
    _linhas_descontos_recibo,
    _linhas_taxa_consulta_recibo,
    _obter_dados_contexto,
    aviso_exibido_recibo,
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
    reconciliar_conta_recibo,
    rotulo_forma_recibo,
    nota_documento_recibo,
    rotulo_numero_recibo,
    rotulo_situacao_recibo,
    rotulo_subtotal_recibo,
    rotulo_total_recibo,
    rotulo_valor_conta_recibo,
    situacao_comprovante_recibo,
    situacao_recibo,
    texto_cadastro_recibo,
    tinta_recibo,
    titulo_recibo,
)
from .cartao import CartaoRecibo, montar_cartao
from .moeda import formatar_moeda_recibo


def _icone(nome: str, cor: str, tamanho: int = 16) -> str:
    """Desenho de linha na cor da clínica, no mesmo lugar do exemplo."""
    caminhos = {
        "pessoa": (
            '<circle cx="12" cy="8" r="3.1"/>'
            '<path d="M5.6 19.4c.8-3.3 3-4.8 6.4-4.8s5.6 1.5 6.4 4.8"/>'
        ),
        "cpf": (
            '<rect x="3.5" y="5" width="17" height="14" rx="2"/>'
            '<circle cx="8.8" cy="11.2" r="1.7"/>'
            '<path d="M6.6 15.7c.5-1.3 1.3-1.9 2.2-1.9s1.7.6 2.2 1.9"/>'
            '<path d="M13.4 9.6h5.2M13.4 12.4h5.2M13.4 15.2h3.2"/>'
        ),
        "calendario": (
            '<rect x="4" y="5" width="16" height="15" rx="2"/>'
            '<path d="M8 3.5v4M16 3.5v4M4 10h16"/>'
        ),
        "pin": (
            '<path d="M12 21s6.2-5.4 6.2-10.2a6.2 6.2 0 1 0-12.4 0C5.8 15.6 12 21 12 21z"/>'
            '<circle cx="12" cy="10.7" r="2"/>'
        ),
        "telefone": (
            '<rect x="8" y="3" width="8" height="18" rx="1.8"/>'
            '<path d="M10.4 6.2h3.2"/>'
        ),
        "email": (
            '<rect x="3" y="6" width="18" height="12" rx="2"/>'
            '<path d="M4 7.6 12 13l8-5.4"/>'
        ),
        "cartao": (
            '<rect x="2.5" y="5.5" width="19" height="13" rx="2"/>'
            '<path d="M2.5 10h19"/>'
        ),
        "caixa": (
            '<path d="M8 8V6.8A1.6 1.6 0 0 1 9.6 5.2h4.8A1.6 1.6 0 0 1 16 6.8V8"/>'
            '<rect x="3.5" y="8" width="17" height="11" rx="2"/>'
            '<path d="M7 12.3h4M7 15.3h8"/>'
        ),
    }
    return (
        f'<svg class="icone" width="{tamanho}" height="{tamanho}" viewBox="0 0 24 24" '
        f'fill="none" stroke="{cor}" stroke-width="1.7" stroke-linecap="round" '
        f'stroke-linejoin="round" aria-hidden="true">{caminhos[nome]}</svg>'
    )


def _icone_quitado() -> str:
    return (
        '<svg class="icone" width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">'
        '<circle cx="12" cy="12" r="10" fill="#1B8A45"/>'
        '<path d="M7.2 12.4 10.3 15.5 16.8 8.6" fill="none" stroke="#fff" '
        'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>'
        "</svg>"
    )


def _campo(icone: str, rotulo: str, valor: str, cor: str) -> str:
    return (
        f'<p class="campo">{_icone(icone, cor)}'
        f'<span><span class="ico">{_t(rotulo)}:</span> {_t(valor)}</span></p>'
    )


def _t(valor) -> str:
    return html.escape(str(valor or ""), quote=True)


def _nome_servico_html(nome: str) -> str:
    """A quantidade e a unidade permanecem na mesma linha do recibo."""
    return re.sub(
        r"(\d+(?:[.,]\d+)?) ([A-Za-zµμ]+)",
        lambda m: f"{m.group(1)}&nbsp;{m.group(2)}",
        _t(nome),
        count=1,
    )


def _logo_http(url: str) -> str:
    texto = (url or "").strip()
    if texto.startswith("https://") or texto.startswith("http://"):
        return texto
    return ""


def _tipo_imagem(conteudo: bytes) -> str:
    if conteudo.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if conteudo.startswith(b"GIF8"):
        return "image/gif"
    if conteudo.startswith(b"RIFF") and conteudo[8:12] == b"WEBP":
        return "image/webp"
    return "image/png"


def _src_logo_recibo(url: str) -> str:
    """Coloca a logomarca dentro do HTML. O endereço público da mídia exige assinatura e o Chrome não imprime a imagem se o download falha."""
    import base64

    texto = _logo_http(url)
    if not texto:
        return ""
    from clinica_beleza.pdf_common.logo import baixar_logo

    conteudo = baixar_logo(texto, timeout=8)
    if not conteudo or len(conteudo) > 2_000_000:
        from core.media_storage import assinar_url_midia

        return assinar_url_midia(texto)
    codigo = base64.b64encode(conteudo).decode("ascii")
    return f"data:{_tipo_imagem(conteudo)};base64,{codigo}"


def _celula_item(descricao: str, quantidade: str, unitario: str, subtotal: str) -> str:
    return (
        "<tr>"
        f'<td class="desc">{descricao}</td>'
        f'<td class="num">{quantidade}</td>'
        f'<td class="num">{unitario}</td>'
        f'<td class="num">{subtotal}</td>'
        "</tr>"
    )


def _linhas_tabela(c: CartaoRecibo) -> str:
    """Produtos e atendimentos usam as mesmas colunas."""
    linhas = []
    for label, valor in c.taxas:
        linhas.append(_celula_item(
            f"• {_t(label)}",
            "1",
            formatar_moeda_recibo(valor),
            formatar_moeda_recibo(valor),
        ))
    for nome, valor, quantidade in c.procedimentos:
        unitario = formatar_moeda_recibo(valor) if quantidade == "1" else "—"
        linhas.append(_celula_item(
            _nome_servico_html(nome),
            quantidade,
            unitario,
            formatar_moeda_recibo(valor),
        ))
    for label, valor in c.convenios:
        linhas.append(
            f'<tr><td class="desc" colspan="4">{_t(label)} {_t(valor)}</td></tr>'
        )
    for item in c.produtos:
        descricao = _t(item["nome"])
        if item["desconto"] > 0.009:
            descricao += f'<br><span class="miudo">desc. {formatar_moeda_recibo(item["desconto"])}</span>'
        linhas.append(_celula_item(
            descricao,
            _t(item["quantidade"]),
            formatar_moeda_recibo(item["preco_unitario"]),
            formatar_moeda_recibo(item["subtotal"]),
        ))
    return "".join(linhas)


def estilo_folha_recibo(cor: str) -> str:
    """Folha A4 do recibo. O resumo do caixa usa a mesma folha."""
    fundo = tinta_recibo(cor, 0.9)
    fundo_tabela = tinta_recibo(cor, 0.82)
    return f"""
  @page {{ size: A4; margin: 12mm; }}
  html {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
  html, body {{ margin: 0; background: #fff; color: #2b2430; }}
  body {{ font-family: "Segoe UI", system-ui, sans-serif; }}
  .folha {{ max-width: 720px; margin: 0 auto; padding: 28px 32px 36px; }}
  .topo {{ text-align: center; }}
  .logo {{ max-height: 92px; max-width: 240px; object-fit: contain; }}
  .marca {{ margin: 0; font-size: 28px; letter-spacing: 0.18em; color: {cor}; font-weight: 700; }}
  .razao {{ margin: 8px 0 0; font-size: 13px; letter-spacing: 0.04em; color: #5c5562; text-transform: uppercase; }}
  .doc, .contato {{ margin: 4px 0 0; font-size: 13px; color: #5c5562; }}
  .icone {{ flex: 0 0 auto; display: block; }}
  .campo, .item {{ display: flex; align-items: center; gap: 8px; }}
  .contato.linha {{ display: flex; justify-content: center; align-items: flex-start; gap: 6px; margin: 3px auto 0; max-width: 560px; }}
  .tinta {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
  .faixa {{ margin: 18px 0 8px; background-color: {cor}; box-shadow: inset 0 0 0 999px {cor}; color: #fff; text-align: center; border-radius: 10px; padding: 10px 16px; font-size: 16px; line-height: 1.35; font-weight: 700; letter-spacing: 0.04em; }}
  .meta {{ text-align: center; color: #5c5562; font-size: 14px; margin: 0 0 16px; }}
  .cliente {{ background-color: {fundo}; box-shadow: inset 0 0 0 999px {fundo}; border-radius: 12px; padding: 8px 16px; margin-bottom: 16px; }}
  .cliente p {{ margin: 3px 0; font-size: 14px; line-height: 1.2; }}
  .ico {{ color: {cor}; font-weight: 700; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  thead th {{ background-color: {fundo_tabela}; box-shadow: inset 0 0 0 999px {fundo_tabela}; text-align: left; padding: 6px 8px; font-size: 12px; letter-spacing: 0.03em; }}
  thead th.num, td.num {{ text-align: right; white-space: nowrap; }}
  td {{ padding: 2px 8px; vertical-align: middle; border-bottom: 1px solid #eee; line-height: 1.2; }}
  .secao {{ margin: 8px 0 4px; color: {cor}; font-weight: 700; letter-spacing: 0.06em; font-size: 13px; }}
  .resumo {{ margin-top: 8px; }}
  .linha {{ display: flex; justify-content: space-between; align-items: baseline; padding: 2px 8px; font-size: 14px; font-weight: 700; }}
  .linha span {{ color: #2b2430; font-weight: 700; text-align: left; }}
  .destaque {{ display: flex; justify-content: space-between; align-items: center; gap: 16px; margin: 12px 0; background-color: {fundo}; box-shadow: inset 0 0 0 999px {fundo}; border-radius: 12px; padding: 8px 8px 8px 16px; }}
  .destaque .rotulo {{ color: {cor}; font-weight: 800; letter-spacing: 0.04em; }}
  .pill {{ background-color: {cor}; box-shadow: inset 0 0 0 999px {cor}; color: #fff; border-radius: 10px; padding: 8px 18px; font-size: 20px; font-weight: 800; }}
  .pill.divida {{ background-color: #8a2b2b; box-shadow: inset 0 0 0 999px #8a2b2b; }}
  .vencido {{ color: #8a2b2b; font-weight: 700; }}
  table.recebimentos {{ margin-top: 8px; }}
  table.recebimentos tr.total td {{ font-weight: 700; border-bottom: none; }}
  .pagamento {{ display: flex; justify-content: space-between; align-items: center; gap: 12px; margin: 8px 0 4px; font-size: 14px; }}
  .selo {{ font-weight: 700; }}
  .selo.ok {{ display: inline-flex; align-items: center; gap: 6px; color: #1b8a45; }}
  .selo.aviso {{ color: #a15c00; }}
  .selo.neutro {{ color: #5c5562; }}
  .ops {{ display: flex; justify-content: space-between; align-items: center; gap: 12px; background-color: {fundo}; box-shadow: inset 0 0 0 999px {fundo}; border-radius: 12px; padding: 12px 16px; margin-top: 14px; font-size: 14px; }}
  .ops .divisoria {{ width: 1px; align-self: stretch; background: #d8cedf; }}
  .rodape {{ margin-top: 16px; background-color: {fundo}; box-shadow: inset 0 0 0 999px {fundo}; border-radius: 12px; padding: 14px 16px 12px; text-align: center; }}
  .obrigado {{ display: flex; align-items: center; justify-content: center; gap: 12px; color: {cor}; font-weight: 700; font-style: italic; margin: 0; }}
  .traco {{ width: 72px; border-top: 1px dashed #b9a8c0; }}
  .nota, .miudo {{ text-align: center; color: #6d6572; font-size: 12px; margin: 4px 0 0; }}
  .centro {{ text-align: center; }}
  .saldo strong {{ color: #8a2b2b; }}
  @media print {{
    .no-print, button {{ display: none !important; }}
    .folha {{ padding: 0; max-width: none; }}
    * {{ -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }}
  }}
"""


def _quando_caixa(valor) -> str:
    if valor is None or valor == "":
        return "—"
    if isinstance(valor, str):
        return valor
    from django.utils import timezone

    momento = valor
    if timezone.is_aware(momento):
        momento = timezone.localtime(momento)
    return momento.strftime("%d/%m/%Y às %H:%M")


def _linhas_resumo_caixa(linhas: list) -> str:
    if not linhas:
        return '<tr><td class="desc" colspan="4">Nenhuma venda de produto nesta gaveta.</td></tr>'
    partes = []
    for item in linhas:
        descricao = _t(item.get("nome") or "Produto")
        cliente = (item.get("cliente") or "").strip()
        if cliente:
            descricao += f'<br><span class="miudo">{_t(cliente)}</span>'
        desconto = float(item.get("desconto") or 0)
        if desconto > 0.009:
            descricao += f'<br><span class="miudo">desc. {formatar_moeda_recibo(desconto)}</span>'
        partes.append(_celula_item(
            descricao,
            _t(item.get("quantidade") or "1"),
            formatar_moeda_recibo(item.get("preco_unitario") or 0),
            formatar_moeda_recibo(item.get("subtotal") or 0),
        ))
    return "".join(partes)


def _cabecalho_loja_recibo(ctx: dict, cor: str) -> str:
    from .context import _linha_documento_loja, _linha_tel_cep, texto_cadastro_recibo

    doc_line = _linha_documento_loja(ctx)
    tel_cep = ctx.get("loja_tel_cep") or _linha_tel_cep(
        ctx.get("loja_telefone", ""), ctx.get("loja_cep", ""),
    )
    logo = _src_logo_recibo(ctx.get("logo_url") or "")
    marca = (
        f'<img class="logo" src="{_t(logo)}" alt="">'
        if logo else
        f'<p class="marca">{_t((ctx.get("loja_nome") or "CLÍNICA").upper())}</p>'
    )
    endereco = _t(texto_cadastro_recibo(ctx.get("loja_endereco") or ""))
    telefone = _t(ctx.get("loja_telefone") or "")
    email = _t(ctx.get("loja_email") or "")
    partes_contato = []
    if endereco:
        partes_contato.append(f'<p class="contato linha">{_icone("pin", cor)}<span>{endereco}</span></p>')
    if telefone:
        partes_contato.append(f'<p class="contato linha">{_icone("telefone", cor)}<span>{telefone}</span></p>')
    if email:
        partes_contato.append(f'<p class="contato linha">{_icone("email", cor)}<span>{email}</span></p>')
    return (
        "<header class=\"topo\">"
        f"{marca}"
        f'{f"<p class=\"doc\">{_t(doc_line)}</p>" if doc_line else ""}'
        f"{''.join(partes_contato)}"
        f'{f"<p class=\"doc\">{_t(tel_cep)}</p>" if tel_cep and not ctx.get("loja_telefone") else ""}'
        "</header>"
    )


def gerar_html_resumo_caixa(ctx: dict) -> str:
    """Impressão do caixa fechado, com a mesma folha do recibo."""
    cor = cor_primaria_recibo(ctx.get("cor_primaria") or "")
    recebido = float(ctx.get("recebido") or 0)
    a_receber = float(ctx.get("a_receber") or 0)
    vendas = float(ctx.get("vendas_produtos") or 0)
    operador = ctx.get("operador") or "Operador"
    caixa = ctx.get("caixa_nome") or "Recepção"
    cliente = (
        _campo("pessoa", "Operador", operador, cor)
        + _campo("caixa", "Caixa", caixa, cor)
        + _campo("calendario", "Aberto", _quando_caixa(ctx.get("aberta_em")), cor)
        + _campo("calendario", "Fechado", _quando_caixa(ctx.get("fechada_em")), cor)
    )
    saldo_html = ""
    if a_receber > 0.009:
        saldo_html = (
            f'<div class="destaque tinta"><span class="rotulo">AINDA A RECEBER</span>'
            f'<span class="pill divida tinta">{formatar_moeda_recibo(a_receber)}</span></div>'
        )
    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<title>Resumo do caixa</title>
<style>
{estilo_folha_recibo(cor)}
</style>
</head><body>
<article class="folha">
  {_cabecalho_loja_recibo(ctx, cor)}
  <h1 class="faixa tinta">RESUMO DO CAIXA</h1>
  <p class="meta">Fechado em {_t(_quando_caixa(ctx.get("fechada_em")))}</p>
  <section class="cliente tinta">{cliente}</section>
  <p class="secao">PRODUTOS</p>
  <table>
    <thead><tr><th class="tinta">Descrição</th><th class="num tinta">Qtd.</th><th class="num tinta">Unitário</th><th class="num tinta">Subtotal</th></tr></thead>
    <tbody>{_linhas_resumo_caixa(ctx.get("linhas") or [])}</tbody>
  </table>
  <div class="resumo">
    <div class="linha"><span>Recebido</span><strong>{formatar_moeda_recibo(recebido)}</strong></div>
    <div class="linha"><span>Ainda a receber</span><strong>{formatar_moeda_recibo(a_receber)}</strong></div>
    <div class="linha"><span>Vendas de produtos</span><strong>{formatar_moeda_recibo(vendas)}</strong></div>
  </div>
  <div class="destaque tinta"><span class="rotulo">RECEBIDO</span><span class="pill tinta">{formatar_moeda_recibo(recebido)}</span></div>
  {saldo_html}
  <div class="rodape tinta">
    <p class="obrigado"><span class="traco"></span>Agradecemos pela preferência!<span class="traco"></span></p>
    <p class="nota">Resumo do caixa · Documento interno</p>
  </div>
  <p class="no-print" style="text-align:center"><button type="button" onclick="imprimirReciboPronto()">Imprimir</button></p>
</article>
<script>
function imprimirReciboPronto() {{
  if (window.__reciboImpresso) return;
  var imgs = [].slice.call(document.images).filter(function(img) {{ return !img.complete; }});
  var disparar = function() {{
    if (window.__reciboImpresso) return;
    window.__reciboImpresso = true;
    try {{ window.focus(); }} catch (e) {{}}
    window.print();
  }};
  if (!imgs.length) {{ disparar(); return; }}
  var faltam = imgs.length;
  var fim = function() {{ if (--faltam <= 0) disparar(); }};
  imgs.forEach(function(img) {{
    img.addEventListener("load", fim);
    img.addEventListener("error", fim);
  }});
  setTimeout(disparar, 2500);
}}
</script>
</body></html>"""


def html_resumo_caixa_da_sessao(sessao, loja) -> str:
    from clinica_beleza.venda_produto_service import nome_exibicao_venda, produtos_da_venda, totais_gaveta

    from .context import _dados_loja_recibo

    linhas = []
    vendas = sessao.vendas.select_related("payment", "paciente").prefetch_related("itens__produto").order_by("id")
    for venda in vendas:
        if getattr(venda, "status", "") == "cancelada":
            continue
        payment = getattr(venda, "payment", None)
        if payment is None or getattr(payment, "status", "") == "CANCELLED":
            continue
        cliente = nome_exibicao_venda(venda) or "Consumidor não identificado"
        produtos = produtos_da_venda(venda)
        if produtos:
            for produto in produtos:
                linhas.append({**produto, "cliente": cliente})
            continue
        total = payment.valor_total if payment.valor_total is not None else payment.amount or 0
        linhas.append({
            "nome": cliente,
            "quantidade": "1",
            "preco_unitario": float(total),
            "desconto": 0,
            "subtotal": float(total),
        })
    dados = _dados_loja_recibo(loja)
    dados.update({
        "operador": sessao.responsavel_nome or sessao.operador_nome or "Operador",
        "caixa_nome": sessao.nome or "Recepção",
        "aberta_em": sessao.aberta_em,
        "fechada_em": sessao.fechada_em,
        "linhas": linhas,
        **totais_gaveta(sessao),
    })
    return gerar_html_resumo_caixa(dados)


def gerar_html_recibo(ctx: dict) -> str:
    """Recibo visual único para venda de produtos e para atendimento."""
    ctx = reconciliar_conta_recibo(ctx)
    c = montar_cartao(ctx)
    saldo = c.saldo
    titulo = c.titulo
    subtitulo = c.subtitulo
    situacao = c.situacao
    cor = c.cor
    titulo_tabela = c.titulo_tabela_html
    linhas_tabela = _linhas_tabela(c)
    somente_produtos = c.somente_produtos
    custeio = c.custeio
    comprovante = c.comprovante
    rotulo_destaque = c.rotulo_destaque
    valor_destaque = c.valor_destaque
    descontos = c.descontos
    subtotal = c.subtotal
    conta_pendente = c.conta_pendente
    resumo = (
        f'<div class="linha"><span>{_t(c.rotulo_conta)}</span>'
        f'<strong>{formatar_moeda_recibo(subtotal)}</strong></div>'
    )
    resumo += "".join(
        f'<div class="linha"><span>{_t(label)}</span>'
        f'<strong>- {formatar_moeda_recibo(valor)}</strong></div>'
        for label, valor in descontos
    )
    protocolo_info = c.protocolo
    if protocolo_info:
        resumo += '<p class="secao">Protocolo</p>'
        for label, valor in protocolo_info:
            resumo += (
                f'<div class="linha"><span>{_t(label)}</span>'
                f'<strong>{formatar_moeda_recibo(valor)}</strong></div>'
            )
    valor_com_desconto = c.valor_com_desconto
    if valor_com_desconto:
        resumo += (
            f'<div class="linha"><span>{_t(valor_com_desconto[0])}</span>'
            f'<strong>{formatar_moeda_recibo(valor_com_desconto[1])}</strong></div>'
        )
    if comprovante:
        linha_procedimento = (
            f'<div class="linha"><span>Valor do procedimento</span>'
            f'<strong>{formatar_moeda_recibo(c.valor_total)}</strong></div>'
        )
        if descontos or protocolo_info or valor_com_desconto:
            resumo += linha_procedimento
        else:
            resumo = linha_procedimento

    valor_pago = c.valor_pago
    detalhes = c.detalhes
    tabela_recebimentos = ""
    formas_texto = c.formas_texto
    if c.varios_recebimentos:
        linhas_receb = "".join(
            "<tr>"
            f'<td>{_t(item["data"] or "—")}</td>'
            f'<td>{_t(item["forma"])}</td>'
            f'<td class="num">{formatar_moeda_recibo(item["valor"])}</td>'
            "</tr>"
            for item in detalhes
        )
        tabela_recebimentos = (
            '<table class="recebimentos"><thead><tr>'
            '<th class="tinta">Data</th><th class="tinta">Forma de pagamento</th>'
            '<th class="num tinta">Valor</th></tr></thead><tbody>'
            f"{linhas_receb}"
            '<tr class="total"><td></td><td>Total recebido</td>'
            f'<td class="num">{formatar_moeda_recibo(c.total_recebido)}</td></tr>'
            "</tbody></table>"
        )
    rotulo_forma = c.rotulo_forma

    if custeio:
        situacao_html = '<span class="selo neutro">Custeado pela clínica</span>'
    elif situacao == "sem_saldo":
        situacao_html = f'<span class="selo neutro">{_t(subtitulo or "Sem valor a pagar")}</span>'
    elif situacao == "parcial":
        situacao_html = f'<span class="selo aviso">{_t(c.rotulo_situacao)}</span>'
    elif situacao == "em_aberto":
        situacao_html = f'<span class="selo aviso">{_t(c.rotulo_situacao)}</span>'
    elif situacao == "quitado":
        situacao_html = f'<span class="selo ok">{_icone_quitado()} Quitado</span>'
    else:
        situacao_html = ""

    saldo_html = ""
    if c.mostrar_saldo:
        saldo_html = (
            f'<div class="linha saldo"><span>Saldo a pagar</span>'
            f'<strong>{formatar_moeda_recibo(saldo)}</strong></div>'
            f'<p class="miudo centro">{_t(c.texto_vencimento)}</p>'
        )
    extra = c.extra
    extra_html = (
        f'<div class="linha"><span>Recebido a maior</span><strong>{formatar_moeda_recibo(extra)}</strong></div>'
        if extra > 0.009 else ""
    )
    aviso_venc = c.aviso_vencimento
    classe_venc = "miudo centro vencido" if c.vencido else "miudo centro"
    vencimento_html = f'<p class="{classe_venc}">{_t(aviso_venc)}</p>' if aviso_venc else ""
    if conta_pendente:
        destaque_html = (
            f'<div class="destaque tinta"><span class="rotulo">Total já pago</span>'
            f'<span class="pill tinta">{formatar_moeda_recibo(valor_pago)}</span></div>'
            f'<div class="destaque tinta"><span class="rotulo">Saldo a pagar</span>'
            f'<span class="pill divida tinta">{formatar_moeda_recibo(saldo)}</span></div>'
        )
    else:
        destaque_html = (
            f'<div class="destaque tinta"><span class="rotulo">{_t(rotulo_destaque)}</span>'
            f'<span class="pill tinta">{formatar_moeda_recibo(valor_destaque)}</span></div>'
        )

    pago_html = ""
    if c.mostrar_pago:
        pago_html = (
            f'<div class="linha"><span>PAGO</span><strong>{formatar_moeda_recibo(valor_pago)}</strong></div>'
        )

    cpf = (ctx.get("paciente_cpf") or "").strip()
    cliente = _campo("pessoa", c.rotulo_pessoa, ctx.get("paciente_nome") or "", cor)
    if cpf:
        cliente += _campo("cpf", "CPF", cpf, cor)
    if not somente_produtos:
        if c.data_atendimento:
            cliente += _campo("calendario", "Data do atendimento", c.data_atendimento, cor)
        if ctx.get("profissional_nome"):
            cliente += _campo("pessoa", "Profissional", ctx.get("profissional_nome") or "", cor)

    operacional = []
    if ctx.get("caixa_nome"):
        operacional.append(
            f'<span class="item">{_icone("caixa", cor)}'
            f'<span><strong>Caixa:</strong> {_t(ctx.get("caixa_nome"))}</span></span>'
        )
    if ctx.get("operador_nome"):
        operacional.append(
            f'<span class="item">{_icone("pessoa", cor)}'
            f'<span><strong>Recebido por:</strong> {_t(ctx.get("operador_nome"))}</span></span>'
        )
    operacional_html = (
        f'<div class="ops tinta">{"<span class=\"divisoria\"></span>".join(operacional)}</div>'
        if operacional else ""
    )

    numero = c.numero
    meta = " · ".join(
        parte for parte in (
            f'{c.rotulo_numero} nº {_t(numero)}' if numero else "",
            f'Emitido em {_t(c.data_emissao)}',
        ) if parte
    )
    aviso = c.aviso
    nota = c.nota
    cabecalho = _cabecalho_loja_recibo(ctx, cor)

    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<title>{_t(titulo)}</title>
<style>{estilo_folha_recibo(cor)}
</style>
</head><body>
<article class="folha">
  {cabecalho}
  <h1 class="faixa tinta">{_t(titulo)}</h1>
  <p class="meta">{meta}</p>
  <section class="cliente tinta">{cliente}</section>
  <p class="secao">{_t(titulo_tabela.upper())}</p>
  <table>
    <thead><tr><th class="tinta">Descrição</th><th class="num tinta">Qtd.</th><th class="num tinta">Unitário</th><th class="num tinta">Subtotal</th></tr></thead>
    <tbody>{linhas_tabela}</tbody>
  </table>
  <div class="resumo">
    {resumo}
    {pago_html}
    {extra_html}
    {saldo_html}
  </div>
  {destaque_html}
  {vencimento_html}
  {tabela_recebimentos}
  {f'<div class="pagamento"><span><strong>Situação:</strong> {_t(situacao_comprovante_recibo(ctx))}</span></div>' if comprovante else f'''<div class="pagamento">
    <span class="item">{_icone("cartao", cor) if formas_texto and not custeio else ''}<span>{f'<strong>{_t(rotulo_forma)}:</strong> {_t(formas_texto)}' if formas_texto else ''}</span></span>
    {situacao_html}
  </div>'''}
  {operacional_html}
  {f'<p class="miudo">{_t(aviso)}</p>' if aviso else ''}
  <div class="rodape tinta">
    <p class="obrigado"><span class="traco"></span>Agradecemos pela preferência!<span class="traco"></span></p>
    <p class="nota">{nota}</p>
  </div>
  <p class="no-print" style="text-align:center"><button type="button" onclick="imprimirReciboPronto()">Imprimir</button></p>
</article>
<script>
function imprimirReciboPronto() {{
  if (window.__reciboImpresso) return;
  var imgs = [].slice.call(document.images).filter(function(img) {{ return !img.complete; }});
  var disparar = function() {{
    if (window.__reciboImpresso) return;
    window.__reciboImpresso = true;
    try {{ window.focus(); }} catch (e) {{}}
    window.print();
  }};
  if (!imgs.length) {{ disparar(); return; }}
  var faltam = imgs.length;
  var fim = function() {{ if (--faltam <= 0) disparar(); }};
  imgs.forEach(function(img) {{
    img.addEventListener("load", fim);
    img.addEventListener("error", fim);
  }});
  setTimeout(disparar, 2500);
}}
</script>
</body></html>"""


def gerar_html_recibo_do_payment(payment) -> str:
    """Carrega o mesmo contexto do PDF e devolve o recibo HTML."""
    appointment = payment.appointment
    if not appointment:
        from clinica_beleza.venda_produto_service import pessoa_recibo, produtos_do_pagamento

        venda = getattr(payment, "venda_balcao", None)
        if venda is None or not produtos_do_pagamento(payment):
            raise ValueError("Pagamento sem agendamento vinculado.")
        return gerar_html_recibo(_obter_dados_contexto(payment, pessoa_recibo(venda), None))
    try:
        from clinica_beleza.models import Appointment

        appointment = (
            Appointment.objects.select_related(
                "patient",
                "procedure",
                "professional",
                "local_atendimento",
                "convenio",
                "consulta",
                "consulta__local_atendimento",
                "consulta__convenio",
            )
            .prefetch_related("appointment_procedures__procedure")
            .get(pk=appointment.pk)
        )
    except Exception:
        pass
    patient = getattr(appointment, "patient", None)
    if not patient:
        raise ValueError("Paciente não encontrado no agendamento.")
    return gerar_html_recibo(_obter_dados_contexto(payment, patient, appointment))
