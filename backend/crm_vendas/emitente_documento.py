"""Resolve dados do emitente (Dados da Loja) em proposta/contrato."""


def documento_tem_emitente_personalizado(documento) -> bool:
    nome = (getattr(documento, "emitente_nome", "") or "").strip()
    return bool(nome)


def obter_dados_emitente_documento(documento) -> dict:
    """Retorna dict no formato de _obter_dados_loja.
    Se o documento tiver emitente personalizado, usa snapshot gravado; senão, dados da loja.
    """
    if documento_tem_emitente_personalizado(documento):
        endereco = (getattr(documento, "emitente_endereco", "") or "").strip() or None
        cpf_cnpj = (getattr(documento, "emitente_cpf_cnpj", "") or "").strip() or None
        responsavel = (getattr(documento, "emitente_responsavel", "") or "").strip() or None
        email = (getattr(documento, "emitente_email", "") or "").strip() or None
        return {
            "nome": (getattr(documento, "emitente_nome", "") or "").strip(),
            "endereco": endereco,
            "cpf_cnpj": cpf_cnpj,
            "telefone": None,
            "admin_nome": responsavel,
            "admin_email": email,
            "logo": None,
        }
    loja_id = getattr(documento, "loja_id", None)
    if not loja_id:
        return {}
    from .pdf_proposta_contrato.formatters import _obter_dados_loja

    data = _obter_dados_loja(loja_id)
    data.setdefault("logo", data.get("logo"))
    return data


def limpar_emitente_se_vazio(validated_data: dict) -> dict:
    """Remove snapshot quando emitente_nome vier vazio (volta ao padrão da loja)."""
    nome = (validated_data.get("emitente_nome") or "").strip()
    if not nome:
        validated_data["emitente_nome"] = ""
        validated_data["emitente_endereco"] = ""
        validated_data["emitente_cpf_cnpj"] = ""
        validated_data["emitente_responsavel"] = ""
        validated_data["emitente_email"] = ""
    return validated_data
