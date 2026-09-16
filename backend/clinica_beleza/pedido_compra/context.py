"""Dados de loja/profissional para pedido de compra."""
from __future__ import annotations


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


def _loja_nome(loja_id: int) -> str:
    from superadmin.models import Loja
    loja = Loja.objects.using("default").filter(id=loja_id).first()
    return (loja.nome if loja else "") or "Clínica"
