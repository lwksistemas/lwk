"""Utilitários para padronização de CPF e CNPJ.
Formata CPF no padrão XXX.XXX.XXX-XX e CNPJ no padrão XX.XXX.XXX/XXXX-XX.
"""
import re


def limpar_cpf(cpf):
    """Remove todos os caracteres não numéricos do CPF."""
    if not cpf:
        return ""
    return re.sub(r"\D", "", str(cpf))


def formatar_cpf(cpf):
    """Formata CPF no padrão XXX.XXX.XXX-XX quando tiver 11 dígitos.
    Se não tiver 11 dígitos (incompleto/inválido), retorna apenas os números.

    Exemplos:
        >>> formatar_cpf("12345678900")
        "123.456.789-00"
        >>> formatar_cpf("123.456.789-00")
        "123.456.789-00"
    """
    if not cpf:
        return ""
    numeros = limpar_cpf(cpf)
    if not numeros:
        return ""
    if len(numeros) == 11:
        return f"{numeros[:3]}.{numeros[3:6]}.{numeros[6:9]}-{numeros[9:]}"
    return numeros


def formatar_cnpj(cnpj):
    """Formata CNPJ no padrão XX.XXX.XXX/XXXX-XX quando tiver 14 dígitos.

    Exemplos:
        >>> formatar_cnpj("12345678000199")
        "12.345.678/0001-99"
    """
    if not cnpj:
        return ""
    numeros = re.sub(r"\D", "", str(cnpj))
    if not numeros:
        return ""
    if len(numeros) == 14:
        return f"{numeros[:2]}.{numeros[2:5]}.{numeros[5:8]}/{numeros[8:12]}-{numeros[12:]}"
    return numeros


def normalizar_cpf_cnpj(valor):
    """Normaliza CPF ou CNPJ: detecta pelo número de dígitos e formata.
    - 11 dígitos → CPF: XXX.XXX.XXX-XX
    - 14 dígitos → CNPJ: XX.XXX.XXX/XXXX-XX
    - Outros → retorna apenas dígitos

    Exemplos:
        >>> normalizar_cpf_cnpj("12345678900")
        "123.456.789-00"
        >>> normalizar_cpf_cnpj("12345678000199")
        "12.345.678/0001-99"
    """
    if not valor:
        return ""
    numeros = re.sub(r"\D", "", str(valor))
    if not numeros:
        return ""
    if len(numeros) == 11:
        return formatar_cpf(numeros)
    if len(numeros) == 14:
        return formatar_cnpj(numeros)
    return numeros


def normalizar_cpf(cpf):
    """Normaliza CPF: limpa e formata. Função principal para usar nos serializers."""
    if not cpf:
        return ""
    return formatar_cpf(cpf)


def somente_digitos_documento(valor) -> str:
    """Retorna apenas dígitos de CPF, CNPJ ou documento genérico."""
    if not valor:
        return ""
    return re.sub(r"\D", "", str(valor))


def eh_cpf(valor) -> bool:
    """True se o documento tiver exatamente 11 dígitos (CPF)."""
    return len(somente_digitos_documento(valor)) == 11


def eh_cnpj(valor) -> bool:
    """True se o documento tiver exatamente 14 dígitos (CNPJ)."""
    return len(somente_digitos_documento(valor)) == 14


def label_empresa_lead(cpf_cnpj, empresa=None, conta_nome=None) -> str | None:
    """Rótulo da coluna Empresa em oportunidades/leads.
    CPF → PESSOA FISICA; CNPJ → empresa do lead ou conta vinculada.
    """
    if eh_cpf(cpf_cnpj):
        return "PESSOA FISICA"
    empresa_txt = (empresa or "").strip()
    if empresa_txt:
        return empresa_txt
    conta_txt = (conta_nome or "").strip()
    if conta_txt:
        return conta_txt
    return None


def documento_preenchido(valor, min_digitos: int = 11) -> bool:
    """True se o documento tem dígitos suficientes para validar unicidade."""
    return len(somente_digitos_documento(valor)) >= min_digitos


def label_documento_campo(field_name: str) -> str:
    """Rótulo amigável para mensagens de erro."""
    return {
        "cpf": "CPF",
        "cnpj": "CNPJ",
        "cpf_cnpj": "CPF/CNPJ",
        "documento": "documento",
    }.get(field_name, field_name.upper())


def existe_documento_duplicado(
    *,
    model,
    field_name: str,
    value: str,
    loja_id=None,
    exclude_pk=None,
    escopo_global: bool = False,
    apenas_ativos: bool = False,
) -> bool:
    """Verifica duplicata comparando somente dígitos (ignora máscara).
    Por padrão escopo por loja_id; escopo_global=True para tabelas globais (ex.: Loja).
    """
    digits = somente_digitos_documento(value)
    if len(digits) < 11:
        return False

    qs = model.objects.all()
    if not escopo_global:
        if loja_id is None:
            return False
        if hasattr(model, "loja_id"):
            qs = qs.filter(loja_id=loja_id)

    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    if apenas_ativos and hasattr(model, "is_active"):
        qs = qs.filter(is_active=True)

    return any(somente_digitos_documento(stored) == digits for _pk, stored in qs.values_list("pk", field_name))


def mensagem_documento_duplicado(
    field_name: str,
    *,
    escopo_global: bool = False,
    entidade: str = "cadastro",
) -> str:
    """Mensagem padrão em português para documento já cadastrado."""
    label = label_documento_campo(field_name)
    if escopo_global and field_name in ("cpf_cnpj", "cpf", "cnpj"):
        if entidade == "usuário":
            return "Já existe um usuário cadastrado com este CPF."
        return f"Já existe uma loja cadastrada com este {label}."
    if field_name == "cnpj" and entidade == "empresa":
        return "Já existe uma empresa cadastrada com este CNPJ nesta loja."
    if field_name == "cnpj" and entidade == "fornecedor":
        return "Já existe um fornecedor cadastrado com este CNPJ nesta loja."
    if field_name == "cpf" and entidade in ("paciente", "cliente"):
        return f"Já existe um {entidade} cadastrado com este CPF nesta loja."
    if field_name == "cpf_cnpj":
        return f"Já existe um {entidade} cadastrado com este CPF/CNPJ nesta loja."
    return f"Já existe um {entidade} com este {label} nesta loja."
