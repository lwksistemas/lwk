"""Vínculo ultrassom ↔ clínica (serial + CPF/CNPJ) e exame ↔ pedido (Accession)."""
from __future__ import annotations

import logging
import re
import secrets
import string

from django.db import connections

logger = logging.getLogger(__name__)

_SERIAL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,63}$")
_CODE_ALPHABET = string.ascii_uppercase + string.digits


def normalizar_serial(value: str | None) -> str:
    raw = (value or "").strip().upper()
    raw = re.sub(r"\s+", "", raw)
    return raw[:64]


def normalizar_cpf_cnpj(value: str | None) -> str:
    return re.sub(r"\D", "", value or "")


def gerar_codigo_vinculo(tamanho: int = 8) -> str:
    """Código aleatório legível (ex.: K7M2P9QX) para parear aparelho/envio."""
    return "".join(secrets.choice(_CODE_ALPHABET) for _ in range(tamanho))


def validar_serial(value: str) -> str:
    serial = normalizar_serial(value)
    if not serial or not _SERIAL_RE.fullmatch(serial):
        raise ValueError(
            "Número de série inválido. Use 3–64 caracteres (letras, números, . _ -)."
        )
    return serial


def _fechar_tenant_db(db_name: str) -> None:
    if db_name in connections:
        try:
            connections[db_name].close()
        except Exception:
            pass


def resolver_equipamento_por_serial(
    numero_serie: str,
    *,
    cpf_cnpj_loja: str | None = None,
) -> dict | None:
    """Localiza clínica + equipamento pelo serial (opcionalmente confirma CPF/CNPJ da loja).

    Retorna dict com loja_id, equipamento_id, ae_title, codigo_vinculo, cpf_cnpj.
    """
    from core.db_config import ensure_loja_database_config
    from superadmin.models import Loja
    from tenants.middleware import set_current_loja_id, set_current_tenant_db

    from .models import Equipamento

    serial = normalizar_serial(numero_serie)
    if not serial:
        return None

    doc = normalizar_cpf_cnpj(cpf_cnpj_loja)
    lojas = Loja.objects.using("default").filter(
        is_active=True,
        tipo_loja__slug__icontains="radiolog",
    )
    if doc:
        # Match por dígitos do documento da loja
        candidatos = []
        for loja in lojas:
            if normalizar_cpf_cnpj(loja.cpf_cnpj) == doc:
                candidatos.append(loja)
        lojas = candidatos
    else:
        lojas = list(lojas)

    for loja in lojas:
        db_name = loja.database_name
        if not ensure_loja_database_config(db_name, conn_max_age=0):
            continue
        set_current_loja_id(loja.id)
        set_current_tenant_db(db_name)
        try:
            eq = (
                Equipamento.objects.using(db_name)
                .filter(loja_id=loja.id, numero_serie=serial, is_active=True)
                .first()
            )
            if not eq:
                continue
            return {
                "loja_id": loja.id,
                "loja_nome": loja.nome,
                "cpf_cnpj": normalizar_cpf_cnpj(loja.cpf_cnpj),
                "equipamento_id": eq.id,
                "equipamento_nome": eq.nome,
                "ae_title": eq.ae_title,
                "codigo_vinculo": eq.codigo_vinculo,
                "numero_serie": eq.numero_serie,
                "database_name": db_name,
            }
        finally:
            set_current_loja_id(None)
            set_current_tenant_db(None)
            _fechar_tenant_db(db_name)

    return None


def serial_ja_vinculado_outra_loja(numero_serie: str, loja_id: int) -> bool:
    """True se o serial já pertence a outra clínica."""
    hit = resolver_equipamento_por_serial(numero_serie)
    if not hit:
        return False
    return int(hit["loja_id"]) != int(loja_id)


def receber_exame_por_accession_e_serial(
    *,
    accession_number: str,
    numero_serie: str,
    cpf_cnpj_loja: str | None = None,
) -> dict:
    """Resolve clínica pelo serial (+ CPF/CNPJ) e exame pelo Accession; arquiva DICOM."""
    from core.db_config import ensure_loja_database_config
    from tenants.middleware import set_current_loja_id, set_current_tenant_db

    from .dicom_storage_service import sincronizar_imagens_pedido
    from .models import PedidoExame

    accession = (accession_number or "").strip()
    if not accession:
        raise ValueError("AccessionNumber é obrigatório para vincular o exame ao pedido")

    vinculo = resolver_equipamento_por_serial(numero_serie, cpf_cnpj_loja=cpf_cnpj_loja)
    if not vinculo:
        raise LookupError(
            "Ultrassom não vinculado à clínica. Cadastre o número de série em Equipamentos."
        )

    if cpf_cnpj_loja:
        doc = normalizar_cpf_cnpj(cpf_cnpj_loja)
        if doc and doc != vinculo["cpf_cnpj"]:
            raise PermissionError(
                "CPF/CNPJ da clínica não confere com o vínculo do número de série."
            )

    db_name = vinculo["database_name"]
    if not ensure_loja_database_config(db_name, conn_max_age=0):
        raise RuntimeError("Schema da clínica indisponível")

    set_current_loja_id(vinculo["loja_id"])
    set_current_tenant_db(db_name)
    try:
        pedido = (
            PedidoExame.objects.using(db_name)
            .select_related("paciente", "equipamento", "procedimento")
            .filter(loja_id=vinculo["loja_id"], accession_number=accession)
            .exclude(status=PedidoExame.Status.CANCELADO)
            .first()
        )
        if not pedido:
            raise LookupError(
                f"Pedido com Accession {accession} não encontrado nesta clínica."
            )

        # Confirma que o pedido usa o mesmo aparelho (se informado)
        if pedido.equipamento_id and pedido.equipamento_id != vinculo["equipamento_id"]:
            raise PermissionError(
                "O Accession pertence a outro equipamento desta clínica."
            )

        pedido = sincronizar_imagens_pedido(pedido)
        return {
            "ok": True,
            "loja_id": vinculo["loja_id"],
            "loja_nome": vinculo["loja_nome"],
            "cpf_cnpj": vinculo["cpf_cnpj"],
            "equipamento_id": vinculo["equipamento_id"],
            "numero_serie": vinculo["numero_serie"],
            "codigo_vinculo": vinculo["codigo_vinculo"],
            "pedido_id": pedido.id,
            "accession_number": pedido.accession_number,
            "status": pedido.status,
            "dicom_media_url": pedido.dicom_media_url,
        }
    finally:
        set_current_loja_id(None)
        set_current_tenant_db(None)
        _fechar_tenant_db(db_name)
