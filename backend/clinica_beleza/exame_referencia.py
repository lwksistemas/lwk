"""Catálogo interno de faixas de referência por sexo e idade.

Usado só como apoio à sugestão. Se o laudo trouxer a faixa, ela tem prioridade.
Não substitui o julgamento do profissional.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation

# codigo -> aliases no PDF e faixas (sexo M/F/A, idade_min inclusiva, idade_max exclusiva None=∞)
CATALOGO_REFERENCIA: dict[str, dict] = {
    "hemoglobina": {
        "nome": "Hemoglobina",
        "unidade": "g/dL",
        "aliases": ("hemoglobina", "hb", "hgb"),
        "faixas": [
            {"sexo": "F", "idade_min": 12, "idade_max": None, "min": 12.0, "max": 16.0},
            {"sexo": "M", "idade_min": 12, "idade_max": None, "min": 13.0, "max": 17.0},
            {"sexo": "A", "idade_min": 0, "idade_max": 12, "min": 11.0, "max": 14.5},
        ],
    },
    "hematocrito": {
        "nome": "Hematócrito",
        "unidade": "%",
        "aliases": ("hematocrito", "hematócrito", "ht", "hct"),
        "faixas": [
            {"sexo": "F", "idade_min": 12, "idade_max": None, "min": 36.0, "max": 46.0},
            {"sexo": "M", "idade_min": 12, "idade_max": None, "min": 40.0, "max": 50.0},
            {"sexo": "A", "idade_min": 0, "idade_max": 12, "min": 34.0, "max": 44.0},
        ],
    },
    "glicose": {
        "nome": "Glicose",
        "unidade": "mg/dL",
        "aliases": ("glicose", "glicemia", "glucose"),
        "faixas": [
            {"sexo": "A", "idade_min": 0, "idade_max": None, "min": 70.0, "max": 99.0},
        ],
    },
    "hba1c": {
        "nome": "Hemoglobina glicada (HbA1c)",
        "unidade": "%",
        "aliases": ("hba1c", "hemoglobina glicada", "a1c"),
        "faixas": [
            {"sexo": "A", "idade_min": 0, "idade_max": None, "min": 4.0, "max": 5.6},
        ],
    },
    "colesterol_total": {
        "nome": "Colesterol total",
        "unidade": "mg/dL",
        "aliases": ("colesterol total", "colesterol"),
        "faixas": [
            {"sexo": "A", "idade_min": 0, "idade_max": 18, "min": 0.0, "max": 170.0},
            {"sexo": "A", "idade_min": 18, "idade_max": None, "min": 0.0, "max": 190.0},
        ],
    },
    "hdl": {
        "nome": "HDL colesterol",
        "unidade": "mg/dL",
        "aliases": ("hdl", "hdl-colesterol", "hdl colesterol"),
        "faixas": [
            {"sexo": "F", "idade_min": 18, "idade_max": None, "min": 50.0, "max": 999.0},
            {"sexo": "M", "idade_min": 18, "idade_max": None, "min": 40.0, "max": 999.0},
            {"sexo": "A", "idade_min": 0, "idade_max": 18, "min": 45.0, "max": 999.0},
        ],
    },
    "ldl": {
        "nome": "LDL colesterol",
        "unidade": "mg/dL",
        "aliases": ("ldl", "ldl-colesterol", "ldl colesterol"),
        "faixas": [
            {"sexo": "A", "idade_min": 0, "idade_max": None, "min": 0.0, "max": 100.0},
        ],
    },
    "triglicerides": {
        "nome": "Triglicerídeos",
        "unidade": "mg/dL",
        "aliases": ("triglicerides", "triglicerídeos", "triglycerides"),
        "faixas": [
            {"sexo": "A", "idade_min": 0, "idade_max": None, "min": 0.0, "max": 150.0},
        ],
    },
    "tsh": {
        "nome": "TSH",
        "unidade": "µUI/mL",
        "aliases": ("tsh", "tireotropina"),
        "faixas": [
            {"sexo": "A", "idade_min": 0, "idade_max": None, "min": 0.4, "max": 4.0},
        ],
    },
    "t4_livre": {
        "nome": "T4 livre",
        "unidade": "ng/dL",
        "aliases": ("t4 livre", "t4l", "tiroxina livre"),
        "faixas": [
            {"sexo": "A", "idade_min": 0, "idade_max": None, "min": 0.7, "max": 1.8},
        ],
    },
    "vitamina_d": {
        "nome": "Vitamina D (25-OH)",
        "unidade": "ng/mL",
        "aliases": ("vitamina d", "25-oh", "25 oh vitamina d", "vitamina d 25"),
        "faixas": [
            {"sexo": "A", "idade_min": 0, "idade_max": None, "min": 30.0, "max": 100.0},
        ],
    },
    "vitamina_b12": {
        "nome": "Vitamina B12",
        "unidade": "pg/mL",
        "aliases": ("vitamina b12", "b12", "cobalamina"),
        "faixas": [
            {"sexo": "A", "idade_min": 0, "idade_max": None, "min": 200.0, "max": 900.0},
        ],
    },
    "ferritina": {
        "nome": "Ferritina",
        "unidade": "ng/mL",
        "aliases": ("ferritina",),
        "faixas": [
            {"sexo": "F", "idade_min": 12, "idade_max": None, "min": 15.0, "max": 150.0},
            {"sexo": "M", "idade_min": 12, "idade_max": None, "min": 30.0, "max": 400.0},
            {"sexo": "A", "idade_min": 0, "idade_max": 12, "min": 15.0, "max": 140.0},
        ],
    },
    "creatinina": {
        "nome": "Creatinina",
        "unidade": "mg/dL",
        "aliases": ("creatinina",),
        "faixas": [
            {"sexo": "F", "idade_min": 12, "idade_max": None, "min": 0.5, "max": 1.1},
            {"sexo": "M", "idade_min": 12, "idade_max": None, "min": 0.7, "max": 1.3},
            {"sexo": "A", "idade_min": 0, "idade_max": 12, "min": 0.3, "max": 0.7},
        ],
    },
    "ureia": {
        "nome": "Ureia",
        "unidade": "mg/dL",
        "aliases": ("ureia", "uréia"),
        "faixas": [
            {"sexo": "A", "idade_min": 0, "idade_max": None, "min": 15.0, "max": 45.0},
        ],
    },
    "tgo": {
        "nome": "TGO (AST)",
        "unidade": "U/L",
        "aliases": ("tgo", "ast", "tgo/ast"),
        "faixas": [
            {"sexo": "A", "idade_min": 0, "idade_max": None, "min": 0.0, "max": 40.0},
        ],
    },
    "tgp": {
        "nome": "TGP (ALT)",
        "unidade": "U/L",
        "aliases": ("tgp", "alt", "tgp/alt"),
        "faixas": [
            {"sexo": "A", "idade_min": 0, "idade_max": None, "min": 0.0, "max": 41.0},
        ],
    },
    "pcr": {
        "nome": "PCR",
        "unidade": "mg/L",
        "aliases": ("pcr", "proteina c reativa", "proteína c reativa"),
        "faixas": [
            {"sexo": "A", "idade_min": 0, "idade_max": None, "min": 0.0, "max": 5.0},
        ],
    },
}


def idade_em_anos(nascimento: date | None, referencia: date | None = None) -> int | None:
    if not nascimento:
        return None
    hoje = referencia or date.today()
    anos = hoje.year - nascimento.year
    if (hoje.month, hoje.day) < (nascimento.month, nascimento.day):
        anos -= 1
    return max(0, anos)


def _faixa_bate(faixa: dict, sexo: str, idade: int | None) -> bool:
    sexo_faixa = (faixa.get("sexo") or "A").upper()
    if sexo_faixa not in ("A", sexo):
        return False
    idade_min = int(faixa.get("idade_min") or 0)
    idade_max = faixa.get("idade_max")
    if idade is None:
        # Sem idade: só aceita faixa que cobre adulto amplo ou qualquer idade.
        return idade_min <= 18 and idade_max is None
    if idade < idade_min:
        return False
    if idade_max is not None and idade >= int(idade_max):
        return False
    return True


def resolver_faixa_catalogo(codigo: str, *, sexo: str, idade: int | None) -> dict | None:
    item = CATALOGO_REFERENCIA.get(codigo)
    if not item:
        return None
    sexo_norm = (sexo or "").upper()[:1]
    if sexo_norm not in ("M", "F"):
        sexo_norm = "A"
    candidatas = [f for f in item["faixas"] if _faixa_bate(f, sexo_norm, idade)]
    if not candidatas and sexo_norm in ("M", "F"):
        candidatas = [f for f in item["faixas"] if _faixa_bate(f, "A", idade)]
    if not candidatas:
        return None
    # Prefere faixa específica do sexo em relação à genérica.
    candidatas.sort(key=lambda f: 0 if f.get("sexo") == sexo_norm else 1)
    escolhida = candidatas[0]
    return {
        "min": float(escolhida["min"]),
        "max": float(escolhida["max"]),
        "unidade": item["unidade"],
        "nome": item["nome"],
        "origem": "catalogo",
    }


def classificar_valor(valor: float, minimo: float | None, maximo: float | None) -> str:
    if minimo is None and maximo is None:
        return "sem_referencia"
    if minimo is not None and valor < minimo:
        return "baixo"
    if maximo is not None and valor > maximo:
        return "alto"
    return "dentro"


def para_decimal(texto) -> float | None:
    if texto is None:
        return None
    bruto = str(texto).strip().replace(" ", "")
    if not bruto:
        return None
    if "," in bruto and "." in bruto:
        bruto = bruto.replace(".", "").replace(",", ".")
    elif "," in bruto:
        bruto = bruto.replace(",", ".")
    try:
        return float(Decimal(bruto))
    except (InvalidOperation, ValueError):
        return None


def alias_para_codigo(nome: str) -> str | None:
    chave = (nome or "").strip().lower()
    if not chave:
        return None
    for codigo, item in CATALOGO_REFERENCIA.items():
        for alias in item["aliases"]:
            if alias in chave or chave in alias:
                return codigo
    return None
