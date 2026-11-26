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


def _tom(cor: str, branco: float) -> str:
    r, g, b = int(cor[1:3], 16), int(cor[3:5], 16), int(cor[5:7], 16)

    def mistura(canal: int) -> int:
        return round(canal + (255 - canal) * branco)

    return f"#{mistura(r):02X}{mistura(g):02X}{mistura(b):02X}"


def _escuro(cor: str) -> str:
    r, g, b = int(cor[1:3], 16), int(cor[3:5], 16), int(cor[5:7], 16)
    return f"#{round(r * 0.72):02X}{round(g * 0.72):02X}{round(b * 0.72):02X}"


def _css_fonte() -> str:
    from pathlib import Path

    caminho = Path(__file__).with_name("fonts") / "GreatVibes-Recibo.ttf"
    if not caminho.is_file():
        return ""
    import base64

    codigo = base64.b64encode(caminho.read_bytes()).decode("ascii")
    return (
        "@font-face{font-family:'ReciboScript';src:url(data:font/ttf;base64,"
        f"{codigo}) format('truetype');font-weight:400;font-style:normal;}}"
    )


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
        from core.pdf_logo import baixar_logo

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


def situacao_do_recibo(dados: dict) -> str:
    """Cancelado, pendente e parcial não usam o rótulo de pagamento quitado."""
    if dados.get("numero") and dados.get("cancelado"):
        return "cancelado"
    formas = [item for item in (dados.get("formas") or []) if isinstance(item, dict) and quantia(item.get("valor")) > 0]
    recebido = sum((quantia(item.get("valor")) for item in formas), quantia(0))
    total = quantia(dados.get("valor"))
    if dados.get("numero") and recebido <= 0:
        return "pendente"
    if total > 0 and recebido > 0 and recebido + quantia("0.009") < total:
        return "parcial"
    if not dados.get("numero"):
        return "previa"
    return "quitado"


def valor_recebido(dados: dict):
    return sum(
        (quantia(item.get("valor")) for item in (dados.get("formas") or []) if isinstance(item, dict)),
        quantia(0),
    )


def rotulo_total(dados: dict) -> str:
    situacao = situacao_do_recibo(dados)
    if situacao == "cancelado":
        return "Valor da operação"
    if situacao == "pendente":
        return "Valor em aberto"
    if situacao == "parcial":
        return "Valor recebido"
    if situacao == "previa":
        return "Total"
    return "Total pago"


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
        f'<svg width="{tamanho}" height="{tamanho}" viewBox="0 0 64 64" fill="none" stroke="{cor}" '
        'stroke-width="2" stroke-linecap="round" aria-hidden="true">'
        '<path d="M14 20c8-8 28-8 36 0"/>'
        '<circle cx="22" cy="46" r="7" fill="#fff"/>'
        '<circle cx="42" cy="46" r="7" fill="#fff"/>'
        '<path d="M27 42 44 16"/><path d="M37 42 20 16"/></svg>'
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
            f'<span style="display:inline-flex;align-items:center;gap:4px;color:{cor};white-space:nowrap">{_icone_svg("telefone", cor)}'
            f'<span style="color:#3a2a2e">{telefone}</span></span>'
        )
    if email:
        if telefone:
            linha_contato.append('<span style="color:#b7a4a8">|</span>')
        linha_contato.append(
            f'<span style="display:inline-flex;align-items:center;gap:4px;color:{cor};white-space:nowrap">{_icone_svg("email", cor)}'
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
    claro = _tom(cor, 0.86)
    escuro = _escuro(cor)
    servicos = dados.get("servicos") or []
    produtos = dados.get("produtos") or []
    linhas = []
    if servicos:
        linhas.append(f'<div class="cabeca" style="background:{claro}"><span>Serviço</span><span>Valor</span></div>')
        for item in servicos:
            profissional = (
                f'<span style="display:block;margin-top:2px;font-size:12px;font-weight:400;color:#6b4a52">Profissional: {html.escape(item.get("profissional") or "")}</span>'
                if item.get("profissional") else ""
            )
            linhas.append(
                '<div class="linha" style="display:flex;justify-content:space-between;gap:12px;border-top:1px solid #ead8dc;padding:8px 12px">'
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
    situacao = situacao_do_recibo(dados)
    faixa = "PRÉVIA — NÃO É COMPROVANTE DE PAGAMENTO" if situacao == "previa" else "COMPROVANTE DE PAGAMENTO<br>(NÃO FISCAL)"
    quando = html.escape(dados.get("quando") or "")
    cliente = html.escape(dados.get("cliente") or "Consumidor")
    recebido = valor_recebido(dados)
    saldo = quantia(dados.get("valor")) - recebido
    if situacao == "parcial":
        bloco_valor = (
            f'<div class="extra"><span>Total da operação</span><span>{_reais(dados.get("valor"))}</span></div>'
            f'<div class="faixa" style="background:{claro};color:{cor}"><span>Valor recebido</span><strong>{_reais(recebido)}</strong></div>'
            f'<div class="extra saldo"><span>Saldo pendente</span><strong>{_reais(saldo)}</strong></div>'
        )
    elif situacao == "cancelado":
        bloco_valor = (
            f'<div class="faixa" style="background:{claro};color:{cor}"><span>Valor da operação</span><strong>{_reais(dados.get("valor"))}</strong></div>'
            '<p class="nota">Valores do histórico. Esta operação foi cancelada e não representa dinheiro recebido.</p>'
        )
    else:
        bloco_valor = (
            f'<div class="faixa" style="background:{claro};color:{cor}"><span>{html.escape(rotulo_total(dados))}</span>'
            f'<strong>{_reais(dados.get("valor"))}</strong></div>'
        )
    if situacao == "cancelado" and formas:
        titulo_formas = "Histórico das formas registradas"
    elif formas and situacao != "pendente":
        titulo_formas = "Formas de pagamento:"
    else:
        titulo_formas = ""
    bloco_formas = ""
    if titulo_formas:
        bloco_formas = f'<div class="formas"><p>{titulo_formas}</p>{"".join(formas)}</div>'
    return f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>Comprovante {html.escape(numero_txt)}</title>
<style>
{_css_fonte()}
body{{margin:0;background:#fff;color:#2a1c20;font-family:Georgia,"Times New Roman",serif}}
.folha{{width:100%;margin:0 auto;background:#fff}}
.miolo{{padding:22px 26px 8px}}
.marca{{display:flex;align-items:center;justify-content:center;gap:12px}}
.traco{{width:1px;height:56px;background:{cor}}}
.nome{{font-size:26px;font-weight:700;line-height:1;color:{cor}}}
.contato{{margin-top:12px;font-family:sans-serif;font-size:12px}}
.separa{{margin-top:12px;height:1px;background:{cor}}}
.banner{{margin-top:12px;border-radius:14px;background:linear-gradient(90deg,{escuro},{cor} 48%,{escuro});color:#fff;text-align:center;padding:12px 14px;font-family:sans-serif;font-weight:700;letter-spacing:.04em}}
.meta,.cliente,.tabela,.formas,.aviso,.extra,.nota{{font-family:sans-serif}}
.meta{{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-top:12px;font-size:13px}}
.cliente{{display:flex;align-items:flex-start;gap:8px;margin-top:10px;border:1px solid #ead8dc;border-radius:12px;padding:10px 12px;font-size:13px}}
.tabela{{margin-top:10px;overflow:hidden;border:1px solid #ead8dc;border-radius:12px;font-size:13px}}
.cabeca,.extra,.faixa{{display:flex;align-items:center;justify-content:space-between;gap:12px}}
.cabeca{{padding:8px 12px;font-weight:700}}
.faixa{{margin-top:10px;border-radius:12px;padding:10px 14px}}
.faixa span{{font-size:16px;font-weight:700}}
.faixa strong{{font-size:22px}}
.extra{{margin-top:8px;padding:0 4px;font-size:13px}}
.saldo strong{{color:{cor}}}
.nota{{margin:8px 0 0;font-size:11px;color:#9f1239}}
.formas{{margin-top:12px;font-size:13px}}
.formas p{{margin:0 0 4px;font-weight:700}}
.aviso{{display:flex;align-items:flex-start;gap:8px;margin-top:12px;border:1px solid #ead8dc;border-radius:12px;background:#fbf7f8;padding:10px 12px;font-size:11px;line-height:1.35;color:#5c3d45}}
.obrigado{{margin:16px 0 0;text-align:center;font-size:34px;line-height:1.05;color:{cor};font-family:'ReciboScript','Segoe Script','Brush Script MT',cursive}}
.tesoura{{display:flex;align-items:center;gap:12px;margin:8px 24px 0;color:{cor}}}
.tesoura span{{flex:1;height:1px;background:{cor}}}
.linha,.cliente,.faixa,.aviso,.obrigado{{break-inside:avoid}}
@page{{size:A4;margin:12mm}}
@media print{{*{{-webkit-print-color-adjust:exact !important;print-color-adjust:exact !important}}}}
</style></head><body><article class="folha">
<div class="miolo">
<div class="marca"><div style="color:{cor}">{marca}</div><div class="traco"></div><div><div class="nome">{nome}</div>{subtitulo_html}<div class="separa" style="width:64px;margin-top:6px"></div></div></div>
<div class="contato">{''.join(contato)}</div>
<div class="separa"></div>
<div class="banner">{faixa}</div>
{aviso}
<div class="meta"><span><strong>Nº:</strong> {html.escape(numero_txt)}</span><span style="display:inline-flex;align-items:center;gap:4px;color:{cor};white-space:nowrap">{_icone_svg("calendario", cor, 15)}<span style="color:#2a1c20">{quando}</span></span></div>
<div class="cliente"><span style="color:{cor}">{_icone_svg("pessoa", cor)}</span><span>Cliente: <strong>{cliente}</strong>{operador_html}</span></div>
<div class="tabela">{''.join(linhas)}</div>
{bloco_valor}
{bloco_formas}
<div class="aviso"><span style="color:{cor}">{_icone_svg("info", cor)}</span><span>Este comprovante não substitui a emissão de Nota Fiscal (NFS-e) ou Cupom Fiscal (NFC-e).</span></div>
<p class="obrigado">Obrigado pela preferência!</p>
<div class="tesoura"><span></span>{_tesoura_svg(cor, 28)}<span></span></div>
</div>
<svg viewBox="0 0 600 70" preserveAspectRatio="none" style="display:block;width:100%;height:56px" aria-hidden="true"><path fill="{cor}" d="M0 38c70-26 130-28 200-6s150 30 210 6 130-28 190-8v40H0z"/><path fill="{cor}" opacity="0.55" d="M0 50c90-18 150-14 230 2s170 14 250-8 80-14 120-6v32H0z"/></svg>
</article></body></html>"""


def pdf_comprovante(dados: dict) -> bytes:
    """O PDF usa o mesmo HTML da prévia e da impressão."""
    from weasyprint import HTML

    return HTML(string=html_comprovante(dados)).write_pdf()
