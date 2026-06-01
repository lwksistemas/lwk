"""
Utilitários para padronização de CPF.
Formata CPF no padrão XXX.XXX.XXX-XX.
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


def normalizar_cpf(cpf):
    """Normaliza CPF: limpa e formata. Função principal para usar nos serializers."""
    if not cpf:
        return ""
    return formatar_cpf(cpf)
