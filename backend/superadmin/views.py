from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny  # ✅ NOVO v738
from django.contrib.auth.models import User
from django.core.management import call_command
from django.conf import settings
from django.db import transaction, connection
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from pathlib import Path
import logging

logger = logging.getLogger(__name__)
from .models import (
    TipoLoja, PlanoAssinatura, Loja, FinanceiroLoja,
    PagamentoLoja, UsuarioSistema, ViolacaoSeguranca, ProfissionalUsuario, MercadoPagoConfig
)
from .serializers import (
    TipoLojaSerializer, PlanoAssinaturaSerializer, LojaSerializer,
    FinanceiroLojaSerializer, PagamentoLojaSerializer, UsuarioSistemaSerializer,
    LojaCreateSerializer, ViolacaoSegurancaSerializer, ViolacaoSegurancaListSerializer
)
from .cache import cached_stat, invalidate_stats_cache

class IsOwnerOrSuperAdmin(permissions.BasePermission):
    """Permissão para proprietário da loja ou super admin"""
    def has_permission(self, request, view):
        # Superadmin sempre tem permissão
        if request.user and request.user.is_superuser:
            return True
        
        # Usuário autenticado tem permissão (verificação específica será feita no método)
        if request.user and request.user.is_authenticated:
            return True
        
        return False
    
    def has_object_permission(self, request, view, obj):
        # Superadmin sempre tem permissão
        if request.user and request.user.is_superuser:
            return True
        
        # Verificar se é o proprietário da loja
        if hasattr(obj, 'owner') and request.user == obj.owner:
            return True
        # Profissional (Clínica da Beleza): pode acessar a loja para trocar senha
        if hasattr(obj, 'id') and getattr(view, 'action', None) == 'alterar_senha_primeiro_acesso':
            if ProfissionalUsuario.objects.filter(user=request.user, loja=obj).exists():
                return True

        return False


class IsSuperAdmin(permissions.BasePermission):
    """Permissão APENAS para super admins - SEGURANÇA CRÍTICA"""
    def has_permission(self, request, view):
        return request.user and request.user.is_superuser and request.user.is_active


class TipoLojaViewSet(viewsets.ModelViewSet):
    serializer_class = TipoLojaSerializer
    permission_classes = [IsSuperAdmin]
    
    def get_queryset(self):
        # ✅ OTIMIZAÇÃO: prefetch lojas relacionadas
        return TipoLoja.objects.prefetch_related('lojas', 'planos').all()


class PlanoAssinaturaViewSet(viewsets.ModelViewSet):
    serializer_class = PlanoAssinaturaSerializer
    permission_classes = [IsSuperAdmin]
    
    def get_queryset(self):
        # ✅ OTIMIZAÇÃO: prefetch relacionamentos
        return PlanoAssinatura.objects.prefetch_related('tipos_loja', 'lojas').all()
    
    @action(detail=False, methods=['get'])
    def por_tipo(self, request):
        """Buscar planos por tipo de loja"""
        tipo_id = request.query_params.get('tipo_id')
        if tipo_id:
            planos = self.get_queryset().filter(tipos_loja__id=tipo_id, is_active=True)
            serializer = self.get_serializer(planos, many=True)
            return Response(serializer.data)
        return Response({'error': 'tipo_id é obrigatório'}, status=400)


class LojaViewSet(viewsets.ModelViewSet):
    permission_classes = [IsSuperAdmin]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return LojaCreateSerializer
        return LojaSerializer
    
    def get_permissions(self):
        # Permitir acesso público aos endpoints info_publica e debug_auth
        if self.action in ['info_publica', 'debug_auth']:
            return []
        # Heartbeat: qualquer usuário autenticado (superadmin ou loja) para monitor de sessão
        if self.action == 'heartbeat':
            return [permissions.IsAuthenticated()]
        return super().get_permissions()
    
    def get_queryset(self):
        # ✅ OTIMIZAÇÃO: select_related para evitar N+1 queries
        queryset = Loja.objects.select_related(
            'tipo_loja',
            'plano',
            'owner',
            'financeiro'
        ).prefetch_related(
            'pagamentos',
            'usuarios_suporte'
        )
        
        # Filtrar por slug se fornecido
        slug = self.request.query_params.get('slug')
        if slug:
            queryset = queryset.filter(slug=slug)
        
        return queryset
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny], authentication_classes=[])
    @action(detail=False, methods=['get'], permission_classes=[])
    def info_publica(self, request):
        """
        Retorna informações públicas da loja para página de login (sem autenticação). 
        Otimizado com cache Redis (TTL 5min) - v663
        """
        from django.core.cache import cache
        
        slug = request.query_params.get('slug')
        if not slug:
            return Response({'error': 'slug é obrigatório'}, status=400)
        slug = slug.strip().lower()
        
        # ✅ OTIMIZAÇÃO v663: Cache Redis com TTL de 5 minutos
        cache_key = f'loja_info_publica:{slug}'
        cached_data = cache.get(cache_key)
        if cached_data:
            logger.debug(f'✅ Cache HIT para loja {slug}')
            return Response(cached_data)
        
        try:
            loja = Loja.objects.select_related('tipo_loja').filter(slug__iexact=slug, is_active=True).first()
            if not loja:
                return Response({'error': 'Loja não encontrada'}, status=404)
            tipo = getattr(loja, 'tipo_loja', None)
            tipo_nome = tipo.nome if tipo else 'Loja'
            
            data = {
                'id': loja.id,
                'nome': getattr(loja, 'nome', '') or '',
                'slug': getattr(loja, 'slug', '') or slug,
                'tipo_loja_nome': tipo_nome,
                'cor_primaria': getattr(loja, 'cor_primaria', None) or '#10B981',
                'cor_secundaria': getattr(loja, 'cor_secundaria', None) or '#059669',
                'logo': getattr(loja, 'logo', None) or '',
                'login_page_url': getattr(loja, 'login_page_url', None) or '',
                'senha_foi_alterada': getattr(loja, 'senha_foi_alterada', False),
                'requer_cpf_cnpj': True,  # SEMPRE requer CPF/CNPJ para maior segurança
            }
            
            # Cachear por 5 minutos (300 segundos)
            cache.set(cache_key, data, 300)
            logger.debug(f'💾 Cache SET para loja {slug}')
            
            return Response(data)
        except Loja.DoesNotExist:
            return Response({'error': 'Loja não encontrada'}, status=404)
        except Exception as e:
            logger.exception('info_publica erro para slug=%s: %s', slug, e)
            return Response(
                {'error': 'Erro ao carregar dados da loja. Tente novamente.'},
                status=500
            )
    
    @action(detail=False, methods=['get'])
    def heartbeat(self, request):
        """
        Endpoint para manter sessão ativa (heartbeat)
        Frontend deve chamar este endpoint a cada 5 minutos para evitar timeout
        """
        from django.utils import timezone
        from .session_manager import SessionManager
        
        if not request.user or not request.user.is_authenticated:
            return Response({
                'error': 'Não autenticado',
                'code': 'NOT_AUTHENTICATED'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Atualizar atividade da sessão
        SessionManager.update_activity(request.user.id)
        
        # Obter informações da sessão
        session_info = SessionManager.get_session_info(request.user.id)
        
        return Response({
            'status': 'alive',
            'user': request.user.username,
            'user_id': request.user.id,
            'timestamp': timezone.now().isoformat(),
            'session': session_info
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], permission_classes=[IsSuperAdmin])
    def debug_auth(self, request):
        """Debug endpoint para verificar autenticação - APENAS SUPERADMIN"""
        return Response({
            'authenticated': request.user.is_authenticated if hasattr(request, 'user') else False,
            'user': str(request.user) if hasattr(request, 'user') and request.user.is_authenticated else 'Anonymous',
            'headers': dict(request.headers),
            'method': request.method,
            'path': request.path,
            'query_params': dict(request.query_params),
            'permissions_checked': True
        })
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def verificar_senha_provisoria(self, request):
        """Verifica se o usuário logado precisa trocar a senha provisória (público para login)"""
        # Se não estiver autenticado, retornar False
        if not request.user or not request.user.is_authenticated:
            return Response({
                'precisa_trocar_senha': False,
                'mensagem': 'Usuário não autenticado'
            })
        
        try:
            # Buscar loja do usuário logado
            loja = Loja.objects.get(owner=request.user)
            
            precisa_trocar = not loja.senha_foi_alterada and bool(loja.senha_provisoria)
            logger.info(f"🔍 Verificar senha provisória - Loja: {loja.slug}, senha_foi_alterada: {loja.senha_foi_alterada}, tem_senha_provisoria: {bool(loja.senha_provisoria)}, precisa_trocar: {precisa_trocar}")
            
            return Response({
                'precisa_trocar_senha': precisa_trocar,
                'loja_id': loja.id,
                'loja_nome': loja.nome,
                'loja_slug': loja.slug,
            })
        except Loja.DoesNotExist:
            return Response({
                'precisa_trocar_senha': False,
                'mensagem': 'Usuário não possui loja associada'
            })
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def debug_senha_status(self, request):
        """DEBUG: Verifica o estado dos campos de senha de uma loja por slug"""
        slug = request.query_params.get('slug')
        if not slug:
            return Response({'error': 'Parâmetro slug é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            loja = Loja.objects.get(slug=slug)
            precisa_trocar = not loja.senha_foi_alterada and bool(loja.senha_provisoria)
            
            return Response({
                'loja_id': loja.id,
                'loja_slug': loja.slug,
                'loja_nome': loja.nome,
                'senha_provisoria_existe': bool(loja.senha_provisoria),
                'senha_provisoria_valor': loja.senha_provisoria[:3] + '***' if loja.senha_provisoria else None,
                'senha_foi_alterada': loja.senha_foi_alterada,
                'precisa_trocar_senha': precisa_trocar,
                'owner_username': loja.owner.username,
                'is_active': loja.is_active,
            })
        except Loja.DoesNotExist:
            return Response({'error': f'Loja com slug "{slug}" não encontrada'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'], permission_classes=[IsOwnerOrSuperAdmin])
    def alterar_senha_primeiro_acesso(self, request, pk=None):
        """
        Altera senha no primeiro acesso: proprietário da loja ou profissional (Clínica da Beleza).
        Proprietário: atualiza senha do User e loja.senha_foi_alterada.
        Profissional: atualiza senha do User e ProfissionalUsuario.precisa_trocar_senha = False.
        """
        if not request.user or not request.user.is_authenticated:
            return Response(
                {'error': 'Autenticação necessária'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        nova_senha = request.data.get('nova_senha')
        confirmar_senha = request.data.get('confirmar_senha')
        if not nova_senha or not confirmar_senha:
            return Response(
                {'error': 'Nova senha e confirmação são obrigatórias'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if nova_senha != confirmar_senha:
            return Response(
                {'error': 'As senhas não coincidem'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if len(nova_senha) < 6:
            return Response(
                {'error': 'A senha deve ter no mínimo 6 caracteres'},
                status=status.HTTP_400_BAD_REQUEST
            )

        loja = self.get_object()
        user = request.user

        # Caso 1: proprietário da loja
        if user == loja.owner:
            if loja.senha_foi_alterada:
                return Response(
                    {'error': 'A senha já foi alterada anteriormente'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            user.set_password(nova_senha)
            user.save()
            loja.senha_foi_alterada = True
            loja.save()
            return Response({
                'message': 'Senha alterada com sucesso!',
                'loja': loja.nome
            })

        # Caso 2: profissional (ProfissionalUsuario) da Clínica da Beleza
        try:
            pu = ProfissionalUsuario.objects.get(user=user, loja=loja)
        except ProfissionalUsuario.DoesNotExist:
            return Response(
                {'error': 'Apenas o proprietário ou um profissional desta loja pode alterar a senha aqui'},
                status=status.HTTP_403_FORBIDDEN
            )
        if not pu.precisa_trocar_senha:
            return Response(
                {'error': 'A senha já foi alterada anteriormente'},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.set_password(nova_senha)
        user.save()
        pu.precisa_trocar_senha = False
        pu.save(update_fields=['precisa_trocar_senha'])
        return Response({
            'message': 'Senha alterada com sucesso!',
            'loja': loja.nome
        })
    
    @action(detail=True, methods=['post'], permission_classes=[IsSuperAdmin])
    def resetar_senha_provisoria(self, request, pk=None):
        """
        Reseta a senha provisória de uma loja (apenas superadmin)
        Usado para corrigir lojas criadas antes da implementação do fluxo de senha provisória
        """
        import secrets
        import string
        from django.core.mail import send_mail
        from django.conf import settings
        
        loja = self.get_object()
        
        # Gerar nova senha provisória
        alphabet = string.ascii_letters + string.digits + "!@#$%&*"
        nova_senha = ''.join(secrets.choice(alphabet) for _ in range(8))
        
        # Atualizar senha do usuário
        user = loja.owner
        user.set_password(nova_senha)
        user.save()
        
        # Atualizar campos da loja
        loja.senha_provisoria = nova_senha
        loja.senha_foi_alterada = False
        loja.save()
        
        logger.info(f"✅ Senha provisória resetada para loja {loja.slug}")
        logger.info(f"   - senha_provisoria: {nova_senha[:3]}***")
        logger.info(f"   - senha_foi_alterada: False")
        
        # Tentar enviar email
        email_enviado = False
        try:
            if hasattr(settings, 'DEFAULT_FROM_EMAIL') and settings.DEFAULT_FROM_EMAIL:
                assunto = f"Nova Senha Provisória - {loja.nome}"
                mensagem = f"""
Olá!

Sua senha foi resetada para a loja "{loja.nome}".

🔐 NOVOS DADOS DE ACESSO:
• URL de Login: https://lwksistemas.com.br{loja.login_page_url}
• Usuário: {user.username}
• Senha Provisória: {nova_senha}

⚠️ IMPORTANTE:
• Esta é uma senha provisória
• Você será solicitado a trocar a senha no primeiro acesso

---
Equipe de Suporte
"""
                send_mail(
                    subject=assunto,
                    message=mensagem,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=True
                )
                email_enviado = True
                logger.info(f"✅ Email enviado para {user.email}")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao enviar email: {e}")
        
        return Response({
            'message': 'Senha provisória resetada com sucesso!',
            'loja_id': loja.id,
            'loja_slug': loja.slug,
            'loja_nome': loja.nome,
            'owner_username': user.username,
            'owner_email': user.email,
            'senha_provisoria': nova_senha,
            'senha_foi_alterada': False,
            'email_enviado': email_enviado,
            'precisa_trocar_senha': True
        })
    
    def destroy(self, request, *args, **kwargs):
        """Exclusão completa da loja com limpeza de todos os dados"""
        loja = self.get_object()
        
        # Coletar informações antes da exclusão
        loja_nome = loja.nome
        loja_slug = loja.slug
        loja_id = loja.id
        database_name = loja.database_name
        database_created = loja.database_created
        owner_username = loja.owner.username
        owner = loja.owner
        owner_id = owner.id
        
        # Contar dados relacionados
        outras_lojas_owner = Loja.objects.filter(owner=loja.owner).exclude(id=loja.id).count()
        
        # Variáveis de controle
        chamados_removidos = 0
        respostas_removidas = 0
        logs_removidos = 0
        alertas_removidos = 0
        banco_removido = False
        asaas_deleted_payments = 0
        asaas_deleted_customer = False
        asaas_local_payments_removed = 0
        asaas_local_customers_removed = 0
        asaas_local_subscriptions_removed = 0
        mercadopago_deleted_payments = 0
        usuario_removido = False
        usuario_sera_removido = outras_lojas_owner == 0
        
        # 1. Remover chamados de suporte da loja (operação independente)
        try:
            from suporte.models import Chamado
            with transaction.atomic():
                chamados = Chamado.objects.filter(loja_slug=loja_slug)
                chamados_removidos = chamados.count()
                for chamado in chamados:
                    respostas_removidas += chamado.respostas.count()
                chamados.delete()
                print(f"✅ Chamados de suporte removidos: {chamados_removidos}")
        except Exception as e:
            print(f"⚠️ Erro ao remover chamados de suporte: {e}")
        
        # 1b. Remover logs, alertas e auditoria da loja
        logs_removidos = 0
        alertas_removidos = 0
        try:
            from .models import HistoricoAcessoGlobal, ViolacaoSeguranca
            from django.db.models import Q
            
            with transaction.atomic():
                # Remover histórico de acessos (logs/auditoria)
                # Inclui: logs da loja (loja_slug) + logs de ações sobre a loja (recurso="Loja" e recurso_id)
                logs = HistoricoAcessoGlobal.objects.filter(
                    Q(loja_slug=loja_slug) |  # Logs de ações dentro da loja
                    Q(recurso='Loja', recurso_id=loja_id)  # Logs de ações sobre a loja (criar/excluir)
                )
                logs_removidos = logs.count()
                logs.delete()
                
                # Remover violações de segurança (alertas)
                alertas = ViolacaoSeguranca.objects.filter(loja__slug=loja_slug)
                alertas_removidos = alertas.count()
                alertas.delete()
                
                if logs_removidos > 0 or alertas_removidos > 0:
                    print(f"✅ Logs/Auditoria removidos: {logs_removidos}, Alertas removidos: {alertas_removidos}")
        except Exception as e:
            print(f"⚠️ Erro ao remover logs/alertas: {e}")
        
        # 2. Remover arquivo SQLite se existir (config do banco é removida após loja.delete(),
        #    para não deixar nome órfão em settings.DATABASES quando o signal re-adiciona a config)
        if database_created:
            try:
                db_path = settings.BASE_DIR / f'db_{database_name}.sqlite3'
                if db_path.exists():
                    import os
                    os.remove(db_path)
                    banco_removido = True
                    print(f"✅ Arquivo do banco removido: {db_path}")
            except Exception as e:
                print(f"⚠️ Erro ao remover arquivo do banco: {e}")
        
        # 3. Remover dados de pagamentos (Asaas + Mercado Pago) - UNIFICADO
        try:
            from .payment_deletion_service import UnifiedPaymentDeletionService
            
            payment_service = UnifiedPaymentDeletionService()
            payment_results = payment_service.delete_all_payments_for_loja(loja_slug)
            
            # Extrair resultados para compatibilidade com código existente
            asaas_result = payment_results['providers'].get('Asaas', {})
            mercadopago_result = payment_results['providers'].get('Mercado Pago', {})
            
            # Asaas
            asaas_deleted_payments = asaas_result.get('api_cancelled', 0)
            asaas_deleted_customer = asaas_result.get('local_deleted_customers', 0) > 0
            asaas_local_payments_removed = asaas_result.get('local_deleted_payments', 0)
            asaas_local_customers_removed = asaas_result.get('local_deleted_customers', 0)
            asaas_local_subscriptions_removed = asaas_result.get('local_deleted_subscriptions', 0)
            
            # Mercado Pago
            mercadopago_deleted_payments = mercadopago_result.get('api_cancelled', 0)
            
            if payment_results['total_cancelled'] > 0:
                print(f"✅ Pagamentos cancelados: {payment_results['total_cancelled']} (Asaas: {asaas_deleted_payments}, MP: {mercadopago_deleted_payments})")
            if payment_results['errors']:
                for error in payment_results['errors']:
                    print(f"⚠️ {error}")
                    
        except Exception as e:
            print(f"⚠️ Erro ao remover dados de pagamentos: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        # 4. Remover a loja (operação principal; signal pre_delete limpa schema e tabelas default)
        try:
            with transaction.atomic():
                loja.delete()
                print(f"✅ Loja removida: {loja_nome}")
        except Exception as e:
            transaction.set_rollback(True)  # evita "current transaction is aborted" em usos posteriores da conexão
            print(f"❌ Erro ao remover loja: {e}")
            return Response(
                {'error': f'Erro ao remover loja: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # 4b. Remover configuração do banco de settings.DATABASES (evitar nome órfão no default)
        #     O signal pre_delete pode ter adicionado a config para limpar o schema tenant.
        if database_name and database_name in settings.DATABASES:
            try:
                del settings.DATABASES[database_name]
                print(f"✅ Configuração do banco removida do settings: {database_name}")
            except Exception as e:
                print(f"⚠️ Erro ao remover config do banco: {e}")
        
        # 5. Remover usuário proprietário se não for usado por outras lojas
        if usuario_sera_removido:
            try:
                user_to_delete = User.objects.filter(id=owner_id).first()
                if user_to_delete and not user_to_delete.is_superuser:
                    with transaction.atomic():
                        user_to_delete.groups.clear()
                        user_to_delete.user_permissions.clear()
                        user_to_delete.delete()
                        usuario_removido = True
                        print(f"✅ Usuário proprietário removido: {owner_username}")
            except Exception as e:
                print(f"⚠️ Erro ao remover usuário (pode já ter sido removido): {e}")
        
        # Retornar resposta de sucesso
        return Response({
            'message': f'Loja "{loja_nome}" foi completamente removida do sistema',
            'detalhes': {
                'loja_id': loja_id,
                'loja_nome': loja_nome,
                'loja_slug': loja_slug,
                'loja_removida': True,
                'suporte': {
                    'chamados_removidos': chamados_removidos,
                    'respostas_removidas': respostas_removidas
                },
                'logs_auditoria': {
                    'logs_removidos': logs_removidos,
                    'alertas_removidos': alertas_removidos
                },
                'banco_dados': {
                    'existia': database_created,
                    'nome': database_name,
                    'arquivo_removido': banco_removido,
                    'config_removida': database_created
                },
                'asaas': {
                    'api': {
                        'pagamentos_cancelados': asaas_deleted_payments,
                        'cliente_removido': asaas_deleted_customer
                    },
                    'local': {
                        'payments_removidos': asaas_local_payments_removed,
                        'customers_removidos': asaas_local_customers_removed,
                        'subscriptions_removidas': asaas_local_subscriptions_removed
                    }
                },
                'mercadopago': {
                    'boletos_pendentes_cancelados': mercadopago_deleted_payments
                },
                'usuario_proprietario': {
                    'username': owner_username,
                    'removido': usuario_removido,
                    'motivo_nao_removido': 'Possui outras lojas' if not usuario_sera_removido else ('Superuser/Staff' if not usuario_removido and usuario_sera_removido else None)
                },
                'limpeza_completa': True
            }
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], permission_classes=[IsOwnerOrSuperAdmin])
    def reenviar_senha(self, request, pk=None):
        """Gera nova senha provisória e envia por email (recuperação de senha)"""
        loja = self.get_object()
        
        # Verificar se o usuário é o proprietário (superadmin já passou pela permissão)
        if not request.user.is_superuser and request.user != loja.owner:
            return Response(
                {'error': 'Apenas o proprietário pode reenviar a senha'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            from django.core.mail import send_mail
            from django.conf import settings
            import random
            import string
            
            # Gerar nova senha provisória
            nova_senha_provisoria = ''.join(random.choices(string.ascii_letters + string.digits + '!@#$%', k=10))
            
            # Atualizar senha do usuário
            user = loja.owner
            user.set_password(nova_senha_provisoria)
            user.save()
            
            # Atualizar loja com nova senha provisória e resetar status
            loja.senha_provisoria = nova_senha_provisoria
            loja.senha_foi_alterada = False  # ✅ Forçar troca de senha no próximo login
            loja.save()
            
            assunto = f"Nova Senha Provisória - {loja.nome}"
            mensagem = f"""
Olá!

Você solicitou a recuperação de senha para sua loja "{loja.nome}".

🔐 NOVA SENHA PROVISÓRIA:
• URL de Login: https://lwksistemas.com.br{loja.login_page_url}
• Usuário: {loja.owner.username}
• Senha Provisória: {nova_senha_provisoria}

⚠️ IMPORTANTE:
• Esta é uma senha provisória gerada automaticamente
• Você será solicitado a alterar esta senha no primeiro acesso
• Por segurança, altere a senha assim que fizer login
• Mantenha seus dados de acesso em segurança

📋 INFORMAÇÕES DA LOJA:
• Nome: {loja.nome}
• Tipo: {loja.tipo_loja.nome}
• Plano: {loja.plano.nome}
• Assinatura: {loja.get_tipo_assinatura_display()}

---
Equipe de Suporte
Sistema Multi-Loja
            """.strip()
            
            send_mail(
                subject=assunto,
                message=mensagem,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[loja.owner.email],
                fail_silently=False
            )
            
            return Response({
                'message': f'Nova senha provisória gerada e enviada para {loja.owner.email}',
                'email_enviado': loja.owner.email,
                'loja': loja.nome,
                'precisa_trocar_senha': True
            })
            
        except Exception as e:
            return Response(
                {'error': f'Erro ao enviar email: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def criar_banco(self, request, pk=None):
        """Cria banco de dados isolado para a loja"""
        loja = self.get_object()
        
        if loja.database_created:
            return Response(
                {'error': 'Banco já foi criado para esta loja'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Adicionar banco às configurações
            db_name = loja.database_name
            db_path = settings.BASE_DIR / f'db_{db_name}.sqlite3'
            
            settings.DATABASES[db_name] = {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': db_path,
                'ATOMIC_REQUESTS': False,
                'AUTOCOMMIT': True,
                'CONN_MAX_AGE': 0,
                'CONN_HEALTH_CHECKS': False,
                'OPTIONS': {},
                'TIME_ZONE': None,
            }
            
            # Executar migrations
            call_command('migrate', '--database', db_name, verbosity=0)
            
            # Criar usuário admin da loja no banco isolado
            from django.contrib.auth.models import User as UserModel
            admin_loja = UserModel.objects.db_manager(db_name).create_user(
                username=loja.owner.username,
                email=loja.owner.email,
                password='senha123',  # Senha padrão
                is_staff=True
            )
            
            # Marcar como criado
            loja.database_created = True
            loja.save()
            
            return Response({
                'message': 'Banco criado com sucesso',
                'database_name': db_name,
                'database_path': str(db_path),
                'admin_username': loja.owner.username,
                'admin_password': 'senha123'
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    # Tamanho estimado do banco isolado por loja (512 MB recomendado para CRM, clínica, e-commerce leve)
    TAMANHO_BANCO_ESTIMATIVA_MB = 512

    @action(detail=True, methods=['get'])
    def info_loja(self, request, pk=None):
        """
        Retorna informações da loja para o superadmin: tamanho do banco, espaço livre, senha, página de login.
        
        ✅ ATUALIZADO v742: Usa dados reais do sistema de monitoramento de storage
        """
        loja = self.get_object()
        
        # ✅ NOVO v742: Usar dados reais do monitoramento de storage
        storage_usado_mb = float(loja.storage_usado_mb) if loja.storage_usado_mb else 0.0
        storage_limite_mb = loja.storage_limite_mb if loja.storage_limite_mb else (loja.plano.espaco_storage_gb * 1024 if loja.plano else 5120)
        storage_percentual = loja.get_storage_percentual()
        storage_livre_mb = storage_limite_mb - storage_usado_mb
        storage_livre_gb = round(storage_livre_mb / 1024, 2)
        
        # Informações sobre última verificação
        ultima_verificacao = loja.storage_ultima_verificacao
        if ultima_verificacao:
            from django.utils import timezone
            tempo_desde_verificacao = timezone.now() - ultima_verificacao
            horas_desde_verificacao = int(tempo_desde_verificacao.total_seconds() / 3600)
        else:
            horas_desde_verificacao = None
        
        # Status do storage
        if storage_percentual >= 100:
            storage_status = 'critical'  # Cheio
            storage_status_texto = 'Storage cheio'
        elif storage_percentual >= 80:
            storage_status = 'warning'  # Alerta
            storage_status_texto = 'Atingindo o limite'
        else:
            storage_status = 'ok'  # Normal
            storage_status_texto = 'Normal'
        
        return Response({
            'id': loja.id,
            'nome': loja.nome,
            'slug': loja.slug,
            # ✅ NOVO v742: Dados reais do monitoramento
            'storage_usado_mb': storage_usado_mb,
            'storage_limite_mb': storage_limite_mb,
            'storage_livre_mb': storage_livre_mb,
            'storage_livre_gb': storage_livre_gb,
            'storage_percentual': storage_percentual,
            'storage_status': storage_status,
            'storage_status_texto': storage_status_texto,
            'storage_alerta_enviado': loja.storage_alerta_enviado,
            'storage_ultima_verificacao': ultima_verificacao.isoformat() if ultima_verificacao else None,
            'storage_horas_desde_verificacao': horas_desde_verificacao,
            # Dados do plano
            'espaco_plano_gb': loja.plano.espaco_storage_gb if loja.plano else 5,
            'plano_nome': loja.plano.nome if loja.plano else 'Sem plano',
            # Dados de acesso
            'senha_provisoria': loja.senha_provisoria or '',
            'login_page_url': loja.login_page_url or '',
            'owner_username': loja.owner.username,
            'owner_email': loja.owner.email,
            # Dados legados (compatibilidade)
            'database_created': loja.database_created,
            'tamanho_banco_mb': storage_usado_mb,  # Compatibilidade
            'tamanho_banco_estimativa_mb': self.TAMANHO_BANCO_ESTIMATIVA_MB,
            'tamanho_banco_motivo': 'Dados reais do monitoramento de storage PostgreSQL',
            'espaco_livre_gb': storage_livre_gb,  # Compatibilidade
        })
    
    @action(detail=False, methods=['get'])
    def estatisticas(self, request):
        """Estatísticas gerais do sistema"""
        total_lojas = Loja.objects.count()
        lojas_ativas = Loja.objects.filter(is_active=True).count()
        lojas_trial = Loja.objects.filter(is_trial=True).count()
        
        # Receita mensal
        from django.db.models import Sum
        receita_mensal = FinanceiroLoja.objects.filter(
            status_pagamento='ativo'
        ).aggregate(total=Sum('valor_mensalidade'))['total'] or 0
        
        return Response({
            'total_lojas': total_lojas,
            'lojas_ativas': lojas_ativas,
            'lojas_trial': lojas_trial,
            'lojas_inativas': total_lojas - lojas_ativas,
            'receita_mensal_estimada': float(receita_mensal),
        })


class FinanceiroLojaViewSet(viewsets.ModelViewSet):
    serializer_class = FinanceiroLojaSerializer
    permission_classes = [IsSuperAdmin]
    
    def get_queryset(self):
        # ✅ OTIMIZAÇÃO: select_related para loja
        return FinanceiroLoja.objects.select_related('loja', 'loja__plano').all()
    
    @action(detail=False, methods=['get'])
    def pendentes(self, request):
        """Lojas com pagamento pendente"""
        pendentes = self.get_queryset().filter(status_pagamento__in=['pendente', 'atrasado'])
        serializer = self.get_serializer(pendentes, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def renovar(self, request, pk=None):
        """
        Cria nova cobrança para renovação de assinatura
        
        ✅ NOVO v719: Endpoint para renovação de assinatura no dashboard
        
        Body (opcional):
            {
                "dia_vencimento": 10  // Dia do mês (1-28)
            }
        
        Returns:
            {
                "success": true,
                "provedor": "asaas",
                "payment_id": "pay_123456",
                "boleto_url": "https://...",
                "pix_qr_code": "00020126...",
                "pix_copy_paste": "00020126...",
                "due_date": "2026-03-10",
                "value": 99.90
            }
        """
        from superadmin.cobranca_service import CobrancaService
        
        try:
            financeiro = self.get_object()
            loja = financeiro.loja
            
            # Obter dia_vencimento do body (opcional)
            dia_vencimento = request.data.get('dia_vencimento')
            
            if dia_vencimento:
                # Validar dia_vencimento
                try:
                    dia_vencimento = int(dia_vencimento)
                    if dia_vencimento < 1 or dia_vencimento > 28:
                        return Response({
                            'success': False,
                            'error': 'dia_vencimento deve estar entre 1 e 28'
                        }, status=status.HTTP_400_BAD_REQUEST)
                except (ValueError, TypeError):
                    return Response({
                        'success': False,
                        'error': 'dia_vencimento deve ser um número inteiro'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            logger.info(f"Renovando assinatura para loja {loja.slug} (dia_vencimento={dia_vencimento})")
            
            # Criar nova cobrança usando CobrancaService
            service = CobrancaService()
            result = service.renovar_cobranca(loja, financeiro, dia_vencimento)
            
            if result.get('success'):
                logger.info(f"✅ Cobrança renovada para loja {loja.slug}: {result.get('payment_id')}")
                return Response(result, status=status.HTTP_200_OK)
            else:
                logger.error(f"❌ Erro ao renovar cobrança para loja {loja.slug}: {result.get('error')}")
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.exception(f"Erro ao renovar assinatura: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def reenviar_senha(self, request, pk=None):
        """
        Reenvia senha provisória manualmente (apenas se pagamento já confirmado)
        
        ✅ NOVO v719: Endpoint para reenvio manual de senha
        
        Permissões: Apenas superadmin
        
        Returns:
            {
                "success": true,
                "message": "Senha reenviada para email@example.com"
            }
        
        Errors:
            - 400: Pagamento ainda não confirmado
            - 404: Loja não encontrada
            - 500: Erro ao enviar email
        """
        from superadmin.email_service import EmailService
        
        try:
            financeiro = self.get_object()
            loja = financeiro.loja
            owner = loja.owner
            
            # Verificar se pagamento já foi confirmado
            if financeiro.status_pagamento != 'ativo':
                return Response({
                    'success': False,
                    'error': f'Pagamento ainda não confirmado. Status atual: {financeiro.get_status_pagamento_display()}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            logger.info(f"Reenviando senha para loja {loja.slug} (owner: {owner.email})")
            
            # Enviar senha usando EmailService
            service = EmailService()
            success = service.enviar_senha_provisoria(loja, owner)
            
            if success:
                logger.info(f"✅ Senha reenviada para {owner.email} (loja {loja.slug})")
                return Response({
                    'success': True,
                    'message': f'Senha reenviada para {owner.email}'
                }, status=status.HTTP_200_OK)
            else:
                logger.warning(f"⚠️ Falha ao reenviar senha para {owner.email} (loja {loja.slug})")
                return Response({
                    'success': False,
                    'error': 'Falha ao enviar email. Email registrado para retry automático.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except Exception as e:
            logger.exception(f"Erro ao reenviar senha: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PagamentoLojaViewSet(viewsets.ModelViewSet):
    serializer_class = PagamentoLojaSerializer
    permission_classes = [IsSuperAdmin]
    
    def get_queryset(self):
        # ✅ OTIMIZAÇÃO: select_related para loja e financeiro
        return PagamentoLoja.objects.select_related('loja', 'financeiro').all()
    
    @action(detail=True, methods=['post'])
    def confirmar_pagamento(self, request, pk=None):
        """Confirmar pagamento de uma loja"""
        pagamento = self.get_object()
        
        from django.utils import timezone
        pagamento.status = 'pago'
        pagamento.data_pagamento = timezone.now()
        pagamento.save()
        
        # Atualizar financeiro
        financeiro = pagamento.financeiro
        financeiro.status_pagamento = 'ativo'
        financeiro.ultimo_pagamento = timezone.now()
        financeiro.total_pago += pagamento.valor
        financeiro.save()
        
        return Response({'message': 'Pagamento confirmado com sucesso'})


class UsuarioSistemaViewSet(viewsets.ModelViewSet):
    serializer_class = UsuarioSistemaSerializer
    permission_classes = [IsSuperAdmin]
    
    def get_queryset(self):
        # ✅ OTIMIZAÇÃO: select_related para user
        return UsuarioSistema.objects.select_related('user').prefetch_related('lojas_acesso').all()
    
    def create(self, request, *args, **kwargs):
        """Criar usuário com senha provisória gerada automaticamente"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # Pegar senha provisória gerada
        senha_provisoria = getattr(serializer.instance, '_senha_provisoria_gerada', None)
        
        # Adicionar senha provisória na resposta
        response_data = serializer.data
        response_data['senha_provisoria'] = senha_provisoria
        response_data['message'] = 'Usuário criado com sucesso! Senha provisória enviada por email.'
        
        headers = self.get_success_headers(serializer.data)
        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)
    
    def destroy(self, request, *args, **kwargs):
        """Exclusão completa do usuário (UsuarioSistema + User do Django). Não permite excluir se for owner de alguma loja."""
        usuario_sistema = self.get_object()
        user_django = usuario_sistema.user
        username = user_django.username
        user_id = user_django.id

        # Evitar órfãos e exclusão acidental: não excluir usuário que é dono de loja
        lojas_owned = Loja.objects.filter(owner=user_django).exists()
        if lojas_owned:
            return Response(
                {
                    'error': 'Não é possível excluir usuário que é proprietário de uma ou mais lojas. Exclua as lojas primeiro ou transfira a propriedade.',
                    'username': username,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        try:
            with transaction.atomic():
                # Limpar sessões manualmente antes de excluir (evita problemas de CASCADE)
                from superadmin.models import UserSession
                sessoes_count = UserSession.objects.filter(user_id=user_id).count()
                UserSession.objects.filter(user_id=user_id).delete()
                if sessoes_count:
                    logger.info(f"   ✅ {sessoes_count} sessão(ões) removida(s)")
                
                # Limpar grupos e permissões
                user_django.groups.clear()
                user_django.user_permissions.clear()
                
                # Excluir User do Django (CASCADE vai excluir UsuarioSistema automaticamente)
                user_django.delete()
                logger.info(f"✅ Usuário excluído: {username} (ID: {user_id})")
            
            return Response({
                'message': f'Usuário "{username}" foi completamente removido do sistema',
                'username': username,
                'detalhes': {
                    'user_id': user_id,
                    'sessoes_removidas': sessoes_count,
                    'usuario_sistema_removido': True,
                    'user_django_removido': True
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"❌ Erro ao excluir usuário {username}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return Response(
                {'error': f'Erro ao excluir usuário: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def suporte(self, request):
        """Listar apenas usuários de suporte"""
        suporte = self.get_queryset().filter(tipo='suporte')
        serializer = self.get_serializer(suporte, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def verificar_senha_provisoria(self, request):
        """Verifica se o usuário logado precisa trocar a senha provisória (público para login)"""
        # Se não estiver autenticado, retornar False
        if not request.user or not request.user.is_authenticated:
            return Response({
                'precisa_trocar_senha': False,
                'mensagem': 'Usuário não autenticado'
            })
        
        try:
            # Buscar UsuarioSistema do usuário logado
            usuario_sistema = UsuarioSistema.objects.get(user=request.user)
            
            return Response({
                'precisa_trocar_senha': not usuario_sistema.senha_foi_alterada and bool(usuario_sistema.senha_provisoria),
                'usuario_id': usuario_sistema.id,
                'usuario_nome': request.user.username,
                'tipo': usuario_sistema.tipo,
            })
        except UsuarioSistema.DoesNotExist:
            return Response({
                'precisa_trocar_senha': False,
                'mensagem': 'Usuário não possui perfil de sistema'
            })
    
    @action(detail=False, methods=['post'], permission_classes=[IsOwnerOrSuperAdmin])
    def alterar_senha_primeiro_acesso(self, request):
        """Permite ao usuário alterar a senha no primeiro acesso (apenas proprietário ou superadmin)"""
        # Verificar se está autenticado
        if not request.user or not request.user.is_authenticated:
            return Response(
                {'detail': 'Autenticação necessária'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        try:
            usuario_sistema = UsuarioSistema.objects.get(user=request.user)
        except UsuarioSistema.DoesNotExist:
            return Response(
                {'detail': 'Usuário não possui perfil de sistema'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Verificar se já alterou a senha
        if usuario_sistema.senha_foi_alterada:
            return Response(
                {'detail': 'A senha já foi alterada anteriormente'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        nova_senha = request.data.get('nova_senha')
        confirmar_senha = request.data.get('confirmar_senha')
        
        if not nova_senha or not confirmar_senha:
            return Response(
                {'detail': 'Nova senha e confirmação são obrigatórias'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if nova_senha != confirmar_senha:
            return Response(
                {'detail': 'As senhas não coincidem'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if len(nova_senha) < 6:
            return Response(
                {'detail': 'A senha deve ter no mínimo 6 caracteres'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Alterar senha do usuário
        user = request.user
        user.set_password(nova_senha)
        user.save()
        
        # Marcar que a senha foi alterada
        usuario_sistema.senha_foi_alterada = True
        usuario_sistema.save()
        
        return Response({
            'message': 'Senha alterada com sucesso!',
            'usuario': user.username,
            'tipo': usuario_sistema.get_tipo_display()
        })
    
    @action(detail=False, methods=['post'], permission_classes=[])
    def recuperar_senha(self, request):
        """Recuperar senha de usuário do sistema (público para recuperação de senha)"""
        email = request.data.get('email')
        tipo = request.data.get('tipo')  # 'superadmin' ou 'suporte'
        
        if not email or not tipo:
            return Response(
                {'detail': 'Email e tipo são obrigatórios'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Buscar usuário pelo email
            user = User.objects.get(email=email)
            
            # Verificar se tem UsuarioSistema associado
            try:
                usuario_sistema = UsuarioSistema.objects.get(user=user, tipo=tipo)
            except UsuarioSistema.DoesNotExist:
                return Response(
                    {'detail': 'Usuário não encontrado ou tipo incorreto'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Gerar nova senha provisória
            import random
            import string
            nova_senha = ''.join(random.choices(string.ascii_letters + string.digits + '!@#$%', k=10))
            
            # Atualizar senha do usuário
            user.set_password(nova_senha)
            user.save()
            
            # Atualizar senha provisória no UsuarioSistema
            usuario_sistema.senha_provisoria = nova_senha
            usuario_sistema.senha_foi_alterada = False
            usuario_sistema.save()
            
            # Enviar email com nova senha
            from django.core.mail import send_mail
            
            tipo_display = 'Super Admin' if tipo == 'superadmin' else 'Suporte'
            url_login = f"https://lwksistemas.com.br/{tipo}/login"
            
            assunto = f"Recuperação de Senha - {tipo_display}"
            mensagem = f"""
Olá {user.first_name or user.username}!

Você solicitou a recuperação de senha para acesso ao sistema.

🔐 NOVOS DADOS DE ACESSO:
• URL de Login: {url_login}
• Usuário: {user.username}
• Senha Provisória: {nova_senha}

⚠️ IMPORTANTE:
• Esta é uma senha provisória gerada automaticamente
• Recomendamos alterar a senha após o login
• Mantenha seus dados de acesso em segurança

Se você não solicitou esta recuperação, entre em contato imediatamente.

---
Equipe LWK Sistemas
            """.strip()
            
            send_mail(
                subject=assunto,
                message=mensagem,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False
            )
            
            return Response({
                'message': 'Senha provisória enviada para o email cadastrado',
                'email': email
            })
            
        except User.DoesNotExist:
            return Response(
                {'detail': 'Email não encontrado no sistema'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'detail': f'Erro ao enviar email: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EmailRetryViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar emails com falha de envio
    
    ✅ NOVO v719: Gerenciamento de retry de emails
    
    Endpoints:
    - GET /emails-retry/ - Lista emails pendentes
    - GET /emails-retry/{id}/ - Detalhes de um email
    - POST /emails-retry/{id}/reprocessar/ - Força reenvio
    - DELETE /emails-retry/{id}/ - Remove email da fila
    
    Permissões: Apenas superadmin
    """
    from superadmin.serializers import EmailRetrySerializer
    from superadmin.models import EmailRetry
    
    serializer_class = EmailRetrySerializer
    permission_classes = [IsSuperAdmin]
    
    def get_queryset(self):
        """
        Retorna emails ordenados por prioridade:
        1. Não enviados com tentativas < max
        2. Ordenados por proxima_tentativa
        """
        from django.db.models import Q
        
        queryset = EmailRetry.objects.select_related('loja').all()
        
        # Filtros opcionais via query params
        enviado = self.request.query_params.get('enviado')
        loja_slug = self.request.query_params.get('loja')
        
        if enviado is not None:
            enviado_bool = enviado.lower() in ['true', '1', 'yes']
            queryset = queryset.filter(enviado=enviado_bool)
        
        if loja_slug:
            queryset = queryset.filter(loja__slug=loja_slug)
        
        # Ordenar: pendentes primeiro, depois por proxima_tentativa
        return queryset.order_by('enviado', 'proxima_tentativa', '-created_at')
    
    @action(detail=False, methods=['get'])
    def pendentes(self, request):
        """
        Lista apenas emails pendentes (não enviados e com tentativas < max)
        
        GET /emails-retry/pendentes/
        """
        from django.db.models import F
        
        pendentes = self.get_queryset().filter(
            enviado=False,
            tentativas__lt=F('max_tentativas')
        )
        
        serializer = self.get_serializer(pendentes, many=True)
        return Response({
            'count': pendentes.count(),
            'results': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def falhados(self, request):
        """
        Lista emails que falharam (atingiram max tentativas)
        
        GET /emails-retry/falhados/
        """
        from django.db.models import F
        
        falhados = self.get_queryset().filter(
            enviado=False,
            tentativas__gte=F('max_tentativas')
        )
        
        serializer = self.get_serializer(falhados, many=True)
        return Response({
            'count': falhados.count(),
            'results': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def reprocessar(self, request, pk=None):
        """
        Força reprocessamento de email falhado
        
        POST /emails-retry/{id}/reprocessar/
        
        Returns:
            {
                "success": true,
                "message": "Email reenviado com sucesso"
            }
        """
        from superadmin.email_service import EmailService
        
        try:
            email_retry = self.get_object()
            
            if email_retry.enviado:
                return Response({
                    'success': False,
                    'error': 'Email já foi enviado'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            logger.info(f"Reprocessando email {email_retry.id} manualmente (admin: {request.user.username})")
            
            # Reenviar usando EmailService
            service = EmailService()
            success = service.reenviar_email(email_retry.id)
            
            if success:
                logger.info(f"✅ Email {email_retry.id} reenviado com sucesso")
                return Response({
                    'success': True,
                    'message': 'Email reenviado com sucesso'
                }, status=status.HTTP_200_OK)
            else:
                logger.warning(f"⚠️ Falha ao reenviar email {email_retry.id}")
                return Response({
                    'success': False,
                    'error': 'Falha ao reenviar email. Verifique os logs.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except Exception as e:
            logger.exception(f"Erro ao reprocessar email: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def reprocessar_todos_pendentes(self, request):
        """
        Reprocessa todos os emails pendentes
        
        POST /emails-retry/reprocessar_todos_pendentes/
        
        Returns:
            {
                "success": true,
                "total": 10,
                "enviados": 8,
                "falhados": 2
            }
        """
        from superadmin.email_service import EmailService
        from django.db.models import F
        
        try:
            pendentes = EmailRetry.objects.filter(
                enviado=False,
                tentativas__lt=F('max_tentativas')
            )
            
            total = pendentes.count()
            enviados = 0
            falhados = 0
            
            logger.info(f"Reprocessando {total} emails pendentes (admin: {request.user.username})")
            
            service = EmailService()
            for email_retry in pendentes:
                if service.reenviar_email(email_retry.id):
                    enviados += 1
                else:
                    falhados += 1
            
            logger.info(f"✅ Reprocessamento concluído: {enviados}/{total} enviados, {falhados} falhas")
            
            return Response({
                'success': True,
                'total': total,
                'enviados': enviados,
                'falhados': falhados
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.exception(f"Erro ao reprocessar emails: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Configuração Mercado Pago (boletos)
@api_view(['GET', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def mercadopago_config(request):
    """GET: retorna config (token mascarado). PATCH: atualiza enabled, use_for_boletos e opcionalmente access_token. Apenas superuser."""
    if not request.user.is_superuser:
        return Response({'detail': 'Sem permissão.'}, status=status.HTTP_403_FORBIDDEN)
    config = MercadoPagoConfig.get_config()
    if request.method == 'GET':
        return Response({
            'enabled': config.enabled,
            'use_for_boletos': config.use_for_boletos,
            'access_token_set': bool(config.access_token),
            'access_token_masked': (config.access_token[:8] + '...' + config.access_token[-4:]) if config.access_token and len(config.access_token) >= 12 else ('****' if config.access_token else ''),
            'public_key': getattr(config, 'public_key', '') or '',
            'chave_pix_estatica': getattr(config, 'chave_pix_estatica', '') or '',
        })
    if request.method == 'PATCH':
        if 'enabled' in request.data:
            config.enabled = bool(request.data['enabled'])
        if 'use_for_boletos' in request.data:
            config.use_for_boletos = bool(request.data['use_for_boletos'])
        if 'access_token' in request.data and request.data['access_token'] is not None:
            config.access_token = str(request.data['access_token']).strip()
        if 'public_key' in request.data and request.data['public_key'] is not None:
            config.public_key = str(request.data['public_key']).strip()[:80]
        if 'chave_pix_estatica' in request.data:
            config.chave_pix_estatica = str(request.data.get('chave_pix_estatica') or '').strip()[:120]
        config.save()
        return Response({
            'enabled': config.enabled,
            'use_for_boletos': config.use_for_boletos,
            'access_token_set': bool(config.access_token),
            'public_key': getattr(config, 'public_key', '') or '',
            'chave_pix_estatica': getattr(config, 'chave_pix_estatica', '') or '',
        })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def mercadopago_test(request):
    """Testa a conexão com a API do Mercado Pago (valida Access Token e disponibilidade de boleto). Apenas superuser."""
    if not request.user.is_superuser:
        return Response({'detail': 'Sem permissão.'}, status=status.HTTP_403_FORBIDDEN)
    config = MercadoPagoConfig.get_config()
    if not config.access_token:
        return Response(
            {'success': False, 'error': 'Access Token não configurado. Salve o token nas configurações antes de testar.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    from .mercadopago_service import MercadoPagoClient
    result = MercadoPagoClient(config.access_token).test_connection()
    if result.get('success'):
        return Response(result)
    return Response(result, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
@api_view(['GET', 'POST'])
@permission_classes([])
def mercadopago_webhook(request):
    """
    Webhook do Mercado Pago para notificações de pagamento.
    Configurar no painel MP: URL = https://seu-dominio.com/api/superadmin/mercadopago-webhook/
    Eventos: payment (pagamento atualizado). Ao receber approved, o sistema atualiza
    PagamentoLoja e FinanceiroLoja e desbloqueia a loja.

    GET: Teste de conectividade (retorna 200 e instruções para testar o POST).
    """
    if request.method == 'GET':
        return Response({
            'status': 'ok',
            'message': 'Endpoint do webhook Mercado Pago ativo.',
            'url': 'https://lwksistemas-38ad47519238.herokuapp.com/api/superadmin/mercadopago-webhook/',
            'test': 'Envie POST com JSON: {"type": "payment", "data": {"id": "<payment_id>"}}. '
                    'Use o ID de um pagamento real (boleto) para testar a confirmação.',
        }, status=status.HTTP_200_OK)

    try:
        # MP envia JSON: type e data.id
        body = request.data if isinstance(getattr(request, 'data', None), dict) else {}
        if not body and request.body:
            import json
            try:
                body = json.loads(request.body.decode('utf-8'))
            except Exception:
                body = {}
        notification_type = body.get('type') or body.get('action')
        data = body.get('data', body) or {}
        payment_id = data.get('id') if isinstance(data, dict) else None
        if not payment_id and isinstance(data, dict) and 'id' in data:
            payment_id = data['id']
        if not notification_type or not payment_id:
            logger.info("Webhook MP ignorado: type=%s, data=%s", notification_type, body)
            return Response({'status': 'ignored'}, status=status.HTTP_200_OK)
        if notification_type != 'payment':
            return Response({'status': 'ignored', 'type': notification_type}, status=status.HTTP_200_OK)
        from .sync_service import process_mercadopago_webhook_payment
        result = process_mercadopago_webhook_payment(str(payment_id))
        if result.get('success') and result.get('processed'):
            return Response({'status': 'processed', 'payment_id': payment_id, 'loja_slug': result.get('loja_slug')}, status=status.HTTP_200_OK)
        return Response({'status': 'ok', 'processed': result.get('processed', False)}, status=status.HTTP_200_OK)
    except Exception as e:
        logger.exception("Erro no webhook Mercado Pago: %s", e)
        return Response({'status': 'error'}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def sync_mercadopago_loja(request):
    """
    Sincroniza pagamentos Mercado Pago de uma loja (consulta API MP e atualiza status/financeiro).
    Uso: POST com { "loja_slug": "slug-da-loja" }. Apenas superadmin.
    Útil quando o webhook não foi recebido ou para atualizar manualmente pelo botão no financeiro.
    """
    if not request.user.is_superuser:
        return Response({'detail': 'Apenas superadmin.'}, status=status.HTTP_403_FORBIDDEN)
    loja_slug = (request.data.get('loja_slug') or '').strip()
    if not loja_slug:
        return Response(
            {'error': 'Envie "loja_slug" no body (ex: {"loja_slug": "minha-loja"}).'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        loja = Loja.objects.get(slug=loja_slug, is_active=True)
    except Loja.DoesNotExist:
        return Response(
            {'error': f'Loja com slug "{loja_slug}" não encontrada.'},
            status=status.HTTP_404_NOT_FOUND,
        )
    try:
        from .sync_service import sync_loja_payments_mercadopago
        resultado = sync_loja_payments_mercadopago(loja)
        processed = resultado.get('processed', 0)
        total_checked = resultado.get('total_checked', 0)
        return Response({
            'success': True,
            'message': f'Loja {loja_slug}: {processed} pagamento(s) atualizado(s) de {total_checked} verificados.',
            'processed': processed,
            'total_checked': total_checked,
            'loja_slug': loja_slug,
        })
    except Exception as e:
        logger.exception("sync_mercadopago_loja: %s", e)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# View para recuperação de senha de lojas (função simples, não ViewSet)
@api_view(['POST'])
@permission_classes([])
def recuperar_senha_loja(request):
    """Recuperar senha de loja pelo email e slug"""
    email = request.data.get('email')
    slug = request.data.get('slug')
    
    if not email or not slug:
        return Response(
            {'detail': 'Email e slug são obrigatórios'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Buscar loja pelo slug
        loja = Loja.objects.get(slug=slug, is_active=True)
        
        # Verificar se o email corresponde ao proprietário
        if loja.owner.email != email:
            return Response(
                {'detail': 'Email não corresponde ao proprietário da loja'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Gerar nova senha provisória
        import random
        import string
        nova_senha = ''.join(random.choices(string.ascii_letters + string.digits + '!@#$%', k=10))
        
        # Atualizar senha do usuário
        loja.owner.set_password(nova_senha)
        loja.owner.save()
        
        # Atualizar senha provisória na loja
        loja.senha_provisoria = nova_senha
        loja.senha_foi_alterada = False
        loja.save()
        
        # Enviar email com nova senha
        from django.core.mail import send_mail
        
        assunto = f"Recuperação de Senha - {loja.nome}"
        mensagem = f"""
Olá!

Você solicitou a recuperação de senha para acesso à sua loja "{loja.nome}".

🔐 NOVOS DADOS DE ACESSO:
• URL de Login: https://lwksistemas.com.br{loja.login_page_url}
• Usuário: {loja.owner.username}
• Senha Provisória: {nova_senha}

⚠️ IMPORTANTE:
• Esta é uma senha provisória gerada automaticamente
• Recomendamos alterar a senha no primeiro acesso
• Mantenha seus dados de acesso em segurança

📋 INFORMAÇÕES DA LOJA:
• Nome: {loja.nome}
• Tipo: {loja.tipo_loja.nome}
• Plano: {loja.plano.nome}

Se você não solicitou esta recuperação, entre em contato imediatamente.

---
Equipe LWK Sistemas
        """.strip()
        
        send_mail(
            subject=assunto,
            message=mensagem,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False
        )
        
        return Response({
            'message': 'Senha provisória enviada para o email cadastrado',
            'email': email
        })
        
    except Loja.DoesNotExist:
        return Response(
            {'detail': 'Loja não encontrada ou inativa'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'detail': f'Erro ao enviar email: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )



class HistoricoAcessoGlobalViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para Histórico de Acesso Global (APENAS LEITURA)
    
    Apenas SuperAdmin pode acessar.
    
    Boas práticas aplicadas:
    - ReadOnlyModelViewSet: Apenas leitura (segurança)
    - Filtros otimizados com Q objects
    - Paginação automática
    - Select_related para otimizar queries
    - Permissões restritas (IsSuperAdmin)
    
    Filtros disponíveis:
    - usuario_email: Email do usuário
    - loja_id: ID da loja
    - loja_slug: Slug da loja
    - acao: Tipo de ação
    - data_inicio: Data inicial (YYYY-MM-DD)
    - data_fim: Data final (YYYY-MM-DD)
    - ip_address: Endereço IP
    - sucesso: true/false
    - search: Busca em nome, email, loja
    """
    
    permission_classes = [IsSuperAdmin]
    
    def get_serializer_class(self):
        """
        Usa serializer otimizado para listagem
        Serializer completo para detalhes
        """
        from .serializers import HistoricoAcessoGlobalSerializer, HistoricoAcessoGlobalListSerializer
        
        if self.action == 'list':
            return HistoricoAcessoGlobalListSerializer
        return HistoricoAcessoGlobalSerializer
    
    def get_queryset(self):
        """
        Queryset otimizado com filtros
        
        Boas práticas:
        - Select_related para evitar N+1 queries
        - Filtros via query params
        - Ordenação por data (mais recente primeiro)
        """
        from .models import HistoricoAcessoGlobal
        from django.db.models import Q
        from datetime import datetime
        
        # Base queryset com select_related para otimização
        queryset = HistoricoAcessoGlobal.objects.select_related(
            'user',
            'loja',
            'loja__tipo_loja'
        ).all()
        
        # Obter parâmetros de filtro
        params = self.request.query_params
        
        # Filtro por usuário (email)
        usuario_email = params.get('usuario_email')
        if usuario_email:
            queryset = queryset.filter(usuario_email__icontains=usuario_email)
        
        # Filtro por loja (ID)
        loja_id = params.get('loja_id')
        if loja_id:
            queryset = queryset.filter(loja_id=loja_id)
        
        # Filtro por loja (slug)
        loja_slug = params.get('loja_slug')
        if loja_slug:
            queryset = queryset.filter(loja_slug__iexact=loja_slug)
        
        # Filtro por loja (nome)
        loja_nome = params.get('loja_nome')
        if loja_nome:
            queryset = queryset.filter(loja_nome__icontains=loja_nome)
        
        # Filtro por ação
        acao = params.get('acao')
        if acao:
            queryset = queryset.filter(acao=acao)
        
        # Filtro por período
        data_inicio = params.get('data_inicio')
        data_fim = params.get('data_fim')
        
        if data_inicio:
            try:
                data_inicio_dt = datetime.strptime(data_inicio, '%Y-%m-%d')
                queryset = queryset.filter(created_at__gte=data_inicio_dt)
            except ValueError:
                pass
        
        if data_fim:
            try:
                data_fim_dt = datetime.strptime(data_fim, '%Y-%m-%d')
                # Incluir o dia inteiro (até 23:59:59)
                from datetime import timedelta
                data_fim_dt = data_fim_dt + timedelta(days=1)
                queryset = queryset.filter(created_at__lt=data_fim_dt)
            except ValueError:
                pass
        
        # Filtro por IP
        ip_address = params.get('ip_address')
        if ip_address:
            queryset = queryset.filter(ip_address=ip_address)
        
        # Filtro por sucesso
        sucesso = params.get('sucesso')
        if sucesso is not None:
            sucesso_bool = sucesso.lower() == 'true'
            queryset = queryset.filter(sucesso=sucesso_bool)
        
        # Busca geral (nome, email, loja)
        search = params.get('search')
        if search:
            queryset = queryset.filter(
                Q(usuario_nome__icontains=search) |
                Q(usuario_email__icontains=search) |
                Q(loja_nome__icontains=search) |
                Q(loja_slug__icontains=search)
            )
        
        return queryset.order_by('-created_at')
    
    @action(detail=False, methods=['get'])
    def estatisticas(self, request):
        """
        Retorna estatísticas do histórico
        
        Retorna:
        - Total de acessos
        - Total de logins
        - Total de ações por tipo
        - Usuários mais ativos
        - Lojas mais ativas
        """
        from .models import HistoricoAcessoGlobal
        from django.db.models import Count
        from datetime import datetime, timedelta
        
        # Período (últimos 30 dias por padrão)
        data_inicio = request.query_params.get('data_inicio')
        data_fim = request.query_params.get('data_fim')
        
        if not data_inicio:
            data_inicio = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not data_fim:
            data_fim = datetime.now().strftime('%Y-%m-%d')
        
        try:
            data_inicio_dt = datetime.strptime(data_inicio, '%Y-%m-%d')
            data_fim_dt = datetime.strptime(data_fim, '%Y-%m-%d') + timedelta(days=1)
        except ValueError:
            return Response(
                {'error': 'Formato de data inválido. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Queryset base
        qs = HistoricoAcessoGlobal.objects.filter(
            created_at__gte=data_inicio_dt,
            created_at__lt=data_fim_dt
        )
        
        # Estatísticas
        stats = {
            'periodo': {
                'inicio': data_inicio,
                'fim': data_fim,
            },
            'total_acessos': qs.count(),
            'total_logins': qs.filter(acao='login').count(),
            'total_sucesso': qs.filter(sucesso=True).count(),
            'total_erros': qs.filter(sucesso=False).count(),
            
            # Ações por tipo
            'acoes_por_tipo': list(
                qs.values('acao')
                .annotate(total=Count('id'))
                .order_by('-total')
            ),
            
            # Usuários mais ativos (top 10)
            'usuarios_mais_ativos': list(
                qs.values('usuario_email', 'usuario_nome')
                .annotate(total=Count('id'))
                .order_by('-total')[:10]
            ),
            
            # Lojas mais ativas (top 10)
            'lojas_mais_ativas': list(
                qs.filter(loja__isnull=False)
                .values('loja_id', 'loja_nome', 'loja_slug')
                .annotate(total=Count('id'))
                .order_by('-total')[:10]
            ),
            
            # IPs mais frequentes (top 10)
            'ips_mais_frequentes': list(
                qs.values('ip_address')
                .annotate(total=Count('id'))
                .order_by('-total')[:10]
            ),
        }
        
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def atividade_temporal(self, request):
        """
        Retorna atividade ao longo do tempo (para gráficos)
        
        Agrupa por dia, hora ou mês dependendo do período
        """
        from .models import HistoricoAcessoGlobal
        from django.db.models import Count
        from django.db.models.functions import TruncDate, TruncHour, TruncMonth
        from datetime import datetime, timedelta
        
        # Período (últimos 7 dias por padrão)
        data_inicio = request.query_params.get('data_inicio')
        data_fim = request.query_params.get('data_fim')
        
        if not data_inicio:
            data_inicio = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        if not data_fim:
            data_fim = datetime.now().strftime('%Y-%m-%d')
        
        try:
            data_inicio_dt = datetime.strptime(data_inicio, '%Y-%m-%d')
            data_fim_dt = datetime.strptime(data_fim, '%Y-%m-%d') + timedelta(days=1)
        except ValueError:
            return Response(
                {'error': 'Formato de data inválido. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Determinar granularidade baseado no período
        dias_diferenca = (data_fim_dt - data_inicio_dt).days
        
        qs = HistoricoAcessoGlobal.objects.filter(
            created_at__gte=data_inicio_dt,
            created_at__lt=data_fim_dt
        )
        
        if dias_diferenca <= 2:
            # Até 2 dias: agrupar por hora
            atividade = list(
                qs.annotate(periodo=TruncHour('created_at'))
                .values('periodo')
                .annotate(
                    total=Count('id'),
                    sucessos=Count('id', filter=Q(sucesso=True)),
                    erros=Count('id', filter=Q(sucesso=False))
                )
                .order_by('periodo')
            )
            granularidade = 'hora'
        elif dias_diferenca <= 90:
            # Até 90 dias: agrupar por dia
            atividade = list(
                qs.annotate(periodo=TruncDate('created_at'))
                .values('periodo')
                .annotate(
                    total=Count('id'),
                    sucessos=Count('id', filter=Q(sucesso=True)),
                    erros=Count('id', filter=Q(sucesso=False))
                )
                .order_by('periodo')
            )
            granularidade = 'dia'
        else:
            # Mais de 90 dias: agrupar por mês
            atividade = list(
                qs.annotate(periodo=TruncMonth('created_at'))
                .values('periodo')
                .annotate(
                    total=Count('id'),
                    sucessos=Count('id', filter=Q(sucesso=True)),
                    erros=Count('id', filter=Q(sucesso=False))
                )
                .order_by('periodo')
            )
            granularidade = 'mes'
        
        # Formatar datas para string
        for item in atividade:
            if granularidade == 'hora':
                item['periodo'] = item['periodo'].strftime('%d/%m/%Y %H:00')
            elif granularidade == 'dia':
                item['periodo'] = item['periodo'].strftime('%d/%m/%Y')
            else:
                item['periodo'] = item['periodo'].strftime('%m/%Y')
        
        return Response({
            'periodo': {
                'inicio': data_inicio,
                'fim': data_fim,
            },
            'granularidade': granularidade,
            'atividade': atividade,
        })
    
    @action(detail=False, methods=['get'])
    def exportar(self, request):
        """
        Exporta histórico em CSV
        
        Aplica os mesmos filtros da listagem
        """
        import csv
        from django.http import HttpResponse
        from datetime import datetime
        
        # Obter queryset filtrado
        queryset = self.get_queryset()
        
        # Limitar a 10000 registros para evitar timeout
        queryset = queryset[:10000]
        
        # Criar resposta CSV
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="historico_acessos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        # Escrever CSV
        writer = csv.writer(response)
        writer.writerow([
            'Data/Hora',
            'Usuário',
            'Email',
            'Loja',
            'Ação',
            'Recurso',
            'IP',
            'Navegador',
            'SO',
            'Sucesso',
        ])
        
        for item in queryset:
            writer.writerow([
                item.created_at.strftime('%d/%m/%Y %H:%M:%S'),
                item.usuario_nome,
                item.usuario_email,
                item.loja_nome or 'SuperAdmin',
                item.get_acao_display(),
                item.recurso or '-',
                item.ip_address,
                item.navegador,
                item.sistema_operacional,
                'Sim' if item.sucesso else 'Não',
            ])
        
        return response
    
    @action(detail=False, methods=['get'])
    def exportar_json(self, request):
        """
        Exporta histórico em JSON
        
        Aplica os mesmos filtros da listagem
        """
        from django.http import JsonResponse
        from datetime import datetime
        
        # Obter queryset filtrado
        queryset = self.get_queryset()
        
        # Limitar a 10000 registros para evitar timeout
        queryset = queryset[:10000]
        
        # Serializar dados
        serializer = self.get_serializer(queryset, many=True)
        
        # Criar resposta JSON
        response = JsonResponse({
            'total': queryset.count(),
            'exportado_em': datetime.now().isoformat(),
            'dados': serializer.data
        }, safe=False)
        
        response['Content-Disposition'] = f'attachment; filename="historico_acessos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json"'
        
        return response
    
    @action(detail=True, methods=['get'])
    def contexto_temporal(self, request, pk=None):
        """
        Retorna contexto temporal de um log específico
        
        Mostra N logs anteriores e N posteriores do mesmo usuário
        para entender o contexto da ação.
        
        Query params:
        - antes: Número de logs anteriores (padrão: 5)
        - depois: Número de logs posteriores (padrão: 5)
        
        Returns:
        - log_atual: Log selecionado
        - logs_anteriores: Lista de logs anteriores
        - logs_posteriores: Lista de logs posteriores
        """
        from .models import HistoricoAcessoGlobal
        
        # Obter log atual
        log_atual = self.get_object()
        
        # Obter parâmetros
        try:
            antes = int(request.query_params.get('antes', 5))
            depois = int(request.query_params.get('depois', 5))
        except ValueError:
            return Response(
                {'error': 'Parâmetros "antes" e "depois" devem ser números inteiros'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Limitar a 20 logs de cada lado
        antes = min(antes, 20)
        depois = min(depois, 20)
        
        # Buscar logs anteriores do mesmo usuário
        logs_anteriores = HistoricoAcessoGlobal.objects.filter(
            usuario_email=log_atual.usuario_email,
            created_at__lt=log_atual.created_at
        ).select_related('user', 'loja').order_by('-created_at')[:antes]
        
        # Buscar logs posteriores do mesmo usuário
        logs_posteriores = HistoricoAcessoGlobal.objects.filter(
            usuario_email=log_atual.usuario_email,
            created_at__gt=log_atual.created_at
        ).select_related('user', 'loja').order_by('created_at')[:depois]
        
        # Serializar
        from .serializers import HistoricoAcessoGlobalListSerializer
        
        return Response({
            'log_atual': HistoricoAcessoGlobalListSerializer(log_atual).data,
            'logs_anteriores': HistoricoAcessoGlobalListSerializer(logs_anteriores, many=True).data,
            'logs_posteriores': HistoricoAcessoGlobalListSerializer(logs_posteriores, many=True).data,
            'total_anteriores': logs_anteriores.count(),
            'total_posteriores': logs_posteriores.count(),
        })
    
    @action(detail=False, methods=['get'])
    def busca_avancada(self, request):
        """
        Busca avançada com texto livre
        
        Busca em múltiplos campos simultaneamente:
        - Nome do usuário
        - Email do usuário
        - Nome da loja
        - Slug da loja
        - Recurso
        - Detalhes da ação
        - URL
        - User agent
        
        Query params:
        - q: Texto de busca (obrigatório)
        - Todos os outros filtros do get_queryset também funcionam
        
        Returns:
        - Resultados paginados com highlight dos termos encontrados
        """
        from .models import HistoricoAcessoGlobal
        from django.db.models import Q
        
        # Obter termo de busca
        query = request.query_params.get('q', '').strip()
        
        if not query:
            return Response(
                {'error': 'Parâmetro "q" (termo de busca) é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Buscar em múltiplos campos
        queryset = self.get_queryset().filter(
            Q(usuario_nome__icontains=query) |
            Q(usuario_email__icontains=query) |
            Q(loja_nome__icontains=query) |
            Q(loja_slug__icontains=query) |
            Q(recurso__icontains=query) |
            Q(detalhes__icontains=query) |
            Q(url__icontains=query) |
            Q(user_agent__icontains=query) |
            Q(ip_address__icontains=query)
        )
        
        # Paginar resultados
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response({
                'termo_busca': query,
                'total_encontrado': queryset.count(),
                'resultados': serializer.data
            })
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'termo_busca': query,
            'total_encontrado': queryset.count(),
            'resultados': serializer.data
        })


class ViolacaoSegurancaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar violações de segurança
    
    Endpoints:
    - GET /api/superadmin/violacoes-seguranca/ - Lista violações
    - GET /api/superadmin/violacoes-seguranca/{id}/ - Detalhes de uma violação
    - PUT /api/superadmin/violacoes-seguranca/{id}/ - Atualizar violação
    - POST /api/superadmin/violacoes-seguranca/{id}/resolver/ - Marcar como resolvida
    - POST /api/superadmin/violacoes-seguranca/{id}/marcar_falso_positivo/ - Marcar como falso positivo
    - GET /api/superadmin/violacoes-seguranca/estatisticas/ - Estatísticas de violações
    
    Boas práticas:
    - Read-only por padrão (apenas SuperAdmin pode modificar)
    - Filtros otimizados
    - Serializers diferentes para list e detail
    - Actions customizadas para operações específicas
    """
    permission_classes = [IsSuperAdmin]
    
    def get_serializer_class(self):
        """
        Usa serializer otimizado para listagem
        Serializer completo para detalhes
        """
        if self.action == 'list':
            return ViolacaoSegurancaListSerializer
        return ViolacaoSegurancaSerializer
    
    def get_queryset(self):
        """
        Retorna violações com filtros aplicados
        
        Filtros disponíveis:
        - status: nova, investigando, resolvida, falso_positivo
        - criticidade: baixa, media, alta, critica
        - tipo: brute_force, rate_limit, etc.
        - loja_id: ID da loja
        - usuario_email: Email do usuário
        - data_inicio: Data inicial (YYYY-MM-DD)
        - data_fim: Data final (YYYY-MM-DD)
        
        Ordenação: Por criticidade (desc) e data (desc)
        """
        from .models import ViolacaoSeguranca
        from datetime import datetime
        
        # Base queryset com select_related para otimização
        queryset = ViolacaoSeguranca.objects.all().select_related(
            'user', 'loja', 'resolvido_por'
        ).prefetch_related('logs_relacionados')
        
        # Filtros
        status = self.request.query_params.get('status')
        criticidade = self.request.query_params.get('criticidade')
        tipo = self.request.query_params.get('tipo')
        loja_id = self.request.query_params.get('loja_id')
        usuario_email = self.request.query_params.get('usuario_email')
        data_inicio = self.request.query_params.get('data_inicio')
        data_fim = self.request.query_params.get('data_fim')
        
        if status:
            queryset = queryset.filter(status=status)
        if criticidade:
            queryset = queryset.filter(criticidade=criticidade)
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        if loja_id:
            queryset = queryset.filter(loja_id=loja_id)
        if usuario_email:
            queryset = queryset.filter(usuario_email__icontains=usuario_email)
        if data_inicio:
            try:
                data_inicio_dt = datetime.strptime(data_inicio, '%Y-%m-%d')
                queryset = queryset.filter(created_at__gte=data_inicio_dt)
            except ValueError:
                pass
        if data_fim:
            try:
                data_fim_dt = datetime.strptime(data_fim, '%Y-%m-%d')
                from datetime import timedelta
                data_fim_dt = data_fim_dt + timedelta(days=1)
                queryset = queryset.filter(created_at__lt=data_fim_dt)
            except ValueError:
                pass
        
        # Ordenação customizada: criticidade (desc) e data (desc)
        # Ordem de criticidade: critica > alta > media > baixa
        from django.db.models import Case, When, IntegerField
        
        queryset = queryset.annotate(
            criticidade_ordem=Case(
                When(criticidade='critica', then=4),
                When(criticidade='alta', then=3),
                When(criticidade='media', then=2),
                When(criticidade='baixa', then=1),
                default=0,
                output_field=IntegerField()
            )
        ).order_by('-criticidade_ordem', '-created_at')
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def resolver(self, request, pk=None):
        """
        Marca violação como resolvida
        
        POST /api/superadmin/violacoes-seguranca/{id}/resolver/
        
        Body (opcional):
        {
            "notas": "Investigado e resolvido. Usuário foi alertado."
        }
        
        Response:
        {
            "status": "resolvida",
            "resolvido_por": "admin@example.com",
            "resolvido_em": "2024-01-15T10:30:00Z"
        }
        """
        from django.utils import timezone
        
        violacao = self.get_object()
        violacao.status = 'resolvida'
        violacao.resolvido_por = request.user
        violacao.resolvido_em = timezone.now()
        violacao.notas = request.data.get('notas', '')
        violacao.save()
        
        logger.info(f"✅ Violação {violacao.id} resolvida por {request.user.email}")
        
        return Response({
            'status': 'resolvida',
            'resolvido_por': request.user.email,
            'resolvido_em': violacao.resolvido_em,
            'notas': violacao.notas
        })
    
    @action(detail=True, methods=['post'])
    def marcar_falso_positivo(self, request, pk=None):
        """
        Marca violação como falso positivo
        
        POST /api/superadmin/violacoes-seguranca/{id}/marcar_falso_positivo/
        
        Body (opcional):
        {
            "notas": "Falso positivo - comportamento normal do sistema."
        }
        
        Response:
        {
            "status": "falso_positivo",
            "resolvido_por": "admin@example.com",
            "resolvido_em": "2024-01-15T10:30:00Z"
        }
        """
        from django.utils import timezone
        
        violacao = self.get_object()
        violacao.status = 'falso_positivo'
        violacao.resolvido_por = request.user
        violacao.resolvido_em = timezone.now()
        violacao.notas = request.data.get('notas', '')
        violacao.save()
        
        logger.info(f"ℹ️  Violação {violacao.id} marcada como falso positivo por {request.user.email}")
        
        return Response({
            'status': 'falso_positivo',
            'resolvido_por': request.user.email,
            'resolvido_em': violacao.resolvido_em,
            'notas': violacao.notas
        })
    
    @action(detail=False, methods=['get'])
    def estatisticas(self, request):
        """
        Estatísticas de violações
        
        GET /api/superadmin/violacoes-seguranca/estatisticas/
        
        Response:
        {
            "total": 150,
            "nao_resolvidas": 25,
            "por_status": [
                {"status": "nova", "count": 10},
                {"status": "investigando", "count": 15},
                {"status": "resolvida", "count": 120},
                {"status": "falso_positivo", "count": 5}
            ],
            "por_criticidade": [
                {"criticidade": "critica", "count": 5},
                {"criticidade": "alta", "count": 20},
                {"criticidade": "media", "count": 50},
                {"criticidade": "baixa", "count": 75}
            ],
            "por_tipo": [
                {"tipo": "brute_force", "count": 30},
                {"tipo": "rate_limit_exceeded", "count": 40},
                ...
            ],
            "ultimas_24h": 12
        }
        """
        from .models import ViolacaoSeguranca
        from django.db.models import Count
        from datetime import timedelta
        from django.utils import timezone
        
        queryset = self.filter_queryset(self.get_queryset())
        
        total = queryset.count()
        nao_resolvidas = queryset.filter(status__in=['nova', 'investigando']).count()
        
        por_status = queryset.values('status').annotate(count=Count('id')).order_by('-count')
        por_criticidade = queryset.values('criticidade').annotate(count=Count('id')).order_by('-count')
        por_tipo = queryset.values('tipo').annotate(count=Count('id')).order_by('-count')
        
        # Violações nas últimas 24h
        cutoff_24h = timezone.now() - timedelta(hours=24)
        ultimas_24h = queryset.filter(created_at__gte=cutoff_24h).count()
        
        return Response({
            'total': total,
            'nao_resolvidas': nao_resolvidas,
            'por_status': list(por_status),
            'por_criticidade': list(por_criticidade),
            'por_tipo': list(por_tipo),
            'ultimas_24h': ultimas_24h
        })


class EstatisticasAuditoriaViewSet(viewsets.ViewSet):
    """
    ViewSet para estatísticas de auditoria
    
    Endpoints:
    - GET /api/superadmin/estatisticas-auditoria/acoes_por_dia/ - Gráfico de ações por dia
    - GET /api/superadmin/estatisticas-auditoria/acoes_por_tipo/ - Distribuição por tipo
    - GET /api/superadmin/estatisticas-auditoria/lojas_mais_ativas/ - Ranking de lojas
    - GET /api/superadmin/estatisticas-auditoria/usuarios_mais_ativos/ - Ranking de usuários
    - GET /api/superadmin/estatisticas-auditoria/horarios_pico/ - Distribuição por hora
    - GET /api/superadmin/estatisticas-auditoria/taxa_sucesso/ - Taxa de sucesso vs falha
    
    Boas práticas:
    - ViewSet sem modelo (apenas actions)
    - Queries otimizadas com agregações
    - Cache de resultados (TODO: implementar Redis)
    - Filtros de período
    """
    permission_classes = [IsSuperAdmin]
    
    @action(detail=False, methods=['get'])
    @cached_stat(ttl=300, key_prefix='acoes_por_dia')
    def acoes_por_dia(self, request):
        """
        Gráfico de ações por dia (últimos N dias ou data_inicio/data_fim)
        
        GET /api/superadmin/estatisticas-auditoria/acoes_por_dia/?data_inicio=2024-01-01&data_fim=2024-01-31
        
        Response: { "acoes": [ {"periodo": "2024-01-15", "total": 150, "sucessos": 140, "erros": 10}, ... ] }
        """
        from .models import HistoricoAcessoGlobal
        from django.db.models.functions import TruncDate
        from django.db.models import Count, Q
        from datetime import timedelta
        from django.utils import timezone
        
        data_inicio_param = request.query_params.get('data_inicio')
        data_fim_param = request.query_params.get('data_fim')
        if data_inicio_param and data_fim_param:
            try:
                from datetime import datetime
                data_inicio = timezone.make_aware(datetime.strptime(data_inicio_param, '%Y-%m-%d'))
                data_fim = timezone.make_aware(datetime.strptime(data_fim_param + ' 23:59:59', '%Y-%m-%d %H:%M:%S'))
            except (ValueError, TypeError):
                dias = 30
                data_inicio = timezone.now() - timedelta(days=dias)
                data_fim = timezone.now()
        else:
            dias = int(request.query_params.get('dias', 30))
            data_inicio = timezone.now() - timedelta(days=dias)
            data_fim = timezone.now()
        
        qs = HistoricoAcessoGlobal.objects.filter(
            created_at__gte=data_inicio,
            created_at__lte=data_fim
        )
        acoes = qs.annotate(
            dia=TruncDate('created_at')
        ).values('dia').annotate(
            total=Count('id'),
            sucessos=Count('id', filter=Q(sucesso=True)),
            erros=Count('id', filter=Q(sucesso=False))
        ).order_by('dia')
        
        resultado = [
            {
                'periodo': item['dia'].strftime('%Y-%m-%d'),
                'total': item['total'],
                'sucessos': item['sucessos'],
                'erros': item['erros']
            }
            for item in acoes
        ]
        return Response({'acoes': resultado})
    
    @action(detail=False, methods=['get'])
    @cached_stat(ttl=300, key_prefix='acoes_por_tipo')
    def acoes_por_tipo(self, request):
        """
        Distribuição de ações por tipo
        
        GET /api/superadmin/estatisticas-auditoria/acoes_por_tipo/
        
        Response:
        [
            {"acao": "criar", "count": 500},
            {"acao": "editar", "count": 300},
            {"acao": "excluir", "count": 100},
            ...
        ]
        """
        from .models import HistoricoAcessoGlobal
        from django.db.models import Count
        
        acoes = HistoricoAcessoGlobal.objects.values('acao').annotate(
            total=Count('id')
        ).order_by('-total')
        
        return Response({'acoes': list(acoes)})
    
    @action(detail=False, methods=['get'])
    @cached_stat(ttl=300, key_prefix='lojas_mais_ativas')
    def lojas_mais_ativas(self, request):
        """
        Ranking de lojas mais ativas
        
        GET /api/superadmin/estatisticas-auditoria/lojas_mais_ativas/?limit=10
        
        Query params:
        - limit: Número de lojas (padrão: 10)
        
        Response:
        [
            {"loja_id": 1, "loja_nome": "Loja A", "count": 1000},
            {"loja_id": 2, "loja_nome": "Loja B", "count": 800},
            ...
        ]
        """
        from .models import HistoricoAcessoGlobal
        from django.db.models import Count
        
        limit = int(request.query_params.get('limit', 10))
        
        lojas = HistoricoAcessoGlobal.objects.exclude(
            loja__isnull=True
        ).values('loja_id', 'loja_nome').annotate(
            total=Count('id')
        ).order_by('-total')[:limit]
        
        return Response({
            'lojas': [{'loja_nome': item['loja_nome'], 'total': item['total']} for item in lojas]
        })
    
    @action(detail=False, methods=['get'])
    @cached_stat(ttl=300, key_prefix='usuarios_mais_ativos')
    def usuarios_mais_ativos(self, request):
        """
        Ranking de usuários mais ativos
        
        GET /api/superadmin/estatisticas-auditoria/usuarios_mais_ativos/?limit=10
        
        Query params:
        - limit: Número de usuários (padrão: 10)
        
        Response:
        [
            {"usuario_email": "user@example.com", "usuario_nome": "João Silva", "count": 500},
            ...
        ]
        """
        from .models import HistoricoAcessoGlobal
        from django.db.models import Count
        
        limit = int(request.query_params.get('limit', 10))
        
        usuarios = HistoricoAcessoGlobal.objects.values(
            'usuario_email', 'usuario_nome'
        ).annotate(
            total=Count('id')
        ).order_by('-total')[:limit]
        
        return Response({
            'usuarios': [{'usuario_nome': item['usuario_nome'], 'total': item['total']} for item in usuarios]
        })
    
    @action(detail=False, methods=['get'])
    @cached_stat(ttl=300, key_prefix='horarios_pico')
    def horarios_pico(self, request):
        """
        Distribuição de ações por hora do dia
        
        GET /api/superadmin/estatisticas-auditoria/horarios_pico/
        
        Response:
        [
            {"hora": 0, "count": 50},
            {"hora": 1, "count": 30},
            ...
            {"hora": 23, "count": 100}
        ]
        """
        from .models import HistoricoAcessoGlobal
        from django.db.models import Count
        from django.db.models.functions import ExtractHour
        
        acoes = HistoricoAcessoGlobal.objects.annotate(
            hora=ExtractHour('created_at')
        ).values('hora').annotate(
            total=Count('id')
        ).order_by('hora')
        
        return Response({
            'horarios': [{'hora': item['hora'], 'total': item['total']} for item in acoes]
        })
    
    @action(detail=False, methods=['get'])
    @cached_stat(ttl=300, key_prefix='taxa_sucesso')
    def taxa_sucesso(self, request):
        """
        Taxa de sucesso vs falha
        
        GET /api/superadmin/estatisticas-auditoria/taxa_sucesso/
        
        Response:
        {
            "total": 10000,
            "sucessos": 9500,
            "falhas": 500,
            "taxa_sucesso": 95.0
        }
        """
        from .models import HistoricoAcessoGlobal
        
        total = HistoricoAcessoGlobal.objects.count()
        sucessos = HistoricoAcessoGlobal.objects.filter(sucesso=True).count()
        falhas = total - sucessos
        
        taxa_sucesso = (sucessos / total * 100) if total > 0 else 0
        
        return Response({
            'total': total,
            'sucessos': sucessos,
            'falhas': falhas,
            'erros': falhas,  # frontend usa "erros"
            'taxa_sucesso': round(taxa_sucesso, 2)
        })


# ✅ NOVO v738: Endpoint para verificação de storage
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verificar_storage_loja(request, loja_id):
    """
    Verifica storage de uma loja específica (manual).
    
    Endpoint: POST /api/superadmin/lojas/{loja_id}/verificar-storage/
    
    Apenas superadmin pode executar.
    """
    if not request.user.is_superuser:
        return Response(
            {'error': 'Apenas superadmin pode verificar storage'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        loja = Loja.objects.get(id=loja_id)
        
        # Executar comando de verificação para esta loja específica
        from django.core.management import call_command
        from io import StringIO
        
        out = StringIO()
        call_command('verificar_storage_lojas', loja_id=loja_id, stdout=out)
        
        # Recarregar dados atualizados
        loja.refresh_from_db()
        
        return Response({
            'success': True,
            'loja': {
                'id': loja.id,
                'nome': loja.nome,
                'slug': loja.slug,
            },
            'storage': {
                'usado_mb': float(loja.storage_usado_mb),
                'limite_mb': loja.storage_limite_mb,
                'percentual': loja.get_storage_percentual(),
                'is_critical': loja.is_storage_critical(),
                'is_full': loja.is_storage_full(),
            },
            'alerta_enviado': loja.storage_alerta_enviado,
            'ultima_verificacao': loja.storage_ultima_verificacao.isoformat() if loja.storage_ultima_verificacao else None,
            'output': out.getvalue()
        })
    
    except Loja.DoesNotExist:
        return Response(
            {'error': 'Loja não encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f'Erro ao verificar storage da loja {loja_id}: {e}', exc_info=True)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def listar_storage_lojas(request):
    """
    Lista uso de storage de todas as lojas.
    
    ✅ ATUALIZADO v743: Retorna dados formatados para dashboard de monitoramento
    
    Endpoint: GET /api/superadmin/storage/
    
    Apenas superadmin pode acessar.
    """
    try:
        from django.utils import timezone
        
        lojas = Loja.objects.all().select_related('plano', 'owner')
        
        dados = []
        for loja in lojas:
            # Calcular horas desde última verificação
            horas_desde_verificacao = None
            if loja.storage_ultima_verificacao:
                tempo_desde = timezone.now() - loja.storage_ultima_verificacao
                horas_desde_verificacao = int(tempo_desde.total_seconds() / 3600)
            
            # Determinar status
            percentual = loja.get_storage_percentual()
            if percentual >= 100:
                storage_status = 'critical'
                storage_status_texto = 'Storage cheio'
            elif percentual >= 80:
                storage_status = 'warning'
                storage_status_texto = 'Atingindo o limite'
            else:
                storage_status = 'ok'
                storage_status_texto = 'Normal'
            
            dados.append({
                'id': loja.id,
                'nome': loja.nome,
                'slug': loja.slug,
                'storage_usado_mb': float(loja.storage_usado_mb) if loja.storage_usado_mb else 0.0,
                'storage_limite_mb': loja.storage_limite_mb if loja.storage_limite_mb else (loja.plano.espaco_storage_gb * 1024 if loja.plano else 5120),
                'storage_livre_mb': (loja.storage_limite_mb if loja.storage_limite_mb else 5120) - (float(loja.storage_usado_mb) if loja.storage_usado_mb else 0.0),
                'storage_percentual': percentual,
                'storage_status': storage_status,
                'storage_status_texto': storage_status_texto,
                'storage_alerta_enviado': loja.storage_alerta_enviado,
                'storage_ultima_verificacao': loja.storage_ultima_verificacao.isoformat() if loja.storage_ultima_verificacao else None,
                'storage_horas_desde_verificacao': horas_desde_verificacao,
                'plano_nome': loja.plano.nome if loja.plano else 'Sem plano',
                'is_active': loja.is_active,
                'is_blocked': loja.is_blocked,
            })
        
        # Ordenar por percentual (maior primeiro)
        dados.sort(key=lambda x: x['storage_percentual'], reverse=True)
        
        return Response({
            'lojas': dados,
            'total': len(dados),
        })
    
    except Exception as e:
        logger.error(f'Erro ao listar storage das lojas: {e}', exc_info=True)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ===== HEALTH CHECK ENDPOINT (v750) =====

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint para load balancer e failover automático.
    Verifica conexão com banco de dados e retorna status do sistema.
    
    Retorna:
    - 200 OK: Sistema saudável
    - 503 Service Unavailable: Sistema com problemas
    """
    try:
        # Verificar conexão com banco de dados
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        
        # Verificar se consegue acessar modelo básico
        from .models import Loja
        loja_count = Loja.objects.count()
        
        return Response({
            'status': 'healthy',
            'database': 'connected',
            'lojas_count': loja_count,
            'timestamp': timezone.now().isoformat(),
            'version': 'v750'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f'Health check falhou: {e}', exc_info=True)
        return Response({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
