"""Mixins e classes base para views da Clínica da Beleza.
Elimina repetição do padrão try/except DoesNotExist e simplifica CRUD.
"""
import logging

from rest_framework import status
from rest_framework.response import Response

from core.loja_request import _loja_id_se_usuario_pode, resolve_loja_id_from_request  # noqa: F401

MSG_ERRO_INTERNO = "Não foi possível concluir a operação. Tente novamente."
MSG_ERRO_PDF = "Não foi possível gerar o PDF. Tente novamente."


def resposta_erro_interno(log: logging.Logger, mensagem: str, exc: BaseException | None = None, *, error=MSG_ERRO_INTERNO):
    """500 genérico: loga o traceback e não devolve str(exc) no JSON."""
    if exc is not None:
        log.exception("%s: %s", mensagem, exc)
    else:
        log.exception("%s", mensagem)
    return Response({"error": error}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
        if getattr(self, "bloquear_andamento_alheio", False):
            from .permissions import recusar_andamento_alheio

            bloqueio = recusar_andamento_alheio(getattr(self, "request", None), obj)
            if bloqueio is not None:
                return None, bloqueio
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

