"""O caixa envia o comprovante pelo e-mail e pelo WhatsApp da loja."""
import logging

from django.db.models import Q

from .caixa_service import quantia

logger = logging.getLogger(__name__)


def reais(valor) -> str:
    texto = f"{quantia(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def texto_do_comprovante(dados: dict, loja_nome: str) -> str:
    linhas = [
        loja_nome or "Salão",
        "COMPROVANTE DE PAGAMENTO (NÃO FISCAL)",
        f"Nº {int(dados.get('numero') or 0):06d} · {dados.get('quando') or ''}",
        f"Cliente: {dados.get('cliente') or 'Consumidor'}",
    ]
    for item in dados.get("servicos") or []:
        linhas.append(f"{item.get('nome') or 'Serviço'} — {reais(item.get('total'))}")
        if item.get("profissional"):
            linhas.append(f"Profissional: {item['profissional']}")
    for item in dados.get("itens") or []:
        linhas.append(f"{item.get('quantidade') or 1}× {item.get('nome') or 'Produto'} — {reais(item.get('total'))}")
    if quantia(dados.get("desconto")) > 0:
        linhas.append(f"Desconto: {reais(dados.get('desconto'))}")
    linhas.append(f"Total pago: {reais(dados.get('valor'))}")
    formas = dados.get("formas") or []
    if formas:
        linhas.append("Formas de pagamento:")
        linhas.extend(f"{item.get('nome') or ''}: {reais(item.get('valor'))}" for item in formas)
    else:
        linhas.append(f"Forma de pagamento: {dados.get('forma_label') or ''}")
    linhas.append("Este comprovante não substitui a emissão de Nota Fiscal (NFS-e) ou Cupom Fiscal (NFC-e).")
    return "\n".join(linhas)


def cliente_da_venda(venda):
    from .models import Recebimento

    filtro = Q(venda=venda)
    if getattr(venda, "recebimento_id", None):
        filtro |= Q(pk=venda.recebimento_id)
    recibo = (
        Recebimento.objects.filter(filtro)
        .select_related("agendamento__cliente")
        .order_by("id")
        .first()
    )
    if recibo is None:
        return None
    return recibo.agendamento.cliente


def _nome_da_loja() -> str:
    from tenants.middleware import get_current_loja_id

    loja_id = get_current_loja_id()
    if not loja_id:
        return "Salão"
    from superadmin.models import Loja

    loja = Loja.objects.filter(pk=loja_id).only("nome").first()
    return loja.nome if loja and loja.nome else "Salão"


def enviar_comprovante(venda, canal: str, *, user=None) -> tuple[bool, str]:
    if canal not in {"email", "whatsapp"}:
        return False, "Escolha e-mail ou WhatsApp."
    if venda is None or not getattr(venda, "is_active", False):
        return False, "Comprovante não encontrado."
    from .comprovante_layout import comprovante_da_venda, html_comprovante, pdf_comprovante

    cliente = cliente_da_venda(venda)
    dados = comprovante_da_venda(venda)
    texto = texto_do_comprovante(dados, (dados.get("salao") or {}).get("nome") or _nome_da_loja())
    if canal == "email":
        return _enviar_email(cliente, venda, texto, html_comprovante(dados))
    return _enviar_whatsapp(cliente, texto, pdf_comprovante(dados), user=user)


def _enviar_email(cliente, venda, texto: str, corpo_html: str) -> tuple[bool, str]:
    email = (getattr(cliente, "email", "") or "").strip()
    if not email:
        return False, "O cliente está sem e-mail."
    numero = int(getattr(venda, "numero", 0) or 0)
    assunto = f"Comprovante {numero:06d}"
    try:
        from core.email_delivery import send_system_mail

        send_system_mail(assunto, texto, [email], html_message=corpo_html)
    except Exception:
        logger.exception("E-mail do comprovante %s não saiu", numero)
        return False, "Não foi possível enviar o e-mail."
    return True, "Recibo enviado por e-mail."


def _enviar_whatsapp(cliente, texto: str, pdf: bytes, *, user=None) -> tuple[bool, str]:
    from tenants.middleware import get_current_loja_id

    from .comunicacao_service import whatsapp_pronto

    telefone = (getattr(cliente, "telefone", "") or "").strip()
    if not telefone:
        return False, "O cliente está sem telefone."
    loja_id = get_current_loja_id()
    if not whatsapp_pronto(loja_id):
        return False, "O WhatsApp desta loja não está conectado."
    from whatsapp.models import WhatsAppConfig
    from whatsapp.services import send_whatsapp, send_whatsapp_document

    config = WhatsAppConfig.objects.filter(loja_id=loja_id).first()
    numero = "comprovante.pdf"
    try:
        from .recibo_publico import publicar_pdf

        ok, erro = send_whatsapp_document(
            telefone,
            publicar_pdf(pdf),
            numero,
            caption="Comprovante de pagamento (não fiscal)",
            user=user,
            config=config,
        )
        if not ok:
            ok, erro = send_whatsapp(telefone, texto, user=user, config=config)
    except Exception:
        logger.exception("WhatsApp do comprovante não saiu")
        return False, "Não foi possível enviar o WhatsApp."
    if not ok:
        return False, erro or "Não foi possível enviar o WhatsApp."
    return True, "Recibo enviado pelo WhatsApp."
