from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
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
    AtividadeListSerializer,
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
    queryset = (
        Atividade.objects.select_related('oportunidade', 'lead')
        .defer('google_event_id')  # Evita coluna que pode não existir em schemas antigos
        .all()
    )
    serializer_class = AtividadeListSerializer

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return AtividadeSerializer
        return AtividadeListSerializer

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
            if dt and timezone.is_naive(dt):
                dt = timezone.make_aware(dt, timezone.utc)
            if dt:
                qs = qs.filter(data__gte=dt)
        data_fim = self.request.query_params.get('data_fim')
        if data_fim:
            dt = parse_datetime(data_fim)
            if dt and timezone.is_naive(dt):
                dt = timezone.make_aware(dt, timezone.utc)
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

        # Atividades de hoje: values() evita coluna google_event_id (pode não existir em schemas antigos)
        hoje_inicio = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        hoje_fim = hoje_inicio + timedelta(days=1)
        atividades_hoje_data = list(
            atividades_qs.filter(
                data__gte=hoje_inicio,
                data__lt=hoje_fim,
            )
            .order_by('concluido', 'data')
            .values('id', 'titulo', 'tipo', 'data', 'concluido', 'observacoes')[:20]
        )
        for a in atividades_hoje_data:
            if a.get('data'):
                a['data'] = a['data'].isoformat() if hasattr(a['data'], 'isoformat') else str(a['data'])

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


class WhatsAppConfigView(APIView):
    """
    Configuração WhatsApp da loja (reutiliza WhatsAppConfig da Clínica da Beleza).
    GET /crm-vendas/whatsapp-config/  → retorna flags
    PATCH /crm-vendas/whatsapp-config/ → atualiza flags
    """
    permission_classes = [IsAuthenticated]

    def _get_config(self, request=None):
        import logging
        logger = logging.getLogger(__name__)
        loja_id = get_current_loja_id()
        if not loja_id and request:
            try:
                lid = request.headers.get('X-Loja-ID')
                if lid:
                    loja_id = int(lid)
            except (ValueError, TypeError):
                pass
            if not loja_id:
                slug = (request.headers.get('X-Tenant-Slug') or '').strip()
                if slug:
                    from superadmin.models import Loja
                    loja = Loja.objects.using('default').filter(slug__iexact=slug).first()
                    if loja:
                        loja_id = loja.id
        if not loja_id:
            logger.warning("WhatsAppConfigView: contexto de loja não encontrado (loja_id e headers vazios)")
            return None
        from whatsapp.models import WhatsAppConfig
        from superadmin.models import Loja
        try:
            loja = Loja.objects.using('default').get(id=loja_id)
            owner_tel = (getattr(loja, 'owner_telefone', None) or '').strip()
            config, created = WhatsAppConfig.objects.get_or_create(
                loja=loja,
                defaults={
                    'enviar_confirmacao': True,
                    'enviar_lembrete_24h': True,
                    'enviar_lembrete_2h': True,
                    'enviar_cobranca': True,
                    'enviar_lembrete_tarefas': True,
                    'whatsapp_numero': owner_tel or '',
                }
            )
            if not created and not (config.whatsapp_numero or '').strip() and owner_tel:
                config.whatsapp_numero = owner_tel
                config.save(update_fields=['whatsapp_numero', 'updated_at'])
            return config
        except Exception as e:
            logger.exception("WhatsAppConfigView._get_config erro loja_id=%s: %s", loja_id, e)
            return None

    def get(self, request):
        config = self._get_config(request)
        if config is None:
            return Response(
                {'error': 'Contexto de loja não encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        loja = config.loja
        owner_telefone = (getattr(loja, 'owner_telefone', None) or '').strip()
        return Response({
            'enviar_confirmacao': config.enviar_confirmacao,
            'enviar_lembrete_24h': config.enviar_lembrete_24h,
            'enviar_lembrete_2h': config.enviar_lembrete_2h,
            'enviar_cobranca': config.enviar_cobranca,
            'enviar_lembrete_tarefas': getattr(config, 'enviar_lembrete_tarefas', True),
            'owner_telefone': owner_telefone,
            'whatsapp_numero': (config.whatsapp_numero or '').strip(),
            'whatsapp_ativo': getattr(config, 'whatsapp_ativo', False),
            'whatsapp_phone_id': (getattr(config, 'whatsapp_phone_id', None) or '').strip(),
            'whatsapp_token_set': bool((getattr(config, 'whatsapp_token', None) or '').strip()),
        })

    def patch(self, request):
        config = self._get_config(request)
        if config is None:
            return Response(
                {'error': 'Contexto de loja não encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        update_fields = ['updated_at']
        for key in ('enviar_confirmacao', 'enviar_lembrete_24h', 'enviar_lembrete_2h', 'enviar_cobranca', 'enviar_lembrete_tarefas'):
            if key in request.data:
                setattr(config, key, bool(request.data[key]))
                update_fields.append(key)
        if 'whatsapp_numero' in request.data:
            config.whatsapp_numero = (request.data.get('whatsapp_numero') or '').strip()[:20]
            update_fields.append('whatsapp_numero')
        if 'whatsapp_ativo' in request.data:
            config.whatsapp_ativo = bool(request.data['whatsapp_ativo'])
            update_fields.append('whatsapp_ativo')
        if 'whatsapp_phone_id' in request.data:
            config.whatsapp_phone_id = (request.data.get('whatsapp_phone_id') or '').strip()[:64]
            update_fields.append('whatsapp_phone_id')
        if 'whatsapp_token' in request.data:
            config.whatsapp_token = (request.data.get('whatsapp_token') or '').strip()[:512]
            update_fields.append('whatsapp_token')
        config.save(update_fields=update_fields)
        loja = config.loja
        owner_telefone = (getattr(loja, 'owner_telefone', None) or '').strip()
        return Response({
            'enviar_confirmacao': config.enviar_confirmacao,
            'enviar_lembrete_24h': config.enviar_lembrete_24h,
            'enviar_lembrete_2h': config.enviar_lembrete_2h,
            'enviar_cobranca': config.enviar_cobranca,
            'enviar_lembrete_tarefas': getattr(config, 'enviar_lembrete_tarefas', True),
            'owner_telefone': owner_telefone,
            'whatsapp_numero': (config.whatsapp_numero or '').strip(),
            'whatsapp_ativo': getattr(config, 'whatsapp_ativo', False),
            'whatsapp_phone_id': (config.whatsapp_phone_id or '').strip(),
            'whatsapp_token_set': bool((config.whatsapp_token or '').strip()),
        })
