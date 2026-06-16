"""
Política de senha (troca de senha / primeiro acesso).

Requisitos:
- Mínimo 6 caracteres
- Pelo menos uma letra (maiúscula ou minúscula)
- Pelo menos um número
- Pelo menos um caractere especial (!@#$%^&*()_+-=[]{}|;':\",./<>?)
"""
from __future__ import annotations

import re

MIN_LENGTH = 6

# Caracteres especiais aceitos
_SPECIAL_CHARS = r'!@#$%^&*()\-_=+\[\]{}|;:\'",.<>/?\\`~'
_SPECIAL_RE = re.compile(rf'[{_SPECIAL_CHARS}]')


def validate_password_policy(password: str) -> tuple[bool, str]:
    """
    Valida política de senha para o sistema LWK.

    Retorna (True, '') se válida, ou (False, mensagem_erro) se inválida.
    """
    if not password or len(password) < MIN_LENGTH:
        return False, f'A senha deve ter no mínimo {MIN_LENGTH} caracteres.'
    if not re.search(r'[A-Za-z]', password):
        return False, 'A senha deve conter pelo menos uma letra.'
    if not re.search(r'\d', password):
        return False, 'A senha deve conter pelo menos um número.'
    if not _SPECIAL_RE.search(password):
        return False, 'A senha deve conter pelo menos um caractere especial (ex: !@#$%).'
    return True, ''


def password_policy_description() -> str:
    """Retorna descrição legível da política para exibir no frontend."""
    return (
        f'A senha deve ter no mínimo {MIN_LENGTH} caracteres, '
        'incluindo letra, número e caractere especial (ex: !@#$%).'
    )


def password_policy_requirements() -> dict:
    """
    Retorna os requisitos da política em formato estruturado para o frontend.

    Exemplo de uso na view:
        from core.password_validation import password_policy_requirements
        return Response({
            'error': msg,
            'requisitos_senha': password_policy_requirements(),
        }, status=400)
    """
    return {
        'descricao': password_policy_description(),
        'regras': [
            {'id': 'min_length',   'texto': f'No mínimo {MIN_LENGTH} caracteres'},
            {'id': 'letter',       'texto': 'Pelo menos uma letra (A-Z ou a-z)'},
            {'id': 'number',       'texto': 'Pelo menos um número (0-9)'},
            {'id': 'special_char', 'texto': 'Pelo menos um caractere especial (ex: !@#$%^&*)'},
        ],
        'exemplos_validos': [
            'Abc@12',
            'Lwk#99',
            'Sal!34',
        ],
    }


def generate_provisional_password(length: int = 6) -> str:
    """
    Gera senha provisória que sempre atende à política (letra + número + especial).

    A senha gerada é fácil de digitar: 3 letras + 2 números + 1 especial,
    embaralhados aleatoriamente.

    Uso:
        from core.password_validation import generate_provisional_password
        nova_senha = generate_provisional_password()
    """
    import random
    import string

    specials = '!@#$%'

    # Garantir pelo menos 1 de cada tipo
    chars = [
        random.choice(string.ascii_uppercase),    # 1 maiúscula
        random.choice(string.ascii_lowercase),    # 1 minúscula
        random.choice(string.digits),             # 1 número
        random.choice(specials),                  # 1 especial
    ]

    # Preencher o restante com mix de letras e números (fáceis de ler)
    pool = string.ascii_letters + string.digits
    remaining = max(length - len(chars), 2)
    chars.extend(random.choices(pool, k=remaining))

    # Embaralhar para não ter padrão previsível
    random.shuffle(chars)
    return ''.join(chars)
