"""Admin e API pública de Novidades da clínica."""
from __future__ import annotations

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from tenants.middleware import _configure_tenant_db_for_loja, get_current_loja_id

from .models import Novidade
from .novidades_service import (
    aplicar_campos_novidade,
    get_or_create_novidade_config,
    novidades_publicas_qs,
    proxima_ordem,
    serialize_config,
    serialize_novidade,
)
from .permissions import CLINICA_ADMIN


def _loja_from_slug(slug: str):
    from superadmin.models import Loja

    return (
        Loja.objects.using("default")
        .select_related("plano")
        .filter(slug=slug, is_active=True)
        .first()
    )


def _ativar_tenant(loja) -> bool:
    return bool(_configure_tenant_db_for_loja(loja))


class NovidadeConfigView(APIView):
    """GET/PATCH /clinica-beleza/novidades/config/"""

    permission_classes = CLINICA_ADMIN

    def get(self, request):
        loja_id = get_current_loja_id()
        cfg = get_or_create_novidade_config(loja_id)
        return Response(serialize_config(cfg))

    def patch(self, request):
        loja_id = get_current_loja_id()
        cfg = get_or_create_novidade_config(loja_id)
        data = request.data or {}
        if "ativo" in data:
            cfg.ativo = bool(data.get("ativo"))
        if "intervalo_carrossel" in data:
            try:
                intervalo = int(data.get("intervalo_carrossel") or 5)
            except (TypeError, ValueError):
                intervalo = 5
            cfg.intervalo_carrossel = max(3, min(30, intervalo))
        cfg.save()
        return Response(serialize_config(cfg))


class NovidadeListView(APIView):
    """GET/POST /clinica-beleza/novidades/"""

    permission_classes = CLINICA_ADMIN

    def get(self, request):
        loja_id = get_current_loja_id()
        qs = Novidade.objects.filter(loja_id=loja_id).order_by("ordem", "id")
        filtro = (request.query_params.get("ativo") or "").strip().lower()
        if filtro in ("1", "true", "sim"):
            qs = qs.filter(ativo=True)
        elif filtro in ("0", "false", "nao", "não"):
            qs = qs.filter(ativo=False)
        busca = (request.query_params.get("q") or "").strip()
        if busca:
            qs = qs.filter(titulo__icontains=busca)
        return Response([serialize_novidade(n) for n in qs])

    def post(self, request):
        loja_id = get_current_loja_id()
        data = request.data or {}
        titulo = str(data.get("titulo") or "").strip()
        if not titulo:
            return Response({"error": "Informe o título da novidade."}, status=status.HTTP_400_BAD_REQUEST)
        item = Novidade(loja_id=loja_id, titulo=titulo, ordem=proxima_ordem(loja_id))
        try:
            aplicar_campos_novidade(item, data)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        item.save()
        return Response(serialize_novidade(item), status=status.HTTP_201_CREATED)


class NovidadeDetailView(APIView):
    """GET/PATCH/DELETE /clinica-beleza/novidades/<pk>/"""

    permission_classes = CLINICA_ADMIN

    def _get(self, pk: int) -> Novidade | None:
        loja_id = get_current_loja_id()
        return Novidade.objects.filter(loja_id=loja_id, pk=pk).first()

    def get(self, request, pk: int):
        item = self._get(pk)
        if not item:
            return Response({"error": "Novidade não encontrada."}, status=status.HTTP_404_NOT_FOUND)
        return Response(serialize_novidade(item))

    def patch(self, request, pk: int):
        item = self._get(pk)
        if not item:
            return Response({"error": "Novidade não encontrada."}, status=status.HTTP_404_NOT_FOUND)
        try:
            aplicar_campos_novidade(item, request.data or {})
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        item.save()
        return Response(serialize_novidade(item))

    def delete(self, request, pk: int):
        item = self._get(pk)
        if not item:
            return Response({"error": "Novidade não encontrada."}, status=status.HTTP_404_NOT_FOUND)
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class NovidadeBulkView(APIView):
    """POST /clinica-beleza/novidades/bulk/  {action, ids}"""

    permission_classes = CLINICA_ADMIN

    def post(self, request):
        loja_id = get_current_loja_id()
        data = request.data or {}
        action = str(data.get("action") or "").strip().lower()
        ids = data.get("ids") or []
        if not isinstance(ids, list):
            return Response({"error": "ids inválidos."}, status=status.HTTP_400_BAD_REQUEST)
        ids = [int(x) for x in ids if str(x).isdigit()]
        qs = Novidade.objects.filter(loja_id=loja_id, id__in=ids)
        if action == "ativar":
            qs.update(ativo=True)
        elif action == "desativar":
            qs.update(ativo=False)
        elif action == "excluir":
            qs.delete()
        else:
            return Response({"error": "Ação inválida."}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"ok": True})


class NovidadePublicoView(APIView):
    """GET /clinica-beleza/novidades/publico/<slug>/"""

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, slug: str):
        loja = _loja_from_slug(slug)
        if not loja:
            return Response({"ativo": False, "itens": [], "intervalo_carrossel": 5})
        if not _ativar_tenant(loja):
            return Response({"ativo": False, "itens": [], "intervalo_carrossel": 5})
        cfg = get_or_create_novidade_config(loja.id)
        if not cfg.ativo:
            return Response({
                "ativo": False,
                "intervalo_carrossel": cfg.intervalo_carrossel,
                "itens": [],
            })
        itens = [serialize_novidade(n) for n in novidades_publicas_qs(loja.id)]
        return Response({
            "ativo": True,
            "intervalo_carrossel": cfg.intervalo_carrossel,
            "itens": itens,
        })
