"""Cabeçalho da loja no comprovante."""
import re

from core.cpf_utils import eh_cnpj, eh_cpf, normalizar_cpf_cnpj
from core.phone_utils import telefone_exibicao_brasileiro

from .cores_recibo import cor_primaria_recibo
def _label_documento_loja(cpf_cnpj: str) -> str:
    """Rótulo CPF ou CNPJ conforme quantidade de dígitos."""
    if eh_cpf(cpf_cnpj):
        return "CPF"
    if eh_cnpj(cpf_cnpj):
        return "CNPJ"
    return "CPF/CNPJ"


def _dados_loja_recibo(loja):
    from superadmin.loja_utils import contato_publico_loja

    doc_raw = (getattr(loja, "cpf_cnpj", "") or "") if loja else ""
    cep_raw = (getattr(loja, "cep", "") or "") if loja else ""
    tel_raw, email_raw = contato_publico_loja(loja)
    loja_telefone = telefone_exibicao_brasileiro(tel_raw)
    loja_cep = _formatar_cep(cep_raw)
    logo_url = _texto_config_loja(loja, "recibo_logo")
    cor = _texto_config_loja(loja, "recibo_cor") or _texto_config_loja(loja, "cor_primaria")
    return {
        "loja_nome": getattr(loja, "nome", "") if loja else "",
        "loja_documento": normalizar_cpf_cnpj(doc_raw),
        "loja_documento_label": _label_documento_loja(doc_raw),
        "loja_cnpj": normalizar_cpf_cnpj(doc_raw),
        "loja_endereco": _formatar_endereco_loja(loja) if loja else "",
        "loja_telefone": loja_telefone,
        "loja_cep": loja_cep,
        "loja_email": email_raw,
        "loja_tel_cep": _linha_tel_cep(loja_telefone, loja_cep),
        "logo_url": logo_url,
        "cor_primaria": cor_primaria_recibo(cor),
    }


def _texto_config_loja(loja, campo: str) -> str:
    """Só texto real. Objeto simulado de teste não vira logomarca."""
    valor = getattr(loja, campo, "") if loja is not None else ""
    if not isinstance(valor, str):
        return ""
    return valor.strip()


def _formatar_cep(cep: str) -> str:
    """Formata CEP no padrão XXXXX-XXX."""
    if not cep:
        return ""
    d = re.sub(r"\D", "", str(cep))
    if len(d) == 8:
        return f"{d[:5]}-{d[5:]}"
    return str(cep).strip()


def _formatar_endereco_loja(loja, *, incluir_cep: bool = False) -> str:
    """Monta endereço da loja (sem CEP por padrão — CEP vai com o telefone)."""
    partes = []
    if getattr(loja, "logradouro", ""):
        end = loja.logradouro
        if getattr(loja, "numero", ""):
            end += f", {loja.numero}"
        partes.append(end)
    if getattr(loja, "bairro", ""):
        partes.append(loja.bairro)
    if getattr(loja, "cidade", ""):
        cidade = loja.cidade
        if getattr(loja, "uf", ""):
            cidade += f" - {loja.uf}"
        partes.append(cidade)
    if incluir_cep and getattr(loja, "cep", ""):
        partes.append(f"CEP {_formatar_cep(loja.cep)}")
    return ", ".join(partes)


def _linha_tel_cep(telefone: str = "", cep: str = "") -> str:
    """Telefone e CEP na mesma linha do cabeçalho do recibo."""
    partes = []
    if telefone:
        partes.append(f"Tel: {telefone}")
    if cep:
        partes.append(f"CEP {cep}")
    return "  ·  ".join(partes)


def _linha_documento_loja(ctx: dict) -> str:
    doc = ctx.get("loja_documento") or ctx.get("loja_cnpj") or ""
    if not doc:
        return ""
    label = ctx.get("loja_documento_label") or _label_documento_loja(doc)
    return f"{label}: {doc}"
