"""Mixins e classes base para views da Clínica da Beleza.
Elimina repetição do padrão try/except DoesNotExist e simplifica CRUD.
"""
from rest_framework import status
from rest_framework.response import Response


class GetObjectMixin:
    """Mixin que fornece get_object(pk) com tratamento padrão de DoesNotExist.
    Requer: model_class (classe do model) e not_found_message (mensagem 404).
    """

    model_class = None
    not_found_message = "Registro não encontrado"
    select_related_fields = None
    prefetch_related_fields = None

    def get_object(self, pk):
        qs = self.model_class.objects
        if self.select_related_fields:
            qs = qs.select_related(*self.select_related_fields)
        if self.prefetch_related_fields:
            qs = qs.prefetch_related(*self.prefetch_related_fields)
        try:
            return qs.get(pk=pk)
        except self.model_class.DoesNotExist:
            return None

    def object_or_404(self, pk):
        """Retorna (obj, None) ou (None, Response 404)."""
        obj = self.get_object(pk)
        if obj is None:
            return None, Response(
                {"error": self.not_found_message},
                status=status.HTTP_404_NOT_FOUND,
            )
        return obj, None


def map_field_names(raw_data, field_map, null_to_empty_fields=None):
    """Utilitário genérico para normalizar nomes de campos (inglês → português).

    Args:
        raw_data: dict de entrada (request.data).
        field_map: dict { 'english_name': 'portuguese_name' }.
        null_to_empty_fields: lista de campos onde None deve virar ''.

    Returns:
        dict normalizado (cópia do original, sem mutação).

    """
    data = raw_data.copy() if hasattr(raw_data, "copy") else dict(raw_data)
    for en, pt in field_map.items():
        if en in data and pt not in data:
            data[pt] = data.pop(en)
    if null_to_empty_fields:
        for field in null_to_empty_fields:
            if field in data and data[field] is None:
                data[field] = ""
    return data


def _loja_id_se_usuario_pode(request, loja):
    """Header só vale com usuário autenticado e vínculo na loja (JWT já passou)."""
    user = getattr(request, "user", None)
    if not user or not getattr(user, "is_authenticated", False) or not loja:
        return None
    from core.tenant_access import user_can_access_loja

    if not user_can_access_loja(user, loja):
        return None
    return loja.id


def resolve_loja_id_from_request(request):
    """Resolve o loja_id a partir dos headers X-Loja-ID ou X-Tenant-Slug.
    Centraliza a lógica que antes estava duplicada em 3+ lugares.
    Fallback de header: só se o usuário autenticado puder acessar a loja.
    Retorna int ou None.
    """
    from tenants.middleware import get_current_loja_id

    loja_id = get_current_loja_id()
    if loja_id:
        return loja_id

    from superadmin.models import Loja

    try:
        lid = request.headers.get("X-Loja-ID")
        if lid:
            loja = Loja.objects.using("default").filter(id=int(lid)).first()
            resolved = _loja_id_se_usuario_pode(request, loja)
            if resolved is not None:
                return resolved
    except (ValueError, TypeError):
        pass

    slug = (request.headers.get("X-Tenant-Slug") or "").strip()
    if slug:
        loja = Loja.objects.using("default").filter(slug__iexact=slug).first()
        return _loja_id_se_usuario_pode(request, loja)

    return None
