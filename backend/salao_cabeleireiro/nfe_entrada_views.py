"""Importação manual e busca automática da NF-e de fornecedor."""
import json
import logging

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .nfe_entrada_service import (
    confirmar_nota,
    guardar_xml,
    ignorar_nota,
    listar_abertas,
    preview_da_nota,
    sincronizar_loja,
)
from .permissions import IsSalaoAdmin, contexto_salao
from .views import _erro

logger = logging.getLogger(__name__)


def _loja(request):
    loja, _prof = contexto_salao(request)
    return loja


class ImportarXmlView(APIView):
    permission_classes = [IsAuthenticated, IsSalaoAdmin]

    def post(self, request):
        from core.upload_validation import validate_xml_upload

        loja = _loja(request)
        if loja is None:
            return _erro("Salão não encontrado.", 404)
        arquivo = request.FILES.get("arquivo")
        if not arquivo:
            return _erro("Envie o arquivo XML da NF-e.")
        valido, mensagem = validate_xml_upload(arquivo)
        if not valido:
            return _erro(mensagem)
        try:
            return Response(guardar_xml(arquivo.read(), loja))
        except ValueError as exc:
            return _erro(str(exc))
        except Exception:
            logger.exception("Falha ao ler o XML do salão")
            return _erro("Não foi possível ler o XML. Verifique o arquivo da NF-e.")


class NfePendentesView(APIView):
    permission_classes = [IsAuthenticated, IsSalaoAdmin]

    def get(self, request):
        if _loja(request) is None:
            return _erro("Salão não encontrado.", 404)
        return Response({"pendentes": listar_abertas()})


class NfeSincronizarView(APIView):
    permission_classes = [IsAuthenticated, IsSalaoAdmin]

    def post(self, request):
        loja = _loja(request)
        if loja is None:
            return _erro("Salão não encontrado.", 404)
        resultado = sincronizar_loja(loja)
        codigo = 200 if resultado.get("ok") else 400
        return Response(resultado, status=codigo)


class NfePendenteDetailView(APIView):
    permission_classes = [IsAuthenticated, IsSalaoAdmin]

    def get(self, request, pk):
        loja = _loja(request)
        if loja is None:
            return _erro("Salão não encontrado.", 404)
        try:
            return Response(preview_da_nota(pk, loja))
        except LookupError as exc:
            return _erro(str(exc), 404)
        except ValueError as exc:
            return _erro(str(exc))


class NfeConfirmarView(APIView):
    permission_classes = [IsAuthenticated, IsSalaoAdmin]

    def post(self, request, pk):
        loja = _loja(request)
        if loja is None:
            return _erro("Salão não encontrado.", 404)
        produtos = request.data.get("produtos")
        if isinstance(produtos, str):
            try:
                produtos = json.loads(produtos)
            except json.JSONDecodeError:
                return _erro("A lista de produtos da nota está inválida.")
        try:
            return Response(confirmar_nota(pk, produtos if isinstance(produtos, list) else None, loja))
        except LookupError as exc:
            return _erro(str(exc), 404)
        except ValueError as exc:
            return _erro(str(exc))


class NfeIgnorarView(APIView):
    permission_classes = [IsAuthenticated, IsSalaoAdmin]

    def post(self, request, pk):
        if _loja(request) is None:
            return _erro("Salão não encontrado.", 404)
        try:
            ignorar_nota(pk)
        except LookupError as exc:
            return _erro(str(exc), 404)
        except ValueError as exc:
            return _erro(str(exc))
        return Response({"pendentes": listar_abertas()})
