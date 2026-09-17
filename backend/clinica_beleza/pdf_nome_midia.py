"""Detecta PDF com UUID/nome genérico e infere o nome estável a partir do conteúdo."""
from __future__ import annotations

import re
from io import BytesIO
from pathlib import Path

UUID_PDF_RE = re.compile(r"^[a-f0-9]{32}\.pdf$", re.I)
NOMES_GENERICOS = frozenset({
    "prescricao", "upload", "file", "document", "arquivo", "pdf", "unnamed", "local",
})
_CONSULTA_ID_RE = re.compile(r"Consulta:\s*#(\d+)")
_SECAO_MARCAS = (
    ("Produtos utilizados", "produtos"),
    ("Notas do atendimento", "atendimento"),
    ("Anamnese", "anamnese"),
    ("Evolução", "evolucao"),
    ("Evolucao", "evolucao"),
)


def precisa_renomear_pdf(filename: str) -> bool:
    nome = Path((filename or "").replace("\\", "/")).name
    if not nome.lower().endswith(".pdf"):
        return False
    if UUID_PDF_RE.match(nome):
        return True
    return Path(nome).stem.lower() in NOMES_GENERICOS


def texto_pdf(conteudo: bytes) -> str:
    if not conteudo or conteudo[:4] != b"%PDF":
        return ""
    try:
        from pypdf import PdfReader

        reader = PdfReader(BytesIO(conteudo))
        partes: list[str] = []
        for pagina in reader.pages[:4]:
            partes.append(pagina.extract_text() or "")
        return "\n".join(partes)
    except Exception:
        return ""


def eh_pdf_memed(texto: str) -> bool:
    t = (texto or "").lower()
    return "memed.com.br" in t or "validador.memed" in t


def nome_pdf_consulta_do_texto(texto: str) -> str | None:
    m = _CONSULTA_ID_RE.search(texto or "")
    if not m:
        return None
    secao = "atendimento"
    for marca, chave in _SECAO_MARCAS:
        if marca in (texto or ""):
            secao = chave
            break
    return f"consulta_{m.group(1)}_{secao}.pdf"


def nome_pdf_prontuario_do_texto(texto: str, patient_id: int | None) -> str | None:
    if not patient_id:
        return None
    t = texto or ""
    if "Prontuário Completo" in t or "Prontuario Completo" in t:
        return f"prontuario_completo_{patient_id}.pdf"
    m = re.search(r"prontuario_([a-z_]+)_", t, re.I)
    if m:
        return f"prontuario_{m.group(1)}_{patient_id}.pdf"
    return None


def nome_pdf_recibo_do_texto(texto: str) -> str | None:
    m = re.search(r"Recibo.*?[#nNº°]\s*(\d+)", texto or "", re.I)
    if m:
        return f"recibo_{m.group(1)}.pdf"
    return None


def nome_estavel_do_texto(
    texto: str,
    *,
    patient_id: int | None = None,
    prescricao_ids: list[str] | None = None,
) -> str | None:
    """Nome definitivo a partir do texto. Prescrição Memed só se houver um ID candidato."""
    consulta = nome_pdf_consulta_do_texto(texto)
    if consulta:
        return consulta
    prontuario = nome_pdf_prontuario_do_texto(texto, patient_id)
    if prontuario:
        return prontuario
    recibo = nome_pdf_recibo_do_texto(texto)
    if recibo:
        return recibo
    if eh_pdf_memed(texto):
        ids = [i for i in (prescricao_ids or []) if i]
        if len(ids) == 1:
            return f"prescricao_{ids[0]}.pdf"
    return None
