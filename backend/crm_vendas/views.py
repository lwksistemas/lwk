from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes, action
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
from .utils import get_current_vendedor_id


class VendedorViewSet(BaseModelViewSet):
    queryset = Vendedor.objects.all()
    serializer_class = VendedorSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if hasattr(Vendedor, 'is_active'):
            return qs.filter(is_active=True)
        return qs

    @action(detail=True, methods=['post'])
    def reenviar_senha(self, request, pk=None):
        """Gera nova senha provisória e envia por e-mail para o vendedor."""
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


class ContaViewSet(BaseModelViewSet):
    queryset = Conta.objects.all()
    serializer_class = ContaSerializer

    def list(self, request, *args, **kwargs):
        from django.core.cache import cache
        from rest_framework.response import Response

        loja_id = get_current_loja_id()
        cache_key = f'crm_contas_list:{loja_id}' if loja_id else None
        if cache_key:
            cached = cache.get(cache_key)
            if cached is not None:
                return Response(cached)
        response = super().list(request, *args, **kwargs)
        if cache_key and response.status_code == 200:
            cache.set(cache_key, response.data, 45)
        return response

    def perform_create(self, serializer):
        super().perform_create(serializer)
        self._invalidate_contas_cache()

    def perform_update(self, serializer):
        super().perform_update(serializer)
        self._invalidate_contas_cache()

    def perform_destroy(self, instance):
        super().perform_destroy(instance)
        self._invalidate_contas_cache()

    def _invalidate_contas_cache(self):
        loja_id = get_current_loja_id()
        if loja_id:
            from django.core.cache import cache
            cache.delete(f'crm_contas_list:{loja_id}')


class LeadViewSet(BaseModelViewSet):
    queryset = Lead.objects.select_related('conta').all()
    serializer_class = LeadSerializer

    def get_serializer_class(self):
        if self.action == 'list':
            return LeadListSerializer
        return LeadSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        vendedor_id = get_current_vendedor_id(self.request)
        if vendedor_id is not None:
            qs = qs.filter(oportunidades__vendedor_id=vendedor_id).distinct()
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
        vendedor_id = get_current_vendedor_id(self.request)
        if vendedor_id is not None:
            qs = qs.filter(vendedor_id=vendedor_id)
        else:
            vendedor_id = self.request.query_params.get('vendedor_id')
            if vendedor_id:
                qs = qs.filter(vendedor_id=vendedor_id)
        etapa = self.request.query_params.get('etapa')
        if etapa:
            qs = qs.filter(etapa=etapa)
        return qs


class AtividadeViewSet(BaseModelViewSet):
    queryset = (
        Atividade.objects.select_related('oportunidade', 'lead')
        .defer('google_event_id')  # Evita coluna que pode não existir em schemas antigos
        .all()
    )
    serializer_class = AtividadeListSerializer

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
        self._invalidate_atividades_cache()

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return AtividadeSerializer
        return AtividadeListSerializer

    def list(self, request, *args, **kwargs):
        from django.core.cache import cache
        from rest_framework.response import Response

        loja_id = get_current_loja_id()
        vendedor_id = get_current_vendedor_id(request)
        data_inicio = request.query_params.get('data_inicio', '')
        data_fim = request.query_params.get('data_fim', '')
        cache_key = None
        if loja_id and data_inicio and data_fim:
            version = cache.get(f'crm_atividades_v:{loja_id}', 0)
            cache_key = f'crm_atividades:{loja_id}:{version}:{vendedor_id or "owner"}:{data_inicio}:{data_fim}'
            cached = cache.get(cache_key)
            if cached is not None:
                return Response(cached)
        response = super().list(request, *args, **kwargs)
        if cache_key and response.status_code == 200:
            cache.set(cache_key, response.data, 45)
        return response

    def perform_update(self, serializer):
        super().perform_update(serializer)
        self._invalidate_atividades_cache()

    def perform_destroy(self, instance):
        super().perform_destroy(instance)
        self._invalidate_atividades_cache()

    def _invalidate_atividades_cache(self):
        loja_id = get_current_loja_id()
        if loja_id:
            from django.core.cache import cache
            try:
                v = cache.get(f'crm_atividades_v:{loja_id}', 0) + 1
                cache.set(f'crm_atividades_v:{loja_id}', v, 86400)
            except Exception:
                pass

    def get_queryset(self):
        qs = super().get_queryset()
        vendedor_id = get_current_vendedor_id(self.request)
        if vendedor_id is not None:
            qs = qs.filter(
                Q(oportunidade__vendedor_id=vendedor_id) | Q(lead__oportunidades__vendedor_id=vendedor_id)
            ).distinct()
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
    Otimizado: cache 60s, queries consolidadas (pipeline em 1 query).
    """
    import logging
    from django.core.cache import cache

    logger = logging.getLogger(__name__)
    loja_id = get_current_loja_id()
    if not loja_id:
        return Response(_empty_dashboard_response(), status=200)

    vendedor_id = get_current_vendedor_id(request)
    cache_key = f'crm_dashboard:{loja_id}:{vendedor_id or "owner"}'
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
            leads_qs = leads_qs.filter(oportunidades__vendedor_id=vendedor_id).distinct()
            opp_qs = opp_qs.filter(vendedor_id=vendedor_id)
            atividades_qs = atividades_qs.filter(
                Q(oportunidade__vendedor_id=vendedor_id) | Q(lead__oportunidades__vendedor_id=vendedor_id)
            ).distinct()
            vendedores_qs = vendedores_qs.filter(id=vendedor_id)

        # 1 query: totais agregados (receita, pipeline, fechados)
        agg = opp_qs.aggregate(
            total_oportunidades=Count('id'),
            receita=Sum('valor', filter=Q(etapa='closed_won')),
            pipeline_aberto=Sum('valor', filter=Q(etapa__in=ETAPAS_PIPELINE)),
            total_fechados=Count('id', filter=Q(etapa__in=['closed_won', 'closed_lost'])),
            total_ganhos=Count('id', filter=Q(etapa='closed_won')),
        )
        total_oportunidades = agg['total_oportunidades'] or 0
        receita = float(agg['receita'] or 0)
        pipeline_aberto = float(agg['pipeline_aberto'] or 0)
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

        # 1 query: atividades de hoje
        hoje_inicio = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        hoje_fim = hoje_inicio + timedelta(days=1)
        atividades_hoje_data = list(
            atividades_qs.filter(data__gte=hoje_inicio, data__lt=hoje_fim)
            .order_by('concluido', 'data')
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
                filter=Q(oportunidades__etapa='closed_won') & Q(oportunidades__data_fechamento__gte=mes_inicio),
            ),
        )
        performance_vendedores = [
            {'id': v.id, 'nome': v.nome, 'receita_mes': float(v.receita_mes or 0)}
            for v in perf_qs
        ]

        payload = {
            'leads': total_leads,
            'oportunidades': total_oportunidades,
            'receita': receita,
            'pipeline_aberto': pipeline_aberto,
            'meta_vendas': 0,
            'taxa_conversao': taxa_conversao,
            'pipeline_por_etapa': pipeline_por_etapa,
            'atividades_hoje': atividades_hoje_data,
            'performance_vendedores': performance_vendedores,
        }
        cache.set(cache_key, payload, 60)
        return Response(payload)
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


class LoginConfigView(APIView):
    """
    GET /crm-vendas/login-config/  → retorna logo, cor_primaria, cor_secundaria
    PATCH /crm-vendas/login-config/ → atualiza personalização da tela de login
    """
    permission_classes = [IsAuthenticated]

    def _get_loja(self, request=None):
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
            logger.warning("LoginConfigView: contexto de loja não encontrado")
            return None
        from superadmin.models import Loja
        try:
            return Loja.objects.using('default').get(id=loja_id)
        except Loja.DoesNotExist:
            return None

    def get(self, request):
        loja = self._get_loja(request)
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
        loja = self._get_loja(request)
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
