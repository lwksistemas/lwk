"""
Views de Estoque — Clínica da Beleza
Controle de produtos (botox, ácido hialurônico, soros, etc.)
"""
import logging
import re

from django.db.models import F, Sum
from django.utils.text import slugify
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .permissions import CLINICA_ESTOQUE, CLINICA_ESTOQUE_LEITURA
from .models import ProdutoEstoque, MovimentacaoEstoque
from .models.estoque import CategoriaEstoque
from .serializers import ProdutoEstoqueSerializer, MovimentacaoEstoqueSerializer
from .serializers.estoque import CategoriaEstoqueSerializer
from .pagination import paginate_queryset
from .views_base import GetObjectMixin, resolve_loja_id_from_request
from .estoque_categorias import (
    categorias_com_contagem,
    garantir_categorias_estoque_padrao,
    normalizar_slug_categoria,
    resolver_categoria,
)

logger = logging.getLogger(__name__)

# Campos para listagem via .values() (inclui numero_nota desde migration 0034).
_PRODUTO_VALUES_FIELDS = (
    'id', 'nome', 'categoria_id', 'categoria__slug', 'categoria__nome', 'categoria__cor',
    'marca', 'unidade_medida',
    'quantidade_atual', 'quantidade_minima', 'preco_custo', 'preco_venda',
    'validade', 'lote', 'numero_nota', 'dias_alerta_validade',
    'observacoes', 'is_active', 'created_at', 'updated_at',
)


def _produto_values_row(row: dict) -> dict:
    item = dict(row)
    item.setdefault('numero_nota', '')
    item['categoria'] = row.get('categoria_id')
    item['categoria_slug'] = row.get('categoria__slug') or 'outro'
    item['categoria_display'] = row.get('categoria__nome') or 'Outro'
    item['categoria_cor'] = row.get('categoria__cor') or '#8B3D52'
    item.pop('categoria__slug', None)
    item.pop('categoria__nome', None)
    item.pop('categoria__cor', None)
    item['estoque_baixo'] = row.get('quantidade_atual', 0) <= row.get('quantidade_minima', 0)
    validade = row.get('validade')
    dias_alerta = row.get('dias_alerta_validade') or 90
    if validade:
        from datetime import date, timedelta
        limite = date.today() + timedelta(days=dias_alerta)
        item['validade_proxima'] = validade <= limite
    else:
        item['validade_proxima'] = False
    return item


def _paginate_produtos_values(queryset, request):
    """Lista produtos via .values() usando paginação padrão."""
    return paginate_queryset(
        queryset.values(*_PRODUTO_VALUES_FIELDS),
        request,
        to_representation=_produto_values_row,
    )


def _filtrar_por_categoria(qs, request):
    categoria_id = request.query_params.get('categoria_id')
    categoria = request.query_params.get('categoria')
    if categoria_id:
        try:
            return qs.filter(categoria_id=int(categoria_id))
        except (TypeError, ValueError):
            return qs.none()
    if not categoria:
        return qs
    cat = str(categoria).strip()
    if cat.isdigit():
        return qs.filter(categoria_id=int(cat))
    return qs.filter(categoria__slug=normalizar_slug_categoria(cat))


class CategoriaEstoqueListView(APIView):
    """GET/POST /clinica-beleza/estoque/categorias/"""
    permission_classes = CLINICA_ESTOQUE

    def get_permissions(self):
        if self.request.method == 'GET':
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
        nome = serializer.validated_data['nome']
        base_slug = slugify(nome, allow_unicode=True)[:50] or 'categoria'
        slug = base_slug
        n = 2
        while CategoriaEstoque.objects.filter(loja_id=loja_id, slug=slug).exists():
            slug = f'{base_slug[:45]}-{n}'
            n += 1
        ordem = serializer.validated_data.get('ordem')
        if ordem is None:
            last = CategoriaEstoque.objects.filter(loja_id=loja_id).order_by('-ordem').first()
            ordem = (last.ordem + 1) if last else 1
        obj = serializer.save(loja_id=loja_id, slug=slug, ordem=ordem)
        obj.produtos_count = 0
        return Response(CategoriaEstoqueSerializer(obj).data, status=status.HTTP_201_CREATED)


class CategoriaEstoqueDetailView(GetObjectMixin, APIView):
    """GET/PUT/DELETE /clinica-beleza/estoque/categorias/<id>/"""
    permission_classes = CLINICA_ESTOQUE
    model_class = CategoriaEstoque
    not_found_message = 'Categoria não encontrada'

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
                {'error': f'Não é possível excluir: há {ativos} produto(s) nesta categoria.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProdutoEstoqueListView(APIView):
    """
    GET /clinica-beleza/estoque/
    POST /clinica-beleza/estoque/
    """
    permission_classes = CLINICA_ESTOQUE

    def get_permissions(self):
        if self.request.method == 'GET':
            return [perm() for perm in CLINICA_ESTOQUE_LEITURA]
        return [perm() for perm in CLINICA_ESTOQUE]

    def get(self, request):
        from tenants.middleware import ensure_loja_context

        ensure_loja_context(request)
        loja_id = resolve_loja_id_from_request(request)
        garantir_categorias_estoque_padrao(loja_id)
        qs = ProdutoEstoque.objects.all().order_by('nome')
        qs = _filtrar_por_categoria(qs, request)
        search = (request.query_params.get('search') or '').strip()
        if search:
            qs = qs.filter(nome__icontains=search)
        apenas_ativos = request.query_params.get('active', 'true').lower() == 'true'
        if apenas_ativos:
            qs = qs.filter(is_active=True)
        estoque_baixo = request.query_params.get('estoque_baixo')
        if estoque_baixo == 'true':
            qs = qs.filter(quantidade_atual__lte=F('quantidade_minima'))
        return _paginate_produtos_values(qs, request)

    def post(self, request):
        from tenants.middleware import ensure_loja_context

        ensure_loja_context(request)
        loja_id = resolve_loja_id_from_request(request)
        garantir_categorias_estoque_padrao(loja_id)
        serializer = ProdutoEstoqueSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProdutoEstoqueDetailView(GetObjectMixin, APIView):
    """GET /clinica-beleza/estoque/<id>/  PUT  DELETE"""
    permission_classes = CLINICA_ESTOQUE
    model_class = ProdutoEstoque
    not_found_message = 'Produto não encontrado'
    select_related_fields = ('categoria',)

    def get_permissions(self):
        if self.request.method == 'GET':
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
            obj, data=request.data, partial=True, context={'request': request},
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

        usos = ConsultaProdutoUtilizado.objects.filter(produto=obj).select_related('consulta')
        if usos.exists():
            n_finalizadas = usos.filter(consulta__status='COMPLETED').count()
            if n_finalizadas:
                return Response(
                    {
                        'error': (
                            'Não é possível excluir este produto: ele foi utilizado em '
                            f'{n_finalizadas} consulta(s) finalizada(s). '
                            'O histórico clínico precisa ser preservado.'
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(
                {
                    'error': (
                        'Não é possível excluir este produto: ele já foi registrado em '
                        'consulta(s). Remova o vínculo nas consultas antes de excluir, '
                        'ou aguarde a finalização — o histórico não pode ser apagado.'
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
                    'error': (
                        'Não é possível excluir este produto porque ele está vinculado '
                        'a outros registros do sistema.'
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
        ids = request.data.get('produto_ids') or request.data.get('ids') or []
        if not isinstance(ids, list) or not ids:
            single = request.data.get('produto_id')
            if single:
                ids = [single]
        try:
            ids = [int(x) for x in ids]
        except (TypeError, ValueError):
            return Response({'error': 'produto_ids inválidos.'}, status=status.HTTP_400_BAD_REQUEST)

        cat_id = request.data.get('categoria_id')
        cat_slug = request.data.get('categoria')
        cat = resolver_categoria(
            loja_id=loja_id,
            categoria_id=int(cat_id) if cat_id not in (None, '') else None,
            slug=str(cat_slug) if cat_slug else None,
        )
        if not cat:
            return Response({'error': 'Categoria destino não encontrada.'}, status=status.HTTP_400_BAD_REQUEST)

        updated = ProdutoEstoque.objects.filter(id__in=ids).update(categoria=cat)
        return Response({'moved': updated, 'categoria_id': cat.id, 'categoria_slug': cat.slug})


class MovimentacaoEstoqueView(GetObjectMixin, APIView):
    """
    GET  /clinica-beleza/estoque/<id>/movimentar/ — lista histórico de movimentações
    POST /clinica-beleza/estoque/<id>/movimentar/ — registra entrada/saída
    """
    permission_classes = CLINICA_ESTOQUE
    model_class = ProdutoEstoque
    not_found_message = 'Produto não encontrado'

    def get(self, request, pk):
        produto, error = self.object_or_404(pk)
        if error:
            return error
        movs = MovimentacaoEstoque.objects.filter(produto=produto).order_by('-created_at')[:50]
        return Response(MovimentacaoEstoqueSerializer(movs, many=True).data)

    def post(self, request, pk):
        produto, error = self.object_or_404(pk)
        if error:
            return error

        from .estoque_movimentacao_service import registrar_movimentacao, EstoqueMovimentacaoError

        try:
            mov = registrar_movimentacao(
                produto=produto,
                tipo=(request.data.get('tipo') or '').strip(),
                quantidade_raw=request.data.get('quantidade', 0),
                motivo=(request.data.get('motivo') or '').strip(),
                profissional_id=request.data.get('profissional_id'),
                appointment_id=request.data.get('appointment_id'),
            )
        except EstoqueMovimentacaoError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'id': mov.id,
            'produto': produto.nome,
            'tipo': mov.tipo,
            'quantidade': float(mov.quantidade),
            'quantidade_atual': float(produto.quantidade_atual),
            'estoque_baixo': produto.estoque_baixo,
        })


class EstoqueResumoView(APIView):
    """
    GET /clinica-beleza/estoque/resumo/
    Resumo: total produtos, estoque baixo, valor total.
    """
    permission_classes = CLINICA_ESTOQUE

    def get(self, request):
        from tenants.middleware import ensure_loja_context
        from datetime import date, timedelta

        ensure_loja_context(request)
        produtos = ProdutoEstoque.objects.filter(is_active=True)
        total_produtos = produtos.count()
        estoque_baixo = produtos.filter(quantidade_atual__lte=F('quantidade_minima')).count()
        valor_total = produtos.aggregate(
            total=Sum(F('quantidade_atual') * F('preco_custo'))
        )['total'] or 0

        hoje = date.today()
        validade_proxima = 0
        for p in produtos.filter(validade__isnull=False).values('validade', 'dias_alerta_validade'):
            limite = hoje + timedelta(days=p['dias_alerta_validade'] or 90)
            if p['validade'] <= limite:
                validade_proxima += 1

        return Response({
            'total_produtos': total_produtos,
            'estoque_baixo': estoque_baixo,
            'validade_proxima': validade_proxima,
            'valor_total_estoque': float(valor_total),
        })


class EstoqueImportarXmlView(APIView):
    """
    POST /clinica-beleza/estoque/importar-xml/
    Upload de XML NF-e para importar produtos ao estoque.

    Body: multipart/form-data com campo 'arquivo' (XML) e 'categoria' (opcional).
    Retorna preview dos produtos encontrados ou cria se 'confirmar=true'.
    """
    permission_classes = CLINICA_ESTOQUE

    def post(self, request):
        from core.upload_validation import validate_xml_upload
        from .estoque_xml_import_service import importar_produtos_xml

        arquivo = request.FILES.get('arquivo')
        if not arquivo:
            return Response({'error': 'Envie o arquivo XML da NF-e.'}, status=status.HTTP_400_BAD_REQUEST)

        valid, msg = validate_xml_upload(arquivo)
        if not valid:
            return Response({'error': msg}, status=status.HTTP_400_BAD_REQUEST)

        loja_id = resolve_loja_id_from_request(request)
        garantir_categorias_estoque_padrao(loja_id)

        categoria_raw = request.data.get('categoria', 'outro')
        categoria_id = request.data.get('categoria_id')
        forcar = str(request.data.get('forcar_categoria', 'false')).lower() in ('true', '1')
        cat = resolver_categoria(
            loja_id=loja_id,
            categoria_id=int(categoria_id) if categoria_id not in (None, '') else None,
            slug=str(categoria_raw) if categoria_raw else 'outro',
        )
        categoria_slug = cat.slug if cat else normalizar_slug_categoria(str(categoria_raw))
        confirmar = str(request.data.get('confirmar', 'false')).lower() in ('true', '1')

        try:
            xml_content = arquivo.read()
            resultado = importar_produtos_xml(
                xml_content,
                categoria=categoria_slug,
                categoria_id=cat.id if cat else None,
                loja_id=loja_id,
                forcar_categoria=forcar,
            )
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception('Erro ao processar XML de estoque: %s', e)
            return Response({'error': 'Erro ao processar o XML. Verifique o formato.'}, status=status.HTTP_400_BAD_REQUEST)

        if not confirmar:
            aviso_destinatario = None
            from tenants.middleware import get_current_loja_id
            from superadmin.models import Loja

            lid = get_current_loja_id() or loja_id
            if lid and resultado.get('nota', {}).get('destinatario_documento'):
                loja = Loja.objects.filter(id=lid).first()
                if loja:
                    loja_doc = re.sub(r'\D', '', loja.cpf_cnpj or '')
                    nf_doc = re.sub(r'\D', '', resultado['nota']['destinatario_documento'])
                    if loja_doc and nf_doc and loja_doc != nf_doc:
                        aviso_destinatario = (
                            f'O destinatário da NF ({resultado["nota"].get("destinatario_nome", "")} - '
                            f'{nf_doc}) não confere com o documento da loja ({loja_doc}).'
                        )

            response_data = {
                'preview': True,
                **resultado,
            }
            if aviso_destinatario:
                response_data['aviso_destinatario'] = aviso_destinatario
            return Response(response_data)

        from .estoque_xml_import_service import confirmar_importacao_xml
        import json

        # Permite override por item enviado no confirm (JSON string ou lista)
        produtos_override = request.data.get('produtos')
        if produtos_override:
            if isinstance(produtos_override, str):
                try:
                    produtos_override = json.loads(produtos_override)
                except json.JSONDecodeError:
                    produtos_override = None
            if isinstance(produtos_override, list) and produtos_override:
                # Mescla overrides de categoria sobre o parse do XML (prioriza slug)
                by_nome = {str(p.get('nome', '')).strip().lower(): p for p in produtos_override if isinstance(p, dict)}
                for p in resultado['produtos']:
                    ov = by_nome.get(str(p.get('nome', '')).strip().lower())
                    if not ov:
                        continue
                    if ov.get('categoria'):
                        p['categoria'] = ov['categoria']
                    if ov.get('categoria_id') not in (None, ''):
                        p['categoria_id'] = ov['categoria_id']
                    # Re-resolve na loja atual para não propagar PK de outro contexto
                    cat = resolver_categoria(
                        loja_id=loja_id,
                        categoria_id=int(p['categoria_id']) if str(p.get('categoria_id') or '').isdigit() else None,
                        slug=p.get('categoria') or 'outro',
                    )
                    if cat:
                        p['categoria'] = cat.slug
                        p['categoria_id'] = cat.id

        result = confirmar_importacao_xml(resultado['produtos'], loja_id=loja_id)

        aviso_destinatario = None
        from tenants.middleware import get_current_loja_id
        from superadmin.models import Loja

        lid = get_current_loja_id() or loja_id
        if lid and resultado.get('nota', {}).get('destinatario_documento'):
            loja = Loja.objects.filter(id=lid).first()
            if loja:
                loja_doc = re.sub(r'\D', '', loja.cpf_cnpj or '')
                nf_doc = re.sub(r'\D', '', resultado['nota']['destinatario_documento'])
                if loja_doc and nf_doc and loja_doc != nf_doc:
                    aviso_destinatario = (
                        f'O destinatário da NF ({resultado["nota"].get("destinatario_nome", "")} - '
                        f'{nf_doc}) não confere com o documento da loja ({loja_doc}).'
                    )

        response_data = {
            **result,
            'nota': resultado['nota'],
        }
        if aviso_destinatario:
            response_data['aviso_destinatario'] = aviso_destinatario

        return Response(
            response_data,
            status=status.HTTP_201_CREATED if (result['criados'] + result['atualizados']) > 0 else status.HTTP_400_BAD_REQUEST,
        )
