"""CRUD e workflow de pedido de compra — não dá entrada no estoque."""
from __future__ import annotations

from decimal import Decimal

from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from clinica_beleza.models.fornecedores import (
    Fornecedor,
    FornecedorProduto,
    PedidoCompra,
    PedidoCompraAssinatura,
    PedidoCompraItem,
    PedidoCompraPaciente,
)
from clinica_beleza.pedido_compra.context import _dados_loja, _dados_profissional
from clinica_beleza.pedido_compra.errors import PedidoCompraError
from clinica_beleza.pedido_compra.formatters import _brl, _decimal, nome_arquivo_pdf_pedido


def _garantir_produto_catalogo(fornecedor: Fornecedor, *, codigo: str, nome: str, unidade: str, preco: Decimal):
    """Grava no catálogo o item digitado no pedido, se o código ainda não existir."""
    codigo = (codigo or "").strip()[:60]
    nome = (nome or "").strip()[:200]
    if not codigo or not nome:
        return None
    existente = FornecedorProduto.objects.filter(fornecedor=fornecedor, codigo=codigo).first()
    if existente:
        campos = []
        if preco > 0 and (existente.preco_ref or Decimal("0")) <= 0:
            existente.preco_ref = preco
            campos.append("preco_ref")
        if nome and not (existente.nome or "").strip():
            existente.nome = nome
            campos.append("nome")
        if campos:
            campos.append("updated_at")
            existente.save(update_fields=campos)
        return existente
    return FornecedorProduto.objects.create(
        fornecedor=fornecedor,
        loja_id=fornecedor.loja_id,
        codigo=codigo,
        nome=nome,
        unidade=(unidade or "un")[:20] or "un",
        preco_ref=preco,
    )

def listar_profissionais_assinantes(loja_id: int) -> list[dict]:
    """Profissionais ativos da clínica para assinar o pedido."""
    from clinica_beleza.models import Professional

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
        if not catalogo:
            catalogo = _garantir_produto_catalogo(
                fornecedor, codigo=codigo, nome=nome, unidade=unidade, preco=preco,
            )
        elif preco > 0 and (catalogo.preco_ref or Decimal("0")) <= 0:
            catalogo.preco_ref = preco
            catalogo.save(update_fields=["preco_ref", "updated_at"])
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
    from clinica_beleza.models import Patient
    from clinica_beleza.patient_search import apply_patient_search

    qs = Patient.objects.filter(loja_id=loja_id, is_active=True).order_by("nome")
    qs = apply_patient_search(qs, termo)[:12]
    return [{"id": p.id, "nome": p.nome, "cpf": p.cpf or ""} for p in qs]


def _montar_pacientes(loja_id: int, raws) -> list[dict]:
    if raws in (None, ""):
        return []
    if not isinstance(raws, list):
        raise PedidoCompraError("Lista de pacientes inválida.")
    from clinica_beleza.models import Patient

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
        from clinica_beleza.models import Professional
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
    from clinica_beleza.media_docs_service import salvar_pdf_loja
    from clinica_beleza.pedido_compra_pdf import gerar_pdf_pedido_compra

    pdf_bytes = gerar_pdf_pedido_compra(pedido)
    url = salvar_pdf_loja(pedido.loja_id, pdf_bytes, nome_arquivo_pdf_pedido(pedido))
    pedido.pdf_url = url or pedido.pdf_url or ""
    if pedido.status not in (PedidoCompra.STATUS_ENVIADO, PedidoCompra.STATUS_CANCELADO):
        pedido.status = PedidoCompra.STATUS_ASSINADO
    pedido.save(update_fields=["pdf_url", "status", "updated_at"])
    return True

def pdf_bytes_pedido(pedido: PedidoCompra) -> bytes:
    from clinica_beleza.pedido_compra_pdf import gerar_pdf_pedido_compra
    return gerar_pdf_pedido_compra(pedido)

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
