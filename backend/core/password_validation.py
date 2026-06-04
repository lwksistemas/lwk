"""
Política mínima de senha (troca de senha / primeiro acesso).
"""
from __future__ import annotations

import re

MIN_LENGTH = 8


def validate_password_policy(password: str) -> tuple[bool, str]:
    """
    Requisitos: 8+ caracteres, pelo menos uma letra e um número.
    """
    if not password or len(password) < MIN_LENGTH:
        return False, f'A senha deve ter no mínimo {MIN_LENGTH} caracteres.'
    if not re.search(r'[A-Za-z]', password):
        return False, 'A senha deve conter pelo menos uma letra.'
    if not re.search(r'\d', password):
        return False, 'A senha deve conter pelo menos um número.'
    return True, ''
