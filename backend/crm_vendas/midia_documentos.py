"""Arquiva a proposta ou o contrato assinado no servidor de mídia da loja.

Pastas, dentro do CPF/CNPJ da loja:
- documentos/{cpf ou cnpj do cliente}/
- prestadoras/{cnpj da prestadora}/
"""
import logging
import re

logger = logging.getLogger(__name__)


def _digitos(valor) -> str:
    return re.sub(r"\D", "", str(valor or ""))


def documento_do_cliente(documento) -> str:
    """CNPJ da conta, quando a venda é de empresa. Senão, o CPF ou CNPJ do lead."""
    oportunidade = getattr(documento, "oportunidade", None)
    lead = getattr(oportunidade, "lead", None)
    conta = getattr(lead, "conta", None)
    cnpj = _digitos(getattr(conta, "cnpj", ""))
    if len(cnpj) == 14:
        return cnpj
    pessoa = _digitos(getattr(lead, "cpf_cnpj", ""))
    if len(pessoa) in (11, 14):
        return pessoa
    return ""


def cnpj_da_prestadora(documento) -> str:
    oportunidade = getattr(documento, "oportunidade", None)
    prestadora = getattr(oportunidade, "empresa_prestadora", None)
    cnpj = _digitos(getattr(prestadora, "cnpj", ""))
    return cnpj if len(cnpj) == 14 else ""


def arquivar_pdf_assinado(documento, pdf_bytes: bytes, filename: str) -> None:
    """Guarda o PDF assinado. Falha de mídia não desfaz o envio ao cliente."""
    if not pdf_bytes:
        return
    loja_id = getattr(documento, "loja_id", None)
    if not loja_id:
        return
    from core.media_pdf import pasta_por_documento, salvar_pdf_pasta

    cliente = documento_do_cliente(documento)
    pasta_cliente = pasta_por_documento("documentos", cliente) or "documentos/sem-documento"
    salvar_pdf_pasta(int(loja_id), pasta_cliente, pdf_bytes, filename)

    prestadora = cnpj_da_prestadora(documento)
    pasta_prestadora = pasta_por_documento("prestadoras", prestadora)
    if pasta_prestadora:
        salvar_pdf_pasta(int(loja_id), pasta_prestadora, pdf_bytes, filename)
