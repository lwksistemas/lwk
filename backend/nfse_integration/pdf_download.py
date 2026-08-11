"""Resolucao de download de PDF/URL da NFS-e."""
from dataclasses import dataclass
from typing import Any, Literal

from .danfe import (
    buscar_url_danfe_issnet,
    buscar_url_danfe_issnet_superadmin,
    obter_url_visualizacao_nfse_loja,
    url_danfe_valida,
)


@dataclass(frozen=True)
class ResultadoDownloadPdf:
    tipo: Literal["url", "pdf"]
    url: str = ""
    conteudo_pdf: bytes = b""
    nome_arquivo: str = ""
    content_disposition: str = "attachment"


def resolver_download_pdf_loja(nfse: Any, loja: Any, loja_id: int) -> ResultadoDownloadPdf:
    """CRM/loja: URL oficial da DANFE (portal).

    Para ISSNet (padrão Nacional) o PDF interno NÃO é a nota fiscal real —
    só redireciona ao link do portal (Nota_Digital_Nacional.aspx). Sem o link,
    o chamador deve orientar a colar a URL do e-mail do ISSNet.
    """
    url_oficial = obter_url_visualizacao_nfse_loja(nfse, loja, loja_id)
    if url_danfe_valida(url_oficial) and _url_parece_portal_oficial(url_oficial):
        return ResultadoDownloadPdf(tipo="url", url=url_oficial)

    if url_danfe_valida(getattr(nfse, "pdf_url", None)) and _url_parece_portal_oficial(nfse.pdf_url):
        return ResultadoDownloadPdf(tipo="url", url=nfse.pdf_url)

    url_danfe = buscar_url_danfe_issnet(nfse, loja_id=loja_id, loja=loja)
    if url_danfe and _url_parece_portal_oficial(url_danfe):
        return ResultadoDownloadPdf(tipo="url", url=url_danfe)

    provedor = (getattr(nfse, "provedor", "") or "").strip().lower()
    if provedor == "issnet":
        # Não servir PDF interno — evita confundir com a DANFE do portal.
        return ResultadoDownloadPdf(tipo="url", url="")

    from .pdf_nfse import gerar_pdf_nfse

    pdf_buffer = gerar_pdf_nfse(nfse, loja)
    pdf_buffer.seek(0)
    nome = f"nfse_{nfse.numero_nf or nfse.id}.pdf"
    return ResultadoDownloadPdf(
        tipo="pdf",
        conteudo_pdf=pdf_buffer.read(),
        nome_arquivo=nome,
        content_disposition="inline",
    )


def _url_parece_portal_oficial(url: str | None) -> bool:
    u = (url or "").lower()
    if not u.startswith("http"):
        return False
    return any(
        marker in u
        for marker in (
            "notaeletronica.com.br",
            "nota_digital",
            "issnetonline.com.br",
            "nfse.gov.br",
            "asaas.com",
        )
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
