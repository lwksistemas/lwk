from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Sum, Count, Q
from django.utils import timezone
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
        return qs


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_data(request):
    """
    Dados do dashboard CRM (estilo Salesforce).
    Retorna: leads, oportunidades, receita, pipeline por etapa,
    atividades do dia, performance por vendedor.
    """
    loja_id = get_current_loja_id()
    if not loja_id:
        return Response({
            'leads': 0,
            'oportunidades': 0,
            'receita': 0,
            'pipeline_aberto': 0,
            'meta_vendas': 0,
            'taxa_conversao': 0,
            'pipeline_por_etapa': [],
            'atividades_hoje': [],
            'performance_vendedores': [],
        }, status=200)

    # Base querysets filtrados por loja
    from .models import Lead, Oportunidade, Atividade, Vendedor

    leads_qs = Lead.objects.filter(loja_id=loja_id)
    opp_qs = Oportunidade.objects.filter(loja_id=loja_id)
    atividades_qs = Atividade.objects.filter(loja_id=loja_id)
    vendedores_qs = Vendedor.objects.filter(loja_id=loja_id, is_active=True)

    # Totais
    total_leads = leads_qs.count()
    total_oportunidades = opp_qs.count()
    receita = opp_qs.filter(etapa='closed_won').aggregate(
        total=Sum('valor')
    )['total'] or 0
    pipeline_aberto = opp_qs.exclude(
        etapa__in=['closed_won', 'closed_lost']
    ).aggregate(total=Sum('valor'))['total'] or 0

    # Pipeline por etapa (valores)
    etapas = [
        'prospecting', 'qualification', 'proposal', 'negotiation', 'closed_won',
    ]
    pipeline_por_etapa = []
    for etapa in etapas:
        valor = opp_qs.filter(etapa=etapa).aggregate(s=Sum('valor'))['s'] or 0
        pipeline_por_etapa.append({
            'etapa': etapa,
            'valor': float(valor),
            'quantidade': opp_qs.filter(etapa=etapa).count(),
        })

    # Atividades de hoje (não concluídas primeiro)
    hoje_inicio = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    hoje_fim = hoje_inicio + timedelta(days=1)
    atividades_hoje = atividades_qs.filter(
        data__gte=hoje_inicio,
        data__lt=hoje_fim,
    ).select_related('oportunidade', 'lead').order_by('concluido', 'data')[:20]
    atividades_hoje_data = AtividadeSerializer(atividades_hoje, many=True).data

    # Performance por vendedor (receita fechada no mês)
    mes_inicio = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    performance_vendedores = []
    for v in vendedores_qs:
        receita_v = Oportunidade.objects.filter(
            loja_id=loja_id,
            vendedor=v,
            etapa='closed_won',
            data_fechamento__gte=mes_inicio,
        ).aggregate(s=Sum('valor'))['s'] or 0
        performance_vendedores.append({
            'id': v.id,
            'nome': v.nome,
            'receita_mes': float(receita_v),
        })

    # Taxa de conversão (simplificada: fechados ganhos / total oportunidades com etapa fechada)
    total_fechados = opp_qs.filter(
        etapa__in=['closed_won', 'closed_lost']
    ).count()
    total_ganhos = opp_qs.filter(etapa='closed_won').count()
    taxa_conversao = round((total_ganhos / total_fechados * 100), 1) if total_fechados else 0

    return Response({
        'leads': total_leads,
        'oportunidades': total_oportunidades,
        'receita': float(receita),
        'pipeline_aberto': float(pipeline_aberto),
        'meta_vendas': 0,  # Pode vir de configuração da loja depois
        'taxa_conversao': taxa_conversao,
        'pipeline_por_etapa': pipeline_por_etapa,
        'atividades_hoje': atividades_hoje_data,
        'performance_vendedores': performance_vendedores,
    })
