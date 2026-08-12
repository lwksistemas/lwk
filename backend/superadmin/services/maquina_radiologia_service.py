"""Libera / suspende máquina do Super Admin no schema da clínica."""
from __future__ import annotations

import logging
from decimal import Decimal

from django.utils import timezone

logger = logging.getLogger(__name__)


def _contexto_tenant(loja):
    from core.db_config import ensure_loja_database_config
    from tenants.middleware import set_current_loja_id, set_current_tenant_db

    db_name = loja.database_name
    if not ensure_loja_database_config(db_name, conn_max_age=0):
        raise RuntimeError(f"Schema da loja {loja.id} indisponível")
    set_current_loja_id(loja.id)
    set_current_tenant_db(db_name)
    return db_name


def _limpar_contexto(db_name: str) -> None:
    from django.db import connections
    from tenants.middleware import set_current_loja_id, set_current_tenant_db

    set_current_loja_id(None)
    set_current_tenant_db(None)
    if db_name in connections:
        try:
            connections[db_name].close()
        except Exception:
            pass


def sincronizar_valor_mensalidade(loja) -> Decimal:
    """Plano + PACS/Worklist + máquinas liberadas."""
    from superadmin.models import ContratoPacsLoja, FinanceiroLoja, MaquinaRadiologia
    from superadmin.services.financeiro_service import FinanceiroService

    valor = Decimal(str(FinanceiroService.calcular_valor_mensalidade(loja)))
    contrato = ContratoPacsLoja.objects.filter(loja=loja, is_active=True).first()
    if contrato:
        valor += contrato.valor_mensal()
    maquinas = MaquinaRadiologia.objects.filter(
        loja=loja, is_active=True, status=MaquinaRadiologia.Status.LIBERADA
    )
    for m in maquinas:
        valor += m.cobranca_mensal or Decimal("0.00")

    fin = FinanceiroLoja.objects.filter(loja=loja).first()
    if fin:
        fin.valor_mensalidade = valor
        fin.save(update_fields=["valor_mensalidade"])
    return valor


def liberar_maquina_no_cliente(maquina) -> dict:
    """Cria/ativa Equipamento no tenant e marca máquina como liberada."""
    from radiologia.equipamento_vinculo_service import gerar_codigo_vinculo
    from radiologia.models import Equipamento
    from superadmin.models import ContratoPacsLoja, MaquinaRadiologia

    loja = maquina.loja
    contrato = ContratoPacsLoja.objects.filter(loja=loja, is_active=True).first()
    if not contrato or not (contrato.dicom_contratado or contrato.worklist_contratado):
        raise PermissionError(
            "A clínica precisa contratar o servidor DICOM e/ou Worklist antes de liberar a máquina."
        )

    codigo = (maquina.codigo_vinculo or "").strip() or gerar_codigo_vinculo()
    db_name = _contexto_tenant(loja)
    try:
        eq = None
        if maquina.equipamento_tenant_id:
            eq = (
                Equipamento.objects.using(db_name)
                .filter(loja_id=loja.id, id=maquina.equipamento_tenant_id)
                .first()
            )
        if not eq:
            eq = (
                Equipamento.objects.using(db_name)
                .filter(loja_id=loja.id, ae_title=maquina.ae_title)
                .first()
            )
        defaults = {
            "nome": maquina.nome,
            "ae_title": maquina.ae_title[:16],
            "modality": maquina.tipo or "US",
            "fabricante": maquina.fabricante,
            "modelo": maquina.modelo,
            "codigo_vinculo": codigo,
            "suporte_dicom_storage": bool(contrato.dicom_contratado),
            "suporte_mwl": bool(contrato.worklist_contratado),
            "cobranca_mensal": maquina.cobranca_mensal,
            "liberado_pelo_superadmin": True,
            "maquina_superadmin_id": maquina.id,
            "is_active": True,
            "loja_id": loja.id,
        }
        if eq:
            for k, v in defaults.items():
                setattr(eq, k, v)
            eq.save()
        else:
            eq = Equipamento(**defaults)
            eq.save(using=db_name)

        maquina.codigo_vinculo = codigo
        maquina.equipamento_tenant_id = eq.id
        maquina.status = MaquinaRadiologia.Status.LIBERADA
        maquina.liberada_em = timezone.now()
        maquina.save(
            update_fields=[
                "codigo_vinculo",
                "equipamento_tenant_id",
                "status",
                "liberada_em",
                "updated_at",
            ]
        )
        valor = sincronizar_valor_mensalidade(loja)
        logger.info("Máquina %s liberada na loja %s (equip tenant=%s)", maquina.id, loja.id, eq.id)
        return {
            "ok": True,
            "maquina_id": maquina.id,
            "equipamento_tenant_id": eq.id,
            "codigo_vinculo": codigo,
            "valor_mensalidade": str(valor),
        }
    finally:
        _limpar_contexto(db_name)


def processar_vinculo_maquina(maquina) -> dict:
    """Super Admin conclui o pareamento DICOM no tenant da clínica."""
    from radiologia.equipamento_vinculo_service import processar_vinculo_dicom_equipamento
    from radiologia.models import Equipamento

    if not maquina.equipamento_tenant_id:
        raise LookupError("Libere a máquina no cliente antes de vincular o DICOM.")

    loja = maquina.loja
    db_name = _contexto_tenant(loja)
    try:
        eq = (
            Equipamento.objects.using(db_name)
            .filter(loja_id=loja.id, id=maquina.equipamento_tenant_id)
            .first()
        )
        if not eq:
            raise LookupError("Equipamento não encontrado no sistema do cliente.")
        return processar_vinculo_dicom_equipamento(eq)
    finally:
        _limpar_contexto(db_name)


def regenerar_codigo_maquina(maquina) -> dict:
    """Gera novo código de vínculo (o ultrassom não reaproveita Accession já usado)."""
    from radiologia.equipamento_vinculo_service import gerar_codigo_vinculo
    from radiologia.models import Equipamento
    from superadmin.models import MaquinaRadiologia

    usados = set(
        MaquinaRadiologia.objects.exclude(pk=maquina.pk)
        .exclude(codigo_vinculo="")
        .values_list("codigo_vinculo", flat=True)
    )
    codigo = gerar_codigo_vinculo()
    while codigo in usados or codigo == (maquina.codigo_vinculo or ""):
        codigo = gerar_codigo_vinculo()
    loja = maquina.loja
    db_name = _contexto_tenant(loja) if maquina.equipamento_tenant_id else None
    try:
        if db_name and maquina.equipamento_tenant_id:
            eq = (
                Equipamento.objects.using(db_name)
                .filter(loja_id=loja.id, id=maquina.equipamento_tenant_id)
                .first()
            )
            if eq:
                eq.codigo_vinculo = codigo
                eq.numero_serie = ""
                eq.vinculado_em = None
                eq.orthanc_study_id_vinculo = ""
                eq.save(
                    update_fields=[
                        "codigo_vinculo",
                        "numero_serie",
                        "vinculado_em",
                        "orthanc_study_id_vinculo",
                        "updated_at",
                    ]
                )
        maquina.codigo_vinculo = codigo
        maquina.save(update_fields=["codigo_vinculo", "updated_at"])
        return {"ok": True, "maquina_id": maquina.id, "codigo_vinculo": codigo}
    finally:
        if db_name:
            _limpar_contexto(db_name)


def suspender_maquina_no_cliente(maquina) -> dict:
    from radiologia.models import Equipamento
    from superadmin.models import MaquinaRadiologia

    loja = maquina.loja
    db_name = _contexto_tenant(loja)
    try:
        if maquina.equipamento_tenant_id:
            eq = (
                Equipamento.objects.using(db_name)
                .filter(loja_id=loja.id, id=maquina.equipamento_tenant_id)
                .first()
            )
            if eq:
                eq.is_active = False
                eq.save(update_fields=["is_active", "updated_at"])
        maquina.status = MaquinaRadiologia.Status.SUSPENSA
        maquina.save(update_fields=["status", "updated_at"])
        valor = sincronizar_valor_mensalidade(loja)
        return {"ok": True, "maquina_id": maquina.id, "valor_mensalidade": str(valor)}
    finally:
        _limpar_contexto(db_name)


def status_dicom_das_maquinas(maquinas) -> dict[int, dict]:
    """Lê no tenant se o exame de teste já gravou o serial."""
    from collections import defaultdict

    from radiologia.models import Equipamento

    por_loja = defaultdict(list)
    for m in maquinas:
        if m.equipamento_tenant_id and m.loja_id:
            por_loja[m.loja_id].append(m)

    out: dict[int, dict] = {}
    lojas = {m.loja_id: m.loja for m in maquinas if m.loja_id}
    for loja_id, items in por_loja.items():
        loja = lojas.get(loja_id)
        if not loja:
            continue
        ids = [m.equipamento_tenant_id for m in items]
        db_name = _contexto_tenant(loja)
        try:
            eqs = {
                eq.id: eq
                for eq in Equipamento.objects.using(db_name).filter(loja_id=loja_id, id__in=ids)
            }
            for m in items:
                eq = eqs.get(m.equipamento_tenant_id)
                out[m.id] = {
                    "dicom_vinculado": bool(eq and eq.vinculado_em),
                    "numero_serie": (eq.numero_serie if eq else "") or "",
                    "vinculado_em": eq.vinculado_em.isoformat() if eq and eq.vinculado_em else None,
                }
        except Exception:
            logger.exception("status_dicom loja=%s", loja_id)
        finally:
            _limpar_contexto(db_name)
    return out
