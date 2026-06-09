"""
Utilitários para padronização de CPF e CNPJ.
Formata CPF no padrão XXX.XXX.XXX-XX e CNPJ no padrão XX.XXX.XXX/XXXX-XX.
"""
import re


def limpar_cpf(cpf):
    """Remove todos os caracteres não numéricos do CPF."""
    if not cpf:
        return ""
    return re.sub(r'\D', '', str(cpf))


def formatar_cpf(cpf):
    """
    Formata CPF no padrão XXX.XXX.XXX-XX quando tiver 11 dígitos.
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
    """
    Formata CNPJ no padrão XX.XXX.XXX/XXXX-XX quando tiver 14 dígitos.

    Exemplos:
        >>> formatar_cnpj("12345678000199")
        "12.345.678/0001-99"
    """
    if not cnpj:
        return ""
    numeros = re.sub(r'\D', '', str(cnpj))
    if not numeros:
        return ""
    if len(numeros) == 14:
        return f"{numeros[:2]}.{numeros[2:5]}.{numeros[5:8]}/{numeros[8:12]}-{numeros[12:]}"
    return numeros


def normalizar_cpf_cnpj(valor):
    """
    Normaliza CPF ou CNPJ: detecta pelo número de dígitos e formata.
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
    numeros = re.sub(r'\D', '', str(valor))
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
