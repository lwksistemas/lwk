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
    cor_primaria_recibo,
    custeado_pela_clinica,
    linha_valor_com_desconto_recibo,
    linha_vencimento_recibo,
    linhas_local_convenio_recibo,
    linhas_protocolo_informativo,
    procedimentos_exibidos_recibo,
    produtos_exibidos_recibo,
    recebido_a_maior_recibo,
    reconciliar_conta_recibo,
    rotulo_forma_recibo,
    rotulo_subtotal_recibo,
    rotulo_total_recibo,
    situacao_recibo,
    tinta_recibo,
    titulo_recibo,
)
from .moeda import formatar_moeda_recibo


def _hora_com_as(valor: str) -> str:
    texto = (valor or "").strip()
    if re.fullmatch(r"\d{2}/\d{2}/\d{4} \d{2}:\d{2}", texto):
        return texto.replace(" ", " às ", 1)
    return texto


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


def _saldo(ctx: dict) -> float:
    valor_pago = ctx.get("valor_pago", 0) or 0
    valor_total = ctx.get("valor_total", 0) or 0
    return float(ctx.get("saldo_devedor", max(valor_total - valor_pago, 0)))


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


def _linhas_tabela(ctx: dict) -> tuple[str, str]:
    """Devolve (título da tabela, linhas). Produtos e atendimentos usam as mesmas colunas."""
    linhas = []
    for label, valor in _linhas_taxa_consulta_recibo(ctx):
        linhas.append(_celula_item(
            f"• {_t(label)}",
            "1",
            formatar_moeda_recibo(valor),
            formatar_moeda_recibo(valor),
        ))
    for nome, valor in procedimentos_exibidos_recibo(ctx):
        if valor > 0.009:
            quantidade, unitario = "1", formatar_moeda_recibo(valor)
        else:
            quantidade, unitario = "—", "—"
        linhas.append(_celula_item(
            _nome_servico_html(nome),
            quantidade,
            unitario,
            formatar_moeda_recibo(valor),
        ))
    for label, valor in linhas_local_convenio_recibo(ctx):
        linhas.append(
            f'<tr><td class="desc" colspan="4">{_t(label)} {_t(valor)}</td></tr>'
        )
    produtos = produtos_exibidos_recibo(ctx)
    for item in produtos:
        descricao = _t(item["nome"])
        if item["desconto"] > 0.009:
            descricao += f'<br><span class="miudo">desc. {formatar_moeda_recibo(item["desconto"])}</span>'
        linhas.append(_celula_item(
            descricao,
            _t(item["quantidade"]),
            formatar_moeda_recibo(item["preco_unitario"]),
            formatar_moeda_recibo(item["subtotal"]),
        ))
    if ctx.get("somente_produtos"):
        titulo = "Produtos"
    elif produtos and len(linhas) > len(produtos):
        titulo = "Procedimentos, serviços e produtos"
    elif produtos:
        titulo = "Produtos"
    else:
        titulo = "Procedimentos e serviços"
    return titulo, "".join(linhas)


def gerar_html_recibo(ctx: dict) -> str:
    """Recibo visual único para venda de produtos e para atendimento."""
    ctx = reconciliar_conta_recibo(ctx)
    saldo = _saldo(ctx)
    titulo, subtitulo = titulo_recibo(ctx)
    situacao = situacao_recibo(ctx)
    cor = cor_primaria_recibo(ctx.get("cor_primaria") or "")
    fundo = tinta_recibo(cor, 0.9)
    fundo_tabela = tinta_recibo(cor, 0.82)
    doc_line = _linha_documento_loja(ctx)
    tel_cep = ctx.get("loja_tel_cep") or _linha_tel_cep(
        ctx.get("loja_telefone", ""), ctx.get("loja_cep", ""),
    )
    data_emissao = _hora_com_as(ctx.get("data_emissao") or ctx.get("data") or "—")
    data_atend = _hora_com_as(ctx.get("data_atendimento") or "")
    titulo_tabela, linhas_tabela = _linhas_tabela(ctx)
    somente_produtos = bool(ctx.get("somente_produtos"))
    custeio = situacao == "quitado" and custeado_pela_clinica(ctx)
    rotulo = rotulo_total_recibo(ctx)
    if situacao == "quitado" and not custeio and rotulo == "Total":
        rotulo_destaque = "TOTAL PAGO"
    elif rotulo == "Total":
        rotulo_destaque = "TOTAL"
    else:
        rotulo_destaque = rotulo

    descontos = _linhas_descontos_recibo(ctx)
    subtotal = float(ctx.get("subtotal", ctx.get("valor_total") or 0))
    resumo = (
        f'<div class="linha"><span>{_t(rotulo_subtotal_recibo(ctx))}</span>'
        f'<strong>{formatar_moeda_recibo(subtotal)}</strong></div>'
    )
    resumo += "".join(
        f'<div class="linha"><span>{_t(label)}</span>'
        f'<strong>- {formatar_moeda_recibo(valor)}</strong></div>'
        for label, valor in descontos
    )
    protocolo_info = linhas_protocolo_informativo(ctx)
    if protocolo_info:
        resumo += '<p class="secao">Protocolo</p>'
        for label, valor in protocolo_info:
            resumo += (
                f'<div class="linha"><span>{_t(label)}</span>'
                f'<strong>{formatar_moeda_recibo(valor)}</strong></div>'
            )
    valor_com_desconto = linha_valor_com_desconto_recibo(ctx)
    if valor_com_desconto:
        resumo += (
            f'<div class="linha"><span>{_t(valor_com_desconto[0])}</span>'
            f'<strong>{formatar_moeda_recibo(valor_com_desconto[1])}</strong></div>'
        )

    valor_pago = float(ctx.get("valor_pago") or 0)
    formas = [
        f for f in (ctx.get("formas_pagamento") or [])
        if float(f.get("valor") or 0) > 0.009
    ]
    if not formas and valor_pago > 0.009:
        formas = [{"metodo": ctx.get("metodo") or "Pagamento", "valor": valor_pago}]
    if custeio:
        formas_texto = "Custeado pela clínica"
    elif len(formas) > 1:
        formas_texto = " · ".join(
            f'{rotulo_forma_recibo(f.get("metodo") or "")} {formatar_moeda_recibo(f.get("valor") or 0)}'
            for f in formas
        )
    elif formas:
        formas_texto = rotulo_forma_recibo(formas[0].get("metodo") or "")
    else:
        formas_texto = (ctx.get("condicao_cobranca") or "").strip()
    rotulo_forma = "Formas de pagamento" if len(formas) > 1 else "Forma de pagamento"

    if custeio:
        situacao_html = '<span class="selo neutro">Custeado pela clínica</span>'
    elif situacao == "sem_saldo":
        situacao_html = f'<span class="selo neutro">{_t(subtitulo or "Sem valor a pagar")}</span>'
    elif situacao == "parcial":
        situacao_html = '<span class="selo aviso">Pagamento parcial</span>'
    elif situacao == "em_aberto":
        situacao_html = '<span class="selo aviso">Em aberto</span>'
    elif situacao == "quitado":
        situacao_html = '<span class="selo ok">✓ Quitado</span>'
    else:
        situacao_html = ""

    saldo_html = ""
    if not custeio and saldo > 0.009:
        saldo_html = (
            f'<div class="linha saldo"><span>SALDO A PAGAR</span>'
            f'<strong>{formatar_moeda_recibo(saldo)}</strong></div>'
            f'<p class="miudo centro">{_t(linha_vencimento_recibo(ctx))}</p>'
        )
    extra = recebido_a_maior_recibo(ctx)
    extra_html = (
        f'<div class="linha"><span>Recebido a maior</span><strong>{formatar_moeda_recibo(extra)}</strong></div>'
        if extra > 0.009 else ""
    )
    pago_html = ""
    if situacao == "parcial" and valor_pago > 0.009:
        pago_html = (
            f'<div class="linha"><span>PAGO</span><strong>{formatar_moeda_recibo(valor_pago)}</strong></div>'
        )

    logo = _src_logo_recibo(ctx.get("logo_url") or "")
    marca = (
        f'<img class="logo" src="{_t(logo)}" alt="">'
        if logo else
        f'<p class="marca">{_t((ctx.get("loja_nome") or "CLÍNICA").upper())}</p>'
    )
    nome_abaixo = ""
    if logo and ctx.get("loja_nome"):
        nome_abaixo = f'<p class="razao">{_t(ctx.get("loja_nome"))}</p>'

    cpf = (ctx.get("paciente_cpf") or "").strip()
    rotulo_pessoa = "Cliente" if somente_produtos else "Paciente"
    cliente = (
        f'<p><span class="ico">{rotulo_pessoa}:</span> <strong>{_t(ctx.get("paciente_nome"))}</strong></p>'
        + (f'<p><span class="ico">CPF:</span> {_t(cpf)}</p>' if cpf else "")
    )
    if not somente_produtos:
        if data_atend:
            cliente += f'<p><span class="ico">Data do atendimento:</span> {_t(data_atend)}</p>'
        if ctx.get("profissional_nome"):
            cliente += f'<p><span class="ico">Profissional:</span> {_t(ctx.get("profissional_nome"))}</p>'

    operacional = []
    if somente_produtos and ctx.get("caixa_nome"):
        operacional.append(f'<span><strong>Caixa:</strong> {_t(ctx.get("caixa_nome"))}</span>')
    if ctx.get("operador_nome"):
        operacional.append(f'<span><strong>Recebido por:</strong> {_t(ctx.get("operador_nome"))}</span>')
    elif not somente_produtos and ctx.get("profissional_nome"):
        operacional.append(f'<span><strong>Profissional:</strong> {_t(ctx.get("profissional_nome"))}</span>')
    operacional_html = f'<div class="ops">{"".join(operacional)}</div>' if operacional else ""

    numero = ctx.get("recibo_numero")
    meta = " · ".join(
        parte for parte in (
            f'Recibo nº {_t(numero)}' if numero else "",
            f'Emitido em {_t(data_emissao)}',
        ) if parte
    )
    aviso = (ctx.get("retorno_aviso") or "").strip()
    nota = (
        "Recibo comercial de produto · Documento não fiscal"
        if somente_produtos else
        "Recibo de prestação de serviços · Documento não fiscal."
    )
    endereco = _t(ctx.get("loja_endereco") or "")
    telefone = _t(ctx.get("loja_telefone") or "")
    email = _t(ctx.get("loja_email") or "")
    meio = "  |  ".join(parte for parte in (telefone, email) if parte)
    contato = "".join(
        f'<p class="contato">{parte}</p>' for parte in (endereco, meio) if parte
    )

    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<title>{_t(titulo)}</title>
<style>
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
  .tinta {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
  .faixa {{ margin: 18px 0 8px; background-color: {cor}; box-shadow: inset 0 0 0 999px {cor}; color: #fff; text-align: center; border-radius: 10px; padding: 10px 16px; font-weight: 700; letter-spacing: 0.04em; }}
  .meta {{ text-align: center; color: #5c5562; font-size: 14px; margin: 0 0 16px; }}
  .cliente {{ background-color: {fundo}; box-shadow: inset 0 0 0 999px {fundo}; border-radius: 12px; padding: 12px 16px; margin-bottom: 16px; }}
  .cliente p {{ margin: 4px 0; font-size: 14px; }}
  .ico {{ color: {cor}; font-weight: 700; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  thead th {{ background-color: {fundo_tabela}; box-shadow: inset 0 0 0 999px {fundo_tabela}; text-align: left; padding: 8px; font-size: 12px; letter-spacing: 0.03em; }}
  thead th.num, td.num {{ text-align: right; white-space: nowrap; }}
  td {{ padding: 8px; vertical-align: top; border-bottom: 1px solid #eee; }}
  .secao {{ margin: 8px 0 4px; color: {cor}; font-weight: 700; letter-spacing: 0.06em; font-size: 13px; }}
  .resumo {{ margin-top: 12px; }}
  .linha {{ display: flex; justify-content: flex-end; gap: 48px; padding: 3px 8px; font-size: 14px; }}
  .linha span {{ color: #5c5562; min-width: 120px; text-align: right; }}
  .destaque {{ display: flex; justify-content: space-between; align-items: center; gap: 16px; margin: 12px 0; background-color: {fundo}; box-shadow: inset 0 0 0 999px {fundo}; border-radius: 12px; padding: 8px 8px 8px 16px; }}
  .destaque .rotulo {{ color: {cor}; font-weight: 800; letter-spacing: 0.04em; }}
  .pill {{ background-color: {cor}; box-shadow: inset 0 0 0 999px {cor}; color: #fff; border-radius: 10px; padding: 8px 18px; font-size: 20px; font-weight: 800; }}
  .pagamento {{ display: flex; justify-content: space-between; align-items: center; gap: 12px; margin: 8px 0 4px; font-size: 14px; }}
  .selo {{ font-weight: 700; }}
  .selo.ok {{ color: #1b8a45; }}
  .selo.aviso {{ color: #a15c00; }}
  .selo.neutro {{ color: #5c5562; }}
  .ops {{ display: flex; justify-content: space-between; gap: 12px; background-color: {fundo}; box-shadow: inset 0 0 0 999px {fundo}; border-radius: 12px; padding: 12px 16px; margin-top: 14px; font-size: 14px; }}
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
</style>
</head><body>
<article class="folha">
  <header class="topo">
    {marca}
    {nome_abaixo}
    {f'<p class="doc">{_t(doc_line)}</p>' if doc_line else ''}
    {contato}
    {f'<p class="doc">{_t(tel_cep)}</p>' if tel_cep and not ctx.get("loja_telefone") else ''}
  </header>
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
  <div class="destaque tinta"><span class="rotulo">{_t(rotulo_destaque)}</span><span class="pill tinta">{formatar_moeda_recibo(ctx.get("valor_total") or 0)}</span></div>
  <div class="pagamento">
    <span>{f'<strong>{_t(rotulo_forma)}:</strong> {_t(formas_texto)}' if formas_texto else ''}</span>
    {situacao_html}
  </div>
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
