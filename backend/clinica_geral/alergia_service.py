"""Confronto simples de alergias cadastradas com o nome do medicamento."""


def tokens_alergia(alergias: str) -> list[str]:
    parts = (alergias or "").replace(";", ",").split(",")
    return [p.strip().lower() for p in parts if len(p.strip()) > 2]


def medicamento_conflita_alergia(alergias: str, medicamento: str) -> bool:
    med = (medicamento or "").strip().lower()
    if not med:
        return False
    return any(token in med or med in token for token in tokens_alergia(alergias))
