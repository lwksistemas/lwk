"""Perfil do profissional logado (Meu Perfil)."""
from __future__ import annotations

from datetime import date, datetime

from tenants.middleware import get_current_loja_id

from .agenda_service import nome_usuario
from .config_service import get_or_create_config
from .models import PerfilProfissional

CAMPOS = (
    "tratamento",
    "celular",
    "telefone",
    "conselho",
    "uf",
    "rg",
    "cpf",
    "nacionalidade",
    "sexo",
    "cbo",
    "estado_civil",
    "foto_url",
)

SEXO_LABEL = {"M": "Masculino", "F": "Feminino", "I": "Indefinido", "": "Não informado"}
ESTADO_CIVIL_LABEL = dict(PerfilProfissional.ESTADO_CIVIL_CHOICES)


def _data_iso(valor: date | None) -> str:
    return valor.isoformat() if valor else ""


def _parse_data(valor) -> date | None:
    texto = str(valor or "").strip()[:10]
    if not texto:
        return None
    try:
        return datetime.strptime(texto, "%Y-%m-%d").date()
    except ValueError:
        return None


def _aplicar_nome(user, nome: str) -> None:
    partes = (nome or "").strip().split(None, 1)
    user.first_name = partes[0] if partes else ""
    user.last_name = partes[1] if len(partes) > 1 else ""


def serializar_perfil(user, perfil: PerfilProfissional) -> dict:
    sexo = perfil.sexo or ""
    estado = perfil.estado_civil or ""
    return {
        "username": getattr(user, "username", "") or "",
        "nome": nome_usuario(user),
        "email": (getattr(user, "email", None) or "").strip(),
        "tratamento": perfil.tratamento or "",
        "celular": perfil.celular or "",
        "telefone": perfil.telefone or "",
        "conselho": perfil.conselho or "",
        "uf": perfil.uf or "",
        "rg": perfil.rg or "",
        "cpf": perfil.cpf or "",
        "data_nascimento": _data_iso(perfil.data_nascimento),
        "nacionalidade": perfil.nacionalidade or "",
        "sexo": sexo,
        "sexo_label": SEXO_LABEL.get(sexo, "Não informado"),
        "cbo": perfil.cbo or "",
        "estado_civil": estado,
        "estado_civil_label": ESTADO_CIVIL_LABEL.get(estado, "Não informado") or "Não informado",
        "foto_url": perfil.foto_url or "",
    }


def get_or_create_perfil(user) -> PerfilProfissional:
    username = (getattr(user, "username", "") or "").strip()
    perfil = PerfilProfissional.objects.filter(username=username).first()
    if perfil:
        return perfil
    config = get_or_create_config()
    loja_id = get_current_loja_id()
    dados = {
        "username": username,
        "telefone": config.telefone or "",
        "conselho": "CRM" if config.crm else "",
        "foto_url": "",
    }
    if loja_id:
        dados["loja_id"] = loja_id
    return PerfilProfissional.objects.create(**dados)


def aplicar_perfil(user, perfil: PerfilProfissional, payload: dict) -> PerfilProfissional:
    dados = payload or {}
    if "nome" in dados:
        _aplicar_nome(user, str(dados.get("nome") or ""))
    if "email" in dados:
        user.email = str(dados.get("email") or "").strip()
    if "nome" in dados or "email" in dados:
        user.save(update_fields=["first_name", "last_name", "email"])

    for campo in CAMPOS:
        if campo not in dados:
            continue
        setattr(perfil, campo, str(dados.get(campo) or "").strip())
    if "uf" in dados:
        perfil.uf = str(dados.get("uf") or "").strip().upper()[:2]
    if "sexo" in dados:
        sexo = str(dados.get("sexo") or "").strip().upper()[:1]
        perfil.sexo = sexo if sexo in ("", "M", "F", "I") else ""
    if "data_nascimento" in dados:
        perfil.data_nascimento = _parse_data(dados.get("data_nascimento"))
    perfil.save()
    return perfil
