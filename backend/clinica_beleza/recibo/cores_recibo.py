"""Cor da faixa e dos fundos do comprovante."""
import re
def cor_primaria_recibo(valor: str) -> str:
    """Cor da faixa do recibo. Usa a personalização da clínica quando é um hex válido."""
    texto = (valor or "").strip()
    if re.fullmatch(r"#[0-9A-Fa-f]{6}", texto):
        return texto.upper()
    return "#8B3D52"


def tinta_recibo(cor: str, fator: float = 0.9) -> str:
    """Mistura a cor da clínica com branco para os fundos do recibo."""
    base = cor_primaria_recibo(cor)
    canais = [int(base[i:i + 2], 16) for i in (1, 3, 5)]
    mistos = [int(round(canal + (255 - canal) * fator)) for canal in canais]
    return "#{:02X}{:02X}{:02X}".format(*mistos)
