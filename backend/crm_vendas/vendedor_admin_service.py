"""Lógica de listagem e acesso do vendedor administrador (owner da loja)."""
import logging
from collections.abc import Callable
from typing import Any

from django.conf import settings
from django.utils.crypto import get_random_string
from rest_framework import status
from rest_framework.response import Response

from core.email_delivery import send_system_mail
from tenants.middleware import get_current_tenant_db

logger = logging.getLogger(__name__)


def dict_admin_loja(loja) -> dict[str, Any]:
    owner = loja.owner
    nome = owner.get_full_name() or owner.username or (owner.email or "").split("@")[0]
    return {
        "id": "admin",
        "nome": nome,
        "email": owner.email or "",
        "telefone": getattr(loja, "owner_telefone", "") or "",
        "cargo": "Administrador",
        "is_admin": True,
        "is_active": True,
        "tem_acesso": True,
    }


def sincronizar_vendedor_admin_owner(loja, owner=None) -> bool:
    """Alinha nome/e-mail/telefone do vendedor CRM ao administrador (User owner).
    Evita nome errado na auditoria e na listagem de funcionários.
    """
    from superadmin.models import VendedorUsuario

    from .models import Vendedor

    if owner is None:
        owner = loja.owner
    if not owner or not getattr(loja, "database_name", None) or not loja.database_created:
        return False

    vu = VendedorUsuario.objects.using("default").filter(user=owner, loja_id=loja.id).first()
    if not vu:
        return False

    nome = (owner.get_full_name() or owner.username or (owner.email or "").split("@")[0]).strip()
    if not nome:
        return False

    updated = Vendedor.objects.using(loja.database_name).filter(
        pk=vu.vendedor_id,
        loja_id=loja.id,
    ).update(
        nome=nome,
        email=(owner.email or "").strip(),
        telefone=(getattr(loja, "owner_telefone", "") or "").strip(),
    )
    return updated > 0


def aplicar_cache_control_sem_store(response) -> None:
    from .views_common import aplicar_cache_control_sem_store as _aplicar

    _aplicar(response)


def ajustar_lista_vendedores_com_admin(
    loja,
    loja_id: int,
    results: list[dict],
    *,
    serialize_vendedor: Callable[[Any], dict] | None = None,
) -> list[dict]:
    """Insere admin virtual, filtra duplicatas legacy e recupera lista vazia com VendedorUsuario.
    """
    from superadmin.models import VendedorUsuario

    from .models import Vendedor

    owner_email_lower = (loja.owner.email or "").strip().lower()
    owner_tem_vendedor = VendedorUsuario.objects.using("default").filter(
        user=loja.owner,
        loja_id=loja_id,
    ).exists()

    if owner_email_lower and not owner_tem_vendedor:
        results = [
            r
            for r in results
            if not (
                r.get("is_admin")
                and (r.get("email") or "").strip().lower() == owner_email_lower
            )
        ]

    owner_ja_existe = False
    for row in results:
        if (row.get("email") or "").strip().lower() == owner_email_lower:
            owner_ja_existe = True
            row["is_admin"] = True
            row["cargo"] = "Administrador"
            break

    if not owner_tem_vendedor and not owner_ja_existe:
        results.insert(0, dict_admin_loja(loja))

    if not results and owner_tem_vendedor:
        vu = VendedorUsuario.objects.using("default").filter(
            user=loja.owner,
            loja_id=loja_id,
        ).first()
        recovered = False
        if vu and serialize_vendedor:
            tenant_db = get_current_tenant_db()
            qs = Vendedor.objects.all_without_filter()
            if tenant_db and tenant_db != "default":
                qs = qs.using(tenant_db)
            vend = qs.filter(pk=vu.vendedor_id).first()
            if vend and vend.loja_id == loja_id and vend.is_active:
                row = serialize_vendedor(vend)
                if owner_email_lower and (row.get("email") or "").strip().lower() == owner_email_lower:
                    row["is_admin"] = True
                    row["cargo"] = "Administrador"
                results = [row]
                recovered = True
            elif vend:
                logger.warning(
                    "Vendedor %s inconsistente (loja_id=%s, is_active=%s)",
                    vu.vendedor_id,
                    vend.loja_id,
                    vend.is_active,
                )
            else:
                logger.warning("VendedorUsuario órfão: vendedor_id=%s", vu.vendedor_id)
        if not recovered:
            results.insert(0, dict_admin_loja(loja))

    return results


def resposta_vendedor_me(request, loja_id: int) -> Response:
    from superadmin.models import Loja, VendedorUsuario

    try:
        loja = Loja.objects.select_related("owner").get(id=loja_id)
        if request.user == loja.owner:
            nome = (
                request.user.get_full_name()
                or request.user.username
                or (request.user.email or "").split("@")[0]
            )
            return Response({
                "id": "admin",
                "nome": nome,
                "email": request.user.email or "",
                "is_admin": True,
            })
    except Loja.DoesNotExist:
        pass

    try:
        vu = VendedorUsuario.objects.using("default").select_related("vendedor").get(
            user=request.user,
            loja_id=loja_id,
        )
        vendedor = vu.vendedor
        return Response({
            "id": vendedor.id,
            "nome": vendedor.nome,
            "email": vendedor.email or "",
            "is_admin": vendedor.is_admin,
        })
    except VendedorUsuario.DoesNotExist:
        return Response({"detail": "Vendedor não encontrado."}, status=status.HTTP_404_NOT_FOUND)


def _enviar_email_senha_provisoria(loja, destino_email: str, nome: str, login: str, senha: str) -> None:
    site_url = getattr(settings, "SITE_URL", "https://lwksistemas.com.br").rstrip("/")
    login_url = f"{site_url}/loja/{loja.slug}/login"
    try:
        send_system_mail(
            "Nova senha provisória - CRM Vendas",
            (
                f"Olá, {nome}!\n\n"
                f"Sua senha foi redefinida.\n\n"
                f"Login: {login}\n"
                f"Nova senha provisória: {senha}\n\n"
                f"Acesse: {login_url}\n\n"
                f"Por segurança, altere sua senha no primeiro acesso."
            ),
            [destino_email],
            fail_silently=True,
        )
    except Exception as exc:
        logger.warning("Falha ao enviar e-mail de senha provisória: %s", exc)


def reenviar_senha_administrador_loja(loja_id: int) -> tuple[dict | None, str | None, int]:
    from superadmin.models import Loja

    try:
        loja = Loja.objects.select_related("owner").get(id=loja_id)
    except Loja.DoesNotExist:
        return None, "Loja não encontrada.", status.HTTP_404_NOT_FOUND

    owner = loja.owner
    if not owner.email:
        return None, "Administrador não possui e-mail cadastrado.", status.HTTP_400_BAD_REQUEST

    senha = get_random_string(8)
    owner.set_password(senha)
    owner.save(update_fields=["password"])
    loja.senha_provisoria = senha
    loja.senha_foi_alterada = False
    loja.save(update_fields=["senha_provisoria", "senha_foi_alterada"])

    nome = owner.get_full_name() or owner.username
    _enviar_email_senha_provisoria(loja, owner.email, nome, owner.username, senha)
    return {
        "detail": f"Senha provisória enviada para {owner.email}",
        "email_enviado": owner.email,
    }, None, status.HTTP_200_OK


def reenviar_senha_vendedor(loja_id: int, vendedor) -> tuple[dict | None, str | None, int]:
    from superadmin.models import Loja, VendedorUsuario

    if not vendedor.email:
        return None, "Vendedor não possui e-mail cadastrado.", status.HTTP_400_BAD_REQUEST

    loja = Loja.objects.using("default").select_related("owner").get(id=loja_id)
    senha = get_random_string(8)

    if vendedor.is_admin:
        if loja.owner.email.lower() != (vendedor.email or "").strip().lower():
            return (
                None,
                "E-mail do administrador não corresponde ao proprietário da loja.",
                status.HTTP_400_BAD_REQUEST,
            )
        loja.owner.set_password(senha)
        loja.owner.save(update_fields=["password"])
        loja.senha_provisoria = senha
        loja.senha_foi_alterada = False
        loja.save(update_fields=["senha_provisoria", "senha_foi_alterada"])
    else:
        try:
            vu = VendedorUsuario.objects.using("default").get(
                loja_id=loja_id,
                vendedor_id=vendedor.id,
            )
        except VendedorUsuario.DoesNotExist:
            return (
                None,
                'Vendedor ainda não possui acesso ao sistema. Use "Criar acesso" ao editar.',
                status.HTTP_400_BAD_REQUEST,
            )
        vu.user.set_password(senha)
        vu.user.save(update_fields=["password"])
        vu.precisa_trocar_senha = True
        vu.save(update_fields=["precisa_trocar_senha"])

    _enviar_email_senha_provisoria(
        loja,
        vendedor.email,
        vendedor.nome or "Vendedor",
        vendedor.email,
        senha,
    )
    return {
        "detail": f"Senha provisória enviada para {vendedor.email}",
        "email_enviado": vendedor.email,
    }, None, status.HTTP_200_OK


def listar_grupos_crm_disponiveis() -> list[dict]:
    from .vendedor_permissoes_service import listar_grupos_crm_com_permissoes

    return listar_grupos_crm_com_permissoes()
