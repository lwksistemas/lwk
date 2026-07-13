"""Resolucao de download de PDF/URL da NFS-e."""
from dataclasses import dataclass
from typing import Any, Literal

from .danfe import buscar_url_danfe_issnet, buscar_url_danfe_issnet_superadmin, url_danfe_valida


@dataclass(frozen=True)
class ResultadoDownloadPdf:
    tipo: Literal["url", "pdf"]
    url: str = ""
    conteudo_pdf: bytes = b""
    nome_arquivo: str = ""
    content_disposition: str = "attachment"


def resolver_download_pdf_loja(nfse: Any, loja: Any, loja_id: int) -> ResultadoDownloadPdf:
    """CRM/loja: URL oficial da DANFE ou PDF interno."""
    if url_danfe_valida(nfse.pdf_url):
        return ResultadoDownloadPdf(tipo="url", url=nfse.pdf_url)

    url_danfe = buscar_url_danfe_issnet(nfse, loja_id=loja_id, loja=loja)
    if url_danfe:
        return ResultadoDownloadPdf(tipo="url", url=url_danfe)

    from .pdf_nfse import gerar_pdf_nfse

    pdf_buffer = gerar_pdf_nfse(nfse, loja)
    pdf_buffer.seek(0)
    nome = f"nfse_{nfse.numero_nf or nfse.id}.pdf"
    return ResultadoDownloadPdf(
        tipo="pdf",
        conteudo_pdf=pdf_buffer.read(),
        nome_arquivo=nome,
        content_disposition="attachment",
    )


def resolver_download_pdf_superadmin(nfse_emitida: Any) -> ResultadoDownloadPdf:
    """Superadmin: Asaas URL, ISSNet ConsultarUrlNfse ou PDF interno."""
    if nfse_emitida.pdf_url and nfse_emitida.provedor == "asaas":
        return ResultadoDownloadPdf(tipo="url", url=nfse_emitida.pdf_url)

    if url_danfe_valida(nfse_emitida.pdf_url):
        return ResultadoDownloadPdf(tipo="url", url=nfse_emitida.pdf_url)

    if nfse_emitida.provedor == "issnet" and nfse_emitida.numero_nf:
        url_danfe = buscar_url_danfe_issnet_superadmin(nfse_emitida)
        if url_danfe:
            return ResultadoDownloadPdf(tipo="url", url=url_danfe)

    from .pdf_nfse import gerar_pdf_nfse

    loja = nfse_emitida.loja
    pdf_buffer = gerar_pdf_nfse(nfse_emitida, loja)
    pdf_buffer.seek(0)
    nome = f"nfse_{nfse_emitida.numero_nf or nfse_emitida.id}.pdf"
    return ResultadoDownloadPdf(
        tipo="pdf",
        conteudo_pdf=pdf_buffer.read(),
        nome_arquivo=nome,
        content_disposition="inline",
    )
