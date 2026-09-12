"""Pedidos de compra — não dão entrada no estoque."""
from __future__ import annotations

import hashlib
import logging
import time
from decimal import Decimal, InvalidOperation
from django.conf import settings
from django.core.cache import cache as django_cache
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from core.assinatura_service import _build_link_assinatura, decodificar_token, gerar_token, normalizar_token_url

from .models.fornecedores import (
    Fornecedor,
    FornecedorProduto,
    PedidoCompra,
    PedidoCompraAssinatura,
    PedidoCompraItem,
)

logger = logging.getLogger(__name__)


class PedidoCompraError(Exception):
    """Erro de validação do pedido de compra."""


def _decimal(raw, default="0") -> Decimal:
    s = str(raw if raw not in (None, "") else default).strip().replace("R$", "").replace(" ", "")
    if not s:
        s = str(default)
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        val = Decimal(s)
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise PedidoCompraError("Valor numérico inválido.") from exc
    return val.quantize(Decimal("0.01"))


def _brl(valor) -> str:
    return f"R$ {Decimal(str(valor or 0)):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _dados_loja(loja_id: int) -> dict:
    from superadmin.models import Loja

    loja = Loja.objects.using("default").filter(id=loja_id).first()
    if not loja:
        return {"nome": "Clínica", "cnpj": "", "logo": "", "endereco": "", "telefone": "", "email": ""}
    partes = []
    if loja.logradouro:
        linha = loja.logradouro
        if loja.numero:
            linha += f", {loja.numero}"
        if loja.bairro:
            linha += f" — {loja.bairro}"
        partes.append(linha)
    if loja.cidade and loja.uf:
        partes.append(f"{loja.cidade}/{loja.uf}")
    elif loja.cidade or loja.uf:
        partes.append(loja.cidade or loja.uf)
    if loja.cep:
        partes.append(f"CEP {loja.cep}")
    return {
        "nome": loja.nome or "Clínica",
        "cnpj": loja.cpf_cnpj or "",
        "logo": (loja.logo or "").strip() or (getattr(loja, "login_logo", "") or "").strip(),
        "endereco": " · ".join(partes),
        "telefone": (loja.telefone_contato or loja.owner_telefone or "").strip(),
        "email": (loja.email_contato or "").strip(),
    }


def _ip_request(request) -> str:
    forwarded = (getattr(request, "META", {}) or {}).get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()[:45]
    return (getattr(request, "META", {}) or {}).get("REMOTE_ADDR", "0.0.0.0") or "0.0.0.0"


def _dados_profissional(prof) -> dict:
    nome = (getattr(prof, "nome", "") or "").strip()
    conselho = ""
    if hasattr(prof, "formatar_conselho"):
        conselho = (prof.formatar_conselho() or "").strip()
    cpf = (getattr(prof, "cpf", "") or "").strip()
    return {
        "id": prof.id,
        "nome": nome,
        "conselho": conselho,
        "cpf": cpf,
        "email": (getattr(prof, "email", "") or "").strip(),
        "telefone": (getattr(prof, "telefone", "") or "").strip(),
        "especialidade": (getattr(prof, "especialidade", "") or "").strip(),
        "registro_profissional": (getattr(prof, "registro_profissional", "") or "").strip(),
    }


def listar_profissionais_assinantes(loja_id: int) -> list[dict]:
    """Profissionais ativos da clínica para assinar o pedido."""
    from .models import Professional

    qs = Professional.objects.filter(loja_id=loja_id, is_active=True).order_by("nome")
    return [_dados_profissional(p) for p in qs if (p.nome or "").strip()]


def proximo_numero(loja_id: int) -> int:
    atual = PedidoCompra.objects.filter(loja_id=loja_id).aggregate(m=Max("numero")).get("m") or 0
    return int(atual) + 1


def _recalcular_total(pedido: PedidoCompra) -> None:
    total = Decimal("0.00")
    for item in pedido.itens.all():
        total += item.quantidade * item.preco
    pedido.valor_total = total.quantize(Decimal("0.01"))
    pedido.save(update_fields=["valor_total", "updated_at"])


def _montar_itens(fornecedor: Fornecedor, itens_raw) -> list[dict]:
    if not itens_raw:
        raise PedidoCompraError("Inclua ao menos um item no pedido.")
    montados: list[dict] = []
    for raw in itens_raw:
        if not isinstance(raw, dict):
            raise PedidoCompraError("Item inválido.")
        codigo = str(raw.get("codigo") or "").strip()
        nome = str(raw.get("nome") or "").strip()
        catalogo = None
        catalogo_id = raw.get("catalogo_id") or raw.get("catalogo")
        if catalogo_id:
            catalogo = FornecedorProduto.objects.filter(
                pk=catalogo_id, fornecedor=fornecedor,
            ).first()
            if catalogo:
                codigo = codigo or catalogo.codigo
                nome = nome or catalogo.nome
        if not codigo or not nome:
            raise PedidoCompraError("Cada item precisa de código e nome.")
        qtd = _decimal(raw.get("quantidade"), "1")
        if qtd <= 0:
            raise PedidoCompraError("Quantidade deve ser maior que zero.")
        preco_raw = raw.get("preco")
        if preco_raw in (None, "") and catalogo:
            preco_raw = catalogo.preco_ref
        preco = _decimal(preco_raw, "0")
        unidade = str(raw.get("unidade") or (catalogo.unidade if catalogo else "un") or "un").strip()[:20]
        montados.append({
            "catalogo": catalogo,
            "codigo": codigo[:60],
            "nome": nome[:200],
            "unidade": unidade or "un",
            "quantidade": qtd,
            "preco": preco,
        })
    return montados


def _substituir_itens(pedido: PedidoCompra, itens: list[dict]) -> None:
    pedido.itens.all().delete()
    PedidoCompraItem.objects.bulk_create([
        PedidoCompraItem(pedido=pedido, **item) for item in itens
    ])
    _recalcular_total(pedido)


def _resolver_fornecedor(loja_id: int, data: dict) -> Fornecedor:
    pk = data.get("fornecedor_id") or data.get("fornecedor")
    forn = Fornecedor.objects.filter(pk=pk, loja_id=loja_id).first()
    if not forn:
        raise PedidoCompraError("Fornecedor não encontrado.")
    return forn


def criar_pedido(loja_id: int, data: dict) -> PedidoCompra:
    forn = _resolver_fornecedor(loja_id, data)
    itens = _montar_itens(forn, data.get("itens") or [])
    with transaction.atomic():
        pedido = PedidoCompra.objects.create(
            loja_id=loja_id,
            numero=proximo_numero(loja_id),
            fornecedor=forn,
            observacoes=str(data.get("observacoes") or "").strip(),
            status=PedidoCompra.STATUS_RASCUNHO,
        )
        _substituir_itens(pedido, itens)
    return pedido


def atualizar_pedido(pedido: PedidoCompra, data: dict) -> PedidoCompra:
    if pedido.status != PedidoCompra.STATUS_RASCUNHO:
        raise PedidoCompraError("Só é possível editar pedido em rascunho.")
    if "fornecedor_id" in data or "fornecedor" in data:
        pedido.fornecedor = _resolver_fornecedor(pedido.loja_id, data)
    if "observacoes" in data:
        pedido.observacoes = str(data.get("observacoes") or "").strip()
        pedido.save(update_fields=["fornecedor", "observacoes", "updated_at"])
    if "itens" in data:
        itens = _montar_itens(pedido.fornecedor, data.get("itens") or [])
        _substituir_itens(pedido, itens)
    return pedido


def cancelar_pedido(pedido: PedidoCompra) -> PedidoCompra:
    if pedido.status in (PedidoCompra.STATUS_ASSINADO, PedidoCompra.STATUS_ENVIADO):
        raise PedidoCompraError("Pedido já assinado não pode ser cancelado.")
    if pedido.status == PedidoCompra.STATUS_CANCELADO:
        return pedido
    pedido.status = PedidoCompra.STATUS_CANCELADO
    pedido.save(update_fields=["status", "updated_at"])
    return pedido


def excluir_pedido(pedido: PedidoCompra) -> None:
    """Remove o pedido e itens/assinaturas (CASCADE). Não altera estoque."""
    pedido.delete()


def _assinatura(pedido: PedidoCompra, tipo: str) -> PedidoCompraAssinatura | None:
    return pedido.assinaturas.filter(tipo=tipo).first()


def clinica_assinou(pedido: PedidoCompra) -> bool:
    ass = _assinatura(pedido, PedidoCompraAssinatura.TIPO_CLINICA)
    return bool(ass and ass.assinado)


def fornecedor_assinou(pedido: PedidoCompra) -> bool:
    ass = _assinatura(pedido, PedidoCompraAssinatura.TIPO_FORNECEDOR)
    return bool(ass and ass.assinado)


def ambas_assinaturas(pedido: PedidoCompra) -> bool:
    return clinica_assinou(pedido) and fornecedor_assinou(pedido)


def garantir_assinatura_fornecedor(pedido: PedidoCompra) -> PedidoCompraAssinatura:
    ass = _assinatura(pedido, PedidoCompraAssinatura.TIPO_FORNECEDOR)
    if ass and ass.token:
        return ass
    token = gerar_token(
        "pedidocompra",
        pedido.id,
        PedidoCompraAssinatura.TIPO_FORNECEDOR,
        pedido.loja_id,
        modulo="clinica_beleza",
        expiracao_dias=14,
    )
    if ass:
        ass.token = token
        ass.nome_assinante = ass.nome_assinante or pedido.fornecedor.razao_social
        ass.email_assinante = ass.email_assinante or (pedido.fornecedor.email or "")
        ass.save(update_fields=["token", "nome_assinante", "email_assinante", "updated_at"])
        return ass
    return PedidoCompraAssinatura.objects.create(
        loja_id=pedido.loja_id,
        pedido=pedido,
        tipo=PedidoCompraAssinatura.TIPO_FORNECEDOR,
        nome_assinante=pedido.fornecedor.razao_social,
        email_assinante=pedido.fornecedor.email or "",
        token=token,
    )


def link_assinatura_fornecedor(pedido: PedidoCompra) -> str:
    ass = garantir_assinatura_fornecedor(pedido)
    return _build_link_assinatura(ass.token, "/assinar-pedido/")


def assinar_clinica(
    pedido: PedidoCompra,
    nome: str,
    ip: str,
    profissional_id=None,
) -> PedidoCompraAssinatura:
    if pedido.status == PedidoCompra.STATUS_CANCELADO:
        raise PedidoCompraError("Pedido cancelado.")
    if not pedido.itens.exists():
        raise PedidoCompraError("Pedido sem itens.")
    prof = None
    if profissional_id:
        from .models import Professional
        prof = Professional.objects.filter(
            pk=profissional_id, loja_id=pedido.loja_id, is_active=True,
        ).first()
        if not prof:
            raise PedidoCompraError("Profissional não encontrado no cadastro da clínica.")
        dados = _dados_profissional(prof)
        nome = dados["nome"]
        conselho = dados["conselho"]
        cpf = dados["cpf"]
        email_prof = dados["email"]
    else:
        nome = (nome or "").strip()
        conselho = ""
        cpf = ""
        email_prof = ""
    if not nome:
        raise PedidoCompraError("Selecione o profissional que assina pela clínica.")
    ass = _assinatura(pedido, PedidoCompraAssinatura.TIPO_CLINICA)
    if ass and ass.assinado:
        raise PedidoCompraError("A clínica já assinou este pedido.")
    if not ass:
        ass = PedidoCompraAssinatura.objects.create(
            loja_id=pedido.loja_id,
            pedido=pedido,
            tipo=PedidoCompraAssinatura.TIPO_CLINICA,
        )
    ass.profissional = prof
    ass.nome_assinante = nome[:200]
    ass.conselho_display = (conselho or "")[:80]
    ass.cpf_assinante = (cpf or "")[:14]
    ass.email_assinante = (email_prof or "")[:254]
    ass.ip_address = ip or "0.0.0.0"
    ass.assinado = True
    ass.assinado_em = timezone.now()
    ass.save()
    finalizar_se_completo(pedido)
    return ass


def finalizar_se_completo(pedido: PedidoCompra) -> bool:
    if not clinica_assinou(pedido):
        return False
    from .media_docs_service import salvar_pdf_loja
    from .pedido_compra_pdf import gerar_pdf_pedido_compra

    pdf_bytes = gerar_pdf_pedido_compra(pedido)
    url = salvar_pdf_loja(pedido.loja_id, pdf_bytes, f"pedido_compra_{pedido.numero}.pdf")
    pedido.pdf_url = url or pedido.pdf_url or ""
    if pedido.status not in (PedidoCompra.STATUS_ENVIADO, PedidoCompra.STATUS_CANCELADO):
        pedido.status = PedidoCompra.STATUS_ASSINADO
    pedido.save(update_fields=["pdf_url", "status", "updated_at"])
    return True


def buscar_assinatura_fornecedor_por_token(token: str) -> PedidoCompraAssinatura | None:
    token = normalizar_token_url(token)
    if not token:
        return None
    ass = PedidoCompraAssinatura.objects.select_related("pedido", "pedido__fornecedor").filter(
        token=token, tipo=PedidoCompraAssinatura.TIPO_FORNECEDOR,
    ).first()
    if ass:
        return ass
    payload = decodificar_token(token)
    if not payload or payload.get("doc_type") != "pedidocompra":
        return None
    doc_id = payload.get("doc_id")
    if not doc_id:
        return None
    return PedidoCompraAssinatura.objects.select_related("pedido", "pedido__fornecedor").filter(
        pedido_id=doc_id,
        tipo=PedidoCompraAssinatura.TIPO_FORNECEDOR,
        assinado=False,
    ).order_by("-id").first()


def assinar_fornecedor(token: str, nome: str, ip: str) -> PedidoCompra:
    ass = buscar_assinatura_fornecedor_por_token(token)
    if not ass:
        raise PedidoCompraError("Link inválido ou expirado.")
    if ass.assinado:
        raise PedidoCompraError("Este pedido já foi assinado pelo fornecedor.")
    pedido = ass.pedido
    if pedido.status == PedidoCompra.STATUS_CANCELADO:
        raise PedidoCompraError("Este pedido foi cancelado.")
    if not clinica_assinou(pedido):
        raise PedidoCompraError("A clínica ainda não assinou este pedido.")
    nome = (nome or "").strip()
    if not nome:
        raise PedidoCompraError("Informe o nome de quem assina.")
    ass.nome_assinante = nome[:200]
    ass.ip_address = ip or "0.0.0.0"
    ass.assinado = True
    ass.assinado_em = timezone.now()
    ass.save()
    finalizar_se_completo(pedido)
    pedido.refresh_from_db()
    return pedido


def _loja_nome(loja_id: int) -> str:
    from superadmin.models import Loja
    loja = Loja.objects.using("default").filter(id=loja_id).first()
    return (loja.nome if loja else "") or "Clínica"


def enviar_link_fornecedor(pedido: PedidoCompra, canais: list[str]) -> dict:
    if pedido.status == PedidoCompra.STATUS_CANCELADO:
        raise PedidoCompraError("Pedido cancelado.")
    if not clinica_assinou(pedido):
        raise PedidoCompraError("A clínica precisa assinar antes de enviar o link ao fornecedor.")
    if fornecedor_assinou(pedido):
        raise PedidoCompraError("O fornecedor já assinou este pedido.")
    canais = [c for c in (canais or []) if c in ("email", "whatsapp")]
    if not canais:
        raise PedidoCompraError("Informe o canal: email ou whatsapp.")
    link = link_assinatura_fornecedor(pedido)
    forn = pedido.fornecedor
    clinica = _loja_nome(pedido.loja_id)
    resultado: dict = {}
    if "email" in canais:
        resultado["email"] = _enviar_link_email(pedido, forn, link, clinica)
    if "whatsapp" in canais:
        resultado["whatsapp"] = _enviar_link_whatsapp(pedido, forn, link, clinica)
    if pedido.status == PedidoCompra.STATUS_RASCUNHO:
        pedido.status = PedidoCompra.STATUS_AGUARDANDO_FORNECEDOR
        pedido.save(update_fields=["status", "updated_at"])
    return resultado


def _enviar_link_email(pedido, forn, link: str, clinica: str) -> dict:
    email = (forn.email or "").strip()
    if not email:
        return {"sucesso": False, "erro": "Fornecedor sem e-mail cadastrado."}
    try:
        from core.assinatura_service import _render_email_html
        from core.email_delivery import create_email_multipart, send_prepared

        total = _brl(pedido.valor_total)
        qtd_itens = pedido.itens.count()
        corpo_txt = (
            f"Olá {forn.razao_social},\n\n"
            f"{clinica} enviou o pedido de compra nº {pedido.numero} "
            f"({qtd_itens} {'item' if qtd_itens == 1 else 'itens'}, total {total}) "
            f"para conferência e assinatura.\n\n"
            f"Abra o link para visualizar o PDF e assinar:\n{link}\n\n"
            f"Atenciosamente,\n{clinica}"
        )
        corpo_html = f"""
<p style="color:#333;font-size:16px;line-height:1.6;margin:0 0 16px;">Olá <strong>{forn.razao_social}</strong>,</p>
<p style="color:#555;font-size:15px;line-height:1.6;margin:0 0 24px;">
<strong>{clinica}</strong> enviou o pedido de compra nº <strong>{pedido.numero}</strong> para você conferir e assinar.
</p>
<table width="100%" style="background:#f8f9fa;border-left:4px solid #8B3D52;border-radius:4px;margin-bottom:24px;"><tr><td style="padding:20px;">
<p style="margin:0 0 8px;color:#666;font-size:13px;">Pedido</p>
<p style="margin:0 0 12px;color:#333;font-size:18px;font-weight:700;">nº {pedido.numero}</p>
<p style="margin:0 0 4px;color:#666;font-size:13px;">{qtd_itens} {"item" if qtd_itens == 1 else "itens"}</p>
<p style="margin:0;color:#8B3D52;font-size:20px;font-weight:700;">{total}</p>
</td></tr></table>
<table width="100%" style="margin-bottom:24px;"><tr><td align="center">
<a href="{link}" style="display:inline-block;background:#8B3D52;color:#ffffff !important;text-decoration:none;padding:14px 32px;border-radius:8px;font-size:16px;font-weight:600;">Visualizar PDF e assinar</a>
</td></tr></table>
<p style="color:#888;font-size:13px;margin:0;">O PDF do pedido segue em anexo. O link acima registra a assinatura digital do fornecedor.</p>
"""
        html = _render_email_html("Pedido de compra", "#8B3D52 0%, #6B2E3F 100%", corpo_html, clinica)
        msg = create_email_multipart(
            subject=f"Pedido de compra nº {pedido.numero} — {clinica}",
            body=corpo_txt,
            to=[email],
            html=html,
        )
        try:
            msg.attach(f"pedido_compra_{pedido.numero}.pdf", pdf_bytes_pedido(pedido), "application/pdf")
        except Exception as pdf_exc:
            logger.warning("Anexo PDF do link pedido #%s: %s", pedido.numero, pdf_exc)
        send_prepared(msg, fail_silently=False)
        return {"sucesso": True}
    except Exception as exc:
        logger.warning("Falha e-mail link pedido #%s: %s", pedido.numero, exc)
        return {"sucesso": False, "erro": str(exc)}


def _enviar_link_whatsapp(pedido, forn, link: str, clinica: str) -> dict:
    telefone = (forn.telefone or "").strip()
    if not telefone:
        return {"sucesso": False, "erro": "Fornecedor sem telefone cadastrado."}
    try:
        from whatsapp.models import WhatsAppConfig
        from whatsapp.services import send_whatsapp

        config = WhatsAppConfig.objects.filter(loja_id=pedido.loja_id).first()
        if not config or not getattr(config, "whatsapp_ativo", False):
            return {"sucesso": False, "erro": "WhatsApp não está ativo. Configure em Configurações → WhatsApp."}
        mensagem = (
            f"{clinica} enviou o pedido de compra nº {pedido.numero} para assinatura.\n\n"
            f"Abra o link para visualizar o PDF e assinar:\n{link}"
        )
        ok, err = send_whatsapp(telefone=telefone, mensagem=mensagem, config=config)
        if not ok:
            return {"sucesso": False, "erro": err or "Erro ao enviar WhatsApp."}
        return {"sucesso": True}
    except Exception as exc:
        logger.warning("Falha WhatsApp link pedido #%s: %s", pedido.numero, exc)
        return {"sucesso": False, "erro": str(exc)}


def pdf_bytes_pedido(pedido: PedidoCompra) -> bytes:
    from .pedido_compra_pdf import gerar_pdf_pedido_compra
    return gerar_pdf_pedido_compra(pedido)


def enviar_pedido_assinado(pedido: PedidoCompra, canais: list[str]) -> dict:
    if pedido.status == PedidoCompra.STATUS_CANCELADO:
        raise PedidoCompraError("Pedido cancelado.")
    if pedido.status == PedidoCompra.STATUS_RASCUNHO or not clinica_assinou(pedido):
        raise PedidoCompraError("Assine o pedido pela clínica antes de enviar ao fornecedor.")
    canais = [c for c in (canais or []) if c in ("email", "whatsapp")]
    if not canais:
        raise PedidoCompraError("Informe o canal: email ou whatsapp.")
    pdf = pdf_bytes_pedido(pedido)
    finalizar_se_completo(pedido)
    resultado: dict = {}
    if "email" in canais:
        resultado["email"] = _enviar_pdf_email(pedido, pdf)
    if "whatsapp" in canais:
        resultado["whatsapp"] = _enviar_pdf_whatsapp(pedido, pdf)
    if any(r.get("sucesso") for r in resultado.values()):
        pedido.status = PedidoCompra.STATUS_ENVIADO
        pedido.save(update_fields=["status", "updated_at"])
    return resultado


def _enviar_pdf_email(pedido: PedidoCompra, pdf_bytes: bytes) -> dict:
    email = (pedido.fornecedor.email or "").strip()
    if not email:
        return {"sucesso": False, "erro": "Fornecedor sem e-mail cadastrado."}
    try:
        from core.email_delivery import create_email_message, send_prepared

        clinica = _loja_nome(pedido.loja_id)
        corpo = (
            f"Olá {pedido.fornecedor.razao_social},\n\n"
            f"Segue em anexo o pedido de compra nº {pedido.numero} assinado.\n\n"
            f"Atenciosamente,\n{clinica}"
        )
        msg = create_email_message(
            subject=f"Pedido de compra nº {pedido.numero} assinado — {clinica}",
            body=corpo,
            to=[email],
        )
        msg.attach(f"pedido_compra_{pedido.numero}.pdf", pdf_bytes, "application/pdf")
        send_prepared(msg, fail_silently=False)
        return {"sucesso": True}
    except Exception as exc:
        logger.warning("Falha e-mail PDF pedido #%s: %s", pedido.numero, exc)
        return {"sucesso": False, "erro": str(exc)}


def _enviar_pdf_whatsapp(pedido: PedidoCompra, pdf_bytes: bytes) -> dict:
    telefone = (pedido.fornecedor.telefone or "").strip()
    if not telefone:
        return {"sucesso": False, "erro": "Fornecedor sem telefone cadastrado."}
    try:
        from whatsapp.models import WhatsAppConfig
        from whatsapp.services import _send_whatsapp_document_evolution, send_whatsapp

        config = WhatsAppConfig.objects.filter(loja_id=pedido.loja_id).first()
        if not config or not getattr(config, "whatsapp_ativo", False):
            return {"sucesso": False, "erro": "WhatsApp não está ativo. Configure em Configurações → WhatsApp."}
        clinica = _loja_nome(pedido.loja_id)
        mensagem = f"{clinica} enviou o pedido de compra nº {pedido.numero} assinado."
        ok, err = send_whatsapp(telefone=telefone, mensagem=mensagem, config=config)
        if not ok:
            return {"sucesso": False, "erro": err or "Erro ao enviar WhatsApp."}
        token = hashlib.sha256(
            f"pedido-{pedido.id}-{int(time.time())}-{settings.SECRET_KEY[:16]}".encode()
        ).hexdigest()[:32]
        django_cache.set(f"pedido_compra_pdf_{token}", {"pedido_id": pedido.id, "pdf": pdf_bytes}, 300)
        api_base = getattr(settings, "API_BASE_URL", "") or "https://api.lwksistemas.com.br"
        pdf_url = f"{api_base}/api/clinica-beleza/estoque/pedidos/{pedido.id}/pdf-public/{token}/"
        try:
            _send_whatsapp_document_evolution(
                telefone, pdf_url, f"pedido_compra_{pedido.numero}.pdf",
                caption=f"Pedido de compra nº {pedido.numero}", config=config,
            )
        except Exception as pdf_err:
            logger.warning("PDF pedido via WhatsApp falhou (texto já enviado): %s", pdf_err)
        return {"sucesso": True}
    except Exception as exc:
        logger.warning("Falha WhatsApp PDF pedido #%s: %s", pedido.numero, exc)
        return {"sucesso": False, "erro": str(exc)}


def pdf_publico_cache(pedido_id: int, token: str) -> bytes | None:
    cached = django_cache.get(f"pedido_compra_pdf_{token}") or {}
    if cached.get("pedido_id") != pedido_id:
        return None
    return cached.get("pdf")


def serializar_pedido(pedido: PedidoCompra) -> dict:
    ass_cli = _assinatura(pedido, PedidoCompraAssinatura.TIPO_CLINICA)
    ass_forn = _assinatura(pedido, PedidoCompraAssinatura.TIPO_FORNECEDOR)
    return {
        "id": pedido.id,
        "numero": pedido.numero,
        "status": pedido.status,
        "status_display": pedido.get_status_display(),
        "observacoes": pedido.observacoes,
        "pdf_url": pedido.pdf_url,
        "valor_total": str(pedido.valor_total),
        "valor_total_display": _brl(pedido.valor_total),
        "loja": _dados_loja(pedido.loja_id),
        "created_at": pedido.created_at.isoformat() if pedido.created_at else None,
        "fornecedor": {
            "id": pedido.fornecedor_id,
            "cnpj": pedido.fornecedor.cnpj,
            "razao_social": pedido.fornecedor.razao_social,
            "nome_fantasia": pedido.fornecedor.nome_fantasia,
            "email": pedido.fornecedor.email,
            "telefone": pedido.fornecedor.telefone,
        },
        "itens": [
            {
                "id": item.id,
                "catalogo_id": item.catalogo_id,
                "codigo": item.codigo,
                "nome": item.nome,
                "unidade": item.unidade,
                "quantidade": str(item.quantidade),
                "preco": str(item.preco),
                "subtotal": str(item.subtotal),
            }
            for item in pedido.itens.all()
        ],
        "assinaturas": {
            "clinica": {
                "assinado": bool(ass_cli and ass_cli.assinado),
                "nome": (ass_cli.nome_assinante if ass_cli else "") or "",
                "conselho": (ass_cli.conselho_display if ass_cli else "") or "",
                "cpf": (ass_cli.cpf_assinante if ass_cli else "") or "",
                "profissional_id": ass_cli.profissional_id if ass_cli else None,
                "em": ass_cli.assinado_em.isoformat() if ass_cli and ass_cli.assinado_em else None,
            },
            "fornecedor": {
                "assinado": bool(ass_forn and ass_forn.assinado),
                "nome": (ass_forn.nome_assinante if ass_forn else "") or "",
                "em": ass_forn.assinado_em.isoformat() if ass_forn and ass_forn.assinado_em else None,
            },
        },
        "pode_enviar_pdf": bool(
            clinica_assinou(pedido) and pedido.status != PedidoCompra.STATUS_CANCELADO
        ),
    }
