"""Permissões RBAC — Clínica da Beleza.

Vínculo mínimo: owner ou ProfissionalUsuario da loja (headers X-Loja-ID / tenant).
Perfis sensíveis: administrador, recepção, profissional, caixa, estoque.
"""
from rest_framework.permissions import BasePermission, IsAuthenticated

from superadmin.models import Loja, ProfissionalUsuario


def _loja_and_profissional(request):
    """Retorna (loja, ProfissionalUsuario|None) ou (None, None).

    O resultado é cacheado no request para evitar queries repetidas quando
    várias permissões são avaliadas na mesma requisição.
    """
    from .views_base import resolve_loja_id_from_request

    cache_attr = "_clinica_loja_ctx_v1"
    if hasattr(request, cache_attr):
        return getattr(request, cache_attr)

    if not request.user or not request.user.is_authenticated:
        result = (None, None)
        setattr(request, cache_attr, result)
        return result
    if request.user.is_superuser:
        result = (None, "superuser")
        setattr(request, cache_attr, result)
        return result

    loja_id = resolve_loja_id_from_request(request)
    if not loja_id:
        result = (None, None)
        setattr(request, cache_attr, result)
        return result

    try:
        loja = Loja.objects.get(pk=loja_id)
    except Loja.DoesNotExist:
        result = (None, None)
        setattr(request, cache_attr, result)
        return result

    if loja.owner_id == request.user.id:
        result = (loja, None)
        setattr(request, cache_attr, result)
        return result

    prof = ProfissionalUsuario.objects.filter(user=request.user, loja=loja).first()
    result = (loja, prof)
    setattr(request, cache_attr, result)
    return result


class IsClinicaLojaMember(BasePermission):
    """Owner ou qualquer profissional vinculado à loja do contexto."""

    message = "Acesso permitido apenas a usuários vinculados a esta clínica."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        loja, prof = _loja_and_profissional(request)
        if prof == "superuser":
            return True
        if loja and loja.owner_id == request.user.id:
            return True
        return prof is not None


class _BaseClinicaProfilePermission(BasePermission):
    """Classe base para permissões RBAC baseadas em perfil.

    Subclasses definem ``allowed_profiles`` (tupla de perfis aceitos) e
    ``message`` (mensagem de negação). O fluxo padrão é:
    1. Usuário autenticado?
    2. Superuser → sim
    3. Loja existe? Owner da loja → sim
    4. ProfissionalUsuario vinculado? Perfil na lista → sim
    """

    allowed_profiles: tuple[str, ...] = ()

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        loja, prof = _loja_and_profissional(request)
        if prof == "superuser":
            return True
        if not loja:
            return False
        if loja.owner_id == request.user.id:
            return True
        if not prof:
            return False
        return prof.perfil in self.allowed_profiles


class IsRecepcaoOrAdmin(_BaseClinicaProfilePermission):
    """Cadastros/recepção ampla: owner, administrador, recepcionista ou recepcao (legado).
    Exclui perfil limpeza, caixa, estoque e profissional.
    """

    message = "Acesso permitido apenas para administrador ou perfil recepção."
    allowed_profiles = (
        ProfissionalUsuario.PERFIL_ADMINISTRADOR,
        ProfissionalUsuario.PERFIL_RECEPCAO,
        ProfissionalUsuario.PERFIL_RECEPCIONISTA,
    )


class IsAgendaOrAdmin(_BaseClinicaProfilePermission):
    """Agenda e bloqueios: recepção/admin (visão completa) ou profissional (escopo próprio).
    """

    message = "Acesso permitido apenas para recepção, administrador ou profissional da clínica."
    allowed_profiles = (
        ProfissionalUsuario.PERFIL_ADMINISTRADOR,
        ProfissionalUsuario.PERFIL_RECEPCAO,
        ProfissionalUsuario.PERFIL_RECEPCIONISTA,
        ProfissionalUsuario.PERFIL_PROFISSIONAL,
    )


class IsClinicaAdmin(_BaseClinicaProfilePermission):
    """Configurações e gestão: owner ou perfil administrador."""

    message = "Acesso permitido apenas para administrador da clínica."
    allowed_profiles = (ProfissionalUsuario.PERFIL_ADMINISTRADOR,)


class IsClinicaClinicalStaff(_BaseClinicaProfilePermission):
    """Prontuário, prescrição e documentos clínicos."""

    message = "Acesso permitido apenas à equipe clínica autorizada."
    allowed_profiles = (
        ProfissionalUsuario.PERFIL_ADMINISTRADOR,
        ProfissionalUsuario.PERFIL_PROFISSIONAL,
        ProfissionalUsuario.PERFIL_RECEPCAO,
        ProfissionalUsuario.PERFIL_RECEPCIONISTA,
    )


class IsClinicaFinanceiro(_BaseClinicaProfilePermission):
    """Financeiro da clínica."""

    message = "Acesso permitido apenas para administrador, recepção ou caixa."
    allowed_profiles = (
        ProfissionalUsuario.PERFIL_ADMINISTRADOR,
        ProfissionalUsuario.PERFIL_RECEPCAO,
        ProfissionalUsuario.PERFIL_RECEPCIONISTA,
        ProfissionalUsuario.PERFIL_CAIXA,
    )


class IsClinicaEstoque(_BaseClinicaProfilePermission):
    """Estoque e insumos."""

    message = "Acesso permitido apenas para administrador, recepção ou estoque."
    allowed_profiles = (
        ProfissionalUsuario.PERFIL_ADMINISTRADOR,
        ProfissionalUsuario.PERFIL_RECEPCAO,
        ProfissionalUsuario.PERFIL_RECEPCIONISTA,
        ProfissionalUsuario.PERFIL_ESTOQUE,
    )


class IsClinicalOrEstoqueStaff(_BaseClinicaProfilePermission):
    """Leitura de estoque na consulta: equipe clínica ou perfil estoque (exclui limpeza/caixa)."""

    message = "Acesso permitido apenas à equipe clínica ou estoque."
    allowed_profiles = (
        ProfissionalUsuario.PERFIL_ADMINISTRADOR,
        ProfissionalUsuario.PERFIL_PROFISSIONAL,
        ProfissionalUsuario.PERFIL_RECEPCAO,
        ProfissionalUsuario.PERFIL_RECEPCIONISTA,
        ProfissionalUsuario.PERFIL_ESTOQUE,
    )


def resolve_agenda_professional_scope(request) -> int | None:
    """Escopo de agenda para o usuário autenticado.

    None — visão completa (owner, admin, recepção).
    int  — professional_id quando perfil profissional (só agenda/bloqueios próprios).
    """
    loja, prof = _loja_and_profissional(request)
    if prof == "superuser" or (loja and loja.owner_id == request.user.id):
        return None
    if not prof:
        return None
    if prof.perfil == ProfissionalUsuario.PERFIL_PROFISSIONAL:
        return prof.professional_id or 0
    return None


def appointment_in_agenda_scope(appointment, scope_professional_id: int | None) -> bool:
    """True se o agendamento pode ser lido/alterado pelo escopo atual."""
    if scope_professional_id is None:
        return True
    if not scope_professional_id:
        return False
    return appointment.professional_id == scope_professional_id


# Atalhos para permission_classes nas views
CLINICA_MEMBER = [IsAuthenticated, IsClinicaLojaMember]
CLINICA_RECEPCAO = [IsAuthenticated, IsClinicaLojaMember, IsRecepcaoOrAdmin]
CLINICA_AGENDA = [IsAuthenticated, IsClinicaLojaMember, IsAgendaOrAdmin]
CLINICA_ADMIN = [IsAuthenticated, IsClinicaLojaMember, IsClinicaAdmin]
CLINICA_CLINICAL = [IsAuthenticated, IsClinicaLojaMember, IsClinicaClinicalStaff]
CLINICA_FINANCEIRO = [IsAuthenticated, IsClinicaLojaMember, IsClinicaFinanceiro]
CLINICA_ESTOQUE = [IsAuthenticated, IsClinicaLojaMember, IsClinicaEstoque]
CLINICA_ESTOQUE_LEITURA = [IsAuthenticated, IsClinicaLojaMember, IsClinicalOrEstoqueStaff]
