"""Comparação entre dois laudos do mesmo paciente (evolução dos marcadores)."""
from __future__ import annotations

from datetime import date

# Marcadores em que subir o valor costuma ser favorável (em direção à faixa ou proteção).
_MELHOR_SE_SOBE = frozenset({
    "hdl",
    "vitamina_d",
    "vitamina_b12",
    "hemoglobina",
    "hematocrito",
    "eritrocitos",
    "testosterona_total",
    "testosterona_livre",
    "t4_livre",  # depende do contexto; sobe a partir de baixo costuma melhorar
})

# Marcadores em que descer o valor costuma ser favorável.
_MELHOR_SE_DESCE = frozenset({
    "ldl",
    "vldl",
    "colesterol_total",
    "triglicerides",
    "glicose",
    "hba1c",
    "psa_total",
    "tgo",
    "tgp",
    "pcr",
    "creatinina",
    "ureia",
    "tsh",  # alto → descer costuma melhorar hipotireoidismo
    "ferritina",  # alto inflamatório → descer; baixo → sobe (tratado via status)
})


def _valor_num(item: dict) -> float | None:
    v = item.get("valor")
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _indice_por_codigo(marcadores: list) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for m in marcadores or []:
        if not isinstance(m, dict):
            continue
        codigo = (m.get("codigo") or "").strip()
        if not codigo or codigo in out:
            continue
        if _valor_num(m) is None:
            continue
        out[codigo] = m
    return out


def _classificar_evolucao(
    codigo: str,
    *,
    valor_ant: float,
    valor_atual: float,
    status_ant: str,
    status_atual: str,
) -> str:
    """Retorna melhorou | piorou | estavel."""
    if abs(valor_atual - valor_ant) < 1e-9:
        return "estavel"
    # Transição de status tem prioridade.
    fora = {"alto", "baixo"}
    if status_ant in fora and status_atual == "dentro":
        return "melhorou"
    if status_ant == "dentro" and status_atual in fora:
        return "piorou"
    # Aproximação da faixa quando ambos fora no mesmo sentido
    if status_ant == "baixo" and status_atual == "baixo":
        return "melhorou" if valor_atual > valor_ant else "piorou"
    if status_ant == "alto" and status_atual == "alto":
        return "melhorou" if valor_atual < valor_ant else "piorou"
    if status_ant == "baixo" and status_atual == "alto":
        return "piorou"
    if status_ant == "alto" and status_atual == "baixo":
        return "piorou"

    delta = valor_atual - valor_ant
    # Variação relativa pequena → estável (≤ 2% ou ≤ 0,1 absoluto para valores pequenos)
    base = abs(valor_ant) if abs(valor_ant) > 1e-9 else 1.0
    if abs(delta) / base <= 0.02 and abs(delta) <= max(0.5, base * 0.02):
        return "estavel"

    if codigo in _MELHOR_SE_SOBE:
        return "melhorou" if delta > 0 else "piorou"
    if codigo in _MELHOR_SE_DESCE:
        return "melhorou" if delta < 0 else "piorou"
    # Neutro: só indica direção
    return "estavel"


def comparar_marcadores(
    marcadores_atual: list,
    marcadores_anterior: list,
    *,
    data_atual: date | None = None,
    data_anterior: date | None = None,
) -> dict:
    """Cruza marcadores comuns e monta linhas de evolução + texto resumo."""
    atual = _indice_por_codigo(marcadores_atual)
    anterior = _indice_por_codigo(marcadores_anterior)
    comuns = sorted(set(atual) & set(anterior), key=lambda c: (atual[c].get("nome") or c))
    linhas: list[dict] = []
    for codigo in comuns:
        a = atual[codigo]
        b = anterior[codigo]
        va = _valor_num(a)
        vb = _valor_num(b)
        if va is None or vb is None:
            continue
        delta = va - vb
        pct = (delta / vb * 100.0) if abs(vb) > 1e-9 else None
        evolucao = _classificar_evolucao(
            codigo,
            valor_ant=vb,
            valor_atual=va,
            status_ant=str(b.get("status") or ""),
            status_atual=str(a.get("status") or ""),
        )
        linhas.append({
            "codigo": codigo,
            "nome": a.get("nome") or b.get("nome") or codigo,
            "unidade": a.get("unidade") or b.get("unidade") or "",
            "valor_anterior": vb,
            "valor_atual": va,
            "delta": round(delta, 4),
            "delta_pct": round(pct, 1) if pct is not None else None,
            "status_anterior": b.get("status") or "",
            "status_atual": a.get("status") or "",
            "evolucao": evolucao,
        })

    melhoraram = sum(1 for L in linhas if L["evolucao"] == "melhorou")
    pioraram = sum(1 for L in linhas if L["evolucao"] == "piorou")
    estaveis = sum(1 for L in linhas if L["evolucao"] == "estavel")

    def _fmt_data(d: date | None) -> str:
        return d.strftime("%d/%m/%Y") if d else "—"

    if not linhas:
        texto = (
            "Não há marcadores em comum com o laudo anterior para comparar. "
            "Importe laudos com os mesmos exames para ver a evolução."
        )
    else:
        texto = (
            f"Comparação com o laudo anterior "
            f"({_fmt_data(data_anterior)} → {_fmt_data(data_atual)}): "
            f"{melhoraram} melhoraram, {pioraram} pioraram, {estaveis} estáveis "
            f"(de {len(linhas)} marcadores em comum). "
            "Não substitui a avaliação profissional."
        )

    return {
        "tem_anterior": True,
        "data_atual": data_atual.isoformat() if data_atual else None,
        "data_anterior": data_anterior.isoformat() if data_anterior else None,
        "resumo": {
            "total_comuns": len(linhas),
            "melhoraram": melhoraram,
            "pioraram": pioraram,
            "estaveis": estaveis,
        },
        "itens": linhas,
        "texto": texto,
    }
