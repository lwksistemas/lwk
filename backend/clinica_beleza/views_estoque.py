"""Views de Estoque — Clínica da Beleza
Controle de produtos (botox, ácido hialurônico, soros, etc.)
"""
import logging

from django.db.models import F, Sum
from django.utils.text import slugify
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .estoque_categorias import (
    categorias_com_contagem,
    garantir_categorias_estoque_padrao,
    resolver_categoria,
)
from .models import MovimentacaoEstoque, ProdutoEstoque
from .models.estoque import CategoriaEstoque
from .permissions import CLINICA_ESTOQUE, CLINICA_ESTOQUE_LEITURA
from .serializers import MovimentacaoEstoqueSerializer, ProdutoEstoqueSerializer
from .serializers.estoque import CategoriaEstoqueSerializer
from .views_base import GetObjectMixin, resolve_loja_id_from_request
from .views_estoque_helpers import (  # noqa: F401
    _PRODUTO_VALUES_FIELDS,
    _filtrar_por_categoria,
    _paginate_produtos_values,
    _produto_values_row,
)
from .views_estoque_xml import (  # noqa: F401
    EstoqueImportarXmlView,
    EstoqueNfePendenteConfirmarView,
    EstoqueNfePendenteIgnorarView,
    EstoqueNfePendentePreviewView,
    EstoqueNfePendentesView,
    EstoqueNfeSincronizarView,
    _mesclar_overrides_categoria,
    _parsear_override_produtos,
    _verificar_destinatario_nf,
)

logger = logging.getLogger(__name__)


class CategoriaEstoqueListView(APIView):
    """GET/POST /clinica-beleza/estoque/categorias/"""

    permission_classes = CLINICA_ESTOQUE

    def get_permissions(self):
        if self.request.method == "GET":
            return [perm() for perm in CLINICA_ESTOQUE_LEITURA]
        return [perm() for perm in CLINICA_ESTOQUE]

    def get(self, request):
        from tenants.middleware import ensure_loja_context

        ensure_loja_context(request)
        loja_id = resolve_loja_id_from_request(request)
        garantir_categorias_estoque_padrao(loja_id)
        qs = categorias_com_contagem(loja_id)
        return Response(CategoriaEstoqueSerializer(qs, many=True).data)

    def post(self, request):
        from tenants.middleware import ensure_loja_context

        ensure_loja_context(request)
        loja_id = resolve_loja_id_from_request(request)
        garantir_categorias_estoque_padrao(loja_id)
        serializer = CategoriaEstoqueSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        nome = serializer.validated_data["nome"]
        base_slug = slugify(nome, allow_unicode=True)[:50] or "categoria"
        slug = base_slug
        n = 2
        while CategoriaEstoque.objects.filter(loja_id=loja_id, slug=slug).exists():
            slug = f"{base_slug[:45]}-{n}"
            n += 1
        ordem = serializer.validated_data.get("ordem")
        if ordem is None:
            last = CategoriaEstoque.objects.filter(loja_id=loja_id).order_by("-ordem").first()
            ordem = (last.ordem + 1) if last else 1
        obj = serializer.save(loja_id=loja_id, slug=slug, ordem=ordem)
        obj.produtos_count = 0
        return Response(CategoriaEstoqueSerializer(obj).data, status=status.HTTP_201_CREATED)


class CategoriaEstoqueDetailView(GetObjectMixin, APIView):
    """GET/PUT/DELETE /clinica-beleza/estoque/categorias/<id>/"""

    permission_classes = CLINICA_ESTOQUE
    model_class = CategoriaEstoque
    not_found_message = "Categoria não encontrada"

    def get(self, request, pk):
        from tenants.middleware import ensure_loja_context

        ensure_loja_context(request)
        obj, error = self.object_or_404(pk)
        if error:
            return error
        obj.produtos_count = obj.produtos.filter(is_active=True).count()
        return Response(CategoriaEstoqueSerializer(obj).data)

    def put(self, request, pk):
        from tenants.middleware import ensure_loja_context

        ensure_loja_context(request)
        obj, error = self.object_or_404(pk)
        if error:
            return error
        serializer = CategoriaEstoqueSerializer(obj, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        obj.produtos_count = obj.produtos.filter(is_active=True).count()
        return Response(CategoriaEstoqueSerializer(obj).data)

    def delete(self, request, pk):
        from tenants.middleware import ensure_loja_context

        ensure_loja_context(request)
        obj, error = self.object_or_404(pk)
        if error:
            return error
        ativos = obj.produtos.filter(is_active=True).count()
        if ativos:
            return Response(
                {"error": f"Não é possível excluir: há {ativos} produto(s) nesta categoria."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProdutoEstoqueListView(APIView):
    """GET /clinica-beleza/estoque/
    POST /clinica-beleza/estoque/
    """

    permission_classes = CLINICA_ESTOQUE

    def get_permissions(self):
        if self.request.method == "GET":
            return [perm() for perm in CLINICA_ESTOQUE_LEITURA]
        return [perm() for perm in CLINICA_ESTOQUE]

    def get(self, request):
        from tenants.middleware import ensure_loja_context

        ensure_loja_context(request)
        loja_id = resolve_loja_id_from_request(request)
        garantir_categorias_estoque_padrao(loja_id)
        qs = ProdutoEstoque.objects.all().order_by("nome")
        qs = _filtrar_por_categoria(qs, request)
        search = (request.query_params.get("search") or "").strip()
        if search:
            qs = qs.filter(nome__icontains=search)
        apenas_ativos = request.query_params.get("active", "true").lower() == "true"
        if apenas_ativos:
            qs = qs.filter(is_active=True)
        estoque_baixo = request.query_params.get("estoque_baixo")
        if estoque_baixo == "true":
            qs = qs.filter(quantidade_atual__lte=F("quantidade_minima"))
        return _paginate_produtos_values(qs, request)

    def post(self, request):
        from tenants.middleware import ensure_loja_context

        ensure_loja_context(request)
        loja_id = resolve_loja_id_from_request(request)
        garantir_categorias_estoque_padrao(loja_id)
        serializer = ProdutoEstoqueSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProdutoEstoqueDetailView(GetObjectMixin, APIView):
    """GET /clinica-beleza/estoque/<id>/  PUT  DELETE"""

    permission_classes = CLINICA_ESTOQUE
    model_class = ProdutoEstoque
    not_found_message = "Produto não encontrado"
    select_related_fields = ("categoria",)

    def get_permissions(self):
        if self.request.method == "GET":
            return [perm() for perm in CLINICA_ESTOQUE_LEITURA]
        return [perm() for perm in CLINICA_ESTOQUE]

    def get(self, request, pk):
        from tenants.middleware import ensure_loja_context

        ensure_loja_context(request)
        obj, error = self.object_or_404(pk)
        if error:
            return error
        return Response(ProdutoEstoqueSerializer(obj).data)

    def put(self, request, pk):
        from tenants.middleware import ensure_loja_context

        ensure_loja_context(request)
        obj, error = self.object_or_404(pk)
        if error:
            return error
        serializer = ProdutoEstoqueSerializer(
            obj, data=request.data, partial=True, context={"request": request},
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        from django.db.models.deletion import ProtectedError

        from .models import ConsultaProdutoUtilizado

        obj, error = self.object_or_404(pk)
        if error:
            return error

        usos = ConsultaProdutoUtilizado.objects.filter(produto=obj).select_related("consulta")
        if usos.exists():
            n_finalizadas = usos.filter(consulta__status="COMPLETED").count()
            if n_finalizadas:
                return Response(
                    {
                        "error": (
                            "Não é possível excluir este produto: ele foi utilizado em "
                            f"{n_finalizadas} consulta(s) finalizada(s). "
                            "O histórico clínico precisa ser preservado."
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(
                {
                    "error": (
                        "Não é possível excluir este produto: ele já foi registrado em "
                        "consulta(s). Remova o vínculo nas consultas antes de excluir, "
                        "ou aguarde a finalização — o histórico não pode ser apagado."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        MovimentacaoEstoque.objects.filter(produto=obj).delete()
        try:
            obj.delete()
        except ProtectedError:
            return Response(
                {
                    "error": (
                        "Não é possível excluir este produto porque ele está vinculado "
                        "a outros registros do sistema."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProdutoEstoqueMoverView(GetObjectMixin, APIView):
    """POST /clinica-beleza/estoque/mover/ — move um ou mais produtos para outra categoria."""

    permission_classes = CLINICA_ESTOQUE

    def post(self, request):
        from tenants.middleware import ensure_loja_context

        ensure_loja_context(request)
        loja_id = resolve_loja_id_from_request(request)
        ids = request.data.get("produto_ids") or request.data.get("ids") or []
        if not isinstance(ids, list) or not ids:
            single = request.data.get("produto_id")
            if single:
                ids = [single]
        try:
            ids = [int(x) for x in ids]
        except (TypeError, ValueError):
            return Response({"error": "produto_ids inválidos."}, status=status.HTTP_400_BAD_REQUEST)

        cat_id = request.data.get("categoria_id")
        cat_slug = request.data.get("categoria")
        cat = resolver_categoria(
            loja_id=loja_id,
            categoria_id=int(cat_id) if cat_id not in (None, "") else None,
            slug=str(cat_slug) if cat_slug else None,
        )
        if not cat:
            return Response({"error": "Categoria destino não encontrada."}, status=status.HTTP_400_BAD_REQUEST)

        updated = ProdutoEstoque.objects.filter(id__in=ids).update(categoria=cat)
        return Response({"moved": updated, "categoria_id": cat.id, "categoria_slug": cat.slug})


class MovimentacaoEstoqueView(GetObjectMixin, APIView):
    """GET  /clinica-beleza/estoque/<id>/movimentar/ — lista histórico de movimentações
    POST /clinica-beleza/estoque/<id>/movimentar/ — registra entrada/saída
    """

    permission_classes = CLINICA_ESTOQUE
    model_class = ProdutoEstoque
    not_found_message = "Produto não encontrado"

    def get(self, request, pk):
        produto, error = self.object_or_404(pk)
        if error:
            return error
        movs = MovimentacaoEstoque.objects.filter(produto=produto).order_by("-created_at")[:50]
        return Response(MovimentacaoEstoqueSerializer(movs, many=True).data)

    def post(self, request, pk):
        produto, error = self.object_or_404(pk)
        if error:
            return error

        from .estoque_movimentacao_service import EstoqueMovimentacaoError, registrar_movimentacao

        try:
            mov = registrar_movimentacao(
                produto=produto,
                tipo=(request.data.get("tipo") or "").strip(),
                quantidade_raw=request.data.get("quantidade", 0),
                motivo=(request.data.get("motivo") or "").strip(),
                profissional_id=request.data.get("profissional_id"),
                appointment_id=request.data.get("appointment_id"),
            )
        except EstoqueMovimentacaoError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "id": mov.id,
            "produto": produto.nome,
            "tipo": mov.tipo,
            "quantidade": float(mov.quantidade),
            "quantidade_atual": float(produto.quantidade_atual),
            "estoque_baixo": produto.estoque_baixo,
        })


class EstoqueResumoView(APIView):
    """GET /clinica-beleza/estoque/resumo/
    Resumo: total produtos, estoque baixo, valor total.
    """

    permission_classes = CLINICA_ESTOQUE

    def get(self, request):
        from datetime import date, timedelta

        from tenants.middleware import ensure_loja_context

        ensure_loja_context(request)
        produtos = ProdutoEstoque.objects.filter(is_active=True)
        total_produtos = produtos.count()
        estoque_baixo = produtos.filter(quantidade_atual__lte=F("quantidade_minima")).count()
        valor_total = produtos.aggregate(
            total=Sum(F("quantidade_atual") * F("preco_custo")),
        )["total"] or 0

        hoje = date.today()
        validade_proxima = 0
        for p in produtos.filter(validade__isnull=False).values("validade", "dias_alerta_validade"):
            limite = hoje + timedelta(days=p["dias_alerta_validade"] or 90)
            if p["validade"] <= limite:
                validade_proxima += 1

        return Response({
            "total_produtos": total_produtos,
            "estoque_baixo": estoque_baixo,
            "validade_proxima": validade_proxima,
            "valor_total_estoque": float(valor_total),
        })


def _decimal(valor) -> str:
    return f"{valor:.2f}" if valor is not None else "0.00"


class EstoqueProdutoComprasView(GetObjectMixin, APIView):
    """GET /clinica-beleza/estoque/<id>/compras/ — fornecedores, preços e lotes."""

    permission_classes = CLINICA_ESTOQUE
    model_class = ProdutoEstoque
    not_found_message = "Produto não encontrado"

    def get(self, request, pk):
        from datetime import date, timedelta

        from .estoque_lotes import resumo_saldos
        from .estoque_nfe_vinculo import custo_total_estoque, serie_da_chave
        from .models import CompraFornecedorEstoque, LoteProdutoEstoque, VinculoProdutoFornecedor

        produto, error = self.object_or_404(pk)
        if error:
            return error

        vinculos = [
            {
                "documento": v.documento,
                "codigo": v.codigo,
                "gtin": v.gtin,
                "fator": f"{v.fator:.4f}",
                "preco": _decimal(v.preco),
                "nome_no_fornecedor": v.nome_no_fornecedor,
            }
            for v in VinculoProdutoFornecedor.objects.filter(produto=produto).order_by("documento", "codigo")
        ]
        compras = []
        for c in CompraFornecedorEstoque.objects.filter(produto=produto).order_by("-data_compra", "-id")[:40]:
            compras.append({
                "documento": c.documento,
                "fornecedor_nome": c.fornecedor_nome,
                "codigo": c.codigo,
                "numero_nota": c.numero_nota,
                "chave": c.chave,
                "data_compra": c.data_compra.isoformat() if c.data_compra else "",
                "quantidade": _decimal(c.quantidade),
                "unidade": c.unidade,
                "quantidade_estoque": _decimal(c.quantidade_estoque),
                "unidade_estoque": c.unidade_estoque,
                "fator": f"{c.fator:.4f}",
                "custo_unitario": _decimal(c.custo_unitario),
                "custo_total": _decimal(custo_total_estoque(c.custo_unitario, c.quantidade_estoque)),
                "serie": serie_da_chave(c.chave),
                "lote": c.lote,
                "validade": c.validade.isoformat() if c.validade else "",
                "usuario": c.usuario,
                "registrado_em": c.created_at.isoformat() if c.created_at else "",
            })
        hoje = date.today()
        limite = hoje + timedelta(days=produto.dias_alerta_validade or 90)
        lotes = []
        for lote in LoteProdutoEstoque.objects.filter(produto=produto, quantidade__gt=0).order_by("validade", "codigo"):
            vencido = bool(lote.validade and lote.validade < hoje)
            lotes.append({
                "codigo": lote.codigo,
                "validade": lote.validade.isoformat() if lote.validade else "",
                "quantidade": _decimal(lote.quantidade),
                "fornecedor_nome": lote.fornecedor_nome,
                "numero_nota": lote.numero_nota,
                "serie": serie_da_chave(lote.chave),
                "chave": lote.chave,
                "alerta_validade": bool(lote.validade and not vencido and lote.validade <= limite),
                "vencido": vencido,
                "sem_validade": lote.validade is None,
            })
        resumo = resumo_saldos(
            produto.quantidade_atual,
            [{"quantidade": lote["quantidade"], "validade": lote["validade"] or None} for lote in lotes],
            ativo=produto.is_active,
            hoje=hoje,
        )
        return Response({
            "exige_lote": produto.exige_lote,
            "quantidade_atual": _decimal(resumo["total"]),
            "quantidade_utilizavel": _decimal(resumo["utilizavel"]),
            "quantidade_em_lotes": _decimal(resumo["em_lotes"]),
            "quantidade_sem_lote": _decimal(resumo["sem_lote"]),
            "vinculos": vinculos,
            "compras": compras,
            "lotes": lotes,
        })
