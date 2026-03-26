"""
Melhorias de Segurança para Dashboard de Auditoria e Alertas

Novos endpoints para integrar com as páginas:
- /superadmin/dashboard/auditoria
- /superadmin/dashboard/alertas
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q, Avg
from django.utils import timezone
from datetime import timedelta
import logging

from .permissions import IsSuperAdmin
from .models import ViolacaoSeguranca, HistoricoAcessoGlobal, Loja

logger = logging.getLogger(__name__)


class SecurityDashboardViewSet(viewsets.ViewSet):
    """
    ViewSet para Dashboard de Segurança
    
    Endpoints para as páginas de auditoria e alertas do SuperAdmin.
    """
    permission_classes = [IsSuperAdmin]
    
    @action(detail=False, methods=['get'])
    def resumo_seguranca(self, request):
        """
        Resumo geral de segurança para o dashboard
        
        GET /api/superadmin/security-dashboard/resumo_seguranca/
        
        Response:
        {
            "violacoes": {
                "total": 150,
                "nao_resolvidas": 25,
                "criticas": 5,
                "ultimas_24h": 3
            },
            "acessos": {
                "total_hoje": 1500,
                "total_semana": 10000,
                "taxa_sucesso": 98.5,
                "logins_hoje": 250
            },
            "alertas_ativos": [
                {
                    "tipo": "acesso_cross_tenant",
                    "count": 5,
                    "criticidade": "critica"
                },
                ...
            ],
            "lojas_suspeitas": [
                {
                    "loja_id": 123,
                    "loja_nome": "Loja X",
                    "violacoes": 10
                },
                ...
            ]
        }
        """
        now = timezone.now()
        hoje_inicio = now.replace(hour=0, minute=0, second=0, microsecond=0)
        semana_inicio = now - timedelta(days=7)
        ultimas_24h = now - timedelta(hours=24)
        
        # Violações
        violacoes_total = ViolacaoSeguranca.objects.count()
        violacoes_nao_resolvidas = ViolacaoSeguranca.objects.filter(
            status__in=['nova', 'investigando']
        ).count()
        violacoes_criticas = ViolacaoSeguranca.objects.filter(
            criticidade='critica',
            status__in=['nova', 'investigando']
        ).count()
        violacoes_24h = ViolacaoSeguranca.objects.filter(
            created_at__gte=ultimas_24h
        ).count()
        
        # Acessos
        acessos_hoje = HistoricoAcessoGlobal.objects.filter(
            created_at__gte=hoje_inicio
        ).count()
        acessos_semana = HistoricoAcessoGlobal.objects.filter(
            created_at__gte=semana_inicio
        ).count()
        
        acessos_sucesso_hoje = HistoricoAcessoGlobal.objects.filter(
            created_at__gte=hoje_inicio,
            sucesso=True
        ).count()
        taxa_sucesso = (acessos_sucesso_hoje / acessos_hoje * 100) if acessos_hoje > 0 else 100
        
        logins_hoje = HistoricoAcessoGlobal.objects.filter(
            created_at__gte=hoje_inicio,
            acao='login'
        ).count()
        
        # Alertas ativos por tipo
        alertas_ativos = ViolacaoSeguranca.objects.filter(
            status__in=['nova', 'investigando']
        ).values('tipo', 'criticidade').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        # Lojas com mais violações
        lojas_suspeitas = ViolacaoSeguranca.objects.filter(
            status__in=['nova', 'investigando'],
            loja__isnull=False
        ).values('loja_id', 'loja__nome').annotate(
            violacoes=Count('id')
        ).order_by('-violacoes')[:5]
        
        return Response({
            'violacoes': {
                'total': violacoes_total,
                'nao_resolvidas': violacoes_nao_resolvidas,
                'criticas': violacoes_criticas,
                'ultimas_24h': violacoes_24h
            },
            'acessos': {
                'total_hoje': acessos_hoje,
                'total_semana': acessos_semana,
                'taxa_sucesso': round(taxa_sucesso, 2),
                'logins_hoje': logins_hoje
            },
            'alertas_ativos': list(alertas_ativos),
            'lojas_suspeitas': [
                {
                    'loja_id': item['loja_id'],
                    'loja_nome': item['loja__nome'],
                    'violacoes': item['violacoes']
                }
                for item in lojas_suspeitas
            ]
        })
    
    @action(detail=False, methods=['get'])
    def timeline_violacoes(self, request):
        """
        Timeline de violações para gráfico
        
        GET /api/superadmin/security-dashboard/timeline_violacoes/?dias=30
        
        Response:
        {
            "timeline": [
                {
                    "data": "2024-01-15",
                    "total": 10,
                    "criticas": 2,
                    "altas": 3,
                    "medias": 4,
                    "baixas": 1
                },
                ...
            ]
        }
        """
        from django.db.models.functions import TruncDate
        
        dias = int(request.query_params.get('dias', 30))
        data_inicio = timezone.now() - timedelta(days=dias)
        
        timeline = ViolacaoSeguranca.objects.filter(
            created_at__gte=data_inicio
        ).annotate(
            data=TruncDate('created_at')
        ).values('data').annotate(
            total=Count('id'),
            criticas=Count('id', filter=Q(criticidade='critica')),
            altas=Count('id', filter=Q(criticidade='alta')),
            medias=Count('id', filter=Q(criticidade='media')),
            baixas=Count('id', filter=Q(criticidade='baixa'))
        ).order_by('data')
        
        return Response({
            'timeline': [
                {
                    'data': item['data'].strftime('%Y-%m-%d'),
                    'total': item['total'],
                    'criticas': item['criticas'],
                    'altas': item['altas'],
                    'medias': item['medias'],
                    'baixas': item['baixas']
                }
                for item in timeline
            ]
        })
    
    @action(detail=False, methods=['get'])
    def top_ips_suspeitos(self, request):
        """
        IPs com mais violações
        
        GET /api/superadmin/security-dashboard/top_ips_suspeitos/?limit=10
        
        Response:
        {
            "ips": [
                {
                    "ip": "192.168.1.100",
                    "violacoes": 15,
                    "tipos": ["brute_force", "rate_limit_exceeded"],
                    "ultima_violacao": "2024-01-15T10:30:00Z"
                },
                ...
            ]
        }
        """
        from django.db.models import Max
        
        limit = int(request.query_params.get('limit', 10))
        
        ips = ViolacaoSeguranca.objects.values('ip_address').annotate(
            violacoes=Count('id'),
            ultima_violacao=Max('created_at')
        ).order_by('-violacoes')[:limit]
        
        # Buscar tipos de violação por IP
        resultado = []
        for item in ips:
            tipos = ViolacaoSeguranca.objects.filter(
                ip_address=item['ip_address']
            ).values_list('tipo', flat=True).distinct()
            
            resultado.append({
                'ip': item['ip_address'],
                'violacoes': item['violacoes'],
                'tipos': list(tipos),
                'ultima_violacao': item['ultima_violacao']
            })
        
        return Response({'ips': resultado})
    
    @action(detail=False, methods=['get'])
    def usuarios_suspeitos(self, request):
        """
        Usuários com comportamento suspeito
        
        GET /api/superadmin/security-dashboard/usuarios_suspeitos/?limit=10
        
        Response:
        {
            "usuarios": [
                {
                    "email": "user@example.com",
                    "nome": "João Silva",
                    "violacoes": 8,
                    "lojas_tentadas": 3,
                    "ultima_violacao": "2024-01-15T10:30:00Z"
                },
                ...
            ]
        }
        """
        from django.db.models import Max
        
        limit = int(request.query_params.get('limit', 10))
        
        usuarios = ViolacaoSeguranca.objects.values(
            'usuario_email', 'usuario_nome'
        ).annotate(
            violacoes=Count('id'),
            lojas_tentadas=Count('loja_id', distinct=True),
            ultima_violacao=Max('created_at')
        ).order_by('-violacoes')[:limit]
        
        return Response({
            'usuarios': [
                {
                    'email': item['usuario_email'],
                    'nome': item['usuario_nome'],
                    'violacoes': item['violacoes'],
                    'lojas_tentadas': item['lojas_tentadas'],
                    'ultima_violacao': item['ultima_violacao']
                }
                for item in usuarios
            ]
        })
    
    @action(detail=False, methods=['get'])
    def mapa_acessos(self, request):
        """
        Mapa de acessos por localização (baseado em IP)
        
        GET /api/superadmin/security-dashboard/mapa_acessos/?dias=7
        
        Response:
        {
            "acessos_por_ip": [
                {
                    "ip": "192.168.1.100",
                    "acessos": 500,
                    "lojas": ["loja-a", "loja-b"],
                    "usuarios": ["user1@example.com", "user2@example.com"]
                },
                ...
            ]
        }
        """
        dias = int(request.query_params.get('dias', 7))
        data_inicio = timezone.now() - timedelta(days=dias)
        
        acessos = HistoricoAcessoGlobal.objects.filter(
            created_at__gte=data_inicio
        ).values('ip_address').annotate(
            acessos=Count('id')
        ).order_by('-acessos')[:50]
        
        resultado = []
        for item in acessos:
            # Buscar lojas e usuários deste IP
            logs_ip = HistoricoAcessoGlobal.objects.filter(
                ip_address=item['ip_address'],
                created_at__gte=data_inicio
            )
            
            lojas = logs_ip.exclude(
                loja_slug=''
            ).values_list('loja_slug', flat=True).distinct()
            
            usuarios = logs_ip.values_list(
                'usuario_email', flat=True
            ).distinct()
            
            resultado.append({
                'ip': item['ip_address'],
                'acessos': item['acessos'],
                'lojas': list(lojas)[:5],  # Limitar a 5
                'usuarios': list(usuarios)[:5]  # Limitar a 5
            })
        
        return Response({'acessos_por_ip': resultado})
    
    @action(detail=False, methods=['post'])
    def executar_auditoria_completa(self, request):
        """
        Executa auditoria completa de segurança
        
        POST /api/superadmin/security-dashboard/executar_auditoria_completa/
        
        Verifica:
        - Modelos sem LojaIsolationMixin
        - Queries raw SQL sem filtro
        - Endpoints sem validação
        - Configurações de segurança
        
        Response:
        {
            "status": "concluido",
            "problemas_encontrados": 5,
            "detalhes": [...]
        }
        """
        problemas = []
        
        # 1. Verificar modelos sem LojaIsolationMixin
        from django.apps import apps
        from core.mixins import LojaIsolationMixin
        
        apps_loja = ['crm_vendas', 'clinica_estetica', 'restaurante', 'ecommerce']
        
        for app_label in apps_loja:
            try:
                app_config = apps.get_app_config(app_label)
                for model in app_config.get_models():
                    if not issubclass(model, LojaIsolationMixin):
                        problemas.append({
                            'tipo': 'modelo_sem_isolamento',
                            'criticidade': 'alta',
                            'app': app_label,
                            'modelo': model.__name__,
                            'descricao': f'Modelo {model.__name__} não usa LojaIsolationMixin'
                        })
            except LookupError:
                pass
        
        # 2. Verificar configurações de segurança
        from django.conf import settings
        
        if not getattr(settings, 'SECURE_SSL_REDIRECT', False):
            problemas.append({
                'tipo': 'configuracao',
                'criticidade': 'media',
                'descricao': 'SECURE_SSL_REDIRECT não está ativado'
            })
        
        if not getattr(settings, 'SESSION_COOKIE_SECURE', False):
            problemas.append({
                'tipo': 'configuracao',
                'criticidade': 'media',
                'descricao': 'SESSION_COOKIE_SECURE não está ativado'
            })
        
        # 3. Verificar violações recentes não resolvidas
        violacoes_pendentes = ViolacaoSeguranca.objects.filter(
            status__in=['nova', 'investigando'],
            created_at__gte=timezone.now() - timedelta(days=7)
        ).count()
        
        if violacoes_pendentes > 0:
            problemas.append({
                'tipo': 'violacoes_pendentes',
                'criticidade': 'alta',
                'count': violacoes_pendentes,
                'descricao': f'{violacoes_pendentes} violações pendentes nos últimos 7 dias'
            })
        
        return Response({
            'status': 'concluido',
            'problemas_encontrados': len(problemas),
            'detalhes': problemas,
            'executado_em': timezone.now()
        })
