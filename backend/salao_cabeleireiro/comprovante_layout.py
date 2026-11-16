"""Comprovante não fiscal do salão. O desenho segue o cadastro da loja, sem endereço fixo."""
import html
import re
from io import BytesIO

from django.utils import timezone

from .caixa_service import ROTULOS, quantia


def _texto(valor) -> str:
    return valor.strip() if isinstance(valor, str) else ""


def _cep(valor: str) -> str:
    digitos = re.sub(r"\D", "", valor or "")
    if len(digitos) == 8:
        return f"{digitos[:5]}-{digitos[5:]}"
    return _texto(valor)


def _telefone(valor: str) -> str:
    digitos = re.sub(r"\D", "", valor or "")
    if len(digitos) == 11:
        return f"({digitos[:2]}) {digitos[2:7]}-{digitos[7:]}"
    if len(digitos) == 10:
        return f"({digitos[:2]}) {digitos[2:6]}-{digitos[6:]}"
    return _texto(valor)


def _reais(valor) -> str:
    texto = f"{quantia(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def _cor(valor: str) -> str:
    cor = _texto(valor)
    if re.fullmatch(r"#[0-9A-Fa-f]{6}", cor):
        return cor
    return "#7A3044"


def cabecalho_da_loja(loja) -> dict:
    """Nome, endereço, contato e cor saem do cadastro. Sem logomarca, o recibo fica só com o nome."""
    from superadmin.loja_utils import contato_publico_loja

    if loja is None:
        return {"nome": "Salão", "subtitulo": "", "endereco": "", "telefone": "", "email": "", "logo": "", "cor": "#7A3044"}
    rua = _texto(getattr(loja, "logradouro", ""))
    numero = _texto(getattr(loja, "numero", ""))
    if rua and numero:
        rua = f"{rua}, {numero}"
    elif numero:
        rua = numero
    cidade = _texto(getattr(loja, "cidade", ""))
    uf = _texto(getattr(loja, "uf", ""))
    if cidade and uf:
        cidade = f"{cidade}/{uf}"
    elif uf:
        cidade = uf
    partes = [item for item in (rua, _texto(getattr(loja, "bairro", "")), cidade) if item]
    cep = _cep(getattr(loja, "cep", ""))
    if cep:
        partes.append(f"CEP {cep}")
    telefone, email = contato_publico_loja(loja)
    tipo = getattr(loja, "tipo_loja", None)
    subtitulo = _texto(getattr(tipo, "nome", "")) if tipo is not None else ""
    logo = _texto(getattr(loja, "recibo_logo", "")) or _texto(getattr(loja, "logo", ""))
    cor = _cor(_texto(getattr(loja, "recibo_cor", "")) or _texto(getattr(loja, "cor_primaria", "")))
    return {
        "nome": _texto(getattr(loja, "nome", "")) or "Salão",
        "subtitulo": subtitulo,
        "endereco": " – ".join(partes),
        "telefone": _telefone(telefone),
        "email": email,
        "logo": logo,
        "cor": cor,
    }


def cabecalho_atual() -> dict:
    from tenants.middleware import get_current_loja_id

    loja_id = get_current_loja_id()
    if not loja_id:
        return cabecalho_da_loja(None)
    from superadmin.models import Loja

    loja = Loja.objects.select_related("tipo_loja").filter(pk=loja_id).first()
    return cabecalho_da_loja(loja)


def _formas(partes) -> list[dict]:
    linhas = []
    for parte in partes or []:
        if not isinstance(parte, dict):
            continue
        linhas.append({
            "nome": ROTULOS.get(parte.get("forma"), parte.get("forma") or ""),
            "valor": f"{quantia(parte.get('valor')):.2f}",
        })
    return linhas


def congelar_venda(venda, recibos, itens) -> dict:
    quando = timezone.localtime(venda.created_at).strftime("%d/%m/%Y às %H:%M")
    return {
        "numero": venda.numero,
        "quando": quando,
        "cliente": venda.cliente_nome or "Consumidor",
        "operador": venda.operador_nome or "",
        "desconto": f"{quantia(venda.desconto):.2f}",
        "valor": f"{quantia(venda.valor):.2f}",
        "cancelado": False,
        "servicos": [
            {
                "nome": item.agendamento.servico.nome,
                "profissional": item.profissional.nome,
                "total": f"{quantia(item.valor):.2f}",
            }
            for item in recibos
        ],
        "produtos": [
            {"nome": item.nome, "quantidade": item.quantidade, "total": f"{quantia(item.total):.2f}"}
            for item in itens
        ],
        "formas": _formas(venda.partes),
        "salao": cabecalho_atual(),
    }


def comprovante_da_venda(venda) -> dict:
    """A segunda via lê o que foi gravado na venda. Recibo antigo monta os valores já salvos."""
    gravado = venda.comprovante if isinstance(getattr(venda, "comprovante", None), dict) else {}
    if gravado.get("numero"):
        return {**gravado, "cancelado": not venda.is_active}
    from .models import Recebimento

    recibos = list(
        Recebimento.objects.filter(venda=venda).select_related("agendamento__servico", "profissional").order_by("id")
    )
    if not recibos and venda.recebimento_id:
        recibos = [venda.recebimento]
    return {
        "numero": venda.numero,
        "quando": timezone.localtime(venda.created_at).strftime("%d/%m/%Y às %H:%M"),
        "cliente": venda.cliente_nome or "Consumidor",
        "operador": venda.operador_nome or "",
        "desconto": f"{quantia(venda.desconto):.2f}",
        "valor": f"{quantia(venda.valor):.2f}",
        "cancelado": not venda.is_active,
        "servicos": [
            {
                "nome": item.agendamento.servico.nome,
                "profissional": item.profissional.nome,
                "total": f"{quantia(item.valor):.2f}",
            }
            for item in recibos
        ],
        "produtos": [
            {"nome": item.nome, "quantidade": item.quantidade, "total": f"{quantia(item.total):.2f}"}
            for item in venda.itens.all()
        ],
        "formas": _formas(venda.partes),
        "salao": cabecalho_atual(),
    }


def html_comprovante(dados: dict) -> str:
    salao = dados.get("salao") or {}
    cor = _cor(salao.get("cor") or "")
    nome = html.escape(salao.get("nome") or "Salão")
    subtitulo = html.escape(salao.get("subtitulo") or "")
    logo = salao.get("logo") or ""
    logo_html = ""
    if isinstance(logo, str) and logo.startswith(("http://", "https://", "/")):
        logo_html = f'<img src="{html.escape(logo, quote=True)}" alt="" style="height:56px;width:auto;object-fit:contain" />'
    contato = []
    if salao.get("telefone"):
        contato.append(html.escape(salao["telefone"]))
    if salao.get("email"):
        contato.append(html.escape(salao["email"]))
    endereco = html.escape(salao.get("endereco") or "")
    servicos = dados.get("servicos") or []
    produtos = dados.get("produtos") or []
    linhas = []
    if servicos:
        linhas.append('<tr><td colspan="2" style="padding:8px 0 4px;font-size:12px;letter-spacing:.04em;color:#6b4a52">SERVIÇOS</td></tr>')
        for item in servicos:
            profissional = f'<div style="color:#8a6e74;font-size:12px">Profissional: {html.escape(item.get("profissional") or "")}</div>' if item.get("profissional") else ""
            linhas.append(
                "<tr>"
                f'<td style="padding:6px 0;border-top:1px solid #f0e4e7"><strong>{html.escape(item.get("nome") or "Serviço")}</strong>{profissional}</td>'
                f'<td style="padding:6px 0;border-top:1px solid #f0e4e7;text-align:right;white-space:nowrap">{_reais(item.get("total"))}</td>'
                "</tr>"
            )
    if produtos:
        linhas.append('<tr><td colspan="2" style="padding:8px 0 4px;font-size:12px;letter-spacing:.04em;color:#6b4a52">PRODUTOS</td></tr>')
        for item in produtos:
            quantidade = item.get("quantidade") or 1
            linhas.append(
                "<tr>"
                f'<td style="padding:6px 0;border-top:1px solid #f0e4e7">{quantidade}× {html.escape(item.get("nome") or "Produto")}</td>'
                f'<td style="padding:6px 0;border-top:1px solid #f0e4e7;text-align:right;white-space:nowrap">{_reais(item.get("total"))}</td>'
                "</tr>"
            )
    desconto = ""
    if quantia(dados.get("desconto")) > 0:
        desconto = (
            "<tr>"
            '<td style="padding:6px 0">Desconto</td>'
            f'<td style="padding:6px 0;text-align:right">{_reais(dados.get("desconto"))}</td>'
            "</tr>"
        )
    formas = "".join(
        "<tr>"
        f'<td style="padding:4px 0;border-top:1px solid #f0e4e7">{html.escape(item.get("nome") or "")}</td>'
        f'<td style="padding:4px 0;border-top:1px solid #f0e4e7;text-align:right">{_reais(item.get("valor"))}</td>'
        "</tr>"
        for item in (dados.get("formas") or [])
    )
    numero = dados.get("numero")
    numero_txt = f"{int(numero):06d}" if numero else "Prévia"
    aviso = ""
    if dados.get("cancelado"):
        aviso = '<p style="margin:8px 0;text-align:center;font-weight:700;color:#9f1239">CANCELADO</p>'
    subtitulo_html = f'<div style="letter-spacing:.14em;font-size:11px;color:{cor}">{subtitulo.upper()}</div>' if subtitulo else ""
    return f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>Comprovante {numero_txt}</title>
<style>
body{{margin:0;background:#f6f1f2;font-family:Georgia,serif;color:#2a1c20}}
.folha{{width:72mm;max-width:100%;margin:0 auto;background:#fff;padding:16px 14px 20px}}
@media print{{
  @page{{size:A4;margin:12mm}}
  body{{background:#fff}}
  .folha{{width:72mm}}
}}
</style></head><body><article class="folha">
<div style="display:flex;gap:10px;align-items:center;justify-content:center;text-align:left">
{logo_html}
<div><div style="font-size:22px;font-weight:700;color:{cor}">{nome}</div>{subtitulo_html}</div>
</div>
<div style="margin-top:10px;font-family:sans-serif;font-size:11px;color:#5c3d45;text-align:center">
{f"<div>{endereco}</div>" if endereco else ""}
{f"<div>{' | '.join(contato)}</div>" if contato else ""}
</div>
<div style="margin-top:12px;background:{cor};color:#fff;text-align:center;padding:8px 6px;font-family:sans-serif;font-weight:700;letter-spacing:.04em">COMPROVANTE DE PAGAMENTO<br>(NÃO FISCAL)</div>
{aviso}
<div style="display:flex;justify-content:space-between;gap:8px;margin-top:10px;font-family:sans-serif;font-size:12px"><span>Nº {numero_txt}</span><span>{html.escape(dados.get("quando") or "")}</span></div>
<div style="margin-top:8px;border:1px solid #f0e4e7;border-radius:8px;padding:8px;font-family:sans-serif;font-size:13px">Cliente: <strong>{html.escape(dados.get("cliente") or "Consumidor")}</strong></div>
<table style="width:100%;border-collapse:collapse;margin-top:8px;font-family:sans-serif;font-size:13px">{''.join(linhas)}{desconto}</table>
<div style="display:flex;justify-content:space-between;margin-top:8px;background:{cor};color:#fff;padding:8px 10px;font-family:sans-serif;font-weight:700"><span>Total pago</span><span>{_reais(dados.get("valor"))}</span></div>
<div style="margin-top:8px;font-family:sans-serif;font-size:13px"><strong>Formas de pagamento</strong><table style="width:100%;border-collapse:collapse">{formas}</table></div>
<p style="margin-top:10px;border:1px solid #f0e4e7;border-radius:8px;padding:8px;font-family:sans-serif;font-size:11px;color:#5c3d45">Este comprovante não substitui a emissão de Nota Fiscal (NFS-e) ou Cupom Fiscal (NFC-e).</p>
<p style="margin:14px 0 0;text-align:center;font-style:italic;color:{cor}">Obrigado pela preferência!</p>
</article></body></html>"""


def pdf_comprovante(dados: dict) -> bytes:
    """PDF estreito, o mesmo cartão da prévia, legível em A4 e em bobina de 80 mm."""
    from reportlab.lib.colors import Color, white
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas

    salao = dados.get("salao") or {}
    cor_hex = _cor(salao.get("cor") or "")
    cor = Color(int(cor_hex[1:3], 16) / 255, int(cor_hex[3:5], 16) / 255, int(cor_hex[5:7], 16) / 255)
    largura = 80 * mm
    linhas = []
    linhas.append(("titulo", salao.get("nome") or "Salão"))
    if salao.get("subtitulo"):
        linhas.append(("sub", salao["subtitulo"]))
    if salao.get("endereco"):
        linhas.append(("miudo", salao["endereco"]))
    contato = " | ".join(item for item in (salao.get("telefone"), salao.get("email")) if item)
    if contato:
        linhas.append(("miudo", contato))
    linhas.append(("faixa", "COMPROVANTE DE PAGAMENTO (NÃO FISCAL)"))
    if dados.get("cancelado"):
        linhas.append(("alerta", "CANCELADO"))
    numero = dados.get("numero")
    numero_txt = f"{int(numero):06d}" if numero else "Prévia"
    linhas.append(("par", f"Nº {numero_txt}", dados.get("quando") or ""))
    linhas.append(("miudo", f"Cliente: {dados.get('cliente') or 'Consumidor'}"))
    if dados.get("servicos"):
        linhas.append(("secao", "SERVIÇOS"))
        for item in dados["servicos"]:
            linhas.append(("item", item.get("nome") or "Serviço", _reais(item.get("total"))))
            if item.get("profissional"):
                linhas.append(("miudo", f"Profissional: {item['profissional']}"))
    if dados.get("produtos"):
        linhas.append(("secao", "PRODUTOS"))
        for item in dados["produtos"]:
            linhas.append(("item", f"{item.get('quantidade') or 1}× {item.get('nome') or 'Produto'}", _reais(item.get("total"))))
    if quantia(dados.get("desconto")) > 0:
        linhas.append(("item", "Desconto", _reais(dados.get("desconto"))))
    linhas.append(("total", "Total pago", _reais(dados.get("valor"))))
    if dados.get("formas"):
        linhas.append(("secao", "FORMAS DE PAGAMENTO"))
        for item in dados["formas"]:
            linhas.append(("item", item.get("nome") or "", _reais(item.get("valor"))))
    linhas.append(("miudo", "Este comprovante não substitui a emissão de Nota Fiscal (NFS-e) ou Cupom Fiscal (NFC-e)."))
    linhas.append(("obrigado", "Obrigado pela preferência!"))
    altura = 28 * mm + len(linhas) * 6.2 * mm
    buffer = BytesIO()
    pagina = canvas.Canvas(buffer, pagesize=(largura, max(altura, 120 * mm)))
    y = pagina._pagesize[1] - 8 * mm
    for linha in linhas:
        tipo = linha[0]
        if tipo == "titulo":
            pagina.setFillColor(cor)
            pagina.setFont("Times-Bold", 14)
            pagina.drawCentredString(largura / 2, y, str(linha[1])[:42])
        elif tipo == "sub":
            pagina.setFillColor(cor)
            pagina.setFont("Times-Roman", 8)
            pagina.drawCentredString(largura / 2, y, str(linha[1]).upper()[:48])
        elif tipo == "faixa":
            pagina.setFillColor(cor)
            pagina.roundRect(4 * mm, y - 2 * mm, largura - 8 * mm, 8 * mm, 1 * mm, fill=1, stroke=0)
            pagina.setFillColor(white)
            pagina.setFont("Times-Bold", 8)
            pagina.drawCentredString(largura / 2, y + 0.6 * mm, linha[1])
        elif tipo == "alerta":
            pagina.setFillColor(Color(0.62, 0.07, 0.22))
            pagina.setFont("Times-Bold", 11)
            pagina.drawCentredString(largura / 2, y, linha[1])
        elif tipo == "par":
            pagina.setFillColor(Color(0.2, 0.12, 0.14))
            pagina.setFont("Times-Roman", 8)
            pagina.drawString(5 * mm, y, str(linha[1])[:24])
            pagina.drawRightString(largura - 5 * mm, y, str(linha[2])[:28])
        elif tipo == "secao":
            pagina.setFillColor(Color(0.42, 0.29, 0.32))
            pagina.setFont("Times-Bold", 8)
            pagina.drawString(5 * mm, y, linha[1])
        elif tipo == "item":
            pagina.setFillColor(Color(0.16, 0.1, 0.12))
            pagina.setFont("Times-Roman", 9)
            pagina.drawString(5 * mm, y, str(linha[1])[:28])
            pagina.drawRightString(largura - 5 * mm, y, str(linha[2]))
        elif tipo == "total":
            pagina.setFillColor(cor)
            pagina.rect(4 * mm, y - 1.5 * mm, largura - 8 * mm, 6 * mm, fill=1, stroke=0)
            pagina.setFillColor(white)
            pagina.setFont("Times-Bold", 9)
            pagina.drawString(6 * mm, y, linha[1])
            pagina.drawRightString(largura - 6 * mm, y, linha[2])
        elif tipo == "obrigado":
            pagina.setFillColor(cor)
            pagina.setFont("Times-Italic", 10)
            pagina.drawCentredString(largura / 2, y, linha[1])
        else:
            pagina.setFillColor(Color(0.36, 0.24, 0.27))
            pagina.setFont("Times-Roman", 7.5)
            pagina.drawString(5 * mm, y, str(linha[1])[:62])
        y -= 6.2 * mm
    pagina.save()
    return buffer.getvalue()
