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


class IsClinicaConsultaOperacional(_BaseClinicaProfilePermission):
    """Lista e recebimento da consulta: profissional, administrador e recepção.

    A recepção controla o financeiro. O prontuário continua só com profissional e admin.
    """

    message = "Acesso permitido apenas ao profissional, administrador ou recepção da clínica."
    allowed_profiles = (
        ProfissionalUsuario.PERFIL_ADMINISTRADOR,
        ProfissionalUsuario.PERFIL_PROFISSIONAL,
        ProfissionalUsuario.PERFIL_RECEPCAO,
        ProfissionalUsuario.PERFIL_RECEPCIONISTA,
    )


class IsClinicaClinicalStaff(_BaseClinicaProfilePermission):
    """Consulta, prontuário, prescrição e documentos — só profissional e admin.

    Recepção agenda e cadastra cliente; não abre consulta.
    """

    message = "Acesso permitido apenas ao profissional ou administrador da clínica."
    allowed_profiles = (
        ProfissionalUsuario.PERFIL_ADMINISTRADOR,
        ProfissionalUsuario.PERFIL_PROFISSIONAL,
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
        ProfissionalUsuario.PERFIL_ESTOQUE,
    )


def oculta_notas_clinicas(request) -> bool:
    """Recepção opera lista e caixa, sem ler nota de evolução do prontuário."""
    if request is None:
        return False
    _loja, prof = _loja_and_profissional(request)
    if prof in (None, "superuser"):
        return False
    return prof.perfil in (
        ProfissionalUsuario.PERFIL_RECEPCAO,
        ProfissionalUsuario.PERFIL_RECEPCIONISTA,
    )


def is_clinica_admin(request) -> bool:
    """True se o usuário é superuser, owner da loja ou perfil administrador.

    Usado para permitir que o admin 'fure' bloqueios operacionais (ex.: inadimplência),
    enquanto a recepção é bloqueada.
    """
    if request is None:
        return False
    loja, prof = _loja_and_profissional(request)
    if prof == "superuser":
        return True
    if loja and getattr(request, "user", None) and loja.owner_id == request.user.id:
        return True
    return bool(prof) and prof.perfil == ProfissionalUsuario.PERFIL_ADMINISTRADOR


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


MSG_CONSULTA_EM_ANDAMENTO = (
    "Consulta em andamento. Só o profissional deste atendimento pode abri-la até finalizar."
)
MSG_REABRIR_SO_QUEM_FEZ = "Só o profissional que realizou esta consulta pode reabri-la."


def login_e_o_prescritor(request, professional_id) -> bool:
    """True só quando o id pedido é o profissional vinculado a este login."""
    meu = professional_id_do_usuario(request)
    if meu is None:
        return False
    try:
        pedido = int(professional_id)
    except (TypeError, ValueError):
        return False
    return pedido == int(meu)


def professional_id_do_usuario(request) -> int | None:
    """Professional.id vinculado ao login.

    Superuser sem cadastro não conta. O dono da loja conta quando o login tem
    o vínculo: o atalho de owner devolve o profissional vazio e escondia esse id.
    """
    if request is None:
        return None
    loja, prof = _loja_and_profissional(request)
    if prof == "superuser":
        return None
    if prof and getattr(prof, "professional_id", None):
        return prof.professional_id
    user = getattr(request, "user", None)
    if not loja or not user or not getattr(user, "is_authenticated", False):
        return None
    if loja.owner_id != user.id:
        return None
    vinculo = (
        ProfissionalUsuario.objects.filter(user=user, loja=loja)
        .only("professional_id")
        .first()
    )
    if vinculo and vinculo.professional_id:
        return vinculo.professional_id
    return None


def usuario_e_profissional_da_consulta(request, consulta) -> bool:
    """True quando o login é o profissional gravado na consulta."""
    meu_id = professional_id_do_usuario(request)
    consulta_id = getattr(consulta, "professional_id", None)
    return bool(meu_id and consulta_id and meu_id == consulta_id)


def recusar_andamento_alheio(request, consulta):
    """403 se a consulta está em atendimento e o login não é o profissional dela."""
    from rest_framework import status
    from rest_framework.response import Response

    if consulta is None or getattr(consulta, "status", None) != "IN_PROGRESS":
        return None
    if usuario_e_profissional_da_consulta(request, consulta):
        return None
    return Response({"error": MSG_CONSULTA_EM_ANDAMENTO}, status=status.HTTP_403_FORBIDDEN)


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
CLINICA_CONSULTA_OPERACIONAL = [IsAuthenticated, IsClinicaLojaMember, IsClinicaConsultaOperacional]
CLINICA_FINANCEIRO = [IsAuthenticated, IsClinicaLojaMember, IsClinicaFinanceiro]
CLINICA_ESTOQUE = [IsAuthenticated, IsClinicaLojaMember, IsClinicaEstoque]
CLINICA_ESTOQUE_LEITURA = [IsAuthenticated, IsClinicaLojaMember, IsClinicalOrEstoqueStaff]
