"""Identidade visual, login e contato do recibo. Os campos ficam na loja, não na clínica."""
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .permissions import IsSalaoAdmin, IsSalaoMembro, contexto_salao


def cores_gravadas(loja) -> dict:
    if loja is None:
        return {"cor_primaria": "", "cor_secundaria": "", "cor_fundo_pagina": "", "agenda_status_colors": {}}
    return {
        "cor_primaria": (loja.cor_primaria or "").strip(),
        "cor_secundaria": (loja.cor_secundaria or "").strip(),
        "cor_fundo_pagina": (getattr(loja, "cor_fundo_pagina", None) or "").strip(),
        "agenda_status_colors": getattr(loja, "agenda_status_colors", None) or {},
    }


def serializar_identidade(loja) -> dict:
    tipo = getattr(loja, "tipo_loja", None)
    cor_tipo = (getattr(tipo, "cor_primaria", None) or "").strip()
    return {
        "logo": (loja.logo or "").strip(),
        "login_background": (loja.login_background or "").strip(),
        "login_logo": (loja.login_logo or "").strip(),
        "cor_primaria": (loja.cor_primaria or "").strip() or cor_tipo or "#7A3044",
        "cor_secundaria": (loja.cor_secundaria or "").strip() or "#4c1d78",
        "cor_fundo_pagina": (getattr(loja, "cor_fundo_pagina", None) or "").strip(),
        "agenda_status_colors": getattr(loja, "agenda_status_colors", None) or {},
        "agenda_visual": (getattr(loja, "agenda_visual", None) or "pulse").strip() or "pulse",
    }


def _gravar_imagem(loja, campo, dados) -> bool:
    if campo not in dados:
        return False
    valor = (dados.get(campo) or "").strip()
    anterior = (getattr(loja, campo) or "").strip()
    if anterior and anterior != valor:
        from core.media_storage import is_media_url, media_delete_by_url

        if is_media_url(anterior):
            media_delete_by_url(anterior)
    setattr(loja, campo, valor[:200])
    return True


def _gravar_cor(loja, campo, dados) -> bool:
    if campo not in dados:
        return False
    from superadmin.theme_colors import normalize_hex_color

    bruto = dados.get(campo)
    if bruto is None or str(bruto).strip() == "":
        setattr(loja, campo, "")
        return True
    cor = normalize_hex_color(bruto)
    if not cor:
        return False
    setattr(loja, campo, cor)
    return True


class IdentidadeView(APIView):
    def get_permissions(self):
        if self.request.method == "PATCH":
            return [IsAuthenticated(), IsSalaoAdmin()]
        return [IsAuthenticated(), IsSalaoMembro()]

    def get(self, request):
        loja, _prof = contexto_salao(request)
        if loja is None:
            return Response({"error": "Salão não encontrado."}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializar_identidade(loja))

    def patch(self, request):
        loja, _prof = contexto_salao(request)
        if loja is None:
            return Response({"error": "Salão não encontrado."}, status=status.HTTP_404_NOT_FOUND)
        dados = request.data or {}
        campos = []
        for imagem in ("logo", "login_background", "login_logo"):
            if _gravar_imagem(loja, imagem, dados):
                campos.append(imagem)
        for cor in ("cor_primaria", "cor_secundaria", "cor_fundo_pagina"):
            if cor in dados and not _gravar_cor(loja, cor, dados):
                return Response({"error": "Informe a cor no formato #RRGGBB."}, status=status.HTTP_400_BAD_REQUEST)
            if cor in dados:
                campos.append(cor)
        if "agenda_status_colors" in dados:
            from superadmin.theme_colors import sanitize_agenda_status_colors

            loja.agenda_status_colors = sanitize_agenda_status_colors(dados.get("agenda_status_colors"))
            campos.append("agenda_status_colors")
        if "agenda_visual" in dados:
            from superadmin.theme_colors import sanitize_agenda_visual

            loja.agenda_visual = sanitize_agenda_visual(dados.get("agenda_visual"))
            campos.append("agenda_visual")
        if campos:
            from django.utils import timezone

            from superadmin.models import Loja

            valores = {campo: getattr(loja, campo) for campo in campos}
            valores["updated_at"] = timezone.now()
            Loja.objects.using("default").filter(pk=loja.pk).update(**valores)
            loja.refresh_from_db(using="default")
            from superadmin.loja_utils import invalidate_loja_info_publica_cache, rebuild_loja_info_publica_cache

            invalidate_loja_info_publica_cache(loja)
            rebuild_loja_info_publica_cache(loja)
        return Response(serializar_identidade(loja))


class LojaInfoView(APIView):
    def get_permissions(self):
        if self.request.method == "PATCH":
            return [IsAuthenticated(), IsSalaoAdmin()]
        return [IsAuthenticated(), IsSalaoMembro()]

    def get(self, request):
        from core.loja_context import LojaContextHelper

        info = LojaContextHelper.get_loja_owner_info()
        if info is None:
            return Response({"error": "Salão não encontrado."}, status=status.HTTP_404_NOT_FOUND)
        return Response(info)

    def patch(self, request):
        from core.loja_contato_api import patch_contato_loja

        return patch_contato_loja(request)
