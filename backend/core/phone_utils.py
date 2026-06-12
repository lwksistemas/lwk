"""
Utilitários para padronização de telefones
Formata telefones brasileiros no padrão (XX) XXXXX-XXXX ou (XX) XXXX-XXXX
"""
import re


def limpar_telefone(telefone):
    """
    Remove todos os caracteres não numéricos do telefone
    
    Args:
        telefone (str): Telefone com ou sem formatação
    
    Returns:
        str: Apenas números
    
    Exemplos:
        >>> limpar_telefone("(11) 98765-4321")
        "11987654321"
        >>> limpar_telefone("11 9 8765-4321")
        "11987654321"
    """
    if not telefone:
        return ""
    return re.sub(r'\D', '', str(telefone))


def formatar_telefone_brasileiro(telefone):
    """
    Formata telefone no padrão brasileiro
    
    Formatos suportados:
    - Celular com DDD: (XX) XXXXX-XXXX (11 dígitos)
    - Fixo com DDD: (XX) XXXX-XXXX (10 dígitos)
    - Celular sem DDD: XXXXX-XXXX (9 dígitos)
    - Fixo sem DDD: XXXX-XXXX (8 dígitos)
    - Outros: retorna como está
    
    Args:
        telefone (str): Telefone com ou sem formatação
    
    Returns:
        str: Telefone formatado ou original se não for padrão brasileiro
    
    Exemplos:
        >>> formatar_telefone_brasileiro("11987654321")
        "(11) 98765-4321"
        >>> formatar_telefone_brasileiro("1133334444")
        "(11) 3333-4444"
        >>> formatar_telefone_brasileiro("987654321")
        "98765-4321"
        >>> formatar_telefone_brasileiro("33334444")
        "3333-4444"
    """
    if not telefone:
        return ""
    
    # Limpar telefone (apenas números)
    numeros = limpar_telefone(telefone)
    
    # Se não tiver números, retornar vazio
    if not numeros:
        return ""
    
    # Celular com DDD (11 dígitos): (XX) XXXXX-XXXX
    if len(numeros) == 11:
        return f"({numeros[:2]}) {numeros[2:7]}-{numeros[7:]}"
    
    # Fixo com DDD (10 dígitos): (XX) XXXX-XXXX
    elif len(numeros) == 10:
        return f"({numeros[:2]}) {numeros[2:6]}-{numeros[6:]}"
    
    # Celular sem DDD (9 dígitos): XXXXX-XXXX
    elif len(numeros) == 9:
        return f"{numeros[:5]}-{numeros[5:]}"
    
    # Fixo sem DDD (8 dígitos): XXXX-XXXX
    elif len(numeros) == 8:
        return f"{numeros[:4]}-{numeros[4:]}"
    
    # Outros casos: retornar apenas números
    # (pode ser telefone internacional, número incompleto, etc)
    return numeros


def telefone_internacional_br(telefone):
    """
    Normaliza telefone brasileiro com código do país (55) — apenas dígitos.
    Usado no cadastro de pacientes para envio WhatsApp (Evolution/Meta).
    """
    if not telefone:
        return ''

    digits = limpar_telefone(telefone)
    if not digits:
        return ''

    if len(digits) >= 12 and digits.startswith('55'):
        out = digits[:15]
        if out.startswith('55') and len(out) > 12 and out[2] == '0':
            out = '55' + out[3:].lstrip('0')
        return out

    if len(digits) == 11 and not digits.startswith('1'):
        return '55' + digits.lstrip('0')

    if len(digits) == 11:
        ddd = int(digits[:2])
        if 11 <= ddd <= 99 and digits[2] == '9':
            return '55' + digits

    if len(digits) == 10:
        return '55' + digits.lstrip('0')

    return digits[:15]


def telefone_exibicao_brasileiro(telefone):
    """Exibe telefone armazenado com 55 no formato (DD) XXXXX-XXXX."""
    if not telefone:
        return ''

    digits = limpar_telefone(telefone)
    if digits.startswith('55') and len(digits) >= 12:
        local = digits[2:].lstrip('0')
        if len(local) >= 8:
            return formatar_telefone_brasileiro(local)

    return formatar_telefone_brasileiro(telefone)


def validar_telefone_brasileiro(telefone):
    """
    Valida se telefone está no formato brasileiro válido
    
    Args:
        telefone (str): Telefone a validar
    
    Returns:
        tuple: (bool, str) - (é_válido, mensagem_erro)
    
    Exemplos:
        >>> validar_telefone_brasileiro("(11) 98765-4321")
        (True, "")
        >>> validar_telefone_brasileiro("123")
        (False, "Telefone deve ter 8, 9, 10 ou 11 dígitos")
    """
    if not telefone:
        return True, ""  # Telefone vazio é válido (campo opcional)
    
    numeros = limpar_telefone(telefone)
    
    # Verificar quantidade de dígitos
    if len(numeros) not in [8, 9, 10, 11]:
        return False, "Telefone deve ter 8, 9, 10 ou 11 dígitos"
    
    # Validar DDD (se tiver)
    if len(numeros) >= 10:
        ddd = int(numeros[:2])
        # DDDs válidos no Brasil: 11-99
        if ddd < 11 or ddd > 99:
            return False, "DDD inválido (deve ser entre 11 e 99)"
    
    # Validar celular (9 dígitos ou 11 com DDD)
    if len(numeros) in [9, 11]:
        primeiro_digito = numeros[-9]  # Primeiro dígito do número (após DDD)
        if primeiro_digito != '9':
            return False, "Celular deve começar com 9"
    
    return True, ""


def normalizar_telefone(telefone):
    """
    Normaliza telefone: limpa e formata
    Função principal para usar nos serializers
    
    Args:
        telefone (str): Telefone em qualquer formato
    
    Returns:
        str: Telefone formatado ou vazio
    
    Exemplos:
        >>> normalizar_telefone("11 9 8765-4321")
        "(11) 98765-4321"
        >>> normalizar_telefone("")
        ""
        >>> normalizar_telefone(None)
        ""
    """
    if not telefone:
        return ""
    
    return formatar_telefone_brasileiro(telefone)
