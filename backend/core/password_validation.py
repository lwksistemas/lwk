"""
Política de senha (troca de senha / primeiro acesso).

Requisitos:
- Mínimo 10 caracteres
- Pelo menos uma letra maiúscula
- Pelo menos uma letra minúscula
- Pelo menos um número
- Pelo menos um caractere especial (!@#$%^&*()_+-=[]{}|;':\",./<>?)
"""
from __future__ import annotations

import re

MIN_LENGTH = 10

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
    if not re.search(r'[A-Z]', password):
        return False, 'A senha deve conter pelo menos uma letra maiúscula.'
    if not re.search(r'[a-z]', password):
        return False, 'A senha deve conter pelo menos uma letra minúscula.'
    if not re.search(r'\d', password):
        return False, 'A senha deve conter pelo menos um número.'
    if not _SPECIAL_RE.search(password):
        return False, 'A senha deve conter pelo menos um caractere especial (ex: !@#$%).'
    return True, ''


def password_policy_description() -> str:
    """Retorna descrição legível da política para exibir no frontend."""
    return (
        f'A senha deve ter no mínimo {MIN_LENGTH} caracteres, '
        'incluindo letra maiúscula, letra minúscula, número e caractere especial (ex: !@#$%).'
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
            {'id': 'uppercase',    'texto': 'Pelo menos uma letra maiúscula (A-Z)'},
            {'id': 'lowercase',    'texto': 'Pelo menos uma letra minúscula (a-z)'},
            {'id': 'number',       'texto': 'Pelo menos um número (0-9)'},
            {'id': 'special_char', 'texto': 'Pelo menos um caractere especial (ex: !@#$%^&*)'},
        ],
        'exemplos_validos': [
            'Minha@Senha1',
            'Acesso#2024!',
            'LWK$istema9',
        ],
    }
