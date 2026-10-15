"""PDF do boleto em aberto, com o nome da assinatura."""
from superadmin.boleto_email import baixar_pdf_boleto, nome_arquivo_boleto_assinatura
from superadmin.financeiro_views.troca_banco import boleto_em_aberto


def pdf_boleto_em_aberto(financeiro) -> tuple[bytes, str, str]:
    """Devolve o PDF, o nome do arquivo e uma mensagem de erro."""
    loja = financeiro.loja
    aberto = boleto_em_aberto(loja)
    if not aberto:
        return b"", "", "Não há boleto em aberto para baixar."
    url = (aberto.boleto_url or "").strip() or (financeiro.boleto_url or "").strip()

    vencimento = getattr(aberto, "data_vencimento", None) or financeiro.data_proxima_cobranca
    provedor = (
        getattr(aberto, "provedor_boleto", None)
        or financeiro.provedor_boleto
        or "asaas"
    )
    payment_id = (getattr(aberto, "asaas_payment_id", None) or "").strip()
    if not payment_id:
        payment_id = (financeiro.asaas_payment_id or "").strip()

    pdf = baixar_pdf_boleto(url) if url else b""
    if not pdf and provedor == "asaas" and payment_id:
        from superadmin.asaas_service import LojaAsaasService

        pdf = LojaAsaasService().baixar_pdf_boleto(payment_id) or b""
    if not pdf:
        return b"", "", "Não foi possível baixar o PDF do boleto."
    return pdf, nome_arquivo_boleto_assinatura(getattr(loja, "cpf_cnpj", ""), vencimento), ""
