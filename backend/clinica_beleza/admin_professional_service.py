"""
Service layer para habilitar/desabilitar o administrador (owner) como Profissional.

Permite que o owner da loja se registre como profissional para atender
clientes e aparecer na agenda, usando soft-delete (is_active) para preservar histórico.
"""
import logging

from .models import Professional

logger = logging.getLogger(__name__)


def habilitar_admin_como_profissional(loja_id: int, user) -> Professional:
    """
    Cria ou reativa o registro Professional vinculado ao owner.

    - Se já existe com is_active=False → reativa (is_active=True)
    - Se já existe com is_active=True → retorna (idempotente)
    - Se não existe → cria com nome/email do user

    Args:
        loja_id: ID da loja (schema) do administrador.
        user: Instância do User (owner da loja).

    Returns:
        Professional: Instância do profissional criado ou reativado.
    """
    try:
        professional = Professional.objects.get(email=user.email, loja_id=loja_id)
        if not professional.is_active:
            professional.is_active = True
            professional.save(update_fields=['is_active', 'updated_at'])
            logger.info(
                "Profissional do admin reativado: loja_id=%s, email=%s",
                loja_id, user.email,
            )
        return professional
    except Professional.DoesNotExist:
        nome = user.first_name or user.username
        professional = Professional.objects.create(
            nome=nome,
            email=user.email,
            telefone='',
            especialidade='Administrador',
            is_active=True,
            loja_id=loja_id,
        )
        logger.info(
            "Profissional do admin criado: loja_id=%s, email=%s, nome=%s",
            loja_id, user.email, nome,
        )
        return professional


def desabilitar_admin_como_profissional(loja_id: int, user) -> None:
    """
    Desativa o Professional do owner (is_active=False).
    Não remove o registro do banco (soft-delete).

    Idempotente: se não existe ou já está inativo, não faz nada.

    Args:
        loja_id: ID da loja (schema) do administrador.
        user: Instância do User (owner da loja).
    """
    try:
        professional = Professional.objects.get(email=user.email, loja_id=loja_id)
        if professional.is_active:
            professional.is_active = False
            professional.save(update_fields=['is_active', 'updated_at'])
            logger.info(
                "Profissional do admin desativado: loja_id=%s, email=%s",
                loja_id, user.email,
            )
    except Professional.DoesNotExist:
        pass


def obter_status_admin_profissional(loja_id: int, user) -> dict:
    """
    Retorna o status do vínculo admin-profissional.

    Args:
        loja_id: ID da loja (schema) do administrador.
        user: Instância do User (owner da loja).

    Returns:
        dict: { "is_enabled": bool, "professional_id": int | None }
    """
    try:
        professional = Professional.objects.get(email=user.email, loja_id=loja_id)
        return {
            "is_enabled": professional.is_active,
            "professional_id": professional.id,
        }
    except Professional.DoesNotExist:
        return {
            "is_enabled": False,
            "professional_id": None,
        }
