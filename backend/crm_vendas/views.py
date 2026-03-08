from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from datetime import timedelta

from core.views import BaseModelViewSet
from .models import Vendedor, Conta, Lead, Contato, Oportunidade, Atividade
from .serializers import (
    VendedorSerializer,
    ContaSerializer,
    LeadSerializer,
    LeadListSerializer,
    ContatoSerializer,
    OportunidadeSerializer,
    AtividadeSerializer,
)
from tenants.middleware import get_current_loja_id


class VendedorViewSet(BaseModelViewSet):
    queryset = Vendedor.objects.all()
    serializer_class = VendedorSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if hasattr(Vendedor, 'is_active'):
            return qs.filter(is_active=True)
        return qs


class ContaViewSet(BaseModelViewSet):
    queryset = Conta.objects.all()
    serializer_class = ContaSerializer


class LeadViewSet(BaseModelViewSet):
    queryset = Lead.objects.select_related('conta').all()
    serializer_class = LeadSerializer

    def get_serializer_class(self):
        if self.action == 'list':
            return LeadListSerializer
        return LeadSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        status = self.request.query_params.get('status')
        if status:
            qs = qs.filter(status=status)
        origem = self.request.query_params.get('origem')
        if origem:
            qs = qs.filter(origem=origem)
        return qs


class ContatoViewSet(BaseModelViewSet):
    queryset = Contato.objects.select_related('conta').all()
    serializer_class = ContatoSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        conta_id = self.request.query_params.get('conta_id')
        if conta_id:
            qs = qs.filter(conta_id=conta_id)
        return qs


class OportunidadeViewSet(BaseModelViewSet):
    queryset = Oportunidade.objects.select_related('lead', 'vendedor').all()
    serializer_class = OportunidadeSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        etapa = self.request.query_params.get('etapa')
        if etapa:
            qs = qs.filter(etapa=etapa)
        vendedor_id = self.request.query_params.get('vendedor_id')
        if vendedor_id:
            qs = qs.filter(vendedor_id=vendedor_id)
        return qs


class AtividadeViewSet(BaseModelViewSet):
    queryset = Atividade.objects.select_related('oportunidade', 'lead').all()
    serializer_class = AtividadeSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        concluido = self.request.query_params.get('concluido')
        if concluido is not None:
            qs = qs.filter(concluido=concluido.lower() == 'true')
        oportunidade_id = self.request.query_params.get('oportunidade_id')
        if oportunidade_id:
            qs = qs.filter(oportunidade_id=oportunidade_id)
        lead_id = self.request.query_params.get('lead_id')
        if lead_id:
            qs = qs.filter(lead_id=lead_id)
        data_inicio = self.request.query_params.get('data_inicio')
        if data_inicio:
            dt = parse_datetime(data_inicio)
            if dt:
                qs = qs.filter(data__gte=dt)
        data_fim = self.request.query_params.get('data_fim')
        if data_fim:
            dt = parse_datetime(data_fim)
            if dt:
                qs = qs.filter(data__lte=dt)
        return qs


def _empty_dashboard_response():
    """Resposta vazia padrão quando não há contexto de loja."""
    return {
        'leads': 0,
        'oportunidades': 0,
        'receita': 0,
        'pipeline_aberto': 0,
        'meta_vendas': 0,
        'taxa_conversao': 0,
        'pipeline_por_etapa': [],
        'atividades_hoje': [],
        'performance_vendedores': [],
    }


ETAPAS_PIPELINE = [
    'prospecting', 'qualification', 'proposal', 'negotiation', 'closed_won',
]


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_data(request):
    """
    Dados do dashboard CRM (estilo Salesforce).
    Retorna: leads, oportunidades, receita, pipeline por etapa,
    atividades do dia, performance por vendedor.
    """
    import logging
    logger = logging.getLogger(__name__)

    loja_id = get_current_loja_id()
    if not loja_id:
        return Response(_empty_dashboard_response(), status=200)

    try:
        from .models import Lead, Oportunidade, Atividade, Vendedor

        # LojaIsolationManager já filtra por loja_id; usar .all() para respeitar o manager
        leads_qs = Lead.objects.all()
        opp_qs = Oportunidade.objects.all()
        atividades_qs = Atividade.objects.all()
        vendedores_qs = Vendedor.objects.filter(is_active=True)

        # Totais (1 query cada)
        total_leads = leads_qs.count()
        total_oportunidades = opp_qs.count()
        receita = opp_qs.filter(etapa='closed_won').aggregate(total=Sum('valor'))['total'] or 0
        pipeline_aberto = opp_qs.exclude(
            etapa__in=['closed_won', 'closed_lost']
        ).aggregate(total=Sum('valor'))['total'] or 0

        # Pipeline por etapa: 1 query por etapa (agregado)
        pipeline_por_etapa = []
        for etapa in ETAPAS_PIPELINE:
            agg = opp_qs.filter(etapa=etapa).aggregate(
                valor=Sum('valor'),
                qtd=Count('id'),
            )
            pipeline_por_etapa.append({
                'etapa': etapa,
                'valor': float(agg['valor'] or 0),
                'quantidade': agg['qtd'] or 0,
            })

        # Atividades de hoje (limitado, com select_related)
        hoje_inicio = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        hoje_fim = hoje_inicio + timedelta(days=1)
        atividades_hoje = atividades_qs.filter(
            data__gte=hoje_inicio,
            data__lt=hoje_fim,
        ).select_related('oportunidade', 'lead').order_by('concluido', 'data')[:20]
        atividades_hoje_data = AtividadeSerializer(atividades_hoje, many=True).data

        # Performance por vendedor: 1 query com annotate (evita loop de queries)
        mes_inicio = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        perf_qs = vendedores_qs.annotate(
            receita_mes=Sum(
                'oportunidades__valor',
                filter=Q(oportunidades__etapa='closed_won') & Q(oportunidades__data_fechamento__gte=mes_inicio),
            ),
        )
        performance_vendedores = [
            {'id': v.id, 'nome': v.nome, 'receita_mes': float(v.receita_mes or 0)}
            for v in perf_qs
        ]

        # Taxa de conversão
        total_fechados = opp_qs.filter(etapa__in=['closed_won', 'closed_lost']).count()
        total_ganhos = opp_qs.filter(etapa='closed_won').count()
        taxa_conversao = round((total_ganhos / total_fechados * 100), 1) if total_fechados else 0

        return Response({
            'leads': total_leads,
            'oportunidades': total_oportunidades,
            'receita': float(receita),
            'pipeline_aberto': float(pipeline_aberto),
            'meta_vendas': 0,
            'taxa_conversao': taxa_conversao,
            'pipeline_por_etapa': pipeline_por_etapa,
            'atividades_hoje': atividades_hoje_data,
            'performance_vendedores': performance_vendedores,
        })
    except Exception as e:
        logger.exception('Erro no dashboard CRM: %s', e)
        return Response(
            {'detail': 'Erro ao carregar dashboard. Tente novamente.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
