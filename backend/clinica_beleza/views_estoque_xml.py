"""Views e helpers de importação XML NF-e para estoque."""
import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .estoque_categorias import (
    garantir_categorias_estoque_padrao,
    normalizar_slug_categoria,
    resolver_categoria,
)
from .permissions import CLINICA_ESTOQUE
from .views_base import resolve_loja_id_from_request

logger = logging.getLogger(__name__)


def _verificar_destinatario_nf(resultado, loja_id):
    """Verifica se o destinatário da NF confere com o documento da loja. Retorna aviso ou None."""
    import re as _re

    from superadmin.models import Loja
    from tenants.middleware import get_current_loja_id

    lid = get_current_loja_id() or loja_id
    if not (lid and resultado.get("nota", {}).get("destinatario_documento")):
        return None
    loja = Loja.objects.filter(id=lid).first()
    if not loja:
        return None
    loja_doc = _re.sub(r"\D", "", loja.cpf_cnpj or "")
    nf_doc = _re.sub(r"\D", "", resultado["nota"]["destinatario_documento"])
    if loja_doc and nf_doc and loja_doc != nf_doc:
        return (
            f'O destinatário da NF ({resultado["nota"].get("destinatario_nome", "")} - '
            f'{nf_doc}) não confere com o documento da loja ({loja_doc}).'
        )
    return None


def _parsear_override_produtos(raw):
    """Converte raw (str JSON ou lista) para lista de dicts, ou None se inválido."""
    import json as _json
    if not raw:
        return None
    if isinstance(raw, str):
        try:
            raw = _json.loads(raw)
        except _json.JSONDecodeError:
            return None
    return raw if isinstance(raw, list) and raw else None


def _mesclar_overrides_categoria(resultado_produtos, produtos_override, loja_id):
    """Aplica overrides de categoria dos produtos_override sobre os produtos do resultado."""
    by_nome = {str(p.get("nome", "")).strip().lower(): p for p in produtos_override if isinstance(p, dict)}
    for p in resultado_produtos:
        ov = by_nome.get(str(p.get("nome", "")).strip().lower())
        if not ov:
            continue
        if ov.get("categoria"):
            p["categoria"] = ov["categoria"]
        if ov.get("categoria_id") not in (None, ""):
            p["categoria_id"] = ov["categoria_id"]
        cat = resolver_categoria(
            loja_id=loja_id,
            categoria_id=int(p["categoria_id"]) if str(p.get("categoria_id") or "").isdigit() else None,
            slug=p.get("categoria") or "outro",
        )
        if cat:
            p["categoria"] = cat.slug
            p["categoria_id"] = cat.id


class EstoqueImportarXmlView(APIView):
    """POST /clinica-beleza/estoque/importar-xml/
    Upload de XML NF-e para importar produtos ao estoque.

    Body: multipart/form-data com campo 'arquivo' (XML) e 'categoria' (opcional).
    Retorna preview dos produtos encontrados ou cria se 'confirmar=true'.
    """

    permission_classes = CLINICA_ESTOQUE

    def post(self, request):
        from core.upload_validation import validate_xml_upload

        from .estoque_xml_import_service import importar_produtos_xml

        arquivo = request.FILES.get("arquivo")
        if not arquivo:
            return Response({"error": "Envie o arquivo XML da NF-e."}, status=status.HTTP_400_BAD_REQUEST)

        valid, msg = validate_xml_upload(arquivo)
        if not valid:
            return Response({"error": msg}, status=status.HTTP_400_BAD_REQUEST)

        loja_id = resolve_loja_id_from_request(request)
        garantir_categorias_estoque_padrao(loja_id)

        categoria_raw = request.data.get("categoria", "outro")
        categoria_id = request.data.get("categoria_id")
        forcar = str(request.data.get("forcar_categoria", "false")).lower() in ("true", "1")
        cat = resolver_categoria(
            loja_id=loja_id,
            categoria_id=int(categoria_id) if categoria_id not in (None, "") else None,
            slug=str(categoria_raw) if categoria_raw else "outro",
        )
        categoria_slug = cat.slug if cat else normalizar_slug_categoria(str(categoria_raw))
        confirmar = str(request.data.get("confirmar", "false")).lower() in ("true", "1")

        try:
            resultado = importar_produtos_xml(
                arquivo.read(),
                categoria=categoria_slug,
                categoria_id=cat.id if cat else None,
                loja_id=loja_id,
                forcar_categoria=forcar,
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception("Erro ao processar XML de estoque: %s", e)
            return Response({"error": "Erro ao processar o XML. Verifique o formato."}, status=status.HTTP_400_BAD_REQUEST)

        if not confirmar:
            resp = {"preview": True, **resultado}
            aviso = _verificar_destinatario_nf(resultado, loja_id)
            if aviso:
                resp["aviso_destinatario"] = aviso
            return Response(resp)

        from .estoque_xml_import_service import confirmar_importacao_xml

        produtos_override = _parsear_override_produtos(request.data.get("produtos"))
        if produtos_override:
            _mesclar_overrides_categoria(resultado["produtos"], produtos_override, loja_id)

        result = confirmar_importacao_xml(resultado["produtos"], loja_id=loja_id)
        response_data = {**result, "nota": resultado["nota"]}
        aviso = _verificar_destinatario_nf(resultado, loja_id)
        if aviso:
            response_data["aviso_destinatario"] = aviso

        return Response(
            response_data,
            status=status.HTTP_201_CREATED if (result["criados"] + result["atualizados"]) > 0 else status.HTTP_400_BAD_REQUEST,
        )
