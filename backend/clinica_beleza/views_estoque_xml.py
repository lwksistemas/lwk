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


def _usuario_da_requisicao(request) -> str:
    user = getattr(request, "user", None)
    if not user or not getattr(user, "is_authenticated", False):
        return ""
    nome = user.get_full_name() if hasattr(user, "get_full_name") else ""
    return (nome or getattr(user, "username", "") or "")[:80]


def _sincronizar_unidade_escolhida(item: dict) -> None:
    """Fator 1 mantém a unidade da nota. Caixa convertida entra na unidade do conteúdo."""
    from decimal import Decimal, InvalidOperation

    try:
        fator = Decimal(str(item.get("fator") or "1"))
    except InvalidOperation:
        return
    if fator == 1:
        item["unidade_estoque"] = item.get("unidade_medida") or item.get("unidade_estoque")
    elif item.get("embalagem_unidade"):
        item["unidade_estoque"] = item["embalagem_unidade"]


def _mesclar_overrides_categoria(resultado_produtos, produtos_override, loja_id):
    """Aplica categoria e a decisão de vínculo escolhida na conferência."""
    overrides = [p for p in produtos_override if isinstance(p, dict)]
    por_indice = len(overrides) == len(resultado_produtos)
    by_nome = {str(p.get("nome", "")).strip().lower(): p for p in overrides}
    for indice, p in enumerate(resultado_produtos):
        ov = overrides[indice] if por_indice else by_nome.get(str(p.get("nome", "")).strip().lower())
        if not ov:
            continue
        if ov.get("categoria"):
            p["categoria"] = ov["categoria"]
        if ov.get("categoria_id") not in (None, ""):
            p["categoria_id"] = ov["categoria_id"]
        for campo in ("acao", "produto_id", "fator", "validade", "lote"):
            if campo in ov and ov[campo] not in (None, ""):
                p[campo] = ov[campo]
        _sincronizar_unidade_escolhida(p)
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
        xml_bytes = arquivo.read()

        try:
            resultado = importar_produtos_xml(
                xml_bytes,
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

        from .estoque_nfe_pendente_service import MSG_JA_IMPORTADA, confirmar_arquivo, guardar_xml, nota_importada

        chave = (resultado.get("nota") or {}).get("chave") or ""
        if chave and nota_importada(chave):
            return Response({"error": MSG_JA_IMPORTADA}, status=status.HTTP_400_BAD_REQUEST)
        if not confirmar and chave:
            try:
                guardar_xml(xml_bytes, loja_id=loja_id, origem="arquivo")
            except ValueError as exc:
                if str(exc) == MSG_JA_IMPORTADA:
                    return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
            except Exception:
                logger.exception("Não foi possível guardar a NF-e pendente")

        if not confirmar:
            resp = {"preview": True, **resultado}
            aviso = _verificar_destinatario_nf(resultado, loja_id)
            if aviso:
                resp["aviso_destinatario"] = aviso
            return Response(resp)

        produtos_override = _parsear_override_produtos(request.data.get("produtos"))
        if produtos_override:
            _mesclar_overrides_categoria(resultado["produtos"], produtos_override, loja_id)

        try:
            result = confirmar_arquivo(
                xml_bytes, resultado["produtos"], loja_id=loja_id, usuario=_usuario_da_requisicao(request),
            )
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        response_data = {**result, "nota": resultado["nota"]}
        aviso = _verificar_destinatario_nf(resultado, loja_id)
        if aviso:
            response_data["aviso_destinatario"] = aviso

        return Response(
            response_data,
            status=status.HTTP_201_CREATED if (result["criados"] + result["atualizados"] + result.get("ignorados", 0)) > 0 else status.HTTP_400_BAD_REQUEST,
        )


class EstoqueNfePendentesView(APIView):
    """GET /clinica-beleza/estoque/nfe-pendentes/"""

    permission_classes = CLINICA_ESTOQUE

    def get(self, request):
        from .estoque_nfe_pendente_service import listar_abertas

        return Response({"pendentes": listar_abertas()})


class EstoqueNfeSincronizarView(APIView):
    """POST /clinica-beleza/estoque/nfe-pendentes/sincronizar/"""

    permission_classes = CLINICA_ESTOQUE

    def post(self, request):
        from superadmin.models import Loja

        from .estoque_nfe_pendente_service import listar_abertas, sincronizar_loja
        from .views_base import resolve_loja_id_from_request

        loja_id = resolve_loja_id_from_request(request)
        loja = Loja.objects.using("default").filter(id=loja_id).first()
        if loja is None:
            return Response({"error": "Loja não encontrada."}, status=status.HTTP_400_BAD_REQUEST)
        resultado = sincronizar_loja(loja)
        status_http = status.HTTP_200_OK if resultado.get("ok") else status.HTTP_400_BAD_REQUEST
        return Response({**resultado, "pendentes": listar_abertas()}, status=status_http)


class EstoqueNfePendentePreviewView(APIView):
    """GET /clinica-beleza/estoque/nfe-pendentes/<pk>/"""

    permission_classes = CLINICA_ESTOQUE
    not_found_message = "Nota não encontrada."

    def get(self, request, pk):
        from .estoque_nfe_pendente_service import preview_da_nota
        from .views_base import resolve_loja_id_from_request

        try:
            dados = preview_da_nota(pk, loja_id=resolve_loja_id_from_request(request))
        except LookupError:
            return Response({"error": self.not_found_message}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(dados)


class EstoqueNfePendenteConfirmarView(APIView):
    """POST /clinica-beleza/estoque/nfe-pendentes/<pk>/confirmar/"""

    permission_classes = CLINICA_ESTOQUE

    def post(self, request, pk):
        from .estoque_nfe_pendente_service import confirmar_nota
        from .views_base import resolve_loja_id_from_request

        loja_id = resolve_loja_id_from_request(request)
        garantir_categorias_estoque_padrao(loja_id)
        try:
            result = confirmar_nota(
                pk,
                _parsear_override_produtos(request.data.get("produtos")),
                loja_id=loja_id,
                usuario=_usuario_da_requisicao(request),
            )
        except LookupError:
            return Response({"error": "Nota não encontrada."}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            result,
            status=status.HTTP_201_CREATED if (result["criados"] + result["atualizados"] + result.get("ignorados", 0)) > 0 else status.HTTP_400_BAD_REQUEST,
        )


class EstoqueNfePendenteIgnorarView(APIView):
    """POST /clinica-beleza/estoque/nfe-pendentes/<pk>/ignorar/"""

    permission_classes = CLINICA_ESTOQUE

    def post(self, request, pk):
        from .estoque_nfe_pendente_service import ignorar_nota

        try:
            ignorar_nota(pk)
        except LookupError:
            return Response({"error": "Nota não encontrada."}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"ok": True})


class EstoqueNfeFinanceiroView(APIView):
    """POST /clinica-beleza/estoque/nfe-financeiro/
    Resposta de quando o XML não diz se a nota foi paga.
    """

    permission_classes = CLINICA_ESTOQUE

    def post(self, request):
        from .estoque_nfe_pagamento import publicar_despesa_nfe
        from .views_base import resolve_loja_id_from_request

        pago = request.data.get("pago")
        if isinstance(pago, bool):
            foi_pago = pago
        else:
            foi_pago = str(pago).strip().lower() in {"1", "true", "sim", "pago"}
        if pago in (None, ""):
            return Response({"error": "Informe se a nota foi paga."}, status=status.HTTP_400_BAD_REQUEST)
        pagamento = {
            "situacao": "indefinido",
            "valor": request.data.get("valor") or "0",
            "data_emissao": str(request.data.get("data_emissao") or "")[:10],
            "forma_pagamento": request.data.get("forma_pagamento") or "",
            "parcelas": [],
        }
        financeiro = publicar_despesa_nfe(
            resolve_loja_id_from_request(request),
            pagamento,
            numero=str(request.data.get("numero") or ""),
            fornecedor=str(request.data.get("fornecedor") or ""),
            chave=str(request.data.get("chave") or ""),
            pago=foi_pago,
            data_vencimento=str(request.data.get("data_vencimento") or "")[:10],
        )
        if not financeiro.get("lancado"):
            return Response(
                {"error": "Informe a data de vencimento da nota." if not foi_pago else "Não foi possível lançar a despesa."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({"financeiro": financeiro}, status=status.HTTP_201_CREATED)
