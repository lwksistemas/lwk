"""
Permissões RBAC — Clínica da Beleza.

Vínculo mínimo: owner ou ProfissionalUsuario da loja (headers X-Loja-ID / tenant).
Perfis sensíveis: administrador, recepção, profissional, caixa, estoque.
"""
from rest_framework.permissions import BasePermission, IsAuthenticated


def _loja_and_profissional(request):
    """Retorna (loja, ProfissionalUsuario|None) ou (None, None)."""
    from .views_base import resolve_loja_id_from_request
    from superadmin.models import Loja, ProfissionalUsuario

    if not request.user or not request.user.is_authenticated:
        return None, None
    if request.user.is_superuser:
        return None, 'superuser'

    loja_id = resolve_loja_id_from_request(request)
    if not loja_id:
        return None, None

    try:
        loja = Loja.objects.get(pk=loja_id)
    except Loja.DoesNotExist:
        return None, None

    if loja.owner_id == request.user.id:
        return loja, None

    prof = ProfissionalUsuario.objects.filter(user=request.user, loja=loja).first()
    return loja, prof


class IsClinicaLojaMember(BasePermission):
    """Owner ou qualquer profissional vinculado à loja do contexto."""

    message = 'Acesso permitido apenas a usuários vinculados a esta clínica.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        loja, prof = _loja_and_profissional(request)
        if prof == 'superuser':
            return True
        if loja and loja.owner_id == request.user.id:
            return True
        return prof is not None


class IsRecepcaoOrAdmin(BasePermission):
    """
    Cadastros/recepção ampla: owner, administrador, recepcionista ou recepcao (legado).
    Exclui perfil limpeza, caixa, estoque e profissional.
    """

    message = 'Acesso permitido apenas para administrador ou perfil recepção.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        loja, prof = _loja_and_profissional(request)
        if prof == 'superuser':
            return True
        if not loja:
            return False
        if loja.owner_id == request.user.id:
            return True
        if not prof:
            return False
        from superadmin.models import ProfissionalUsuario

        return prof.perfil in (
            ProfissionalUsuario.PERFIL_ADMINISTRADOR,
            ProfissionalUsuario.PERFIL_RECEPCAO,
            ProfissionalUsuario.PERFIL_RECEPCIONISTA,
        )


class IsAgendaOrAdmin(BasePermission):
    """
    Agenda e bloqueios: recepção/admin (visão completa) ou profissional (escopo próprio).
    """

    message = 'Acesso permitido apenas para recepção, administrador ou profissional da clínica.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        loja, prof = _loja_and_profissional(request)
        if prof == 'superuser':
            return True
        if not loja:
            return False
        if loja.owner_id == request.user.id:
            return True
        if not prof:
            return False
        from superadmin.models import ProfissionalUsuario

        return prof.perfil in (
            ProfissionalUsuario.PERFIL_ADMINISTRADOR,
            ProfissionalUsuario.PERFIL_RECEPCAO,
            ProfissionalUsuario.PERFIL_RECEPCIONISTA,
            ProfissionalUsuario.PERFIL_PROFISSIONAL,
        )


class IsClinicaAdmin(BasePermission):
    """Configurações e gestão: owner ou perfil administrador."""

    message = 'Acesso permitido apenas para administrador da clínica.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        loja, prof = _loja_and_profissional(request)
        if prof == 'superuser':
            return True
        if not loja:
            return False
        if loja.owner_id == request.user.id:
            return True
        if not prof:
            return False
        from superadmin.models import ProfissionalUsuario

        return prof.perfil == ProfissionalUsuario.PERFIL_ADMINISTRADOR


class IsClinicaClinicalStaff(BasePermission):
    """Prontuário, prescrição e documentos clínicos."""

    message = 'Acesso permitido apenas à equipe clínica autorizada.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        loja, prof = _loja_and_profissional(request)
        if prof == 'superuser':
            return True
        if not loja:
            return False
        if loja.owner_id == request.user.id:
            return True
        if not prof:
            return False
        from superadmin.models import ProfissionalUsuario

        return prof.perfil in (
            ProfissionalUsuario.PERFIL_ADMINISTRADOR,
            ProfissionalUsuario.PERFIL_PROFISSIONAL,
            ProfissionalUsuario.PERFIL_RECEPCAO,
            ProfissionalUsuario.PERFIL_RECEPCIONISTA,
        )


class IsClinicaFinanceiro(BasePermission):
    """Financeiro da clínica."""

    message = 'Acesso permitido apenas para administrador, recepção ou caixa.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        loja, prof = _loja_and_profissional(request)
        if prof == 'superuser':
            return True
        if not loja:
            return False
        if loja.owner_id == request.user.id:
            return True
        if not prof:
            return False
        from superadmin.models import ProfissionalUsuario

        return prof.perfil in (
            ProfissionalUsuario.PERFIL_ADMINISTRADOR,
            ProfissionalUsuario.PERFIL_RECEPCAO,
            ProfissionalUsuario.PERFIL_RECEPCIONISTA,
            ProfissionalUsuario.PERFIL_CAIXA,
        )


class IsClinicaEstoque(BasePermission):
    """Estoque e insumos."""

    message = 'Acesso permitido apenas para administrador, recepção ou estoque.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        loja, prof = _loja_and_profissional(request)
        if prof == 'superuser':
            return True
        if not loja:
            return False
        if loja.owner_id == request.user.id:
            return True
        if not prof:
            return False
        from superadmin.models import ProfissionalUsuario

        return prof.perfil in (
            ProfissionalUsuario.PERFIL_ADMINISTRADOR,
            ProfissionalUsuario.PERFIL_RECEPCAO,
            ProfissionalUsuario.PERFIL_RECEPCIONISTA,
            ProfissionalUsuario.PERFIL_ESTOQUE,
        )


class IsClinicalOrEstoqueStaff(BasePermission):
    """Leitura de estoque na consulta: equipe clínica ou perfil estoque (exclui limpeza/caixa)."""

    message = 'Acesso permitido apenas à equipe clínica ou estoque.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        loja, prof = _loja_and_profissional(request)
        if prof == 'superuser':
            return True
        if not loja:
            return False
        if loja.owner_id == request.user.id:
            return True
        if not prof:
            return False
        from superadmin.models import ProfissionalUsuario

        return prof.perfil in (
            ProfissionalUsuario.PERFIL_ADMINISTRADOR,
            ProfissionalUsuario.PERFIL_PROFISSIONAL,
            ProfissionalUsuario.PERFIL_RECEPCAO,
            ProfissionalUsuario.PERFIL_RECEPCIONISTA,
            ProfissionalUsuario.PERFIL_ESTOQUE,
        )


def resolve_agenda_professional_scope(request) -> int | None:
    """
    Escopo de agenda para o usuário autenticado.

    None — visão completa (owner, admin, recepção).
    int  — professional_id quando perfil profissional (só agenda/bloqueios próprios).
    """
    loja, prof = _loja_and_profissional(request)
    if prof == 'superuser' or (loja and loja.owner_id == request.user.id):
        return None
    if not prof:
        return None
    from superadmin.models import ProfissionalUsuario

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
