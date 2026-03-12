from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from django.db.models import Sum, Count, Q, Exists, OuterRef
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from datetime import timedelta
import logging

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
from .utils import get_current_vendedor_id, get_loja_from_context
from .mixins import CRMPermissionMixin, VendedorFilterMixin
from .cache import CRMCacheManager
from .decorators import cache_list_response

logger = logging.getLogger(__name__)


# ✅ OTIMIZAÇÃO: Paginação para reduzir tempo de resposta
class CRMPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100


class VendedorViewSet(CRMPermissionMixin, BaseModelViewSet):
    queryset = Vendedor.objects.all()
    serializer_class = VendedorSerializer
    pagination_class = CRMPagination  # ✅ OTIMIZAÇÃO: Paginação

    def _ensure_owner_vendedor(self):
        """Garante que o administrador da loja exista como vendedor (para lojas antigas)."""
        from superadmin.services import ProfessionalService
        from superadmin.models import Loja

        loja_id = get_current_loja_id()
        if not loja_id:
            return
        try:
            loja = Loja.objects.select_related('owner', 'tipo_loja').get(id=loja_id)
            if loja.tipo_loja and loja.tipo_loja.nome == 'CRM Vendas':
                ProfessionalService.criar_vendedor_admin_crm(
                    loja, loja.owner, getattr(loja, 'owner_telefone', '') or ''
                )
        except Loja.DoesNotExist:
            pass
        except Exception:
            pass  # Não falhar a listagem

    def get_queryset(self):
        """✅ OTIMIZAÇÃO: Anotar tem_acesso para evitar N+1 queries"""
        qs = super().get_queryset()
        
        # Anotar se vendedor tem acesso (evita N+1)
        from superadmin.models import VendedorUsuario
        loja_id = get_current_loja_id()
        if loja_id:
            qs = qs.annotate(
                tem_acesso_anotado=Exists(
                    VendedorUsuario.objects.filter(
                        loja_id=loja_id,
                        vendedor_id=OuterRef('id')
                    )
                )
            )
        
        if hasattr(Vendedor, 'is_active'):
            return qs.filter(is_active=True)
        return qs

    def list(self, request, *args, **kwargs):
        bloqueio = self.bloquear_vendedor(request, 'Vendedores não têm permissão para acessar configurações de funcionários.')
        if bloqueio:
            return bloqueio
        self._ensure_owner_vendedor()
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        bloqueio = self.bloquear_vendedor(request, 'Vendedores não têm permissão para acessar configurações de funcionários.')
        if bloqueio:
            return bloqueio
        return super().create(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        bloqueio = self.bloquear_vendedor(request, 'Vendedores não têm permissão para acessar configurações de funcionários.')
        if bloqueio:
            return bloqueio
        return super().retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        bloqueio = self.bloquear_vendedor(request, 'Vendedores não têm permissão para acessar configurações de funcionários.')
        if bloqueio:
            return bloqueio
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        bloqueio = self.bloquear_vendedor(request, 'Vendedores não têm permissão para acessar configurações de funcionários.')
        if bloqueio:
            return bloqueio
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        bloqueio = self.bloquear_vendedor(request, 'Vendedores não têm permissão para acessar configurações de funcionários.')
        if bloqueio:
            return bloqueio
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def reenviar_senha(self, request, pk=None):
        """Gera nova senha provisória e envia por e-mail para o vendedor."""
        bloqueio = self.bloquear_vendedor(request, 'Vendedores não têm permissão para acessar configurações de funcionários.')
        if bloqueio:
            return bloqueio
        vendedor = self.get_object()
        if not vendedor.email:
            return Response(
                {'detail': 'Vendedor não possui e-mail cadastrado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        from django.contrib.auth import get_user_model
        from django.utils.crypto import get_random_string
        from django.core.mail import send_mail
        from django.conf import settings
        from superadmin.models import Loja, VendedorUsuario

        User = get_user_model()
        loja_id = get_current_loja_id()
        if not loja_id:
            return Response(
                {'detail': 'Contexto de loja não encontrado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            vu = VendedorUsuario.objects.using('default').get(
                loja_id=loja_id,
                vendedor_id=vendedor.id,
            )
        except VendedorUsuario.DoesNotExist:
            return Response(
                {'detail': 'Vendedor ainda não possui acesso ao sistema. Use "Criar acesso" ao cadastrar.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        loja = Loja.objects.using('default').get(id=loja_id)
        senha_provisoria = get_random_string(8)
        user = vu.user
        user.set_password(senha_provisoria)
        user.save(update_fields=['password'])
        vu.precisa_trocar_senha = True
        vu.save(update_fields=['precisa_trocar_senha'])
        site_url = getattr(settings, 'SITE_URL', 'https://lwksistemas.com.br').rstrip('/')
        login_url = f"{site_url}/loja/{loja.slug}/login"
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or 'noreply@lwksistemas.com.br'
        try:
            send_mail(
                subject='Nova senha provisória - CRM Vendas',
                message=(
                    f"Olá, {vendedor.nome or 'Vendedor'}!\n\n"
                    f"Sua senha foi redefinida.\n\n"
                    f"Login: {vendedor.email}\n"
                    f"Nova senha provisória: {senha_provisoria}\n\n"
                    f"Acesse: {login_url}\n\n"
                    f"Por segurança, altere sua senha no primeiro acesso."
                ),
                from_email=from_email,
                recipient_list=[vendedor.email],
                fail_silently=True,
            )
        except Exception:
            pass
        return Response({
            'detail': f'Senha provisória enviada para {vendedor.email}',
            'email_enviado': vendedor.email,
        })


class ContaViewSet(VendedorFilterMixin, BaseModelViewSet):
    queryset = Conta.objects.select_related('vendedor').prefetch_related('leads', 'contatos').all()
    serializer_class = ContaSerializer
    pagination_class = CRMPagination  # ✅ OTIMIZAÇÃO: Paginação
    
    # Configuração do VendedorFilterMixin
    vendedor_filter_field = 'vendedor_id'
    vendedor_filter_related = ['leads__oportunidades__vendedor_id', 'leads__vendedor_id']

    @cache_list_response(CRMCacheManager.CONTAS, ttl=300)  # ✅ OTIMIZAÇÃO: Cache 5min
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def perform_create(self, serializer):
        vendedor_id = get_current_vendedor_id(self.request)
        if vendedor_id is not None:
            serializer.save(vendedor_id=vendedor_id)
        else:
            serializer.save()
        CRMCacheManager.invalidate_contas(get_current_loja_id())

    def perform_update(self, serializer):
        super().perform_update(serializer)
        CRMCacheManager.invalidate_contas(get_current_loja_id())

    def perform_destroy(self, instance):
        super().perform_destroy(instance)
        CRMCacheManager.invalidate_contas(get_current_loja_id())


class LeadViewSet(VendedorFilterMixin, BaseModelViewSet):
    queryset = Lead.objects.select_related('conta', 'vendedor').prefetch_related('oportunidades').all()
    serializer_class = LeadSerializer
    pagination_class = CRMPagination  # ✅ OTIMIZAÇÃO: Paginação
    
    # Configuração do VendedorFilterMixin
    vendedor_filter_field = 'vendedor_id'
    vendedor_filter_related = ['oportunidades__vendedor_id']

    def get_serializer_class(self):
        if self.action == 'list':
            return LeadListSerializer
        return LeadSerializer

    def perform_create(self, serializer):
        vendedor_id = get_current_vendedor_id(self.request)
        if vendedor_id is not None:
            serializer.save(vendedor_id=vendedor_id)
        else:
            serializer.save()

    def get_queryset(self):
        qs = super().get_queryset()
        # Filtros adicionais (além do filtro de vendedor do mixin)
        status = self.request.query_params.get('status')
        if status:
            qs = qs.filter(status=status)
        origem = self.request.query_params.get('origem')
        if origem:
            qs = qs.filter(origem=origem)
        return qs


class ContatoViewSet(VendedorFilterMixin, BaseModelViewSet):
    queryset = Contato.objects.select_related('conta').all()
    serializer_class = ContatoSerializer
    pagination_class = CRMPagination  # ✅ OTIMIZAÇÃO: Paginação
    
    # Configuração do VendedorFilterMixin
    vendedor_filter_field = 'conta__vendedor_id'
    vendedor_filter_related = ['conta__leads__oportunidades__vendedor_id', 'conta__leads__vendedor_id']
    vendedor_filter_related = ['conta__leads__oportunidades__vendedor_id', 'conta__leads__vendedor_id']

    def get_queryset(self):
        qs = super().get_queryset()
        # Filtros adicionais (além do filtro de vendedor do mixin)
        conta_id = self.request.query_params.get('conta_id')
        if conta_id:
            qs = qs.filter(conta_id=conta_id)
        return qs


class OportunidadeViewSet(VendedorFilterMixin, BaseModelViewSet):
    queryset = Oportunidade.objects.select_related('lead', 'vendedor', 'lead__conta').prefetch_related('atividades').all()
    serializer_class = OportunidadeSerializer
    pagination_class = CRMPagination  # ✅ OTIMIZAÇÃO: Paginação
    
    # Configuração do VendedorFilterMixin
    vendedor_filter_field = 'vendedor_id'
    vendedor_filter_related = []

    def perform_create(self, serializer):
        vendedor_id = get_current_vendedor_id(self.request)
        data = serializer.validated_data
        if vendedor_id is not None and not data.get('vendedor'):
            serializer.save(vendedor_id=vendedor_id)
        else:
            serializer.save()

    def perform_update(self, serializer):
        """Mantém o vendedor ao atualizar se não for especificado"""
        vendedor_id = get_current_vendedor_id(self.request)
        instance = serializer.instance
        data = serializer.validated_data
        
        # Se é vendedor logado e a oportunidade não tem vendedor, vincular
        if vendedor_id is not None and instance.vendedor_id is None and not data.get('vendedor'):
            serializer.save(vendedor_id=vendedor_id)
        else:
            serializer.save()

    def get_queryset(self):
        qs = super().get_queryset()
        # Filtros adicionais (além do filtro de vendedor do mixin)
        # Se não for vendedor, permitir filtrar por vendedor_id via query param
        if get_current_vendedor_id(self.request) is None:
            vendedor_id = self.request.query_params.get('vendedor_id')
            if vendedor_id:
                qs = qs.filter(vendedor_id=vendedor_id)
        etapa = self.request.query_params.get('etapa')
        if etapa:
            qs = qs.filter(etapa=etapa)
        return qs


class AtividadeViewSet(VendedorFilterMixin, BaseModelViewSet):
    queryset = (
        Atividade.objects.select_related('oportunidade', 'lead')
        .defer('google_event_id')  # Evita coluna que pode não existir em schemas antigos
        .all()
    )
    serializer_class = AtividadeListSerializer
    pagination_class = CRMPagination  # ✅ OTIMIZAÇÃO: Paginação
    
    # Configuração do VendedorFilterMixin
    vendedor_filter_field = 'oportunidade__vendedor_id'
    vendedor_filter_related = ['lead__oportunidades__vendedor_id']

    def perform_create(self, serializer):
        super().perform_create(serializer)
        atividade = serializer.instance
        if atividade and getattr(atividade, 'loja_id', None):
            try:
                from superadmin.models import Loja
                from notificacoes.services import notify
                loja = Loja.objects.using('default').filter(id=atividade.loja_id).select_related('owner').first()
                if loja and loja.owner_id:
                    data_str = atividade.data.strftime('%d/%m/%Y %H:%M') if atividade.data else ''
                    tipo_label = atividade.get_tipo_display() if hasattr(atividade, 'get_tipo_display') else atividade.tipo
                    notify(
                        user=loja.owner,
                        titulo=f'Nova atividade: {atividade.titulo[:50]}{"..." if len(atividade.titulo) > 50 else ""}',
                        mensagem=f'{tipo_label}: {atividade.titulo} — {data_str}',
                        tipo='tarefa',
                        canal='in_app',
                        metadata={
                            'url': f'/loja/{loja.slug}/crm-vendas/calendario',
                            'atividade_id': atividade.id,
                            'loja_id': loja.id,
                        },
                    )
            except Exception:
                pass  # Notificação é best-effort; não falha a criação
        CRMCacheManager.invalidate_atividades(get_current_loja_id())

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return AtividadeSerializer
        return AtividadeListSerializer

    @cache_list_response(CRMCacheManager.ATIVIDADES, ttl=300, extra_keys=['data_inicio', 'data_fim'])  # ✅ OTIMIZAÇÃO: Cache 5min
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def perform_update(self, serializer):
        super().perform_update(serializer)
        CRMCacheManager.invalidate_atividades(get_current_loja_id())

    def perform_destroy(self, instance):
        """
        Deleta atividade e remove do Google Calendar se tiver google_event_id
        """
        # Se tem google_event_id, deletar do Google Calendar
        if instance.google_event_id:
            try:
                from superadmin.models import GoogleCalendarConnection
                from crm_vendas.google_calendar_service import delete_google_event
                loja_id = get_current_loja_id()
                
                # Buscar conexão do Google Calendar (proprietário ou vendedor)
                connection = GoogleCalendarConnection.objects.filter(
                    loja_id=loja_id
                ).exclude(
                    access_token=''
                ).first()
                
                if connection:
                    success = delete_google_event(connection, instance.google_event_id)
                    if success:
                        logger.info(f"✅ Evento deletado do Google Calendar: {instance.google_event_id}")
                    else:
                        logger.warning(f"⚠️ Falha ao deletar evento do Google Calendar: {instance.google_event_id}")
            except Exception as e:
                logger.warning(f"⚠️ Erro ao deletar evento do Google Calendar: {e}")
                # Continuar com a exclusão mesmo se falhar no Google Calendar
        
        super().perform_destroy(instance)
        CRMCacheManager.invalidate_atividades(get_current_loja_id())

    def get_queryset(self):
        qs = super().get_queryset()
        # Filtros adicionais (além do filtro de vendedor do mixin)
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

# Etapas em andamento (excluindo fechadas)
ETAPAS_EM_ANDAMENTO = [
    'prospecting', 'qualification', 'proposal', 'negotiation',
]


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_data(request):
    """
    Dados do dashboard CRM (estilo Salesforce).
    Otimizado: cache 120s, queries consolidadas (pipeline em 1 query).
    """
    import logging

    logger = logging.getLogger(__name__)
    loja_id = get_current_loja_id()
    if not loja_id:
        return Response(_empty_dashboard_response(), status=200)

    vendedor_id = get_current_vendedor_id(request)
    cache_key = CRMCacheManager.get_cache_key(
        CRMCacheManager.DASHBOARD,
        loja_id,
        vendedor_id
    )
    
    if cache_key:
        from django.core.cache import cache
        cached = cache.get(cache_key)
        if cached:
            return Response(cached)

    try:
        from .models import Lead, Oportunidade, Atividade, Vendedor

        leads_qs = Lead.objects.all()
        opp_qs = Oportunidade.objects.all()
        atividades_qs = Atividade.objects.all()
        vendedores_qs = Vendedor.objects.filter(is_active=True)

        if vendedor_id is not None:
            leads_qs = leads_qs.filter(
                Q(oportunidades__vendedor_id=vendedor_id) | Q(vendedor_id=vendedor_id)
            ).distinct()
            opp_qs = opp_qs.filter(vendedor_id=vendedor_id)
            atividades_qs = atividades_qs.filter(
                Q(oportunidade__vendedor_id=vendedor_id) | Q(lead__oportunidades__vendedor_id=vendedor_id)
            ).distinct()
            vendedores_qs = vendedores_qs.filter(id=vendedor_id)

        # 1 query: totais agregados (receita, pipeline, fechados)
        agg = opp_qs.aggregate(
            total_oportunidades=Count('id'),
            receita=Sum('valor', filter=Q(etapa='closed_won')),
            pipeline_aberto=Sum('valor', filter=Q(etapa__in=ETAPAS_EM_ANDAMENTO)),  # Apenas em andamento
            oportunidades_em_andamento=Count('id', filter=Q(etapa__in=ETAPAS_EM_ANDAMENTO)),  # Contagem em andamento
            total_fechados=Count('id', filter=Q(etapa__in=['closed_won', 'closed_lost'])),
            total_ganhos=Count('id', filter=Q(etapa='closed_won')),
        )
        total_oportunidades = agg['total_oportunidades'] or 0
        receita = float(agg['receita'] or 0)
        pipeline_aberto = float(agg['pipeline_aberto'] or 0)
        oportunidades_em_andamento = agg['oportunidades_em_andamento'] or 0
        total_fechados = agg['total_fechados'] or 0
        total_ganhos = agg['total_ganhos'] or 0
        taxa_conversao = round((total_ganhos / total_fechados * 100), 1) if total_fechados else 0

        # 1 query: pipeline por etapa (values + annotate)
        pipeline_map = {
            row['etapa']: {'valor': float(row['valor'] or 0), 'quantidade': row['qtd'] or 0}
            for row in opp_qs.filter(etapa__in=ETAPAS_PIPELINE)
            .values('etapa')
            .annotate(valor=Sum('valor'), qtd=Count('id'))
        }
        pipeline_por_etapa = [
            {'etapa': e, **(pipeline_map.get(e, {'valor': 0, 'quantidade': 0}))}
            for e in ETAPAS_PIPELINE
        ]

        # 1 query: total leads
        total_leads = leads_qs.count()

        # 1 query: atividades próximas (hoje + próximos 7 dias)
        hoje_inicio = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        proximos_7_dias = hoje_inicio + timedelta(days=7)
        atividades_hoje_data = list(
            atividades_qs.filter(data__gte=hoje_inicio, data__lt=proximos_7_dias, concluido=False)
            .order_by('data')
            .values('id', 'titulo', 'tipo', 'data', 'concluido', 'observacoes')[:20]
        )
        for a in atividades_hoje_data:
            if a.get('data'):
                a['data'] = a['data'].isoformat() if hasattr(a['data'], 'isoformat') else str(a['data'])

        # 1 query: performance vendedores
        mes_inicio = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        perf_qs = vendedores_qs.annotate(
            receita_mes=Sum(
                'oportunidades__valor',
                filter=Q(oportunidades__etapa='closed_won') & (
                    Q(oportunidades__data_fechamento_ganho__gte=mes_inicio) |
                    (Q(oportunidades__data_fechamento_ganho__isnull=True) & Q(oportunidades__data_fechamento__gte=mes_inicio))
                ),
            ),
            comissao_mes=Sum(
                'oportunidades__valor_comissao',
                filter=Q(oportunidades__etapa='closed_won') & (
                    Q(oportunidades__data_fechamento_ganho__gte=mes_inicio) |
                    (Q(oportunidades__data_fechamento_ganho__isnull=True) & Q(oportunidades__data_fechamento__gte=mes_inicio))
                ),
            ),
        )
        performance_vendedores = [
            {'id': v.id, 'nome': v.nome, 'receita_mes': float(v.receita_mes or 0), 'comissao_mes': float(v.comissao_mes or 0)}
            for v in perf_qs
        ]

        # Comissão total do mês (todas as oportunidades, independente de vendedor)
        comissao_total_mes = opp_qs.filter(
            etapa='closed_won',
            valor_comissao__isnull=False
        ).filter(
            Q(data_fechamento_ganho__gte=mes_inicio) |
            (Q(data_fechamento_ganho__isnull=True) & Q(data_fechamento__gte=mes_inicio))
        ).aggregate(total=Sum('valor_comissao'))['total'] or 0

        payload = {
            'leads': total_leads,
            'oportunidades': total_oportunidades,
            'receita': receita,
            'pipeline_aberto': pipeline_aberto,
            'oportunidades_em_andamento': oportunidades_em_andamento,
            'meta_vendas': 0,
            'taxa_conversao': taxa_conversao,
            'pipeline_por_etapa': pipeline_por_etapa,
            'atividades_hoje': atividades_hoje_data,
            'performance_vendedores': performance_vendedores,
            'comissao_total_mes': float(comissao_total_mes),
        }
        if cache_key:
            from django.core.cache import cache
            cache.set(cache_key, payload, 120)  # 2 minutos
        return Response(payload)
    except Exception as e:
        logger.exception('Erro no dashboard CRM: %s', e)
        return Response(
            {'detail': 'Erro ao carregar dashboard. Tente novamente.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class WhatsAppConfigView(CRMPermissionMixin, APIView):
    """
    Configuração WhatsApp da loja (reutiliza WhatsAppConfig da Clínica da Beleza).
    GET /crm-vendas/whatsapp-config/  → retorna flags
    PATCH /crm-vendas/whatsapp-config/ → atualiza flags
    """
    permission_classes = [IsAuthenticated]

    def _get_config(self, request=None):
        import logging
        logger = logging.getLogger(__name__)
        loja = get_loja_from_context(request)
        if not loja:
            logger.warning("WhatsAppConfigView: contexto de loja não encontrado")
            return None
        
        from whatsapp.models import WhatsAppConfig
        try:
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
            logger.exception("WhatsAppConfigView._get_config erro: %s", e)
            return None

    def get(self, request):
        bloqueio = self.bloquear_vendedor(request)
        if bloqueio:
            return bloqueio
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
        bloqueio = self.bloquear_vendedor(request)
        if bloqueio:
            return bloqueio
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


class LoginConfigView(CRMPermissionMixin, APIView):
    """
    GET /crm-vendas/login-config/  → retorna logo, cor_primaria, cor_secundaria
    PATCH /crm-vendas/login-config/ → atualiza personalização da tela de login
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        bloqueio = self.bloquear_vendedor(request)
        if bloqueio:
            return bloqueio
        loja = get_loja_from_context(request)
        if loja is None:
            return Response(
                {'error': 'Contexto de loja não encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        tipo = getattr(loja, 'tipo_loja', None)
        cor_default = getattr(tipo, 'cor_primaria', None) if tipo else None
        cor_primaria = (loja.cor_primaria or '').strip() or cor_default or '#10B981'
        cor_secundaria = (loja.cor_secundaria or '').strip() or '#059669'
        return Response({
            'logo': (loja.logo or '').strip(),
            'cor_primaria': cor_primaria,
            'cor_secundaria': cor_secundaria,
        })

    def patch(self, request):
        bloqueio = self.bloquear_vendedor(request)
        if bloqueio:
            return bloqueio
        loja = get_loja_from_context(request)
        if loja is None:
            return Response(
                {'error': 'Contexto de loja não encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        update_fields = ['updated_at']
        if 'logo' in request.data:
            val = (request.data.get('logo') or '').strip()
            loja.logo = val[:200] if val else ''  # URLField max_length=200
            update_fields.append('logo')
        if 'cor_primaria' in request.data:
            val = (request.data.get('cor_primaria') or '').strip()
            if val and val.startswith('#') and len(val) <= 7:
                loja.cor_primaria = val[:7]
                update_fields.append('cor_primaria')
        if 'cor_secundaria' in request.data:
            val = (request.data.get('cor_secundaria') or '').strip()
            if val and val.startswith('#') and len(val) <= 7:
                loja.cor_secundaria = val[:7]
                update_fields.append('cor_secundaria')
        loja.save(update_fields=update_fields)
        from django.core.cache import cache
        cache_key = f'loja_info_publica:{loja.slug}'
        cache.delete(cache_key)
        return Response({
            'logo': (loja.logo or '').strip(),
            'cor_primaria': loja.cor_primaria or '#10B981',
            'cor_secundaria': loja.cor_secundaria or '#059669',
        })
