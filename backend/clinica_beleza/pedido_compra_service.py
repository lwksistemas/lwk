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

from .models.fornecedores import (
    Fornecedor,
    FornecedorProduto,
    PedidoCompra,
    PedidoCompraAssinatura,
    PedidoCompraItem,
    PedidoCompraPaciente,
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


def _fmt_numero(numero) -> str:
    try:
        return f"{int(numero):02d}"
    except (TypeError, ValueError):
        return str(numero)


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


def _cpf_digits(raw) -> str:
    return "".join(c for c in str(raw or "") if c.isdigit())


def _normalizar_cpf(raw) -> str:
    from core.validators import formatar_cpf

    digits = _cpf_digits(raw)
    if len(digits) == 11:
        return formatar_cpf(digits)
    return str(raw or "").strip()[:14]


def buscar_pacientes_pedido(loja_id: int, termo: str) -> list[dict]:
    from .models import Patient
    from .patient_search import apply_patient_search

    qs = Patient.objects.filter(loja_id=loja_id, is_active=True).order_by("nome")
    qs = apply_patient_search(qs, termo)[:12]
    return [{"id": p.id, "nome": p.nome, "cpf": p.cpf or ""} for p in qs]


def _montar_pacientes(loja_id: int, raws) -> list[dict]:
    if raws in (None, ""):
        return []
    if not isinstance(raws, list):
        raise PedidoCompraError("Lista de pacientes inválida.")
    from .models import Patient

    montados: list[dict] = []
    vistos_id: set[int] = set()
    vistos_cpf: set[str] = set()
    for raw in raws:
        if not isinstance(raw, dict):
            raise PedidoCompraError("Paciente inválido.")
        patient = None
        patient_id = raw.get("patient_id") or raw.get("paciente_id")
        if patient_id:
            patient = Patient.objects.filter(pk=patient_id, loja_id=loja_id).first()
            if not patient:
                raise PedidoCompraError("Paciente não encontrado no cadastro.")
            if patient.id in vistos_id:
                continue
            vistos_id.add(patient.id)
        nome = str(raw.get("nome") or (patient.nome if patient else "")).strip()
        cpf = _normalizar_cpf(raw.get("cpf") if raw.get("cpf") not in (None, "") else (patient.cpf if patient else ""))
        if not nome:
            if not patient:
                continue
            raise PedidoCompraError("Informe o nome do paciente.")
        cpf_key = _cpf_digits(cpf)
        if cpf_key:
            if cpf_key in vistos_cpf:
                continue
            vistos_cpf.add(cpf_key)
        montados.append({
            "patient": patient,
            "nome": nome[:200],
            "cpf": cpf,
        })
    return montados


def _substituir_pacientes(pedido: PedidoCompra, pacientes: list[dict]) -> None:
    pedido.pacientes.all().delete()
    if not pacientes:
        return
    PedidoCompraPaciente.objects.bulk_create([
        PedidoCompraPaciente(pedido=pedido, **item) for item in pacientes
    ])


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
        _substituir_pacientes(pedido, _montar_pacientes(loja_id, data.get("pacientes") or []))
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
    if "pacientes" in data:
        _substituir_pacientes(pedido, _montar_pacientes(pedido.loja_id, data.get("pacientes")))
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


def _loja_nome(loja_id: int) -> str:
    from superadmin.models import Loja
    loja = Loja.objects.using("default").filter(id=loja_id).first()
    return (loja.nome if loja else "") or "Clínica"


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
        from core.assinatura_service import _render_email_html
        from core.email_delivery import create_email_multipart, send_prepared

        clinica = _loja_nome(pedido.loja_id)
        forn = pedido.fornecedor
        numero = _fmt_numero(pedido.numero)
        total = _brl(pedido.valor_total)
        qtd_itens = pedido.itens.count()
        destinatario = (forn.nome_fantasia or forn.razao_social or "fornecedor").strip()
        corpo_txt = (
            f"Prezado(a) {destinatario},\n\n"
            f"Encaminhamos o pedido de compra nº {numero} da {clinica}, "
            f"já assinado pelo profissional responsável, para processamento.\n\n"
            f"Itens: {qtd_itens}\n"
            f"Valor total: {total}\n\n"
            f"O PDF oficial segue em anexo.\n\n"
            f"Atenciosamente,\n{clinica}"
        )
        corpo_html = f"""
<p style="color:#333;font-size:16px;line-height:1.6;margin:0 0 16px;">Prezado(a) <strong>{destinatario}</strong>,</p>
<p style="color:#555;font-size:15px;line-height:1.6;margin:0 0 24px;">
A <strong>{clinica}</strong> encaminha o pedido de compra nº <strong>{numero}</strong>,
já assinado pelo profissional responsável, para processamento junto à sua empresa.
</p>
<table width="100%" style="background:#f8f9fa;border-left:4px solid #8B3D52;border-radius:4px;margin-bottom:24px;"><tr><td style="padding:20px;">
<p style="margin:0 0 8px;color:#666;font-size:13px;">Pedido de compra</p>
<p style="margin:0 0 12px;color:#333;font-size:22px;font-weight:700;">nº {numero}</p>
<p style="margin:0 0 4px;color:#666;font-size:13px;">{qtd_itens} {"item" if qtd_itens == 1 else "itens"}</p>
<p style="margin:0;color:#8B3D52;font-size:20px;font-weight:700;">{total}</p>
</td></tr></table>
<p style="color:#555;font-size:14px;line-height:1.6;margin:0 0 8px;">O documento oficial em PDF segue em anexo.</p>
<p style="color:#888;font-size:13px;margin:0;">Em caso de dúvidas, responda a este e-mail ou entre em contato com a clínica.</p>
"""
        html = _render_email_html("Pedido de compra", "#8B3D52 0%, #6B2E3F 100%", corpo_html, clinica)
        msg = create_email_multipart(
            subject=f"Pedido de compra nº {numero} — {clinica}",
            body=corpo_txt,
            to=[email],
            html=html,
        )
        msg.attach(f"pedido_compra_{numero}.pdf", pdf_bytes, "application/pdf")
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
        numero = _fmt_numero(pedido.numero)
        mensagem = (
            f"{clinica} encaminha o pedido de compra nº {numero}, "
            f"assinado pelo profissional responsável. O PDF segue em anexo."
        )
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
                telefone, pdf_url, f"pedido_compra_{numero}.pdf",
                caption=f"Pedido de compra nº {numero} — {clinica}", config=config,
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
        "pacientes": [
            {
                "id": row.id,
                "patient_id": row.patient_id,
                "nome": row.nome,
                "cpf": row.cpf,
            }
            for row in pedido.pacientes.all()
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
        },
        "pode_enviar_pdf": bool(
            clinica_assinou(pedido) and pedido.status != PedidoCompra.STATUS_CANCELADO
        ),
    }
