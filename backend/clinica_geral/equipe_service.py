"""Cadastro de especialidades, profissionais e funcionários da loja."""
from __future__ import annotations

ESPECIALIDADE_PADRAO = "Clínica médica"

CARGO_LABEL = {
    "recepcao": "Recepção",
    "administracao": "Administração",
    "financeiro": "Financeiro",
    "outros": "Outros",
}


def cargo_label(cargo: str) -> str:
    return CARGO_LABEL.get((cargo or "").strip(), "Outros")


def garantir_especialidade_padrao() -> Especialidade:
    from .models import Especialidade

    ativa = Especialidade.objects.filter(is_active=True).order_by("nome").first()
    if ativa:
        return ativa
    inativa = Especialidade.objects.filter(nome=ESPECIALIDADE_PADRAO).first()
    if inativa:
        inativa.is_active = True
        inativa.save(update_fields=["is_active"])
        return inativa
    return Especialidade.objects.create(nome=ESPECIALIDADE_PADRAO)


def normalizar_uf(uf: str) -> str:
    return (uf or "").strip().upper()[:2]


def normalizar_nome(nome: str) -> str:
    return (nome or "").strip()
