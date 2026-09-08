"""Finalização de PDF: aplica papel timbrado de fundo quando configurado.

Extrai o passo repetido em vários geradores de PDF da clínica
(comissões, repasse, prontuário): pegar os bytes do buffer já construído e,
se o cabeçalho resolvido for do tipo "timbrado", mesclar o PDF de fundo.
"""
from io import BytesIO

from .timbrado import merge_timbrado_fundo


def finalize_pdf_com_timbrado(buffer: BytesIO, tipo_cab: str, dados_cab) -> BytesIO:
    """Retorna um BytesIO pronto a partir de um buffer de PDF já construído.

    Args:
        buffer: BytesIO onde o ``SimpleDocTemplate.build()`` já escreveu o PDF.
        tipo_cab: tipo de cabeçalho resolvido ("timbrado", "logo" ou "texto").
        dados_cab: quando ``tipo_cab == "timbrado"``, os bytes do PDF timbrado.

    Se o cabeçalho for "timbrado", mescla o fundo; caso contrário devolve o
    conteúdo original. Sempre retorna um BytesIO posicionado no início.
    """
    pdf_bytes = buffer.getvalue()
    if tipo_cab == "timbrado":
        pdf_bytes = merge_timbrado_fundo(pdf_bytes, dados_cab)
    out = BytesIO(pdf_bytes)
    out.seek(0)
    return out
