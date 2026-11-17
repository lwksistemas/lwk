"""Comprovante não fiscal do salão. O desenho segue o cadastro da loja, sem endereço fixo."""
import html
import re
from io import BytesIO

from django.utils import timezone

from .caixa_service import quantia


def _texto(valor) -> str:
    return valor.strip() if isinstance(valor, str) else ""


def _cep(valor: str) -> str:
    digitos = re.sub(r"\D", "", valor or "")
    if len(digitos) == 8:
        return f"{digitos[:5]}-{digitos[5:]}"
    return _texto(valor)


def _telefone(valor: str) -> str:
    digitos = re.sub(r"\D", "", valor or "")
    if digitos.startswith("55") and len(digitos) in {12, 13}:
        digitos = digitos[2:]
    if len(digitos) == 11:
        return f"({digitos[:2]}) {digitos[2:7]}-{digitos[7:]}"
    if len(digitos) == 10:
        return f"({digitos[:2]}) {digitos[2:6]}-{digitos[6:]}"
    return _texto(valor)


def _reais(valor) -> str:
    texto = f"{quantia(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def _documento(valor: str) -> str:
    digitos = re.sub(r"\D", "", valor or "")
    if len(digitos) == 11:
        return f"CPF {digitos[:3]}.{digitos[3:6]}.{digitos[6:9]}-{digitos[9:]}"
    if len(digitos) == 14:
        return f"CNPJ {digitos[:2]}.{digitos[2:5]}.{digitos[5:8]}/{digitos[8:12]}-{digitos[12:]}"
    return ""


def _cor(valor: str) -> str:
    cor = _texto(valor)
    if re.fullmatch(r"#[0-9A-Fa-f]{6}", cor):
        return cor
    return "#7A3044"


def _logo_exibicao(url: str) -> str:
    """A mídia exige assinatura. O endereço cru do cadastro não abre no navegador nem no PDF."""
    texto = _texto(url)
    if not texto:
        return ""
    try:
        from core.media_storage import assinar_url_midia, is_media_url

        if is_media_url(texto):
            return assinar_url_midia(texto)
    except Exception:
        return texto
    return texto


def _bytes_da_logo(url: str) -> bytes | None:
    texto = _texto(url)
    if not texto:
        return None
    try:
        from clinica_beleza.pdf_common.logo import baixar_logo

        conteudo = baixar_logo(texto, timeout=8)
    except Exception:
        return None
    if not conteudo or len(conteudo) > 2_000_000:
        return None
    return conteudo


def _src_logo(url: str) -> str:
    conteudo = _bytes_da_logo(url)
    if conteudo:
        import base64

        tipo = "image/png"
        if conteudo.startswith(b"\xff\xd8"):
            tipo = "image/jpeg"
        elif conteudo.startswith(b"GIF8"):
            tipo = "image/gif"
        elif conteudo.startswith(b"RIFF") and conteudo[8:12] == b"WEBP":
            tipo = "image/webp"
        return f"data:{tipo};base64,{base64.b64encode(conteudo).decode('ascii')}"
    return _logo_exibicao(url)


def cabecalho_da_loja(loja) -> dict:
    """Nome, endereço, contato e cor saem do cadastro. Sem logomarca, o desenho usa a tesoura do modelo."""
    from superadmin.loja_utils import contato_publico_loja

    if loja is None:
        return {"nome": "Salão", "subtitulo": "", "endereco": "", "documento": "", "telefone": "", "email": "", "logo": "", "cor": "#7A3044"}
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
    endereco = _texto(getattr(loja, "recibo_endereco", "")) or " – ".join(partes)
    documento = _documento(getattr(loja, "recibo_documento", "")) or _documento(getattr(loja, "cpf_cnpj", ""))
    telefone, email = contato_publico_loja(loja)
    tipo = getattr(loja, "tipo_loja", None)
    subtitulo = _texto(getattr(tipo, "nome", "")) if tipo is not None else ""
    if subtitulo.casefold().startswith("salão de "):
        subtitulo = subtitulo[9:].strip()
    logo = _logo_exibicao(_texto(getattr(loja, "recibo_logo", "")) or _texto(getattr(loja, "logo", "")))
    cor = _cor(_texto(getattr(loja, "recibo_cor", "")) or _texto(getattr(loja, "cor_primaria", "")))
    return {
        "nome": _texto(getattr(loja, "nome", "")) or "Salão",
        "subtitulo": subtitulo,
        "endereco": endereco,
        "documento": documento,
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
    from .formas_service import rotulos_conhecidos

    nomes = rotulos_conhecidos()
    linhas = []
    for parte in partes or []:
        if not isinstance(parte, dict):
            continue
        codigo = parte.get("forma") or ""
        linhas.append({
            "nome": nomes.get(codigo, codigo),
            "valor": f"{quantia(parte.get('valor')):.2f}",
        })
    return linhas


def _linhas_do_recibo(recibo) -> list[dict]:
    from .procedimentos_service import servicos_do_agendamento

    servicos = servicos_do_agendamento(recibo.agendamento)
    profissional = recibo.profissional.nome
    if len(servicos) <= 1:
        return [{
            "nome": servicos[0].nome,
            "profissional": profissional,
            "total": f"{quantia(recibo.valor):.2f}",
        }]
    return [
        {"nome": servico.nome, "profissional": profissional, "total": f"{quantia(servico.preco):.2f}"}
        for servico in servicos
    ]


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
        "servicos": [linha for item in recibos for linha in _linhas_do_recibo(item)],
        "produtos": [
            {"nome": item.nome, "quantidade": item.quantidade, "total": f"{quantia(item.total):.2f}"}
            for item in itens
        ],
        "formas": _formas(venda.partes),
        "salao": cabecalho_atual(),
    }


def _com_cancelamento(venda, dados: dict) -> dict:
    saida = dict(dados)
    saida["cancelado"] = not venda.is_active
    if getattr(venda, "cancelado_em", None):
        saida["cancelado_em"] = timezone.localtime(venda.cancelado_em).strftime("%d/%m/%Y às %H:%M")
    if getattr(venda, "cancelado_por", ""):
        saida["cancelado_por"] = venda.cancelado_por
    if getattr(venda, "motivo_cancelamento", ""):
        saida["motivo"] = venda.motivo_cancelamento
    if not venda.is_active:
        from .sessao_service import texto_estorno

        saida["estorno"] = texto_estorno(venda)
    return saida


def operador_visivel(dados: dict) -> str:
    return (dados.get("operador") or "").strip()


def rotulo_total(dados: dict) -> str:
    return "Valor original" if dados.get("cancelado") else "Total pago"


def texto_cancelamento(dados: dict) -> str:
    if not dados.get("cancelado"):
        return ""
    partes = ["Pagamento cancelado"]
    if dados.get("cancelado_em"):
        partes.append(f"em {dados['cancelado_em']}")
    if dados.get("cancelado_por"):
        partes.append(f"por {dados['cancelado_por']}")
    if dados.get("motivo"):
        partes.append(f"Motivo: {dados['motivo']}")
    if dados.get("estorno"):
        partes.append(dados["estorno"])
    return partes[0] if len(partes) == 1 else f"{partes[0]}. {' '.join(partes[1:])}"


def _com_identidade_atual(dados: dict) -> dict:
    """O miolo da venda fica congelado. Nome, cor, logo, endereço e documento seguem o cadastro atual."""
    from tenants.middleware import get_current_loja_id

    if not get_current_loja_id():
        return dados
    saida = dict(dados)
    saida["salao"] = cabecalho_atual()
    return saida


def comprovante_da_venda(venda) -> dict:
    """A segunda via lê o que foi gravado na venda. Recibo antigo monta os valores já salvos."""
    gravado = venda.comprovante if isinstance(getattr(venda, "comprovante", None), dict) else {}
    if gravado.get("numero"):
        return _com_identidade_atual(_com_cancelamento(venda, gravado))
    from .models import Recebimento

    recibos = list(
        Recebimento.objects.filter(venda=venda).select_related("agendamento__servico", "profissional").order_by("id")
    )
    if not recibos and venda.recebimento_id:
        recibos = [venda.recebimento]
    return _com_cancelamento(venda, {
        "numero": venda.numero,
        "quando": timezone.localtime(venda.created_at).strftime("%d/%m/%Y às %H:%M"),
        "cliente": venda.cliente_nome or "Consumidor",
        "operador": venda.operador_nome or "",
        "desconto": f"{quantia(venda.desconto):.2f}",
        "valor": f"{quantia(venda.valor):.2f}",
        "cancelado": not venda.is_active,
        "servicos": [linha for item in recibos for linha in _linhas_do_recibo(item)],
        "produtos": [
            {"nome": item.nome, "quantidade": item.quantidade, "total": f"{quantia(item.total):.2f}"}
            for item in venda.itens.all()
        ],
        "formas": _formas(venda.partes),
        "salao": cabecalho_atual(),
    })


def _icone_svg(nome: str, cor: str, tamanho: int = 16) -> str:
    comum = f'width="{tamanho}" height="{tamanho}" viewBox="0 0 24 24" fill="none" stroke="{cor}" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"'
    desenhos = {
        "pin": f'<svg {comum}><path d="M12 21s6.2-5.4 6.2-10.2a6.2 6.2 0 1 0-12.4 0C5.8 15.6 12 21 12 21z"/><circle cx="12" cy="10.7" r="2"/></svg>',
        "telefone": f'<svg {comum}><path d="M7 3.5h2.4l1.2 3-1.7 1a12 12 0 0 0 5.6 5.6l1-1.7 3 1.2V15a2 2 0 0 1-2.2 2A14.5 14.5 0 0 1 5 6.7 2 2 0 0 1 7 3.5z"/></svg>',
        "email": f'<svg {comum}><rect x="3" y="5" width="18" height="14" rx="2"/><path d="m4 7 8 6 8-6"/></svg>',
        "pessoa": f'<svg {comum}><circle cx="12" cy="8" r="3.1"/><path d="M5.6 19.4c.8-3.3 3-4.8 6.4-4.8s5.6 1.5 6.4 4.8"/></svg>',
        "calendario": f'<svg {comum}><rect x="4" y="5" width="16" height="15" rx="2"/><path d="M8 3.5v4M16 3.5v4M4 10h16"/></svg>',
        "dinheiro": f'<svg {comum}><rect x="2.5" y="6" width="19" height="12" rx="2"/><circle cx="12" cy="12" r="2.2"/></svg>',
        "pix": f'<svg {comum}><path d="m12 3 3.2 3.2L12 9.4 8.8 6.2zM12 14.6l3.2 3.2L12 21l-3.2-3.2zM3 12l3.2-3.2L9.4 12 6.2 15.2zM14.6 12l3.2-3.2L21 12l-3.2 3.2z"/></svg>',
        "cartao": f'<svg {comum}><rect x="2.5" y="5" width="19" height="14" rx="2"/><path d="M2.5 10h19"/></svg>',
        "info": f'<svg {comum}><circle cx="12" cy="12" r="8.5"/><path d="M12 11v5M12 8h.01"/></svg>',
    }
    return desenhos.get(nome, f'<svg {comum}><circle cx="12" cy="12" r="8"/></svg>')


def _tesoura_svg(cor: str, tamanho: int) -> str:
    return (
        f'<svg width="{tamanho}" height="{tamanho}" viewBox="0 0 72 72" fill="none" stroke="{cor}" '
        'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
        '<path d="M36 8c-16 3-26 14-28 28 8-10 16-14 28-14s20 4 28 14C62 22 52 11 36 8z"/>'
        '<circle cx="24" cy="52" r="7"/><circle cx="48" cy="52" r="7"/>'
        '<path d="M29 47 47 16"/><path d="M43 47 25 16"/></svg>'
    )


def _chave_forma(nome: str) -> str:
    texto = _texto(nome).lower()
    troca = str.maketrans("áàâãéêíóôõúç", "aaaaeeiooouc")
    texto = texto.translate(troca)
    if "pix" in texto:
        return "pix"
    if "dinheiro" in texto:
        return "dinheiro"
    if "debito" in texto or "credito" in texto or "cart" in texto:
        return "cartao"
    return "outro"


def html_comprovante(dados: dict) -> str:
    salao = dados.get("salao") or {}
    cor = _cor(salao.get("cor") or "")
    nome = html.escape(salao.get("nome") or "Salão")
    subtitulo = html.escape((salao.get("subtitulo") or "").upper())
    logo = _src_logo(str(salao.get("logo") or ""))
    if logo.startswith(("http://", "https://", "/", "data:")):
        marca = f'<img src="{html.escape(logo, quote=True)}" alt="" style="height:64px;width:auto;max-width:88px;object-fit:contain" />'
    else:
        marca = _tesoura_svg(cor, 64)
    endereco = html.escape(salao.get("endereco") or "")
    telefone = html.escape(_telefone(salao.get("telefone") or "")) if salao.get("telefone") else ""
    email = html.escape(salao.get("email") or "")
    contato = []
    if endereco:
        contato.append(
            f'<div style="display:flex;align-items:flex-start;gap:6px;color:{cor}">{_icone_svg("pin", cor)}'
            f'<span style="color:#3a2a2e">{endereco}</span></div>'
        )
    linha_contato = []
    if telefone:
        linha_contato.append(
            f'<span style="display:inline-flex;align-items:center;gap:4px;color:{cor}">{_icone_svg("telefone", cor)}'
            f'<span style="color:#3a2a2e">{telefone}</span></span>'
        )
    if email:
        if telefone:
            linha_contato.append('<span style="color:#b7a4a8">|</span>')
        linha_contato.append(
            f'<span style="display:inline-flex;align-items:center;gap:4px;color:{cor}">{_icone_svg("email", cor)}'
            f'<span style="color:#3a2a2e">{email}</span></span>'
        )
    if linha_contato:
        contato.append(f'<div style="display:flex;flex-wrap:wrap;align-items:center;gap:8px">{"".join(linha_contato)}</div>')
    documento = html.escape(salao.get("documento") or "")
    if documento:
        contato.append(f'<div style="color:#3a2a2e">{documento}</div>')
    subtitulo_html = (
        f'<div style="margin-top:4px;font-size:11px;letter-spacing:.22em;text-transform:uppercase;color:{cor}">{subtitulo}</div>'
        if subtitulo else ""
    )
    servicos = dados.get("servicos") or []
    produtos = dados.get("produtos") or []
    linhas = []
    if servicos:
        linhas.append('<div style="display:flex;justify-content:space-between;padding:8px 12px;font-weight:700"><span>Serviço</span><span>Valor</span></div>')
        for item in servicos:
            profissional = (
                f'<span style="display:block;margin-top:2px;font-size:12px;font-weight:400;color:#6b4a52">Profissional: {html.escape(item.get("profissional") or "")}</span>'
                if item.get("profissional") else ""
            )
            linhas.append(
                '<div style="display:flex;justify-content:space-between;gap:12px;border-top:1px solid #ead8dc;padding:8px 12px">'
                f'<span><strong>{html.escape(item.get("nome") or "Serviço")}</strong>{profissional}</span>'
                f'<span style="white-space:nowrap">{_reais(item.get("total"))}</span></div>'
            )
    if produtos:
        linhas.append('<div style="display:flex;justify-content:space-between;border-top:1px solid #ead8dc;padding:8px 12px;font-weight:700"><span>Produto</span><span>Valor</span></div>')
        for item in produtos:
            quantidade = item.get("quantidade") or 1
            prefixo = f"{quantidade}× " if quantidade > 1 else ""
            linhas.append(
                '<div style="display:flex;justify-content:space-between;gap:12px;border-top:1px solid #ead8dc;padding:8px 12px">'
                f'<span>{prefixo}{html.escape(item.get("nome") or "Produto")}</span>'
                f'<span style="white-space:nowrap">{_reais(item.get("total"))}</span></div>'
            )
    if quantia(dados.get("desconto")) > 0:
        linhas.append(
            '<div style="display:flex;justify-content:space-between;border-top:1px solid #ead8dc;padding:8px 12px">'
            f'<span>Desconto</span><span>{_reais(dados.get("desconto"))}</span></div>'
        )
    formas = []
    for item in dados.get("formas") or []:
        nome_forma = html.escape(item.get("nome") or "")
        formas.append(
            '<div style="display:flex;align-items:center;justify-content:space-between;gap:8px;border-bottom:1px solid #ead8dc;padding:6px 0">'
            f'<span style="display:inline-flex;align-items:center;gap:8px;color:{cor}">{_icone_svg(_chave_forma(item.get("nome") or ""), cor)}'
            f'<span style="color:#2a1c20">{nome_forma}</span></span>'
            f'<span>{_reais(item.get("valor"))}</span></div>'
        )
    numero = dados.get("numero")
    numero_txt = f"{int(numero):06d}" if numero else "Sem número"
    aviso = ""
    if dados.get("cancelado"):
        detalhe = html.escape(texto_cancelamento(dados))
        aviso = (
            '<p style="margin:8px 0 0;text-align:center;font-family:sans-serif;font-weight:700;color:#9f1239">CANCELADO</p>'
            f'<p style="margin:0;text-align:center;font-family:sans-serif;font-size:11px;color:#9f1239">{detalhe}</p>'
        )
    operador = operador_visivel(dados)
    operador_html = (
        f'<span style="display:block;margin-top:2px;font-size:12px;color:#5c3d45">Operador: {html.escape(operador)}</span>'
        if operador else ""
    )
    faixa = "PRÉVIA — NÃO É COMPROVANTE DE PAGAMENTO" if not numero else "COMPROVANTE DE PAGAMENTO<br>(NÃO FISCAL)"
    rotulo = html.escape(rotulo_total(dados))
    quando = html.escape(dados.get("quando") or "")
    cliente = html.escape(dados.get("cliente") or "Consumidor")
    return f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>Comprovante {html.escape(numero_txt)}</title>
<style>
body{{margin:0;background:#fff;color:#2a1c20;font-family:Georgia,"Times New Roman",serif}}
.folha{{width:170mm;max-width:100%;margin:0 auto;background:#fff}}
@media print{{
  @page{{size:A4;margin:12mm}}
  *{{-webkit-print-color-adjust:exact !important;print-color-adjust:exact !important}}
}}
</style></head><body><article class="folha">
<div style="padding:22px 26px 8px">
<div style="display:flex;align-items:center;justify-content:center;gap:12px">
<div style="color:{cor}">{marca}</div>
<div style="width:1px;height:56px;background:{cor}"></div>
<div>
<div style="font-size:26px;font-weight:700;line-height:1;color:{cor}">{nome}</div>
{subtitulo_html}
<div style="margin-top:6px;width:64px;height:1px;background:{cor}"></div>
</div>
</div>
<div style="margin-top:12px;font-family:sans-serif;font-size:12px">{''.join(contato)}</div>
<div style="margin-top:12px;height:1px;background:{cor}"></div>
<div style="margin-top:12px;border-radius:12px;background:{cor};color:#fff;text-align:center;padding:10px 12px;font-family:sans-serif;font-weight:700;letter-spacing:.04em">{faixa}</div>
{aviso}
<div style="display:flex;align-items:center;justify-content:space-between;gap:8px;margin-top:12px;font-family:sans-serif;font-size:13px"><span><strong>Nº:</strong> {html.escape(numero_txt)}</span><span style="display:inline-flex;align-items:center;gap:4px;color:{cor}">{_icone_svg("calendario", cor, 15)}<span style="color:#2a1c20">{quando}</span></span></div>
<div style="display:flex;align-items:flex-start;gap:8px;margin-top:10px;border:1px solid #ead8dc;border-radius:12px;padding:10px 12px;font-family:sans-serif;font-size:13px"><span style="color:{cor}">{_icone_svg("pessoa", cor)}</span><span>Cliente: <strong>{cliente}</strong>{operador_html}</span></div>
<div style="margin-top:10px;overflow:hidden;border:1px solid #ead8dc;border-radius:12px;font-family:sans-serif;font-size:13px">{''.join(linhas)}</div>
<div style="display:flex;align-items:center;justify-content:space-between;margin-top:10px;border-radius:12px;background:{cor};color:#fff;padding:10px 14px;font-family:sans-serif"><span style="font-size:15px;font-weight:700">{rotulo}:</span><span style="font-size:20px;font-weight:700">{_reais(dados.get("valor"))}</span></div>
<div style="margin-top:12px;font-family:sans-serif;font-size:13px"><p style="margin:0 0 4px;font-weight:700">Formas de pagamento:</p>{''.join(formas)}</div>
<div style="display:flex;align-items:flex-start;gap:8px;margin-top:12px;border:1px solid #ead8dc;border-radius:12px;padding:10px 12px;font-family:sans-serif;font-size:11px;line-height:1.35;color:#5c3d45"><span style="color:{cor}">{_icone_svg("info", cor)}</span><span>Este comprovante não substitui a emissão de Nota Fiscal (NFS-e) ou Cupom Fiscal (NFC-e).</span></div>
<p style="margin:16px 0 0;text-align:center;font-size:26px;line-height:1.1;color:{cor};font-family:'Segoe Script','Brush Script MT','URW Chancery L',cursive">Obrigado pela preferência!</p>
<div style="display:flex;align-items:center;gap:12px;margin:8px 24px 0;color:{cor}"><span style="flex:1;height:1px;background:{cor}"></span>{_tesoura_svg(cor, 22)}<span style="flex:1;height:1px;background:{cor}"></span></div>
</div>
<svg viewBox="0 0 600 70" preserveAspectRatio="none" style="display:block;width:100%;height:56px" aria-hidden="true"><path fill="{cor}" d="M0 38c70-26 130-28 200-6s150 30 210 6 130-28 190-8v40H0z"/><path fill="{cor}" opacity="0.55" d="M0 50c90-18 150-14 230 2s170 14 250-8 80-14 120-6v32H0z"/></svg>
</article></body></html>"""


def pdf_comprovante(dados: dict) -> bytes:
    """PDF em A4, o mesmo cartão da prévia e da impressão."""
    from reportlab.lib.colors import Color, white
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    salao = dados.get("salao") or {}
    cor_hex = _cor(salao.get("cor") or "")
    cor = Color(int(cor_hex[1:3], 16) / 255, int(cor_hex[3:5], 16) / 255, int(cor_hex[5:7], 16) / 255)
    tinta = Color(0.16, 0.11, 0.13)
    cinza = Color(0.42, 0.29, 0.32)
    branco = white
    largura = A4[0]
    esquerda = 40
    direita = largura - 40
    miolo = direita - esquerda

    def _linhas(texto, tamanho):
        if not texto:
            return 0
        capacidade = max(24, int(miolo / (tamanho * 0.48)))
        return max(1, (len(str(texto)) + capacidade - 1) // capacidade)

    altura_pagina = 42 + 62
    if salao.get("endereco"):
        altura_pagina += 13 * _linhas(salao.get("endereco"), 9)
    if salao.get("documento"):
        altura_pagina += 13
    if salao.get("telefone") or salao.get("email"):
        altura_pagina += 16
    altura_pagina += 14 + (34 if dados.get("numero") else 24) + 14
    if dados.get("cancelado"):
        altura_pagina += 20 + 10 * _linhas(texto_cancelamento(dados), 8)
    altura_pagina += 16 + (40 if operador_visivel(dados) else 30)
    tabela = 0
    if dados.get("servicos"):
        tabela += 16 + sum(26 if item.get("profissional") else 16 for item in dados["servicos"])
    if dados.get("produtos"):
        tabela += 16 + 16 * len(dados["produtos"])
    if quantia(dados.get("desconto")) > 0:
        tabela += 16
    if tabela:
        altura_pagina += tabela + 20
    altura_pagina += 42
    if dados.get("formas"):
        altura_pagina += 22 + 18 * len(dados["formas"])
    altura_pagina += 36 + 11 * _linhas("Este comprovante não substitui a emissão de Nota Fiscal (NFS-e) ou Cupom Fiscal (NFC-e).", 8)
    altura_pagina += 90
    altura_pagina = min(A4[1], altura_pagina)
    buffer = BytesIO()
    pagina = canvas.Canvas(buffer, pagesize=(largura, altura_pagina))
    y = altura_pagina - 42

    def quebra(texto, fonte, tamanho, limite):
        palavras = str(texto or "").split()
        if not palavras:
            return [""]
        linhas, atual = [], ""
        for palavra in palavras:
            candidato = f"{atual} {palavra}".strip()
            if pagina.stringWidth(candidato, fonte, tamanho) <= limite:
                atual = candidato
            else:
                if atual:
                    linhas.append(atual)
                atual = palavra
        if atual:
            linhas.append(atual)
        return linhas

    def tesoura(cx, cy, escala):
        pagina.setStrokeColor(cor)
        pagina.setFillColor(branco)
        pagina.setLineWidth(max(0.8, 1.1 * escala))
        pagina.setLineCap(1)
        pagina.circle(cx - 8 * escala, cy - 6 * escala, 5 * escala, stroke=1, fill=0)
        pagina.circle(cx + 8 * escala, cy - 6 * escala, 5 * escala, stroke=1, fill=0)
        pagina.line(cx - 4 * escala, cy - 2 * escala, cx + 8 * escala, cy + 16 * escala)
        pagina.line(cx + 4 * escala, cy - 2 * escala, cx - 8 * escala, cy + 16 * escala)
        pagina.arc(cx - 26 * escala, cy, cx - 2 * escala, cy + 22 * escala, 20, 230)
        pagina.arc(cx + 2 * escala, cy, cx + 26 * escala, cy + 22 * escala, -70, 230)

    def marca(tipo, x, cy):
        pagina.saveState()
        pagina.setStrokeColor(cor)
        pagina.setLineWidth(0.9)
        pagina.setLineCap(1)
        if tipo == "pin":
            pagina.circle(x + 5, cy + 6, 2.4, stroke=1, fill=0)
            pagina.line(x + 5, cy + 3.6, x + 5, cy)
        elif tipo == "pessoa":
            pagina.circle(x + 5, cy + 7, 2.3, stroke=1, fill=0)
            pagina.arc(x + 1, cy - 1, x + 9, cy + 6, 200, 140)
        elif tipo == "calendario":
            pagina.roundRect(x, cy, 11, 9, 1, stroke=1, fill=0)
            pagina.line(x, cy + 6, x + 11, cy + 6)
        elif tipo == "dinheiro":
            pagina.roundRect(x, cy + 1, 12, 8, 1.2, stroke=1, fill=0)
            pagina.circle(x + 6, cy + 5, 1.7, stroke=1, fill=0)
        elif tipo == "pix":
            pagina.saveState()
            pagina.translate(x + 6, cy + 5)
            pagina.rotate(45)
            pagina.rect(-2.2, -2.2, 4.4, 4.4, stroke=1, fill=0)
            pagina.restoreState()
        elif tipo == "cartao":
            pagina.roundRect(x, cy + 1, 13, 8, 1, stroke=1, fill=0)
            pagina.line(x, cy + 6, x + 13, cy + 6)
        elif tipo == "telefone":
            pagina.roundRect(x + 3, cy + 1, 5, 8, 1, stroke=1, fill=0)
            pagina.line(x + 1, cy + 3, x + 4, cy + 5)
            pagina.line(x + 7, cy + 5, x + 10, cy + 7)
        elif tipo == "email":
            pagina.rect(x, cy + 2, 12, 8, stroke=1, fill=0)
            pagina.line(x, cy + 10, x + 6, cy + 6)
            pagina.line(x + 12, cy + 10, x + 6, cy + 6)
        elif tipo == "info":
            pagina.circle(x + 5, cy + 5, 5, stroke=1, fill=0)
            pagina.setFillColor(cor)
            pagina.setFont("Times-Bold", 7)
            pagina.drawCentredString(x + 5, cy + 2.4, "i")
        else:
            pagina.circle(x + 4, cy + 4, 3, stroke=1, fill=0)
        pagina.restoreState()

    centro = largura / 2
    desenhou_logo = False
    conteudo = _bytes_da_logo(str(salao.get("logo") or ""))
    if conteudo:
        try:
            from PIL import Image as PILImage
            from reportlab.lib.utils import ImageReader

            pil = PILImage.open(BytesIO(conteudo))
            if pil.mode not in ("RGB", "RGBA"):
                pil = pil.convert("RGBA")
            buf = BytesIO()
            pil.save(buf, format="PNG")
            buf.seek(0)
            imagem = ImageReader(buf)
            iw, ih = imagem.getSize()
            alt = 46
            larg = min(70, alt * iw / max(ih, 1))
            pagina.drawImage(imagem, centro - 108, y - 40, width=larg, height=alt, mask="auto", preserveAspectRatio=True, anchor="c")
            desenhou_logo = True
        except Exception:
            desenhou_logo = False
    if not desenhou_logo:
        tesoura(centro - 86, y - 18, 1.05)
    pagina.setStrokeColor(cor)
    pagina.setLineWidth(1)
    pagina.line(centro - 48, y - 40, centro - 48, y + 4)
    pagina.setFillColor(cor)
    pagina.setFont("Times-Bold", 22)
    pagina.drawString(centro - 36, y - 14, str(salao.get("nome") or "Salão")[:28])
    subtitulo = str(salao.get("subtitulo") or "").upper()
    if subtitulo:
        pagina.setFont("Times-Roman", 9)
        pagina.drawString(centro - 36, y - 28, subtitulo[:36])
    pagina.setLineWidth(0.8)
    pagina.line(centro - 36, y - 36, centro + 20, y - 36)
    y -= 62

    pagina.setFillColor(tinta)
    pagina.setFont("Times-Roman", 9)
    if salao.get("endereco"):
        for linha in quebra(salao.get("endereco"), "Times-Roman", 9, miolo - 16):
            marca("pin", esquerda, y - 2)
            pagina.setFillColor(tinta)
            pagina.drawString(esquerda + 16, y, linha)
            y -= 13
    telefone = _telefone(salao.get("telefone") or "")
    email = str(salao.get("email") or "")
    cursor = esquerda
    if telefone or email:
        pagina.setFont("Times-Roman", 9)
        if telefone:
            marca("telefone", cursor, y - 2)
            pagina.setFillColor(tinta)
            pagina.drawString(cursor + 16, y, telefone)
            cursor += 16 + pagina.stringWidth(telefone, "Times-Roman", 9) + 8
        if telefone and email:
            pagina.setFillColor(cinza)
            pagina.drawString(cursor, y, "|")
            cursor += pagina.stringWidth("|", "Times-Roman", 9) + 8
        if email:
            marca("email", cursor, y - 2)
            pagina.setFillColor(tinta)
            pagina.drawString(cursor + 16, y, email[:42])
        y -= 16
    if salao.get("documento"):
        pagina.setFillColor(tinta)
        pagina.setFont("Times-Roman", 9)
        pagina.drawString(esquerda, y, str(salao.get("documento"))[:60])
        y -= 13
    pagina.setStrokeColor(cor)
    pagina.setLineWidth(0.8)
    pagina.line(esquerda, y, direita, y)
    y -= 14

    faixa = "PRÉVIA — NÃO É COMPROVANTE DE PAGAMENTO" if not dados.get("numero") else "COMPROVANTE DE PAGAMENTO"
    extra = "" if not dados.get("numero") else "(NÃO FISCAL)"
    altura_faixa = 34 if extra else 24
    pagina.setFillColor(cor)
    pagina.roundRect(esquerda, y - altura_faixa, miolo, altura_faixa, 8, stroke=0, fill=1)
    pagina.setFillColor(branco)
    pagina.setFont("Times-Bold", 11)
    pagina.drawCentredString(largura / 2, y - (14 if extra else 16), faixa)
    if extra:
        pagina.setFont("Times-Bold", 10)
        pagina.drawCentredString(largura / 2, y - 28, extra)
    y -= altura_faixa + 14

    if dados.get("cancelado"):
        pagina.setFillColor(Color(0.62, 0.07, 0.22))
        pagina.setFont("Times-Bold", 12)
        pagina.drawCentredString(largura / 2, y, "CANCELADO")
        y -= 12
        detalhe = texto_cancelamento(dados)
        pagina.setFont("Times-Roman", 8)
        for linha in quebra(detalhe, "Times-Roman", 8, miolo):
            pagina.drawCentredString(largura / 2, y, linha)
            y -= 10
        y -= 4

    numero = dados.get("numero")
    numero_txt = f"{int(numero):06d}" if numero else "Sem número"
    pagina.setFillColor(tinta)
    pagina.setFont("Times-Bold", 10)
    pagina.drawString(esquerda, y, "Nº:")
    pagina.setFont("Times-Roman", 10)
    pagina.drawString(esquerda + 22, y, numero_txt)
    quando = str(dados.get("quando") or "")
    marca("calendario", direita - pagina.stringWidth(quando, "Times-Roman", 10) - 18, y - 2)
    pagina.setFillColor(tinta)
    pagina.drawRightString(direita, y, quando)
    y -= 16

    cliente = f"Cliente: {dados.get('cliente') or 'Consumidor'}"
    operador = operador_visivel(dados)
    altura_cliente = 32 if operador else 22
    pagina.setStrokeColor(Color(0.92, 0.847, 0.863))
    pagina.setLineWidth(0.8)
    pagina.roundRect(esquerda, y - altura_cliente + 8, miolo, altura_cliente, 8, stroke=1, fill=0)
    marca("pessoa", esquerda + 8, y - 6)
    pagina.setFillColor(tinta)
    pagina.setFont("Times-Roman", 11)
    pagina.drawString(esquerda + 26, y - 2, cliente[:70])
    if operador:
        pagina.setFillColor(cinza)
        pagina.setFont("Times-Roman", 8)
        pagina.drawString(esquerda + 26, y - 14, f"Operador: {operador[:60]}")
    y -= altura_cliente + 8

    blocos = []
    if dados.get("servicos"):
        blocos.append(("cabeca", "Serviço", "Valor"))
        for item in dados["servicos"]:
            blocos.append(("servico", item.get("nome") or "Serviço", item.get("profissional") or "", _reais(item.get("total"))))
    if dados.get("produtos"):
        blocos.append(("cabeca", "Produto", "Valor"))
        for item in dados["produtos"]:
            quantidade = item.get("quantidade") or 1
            nome_produto = item.get("nome") or "Produto"
            if quantidade > 1:
                nome_produto = f"{quantidade}× {nome_produto}"
            blocos.append(("produto", nome_produto, _reais(item.get("total"))))
    if quantia(dados.get("desconto")) > 0:
        blocos.append(("produto", "Desconto", _reais(dados.get("desconto"))))
    altura_tabela = 8
    for bloco in blocos:
        altura_tabela += 26 if bloco[0] == "servico" and bloco[2] else 16
    if blocos:
        base = y - altura_tabela
        pagina.roundRect(esquerda, base, miolo, altura_tabela, 8, stroke=1, fill=0)
        cursor = y - 14
        for bloco in blocos:
            pagina.setFillColor(tinta)
            if bloco[0] == "cabeca":
                pagina.setFont("Times-Bold", 11)
                pagina.drawString(esquerda + 10, cursor, bloco[1])
                pagina.drawRightString(direita - 10, cursor, bloco[2])
                cursor -= 16
            elif bloco[0] == "servico":
                pagina.setFont("Times-Bold", 11)
                pagina.drawString(esquerda + 10, cursor, str(bloco[1])[:42])
                pagina.drawRightString(direita - 10, cursor, bloco[3])
                if bloco[2]:
                    pagina.setFillColor(cinza)
                    pagina.setFont("Times-Roman", 8)
                    pagina.drawString(esquerda + 10, cursor - 11, f"Profissional: {bloco[2]}"[:64])
                    cursor -= 26
                else:
                    cursor -= 16
            else:
                pagina.setFont("Times-Roman", 11)
                pagina.drawString(esquerda + 10, cursor, str(bloco[1])[:42])
                pagina.drawRightString(direita - 10, cursor, bloco[2])
                cursor -= 16
        y = base - 12

    rotulo = f"{rotulo_total(dados)}:"
    pagina.setFillColor(cor)
    pagina.roundRect(esquerda, y - 26, miolo, 28, 8, stroke=0, fill=1)
    pagina.setFillColor(branco)
    pagina.setFont("Times-Bold", 12)
    pagina.drawString(esquerda + 12, y - 16, rotulo)
    pagina.setFont("Times-Bold", 16)
    pagina.drawRightString(direita - 12, y - 17, _reais(dados.get("valor")))
    y -= 42

    formas = dados.get("formas") or []
    if formas:
        pagina.setFillColor(tinta)
        pagina.setFont("Times-Bold", 11)
        pagina.drawString(esquerda, y, "Formas de pagamento:")
        y -= 16
        for item in formas:
            pagina.setStrokeColor(Color(0.92, 0.847, 0.863))
            pagina.setLineWidth(0.6)
            pagina.line(esquerda, y - 4, direita, y - 4)
            marca(_chave_forma(item.get("nome") or ""), esquerda, y - 2)
            pagina.setFillColor(tinta)
            pagina.setFont("Times-Roman", 11)
            pagina.drawString(esquerda + 18, y, str(item.get("nome") or "")[:40])
            pagina.drawRightString(direita, y, _reais(item.get("valor")))
            y -= 18
        y -= 6

    aviso = "Este comprovante não substitui a emissão de Nota Fiscal (NFS-e) ou Cupom Fiscal (NFC-e)."
    linhas_aviso = quebra(aviso, "Times-Roman", 8, miolo - 28)
    altura_aviso = 12 + 11 * len(linhas_aviso)
    pagina.setStrokeColor(Color(0.92, 0.847, 0.863))
    pagina.roundRect(esquerda, y - altura_aviso + 6, miolo, altura_aviso, 8, stroke=1, fill=0)
    marca("info", esquerda + 8, y - 8)
    pagina.setFillColor(cinza)
    pagina.setFont("Times-Roman", 8)
    cursor = y - 4
    for linha in linhas_aviso:
        pagina.drawString(esquerda + 24, cursor, linha)
        cursor -= 11
    y -= altura_aviso + 22

    pagina.setFillColor(cor)
    pagina.setFont("Times-Italic", 18)
    pagina.drawCentredString(largura / 2, y, "Obrigado pela preferência!")
    y -= 16
    pagina.setStrokeColor(cor)
    pagina.setLineWidth(0.7)
    pagina.line(esquerda + 50, y + 6, centro - 16, y + 6)
    pagina.line(centro + 16, y + 6, direita - 50, y + 6)
    tesoura(centro, y - 2, 0.45)
    y -= 28
    def onda(base, alpha):
        traco = pagina.beginPath()
        traco.moveTo(0, base + 8)
        traco.curveTo(largura * 0.16, base + 32, largura * 0.34, base + 2, largura * 0.52, base + 20)
        traco.curveTo(largura * 0.7, base + 38, largura * 0.86, base + 6, largura, base + 16)
        traco.lineTo(largura, base - 4)
        traco.lineTo(0, base - 4)
        traco.close()
        pagina.setFillColor(Color(cor.red, cor.green, cor.blue, alpha=alpha))
        pagina.drawPath(traco, stroke=0, fill=1)

    onda(y, 1)
    onda(y - 10, 0.45)
    numero_arquivo = numero_txt if numero else "previa"
    pagina.setTitle(f"Comprovante {numero_arquivo}")
    pagina.save()
    return buffer.getvalue()
