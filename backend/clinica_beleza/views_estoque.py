"""
Views de Estoque — Clínica da Beleza
Controle de produtos (botox, ácido hialurônico, soros, etc.)
"""
import logging
from decimal import Decimal

from django.db.models import F, Sum
from rest_framework.views import APIView
from rest_framework.response import Response
from .permissions import CLINICA_ESTOQUE, CLINICA_ESTOQUE_LEITURA
from rest_framework import status

from .models import ProdutoEstoque, MovimentacaoEstoque
from .serializers import ProdutoEstoqueSerializer, MovimentacaoEstoqueSerializer
from .pagination import paginate_queryset
from .views_base import GetObjectMixin

logger = logging.getLogger(__name__)

# Campos para listagem via .values() (inclui numero_nota desde migration 0034).
_PRODUTO_VALUES_FIELDS = (
    'id', 'nome', 'categoria', 'marca', 'unidade_medida',
    'quantidade_atual', 'quantidade_minima', 'preco_custo', 'preco_venda',
    'validade', 'lote', 'numero_nota', 'dias_alerta_validade',
    'observacoes', 'is_active', 'created_at', 'updated_at',
)
_CATEGORIA_LABELS = dict(ProdutoEstoque.CATEGORIA_CHOICES)


def _produto_values_row(row: dict) -> dict:
    item = dict(row)
    item.setdefault('numero_nota', '')
    item['categoria_display'] = _CATEGORIA_LABELS.get(row.get('categoria'), row.get('categoria'))
    item['estoque_baixo'] = row.get('quantidade_atual', 0) <= row.get('quantidade_minima', 0)
    # Alerta de validade
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


class ProdutoEstoqueListView(APIView):
    """
    GET /clinica-beleza/estoque/
    POST /clinica-beleza/estoque/
    """
    permission_classes = CLINICA_ESTOQUE

    def get_permissions(self):
        # Profissionais em consulta listam insumos; gestão (POST/PUT) continua CLINICA_ESTOQUE.
        if self.request.method == 'GET':
            return [perm() for perm in CLINICA_ESTOQUE_LEITURA]
        return [perm() for perm in CLINICA_ESTOQUE]

    def get(self, request):
        from tenants.middleware import ensure_loja_context

        ensure_loja_context(request)
        qs = ProdutoEstoque.objects.all().order_by('nome')
        categoria = request.query_params.get('categoria')
        if categoria:
            qs = qs.filter(categoria=categoria)
        search = (request.query_params.get('search') or '').strip()
        if search:
            qs = qs.filter(nome__icontains=search)
        apenas_ativos = request.query_params.get('active', 'true').lower() == 'true'
        if apenas_ativos:
            qs = qs.filter(is_active=True)
        estoque_baixo = request.query_params.get('estoque_baixo')
        if estoque_baixo == 'true':
            qs = qs.filter(quantidade_atual__lte=F('quantidade_minima'))
        # Sempre via .values() para resposta leve na listagem.
        return _paginate_produtos_values(qs, request)

    def post(self, request):
        serializer = ProdutoEstoqueSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProdutoEstoqueDetailView(GetObjectMixin, APIView):
    """GET /clinica-beleza/estoque/<id>/  PUT  DELETE"""
    permission_classes = CLINICA_ESTOQUE
    model_class = ProdutoEstoque
    not_found_message = 'Produto não encontrado'

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
        serializer = ProdutoEstoqueSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        obj, error = self.object_or_404(pk)
        if error:
            return error
        # Hard delete: remove produto e movimentações associadas
        MovimentacaoEstoque.objects.filter(produto=obj).delete()
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


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

        tipo = request.data.get('tipo', '').strip()
        if tipo not in ('entrada', 'saida', 'ajuste'):
            return Response({'error': 'Tipo deve ser: entrada, saida ou ajuste'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            quantidade = Decimal(str(request.data.get('quantidade', 0)))
            if quantidade <= 0:
                return Response({'error': 'Quantidade deve ser maior que zero'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({'error': 'Quantidade inválida'}, status=status.HTTP_400_BAD_REQUEST)

        motivo = (request.data.get('motivo') or '').strip()
        profissional_id = request.data.get('profissional_id')
        appointment_id = request.data.get('appointment_id')

        # Atualizar quantidade
        if tipo == 'entrada':
            produto.quantidade_atual += quantidade
        elif tipo == 'saida':
            if produto.quantidade_atual < quantidade:
                return Response(
                    {'error': f'Estoque insuficiente. Disponível: {produto.quantidade_atual} {produto.unidade_medida}'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            produto.quantidade_atual -= quantidade
        elif tipo == 'ajuste':
            produto.quantidade_atual = quantidade

        produto.save(update_fields=['quantidade_atual', 'updated_at'])

        # Registrar movimentação
        mov = MovimentacaoEstoque.objects.create(
            produto=produto,
            tipo=tipo,
            quantidade=quantidade,
            motivo=motivo,
            profissional_id=profissional_id,
            appointment_id=appointment_id,
        )

        return Response({
            'id': mov.id,
            'produto': produto.nome,
            'tipo': tipo,
            'quantidade': float(quantidade),
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

        # Produtos com validade próxima do vencimento
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

        categoria = request.data.get('categoria', 'outro')
        confirmar = request.data.get('confirmar', 'false').lower() in ('true', '1')

        try:
            xml_content = arquivo.read()
            resultado = importar_produtos_xml(xml_content, categoria=categoria)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception('Erro ao processar XML de estoque: %s', e)
            return Response({'error': 'Erro ao processar o XML. Verifique o formato.'}, status=status.HTTP_400_BAD_REQUEST)

        if not confirmar:
            # Preview: retorna produtos encontrados sem salvar
            # Verificar se destinatário confere com a loja
            from tenants.middleware import get_current_loja_id
            from superadmin.models import Loja
            import re

            aviso_destinatario = None
            loja_id = get_current_loja_id()
            if loja_id and resultado.get('nota', {}).get('destinatario_documento'):
                loja = Loja.objects.filter(id=loja_id).first()
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

        # Confirmar: criar ou atualizar produtos no estoque
        from .estoque_xml_import_service import confirmar_importacao_xml

        result = confirmar_importacao_xml(resultado['produtos'])

        # Incluir aviso de destinatário também na confirmação
        from tenants.middleware import get_current_loja_id
        from superadmin.models import Loja
        import re

        aviso_destinatario = None
        loja_id = get_current_loja_id()
        if loja_id and resultado.get('nota', {}).get('destinatario_documento'):
            loja = Loja.objects.filter(id=loja_id).first()
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
