"""
Views de Estoque — Clínica da Beleza
Controle de produtos (botox, ácido hialurônico, soros, etc.)
"""
import logging
from decimal import Decimal
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import ProdutoEstoque, MovimentacaoEstoque

logger = logging.getLogger(__name__)


class ProdutoEstoqueListView(APIView):
    """
    GET /clinica-beleza/estoque/
    POST /clinica-beleza/estoque/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = ProdutoEstoque.objects.all().order_by('nome')
        categoria = request.query_params.get('categoria')
        if categoria:
            qs = qs.filter(categoria=categoria)
        apenas_ativos = request.query_params.get('active', 'true').lower() == 'true'
        if apenas_ativos:
            qs = qs.filter(is_active=True)
        estoque_baixo = request.query_params.get('estoque_baixo')
        if estoque_baixo == 'true':
            from django.db.models import F
            qs = qs.filter(quantidade_atual__lte=F('quantidade_minima'))

        data = []
        for p in qs:
            data.append({
                'id': p.id,
                'nome': p.nome,
                'categoria': p.categoria,
                'categoria_display': p.get_categoria_display(),
                'marca': p.marca,
                'unidade_medida': p.unidade_medida,
                'quantidade_atual': float(p.quantidade_atual),
                'quantidade_minima': float(p.quantidade_minima),
                'preco_custo': float(p.preco_custo),
                'preco_venda': float(p.preco_venda),
                'validade': p.validade.isoformat() if p.validade else None,
                'lote': p.lote,
                'observacoes': p.observacoes,
                'is_active': p.is_active,
                'estoque_baixo': p.estoque_baixo,
                'created_at': p.created_at.isoformat() if p.created_at else None,
            })
        return Response(data)

    def post(self, request):
        d = request.data
        try:
            produto = ProdutoEstoque.objects.create(
                nome=(d.get('nome') or '').strip(),
                categoria=d.get('categoria', 'outro'),
                marca=(d.get('marca') or '').strip(),
                unidade_medida=d.get('unidade_medida', 'unidade'),
                quantidade_atual=Decimal(str(d.get('quantidade_atual', 0))),
                quantidade_minima=Decimal(str(d.get('quantidade_minima', 0))),
                preco_custo=Decimal(str(d.get('preco_custo', 0))),
                preco_venda=Decimal(str(d.get('preco_venda', 0))),
                validade=d.get('validade') or None,
                lote=(d.get('lote') or '').strip(),
                observacoes=(d.get('observacoes') or '').strip(),
            )
            return Response({
                'id': produto.id,
                'nome': produto.nome,
                'categoria': produto.categoria,
                'quantidade_atual': float(produto.quantidade_atual),
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.exception('Erro ao criar produto estoque: %s', e)
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ProdutoEstoqueDetailView(APIView):
    """GET /clinica-beleza/estoque/<id>/  PUT  DELETE"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            p = ProdutoEstoque.objects.get(pk=pk)
            return Response({
                'id': p.id, 'nome': p.nome, 'categoria': p.categoria,
                'categoria_display': p.get_categoria_display(),
                'marca': p.marca, 'unidade_medida': p.unidade_medida,
                'quantidade_atual': float(p.quantidade_atual),
                'quantidade_minima': float(p.quantidade_minima),
                'preco_custo': float(p.preco_custo), 'preco_venda': float(p.preco_venda),
                'validade': p.validade.isoformat() if p.validade else None,
                'lote': p.lote, 'observacoes': p.observacoes,
                'is_active': p.is_active, 'estoque_baixo': p.estoque_baixo,
            })
        except ProdutoEstoque.DoesNotExist:
            return Response({'error': 'Produto não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        try:
            p = ProdutoEstoque.objects.get(pk=pk)
            d = request.data
            if 'nome' in d: p.nome = (d['nome'] or '').strip()
            if 'categoria' in d: p.categoria = d['categoria']
            if 'marca' in d: p.marca = (d['marca'] or '').strip()
            if 'unidade_medida' in d: p.unidade_medida = d['unidade_medida']
            if 'quantidade_minima' in d: p.quantidade_minima = Decimal(str(d['quantidade_minima']))
            if 'preco_custo' in d: p.preco_custo = Decimal(str(d['preco_custo']))
            if 'preco_venda' in d: p.preco_venda = Decimal(str(d['preco_venda']))
            if 'validade' in d: p.validade = d['validade'] or None
            if 'lote' in d: p.lote = (d['lote'] or '').strip()
            if 'observacoes' in d: p.observacoes = (d['observacoes'] or '').strip()
            if 'is_active' in d: p.is_active = bool(d['is_active'])
            p.save()
            return Response({'id': p.id, 'nome': p.nome, 'quantidade_atual': float(p.quantidade_atual)})
        except ProdutoEstoque.DoesNotExist:
            return Response({'error': 'Produto não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        try:
            p = ProdutoEstoque.objects.get(pk=pk)
            p.is_active = False
            p.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ProdutoEstoque.DoesNotExist:
            return Response({'error': 'Produto não encontrado'}, status=status.HTTP_404_NOT_FOUND)


class MovimentacaoEstoqueView(APIView):
    """
    POST /clinica-beleza/estoque/<id>/movimentar/
    Registra entrada ou saída de estoque e atualiza quantidade.
    Body: { "tipo": "entrada"|"saida"|"ajuste", "quantidade": 5, "motivo": "Compra fornecedor" }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            produto = ProdutoEstoque.objects.get(pk=pk)
        except ProdutoEstoque.DoesNotExist:
            return Response({'error': 'Produto não encontrado'}, status=status.HTTP_404_NOT_FOUND)

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
                return Response({'error': f'Estoque insuficiente. Disponível: {produto.quantidade_atual} {produto.unidade_medida}'}, status=status.HTTP_400_BAD_REQUEST)
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


class HistoricoEstoqueView(APIView):
    """
    GET /clinica-beleza/estoque/<id>/historico/
    Retorna histórico de movimentações do produto.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            produto = ProdutoEstoque.objects.get(pk=pk)
        except ProdutoEstoque.DoesNotExist:
            return Response({'error': 'Produto não encontrado'}, status=status.HTTP_404_NOT_FOUND)

        movs = MovimentacaoEstoque.objects.filter(produto=produto).select_related('profissional').order_by('-created_at')[:50]
        data = [{
            'id': m.id,
            'tipo': m.tipo,
            'tipo_display': m.get_tipo_display(),
            'quantidade': float(m.quantidade),
            'motivo': m.motivo,
            'profissional_nome': m.profissional.nome if m.profissional else None,
            'created_at': m.created_at.isoformat(),
        } for m in movs]
        return Response({'produto': produto.nome, 'movimentacoes': data})


class EstoqueResumoView(APIView):
    """
    GET /clinica-beleza/estoque/resumo/
    Resumo: total produtos, estoque baixo, valor total.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.db.models import Sum, F, Count, Q

        produtos = ProdutoEstoque.objects.filter(is_active=True)
        total_produtos = produtos.count()
        estoque_baixo = produtos.filter(quantidade_atual__lte=F('quantidade_minima')).count()
        valor_total = produtos.aggregate(
            total=Sum(F('quantidade_atual') * F('preco_custo'))
        )['total'] or 0

        return Response({
            'total_produtos': total_produtos,
            'estoque_baixo': estoque_baixo,
            'valor_total_estoque': float(valor_total),
        })
