"""Data de cada atualização da opinião pós-venda e do histórico."""
import re

_DATA_NO_TEXTO = re.compile(
    r"\[\d{2}/\d{2}/\d{4} \d{2}:\d{2}\]|\[\d{1,2}:\d{2},\s*\d{1,2}/\d{1,2}/\d{4}\]"
)


def texto_tem_data(texto: str) -> bool:
    return bool(_DATA_NO_TEXTO.search(texto or ""))


def datar_atualizacao(texto_anterior: str, texto_novo: str, agora) -> str:
    """Marca só o trecho novo. O que já estava escrito permanece com a data antiga."""
    anterior = (texto_anterior or "").strip()
    novo = (texto_novo or "").strip()
    if not novo or novo == anterior:
        return novo
    marca = agora.strftime("%d/%m/%Y %H:%M")
    if anterior and novo.startswith(anterior):
        extra = novo[len(anterior):].strip()
        if not extra or texto_tem_data(extra[:40]):
            return f"{anterior}\n{extra}".strip() if extra else anterior
        return f"{anterior}\n[{marca}] {extra}".strip()
    if texto_tem_data(novo[:40]):
        return novo
    return f"[{marca}] {novo}"
