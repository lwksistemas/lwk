from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.core.management import call_command
from django.conf import settings
from django.db import transaction, connection
from pathlib import Path
import logging

logger = logging.getLogger(__name__)
from .models import (
    TipoLoja, PlanoAssinatura, Loja, FinanceiroLoja,
    PagamentoLoja, UsuarioSistema
)
from .serializers import (
    TipoLojaSerializer, PlanoAssinaturaSerializer, LojaSerializer,
    FinanceiroLojaSerializer, PagamentoLojaSerializer, UsuarioSistemaSerializer,
    LojaCreateSerializer
)

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
        if hasattr(obj, 'owner'):
            return request.user == obj.owner
        
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
    def info_publica(self, request):
        """Retorna informações públicas da loja para página de login (sem autenticação). Otimizado e defensivo."""
        slug = request.query_params.get('slug')
        if not slug:
            return Response({'error': 'slug é obrigatório'}, status=400)
        slug = slug.strip()
        try:
            loja = Loja.objects.select_related('tipo_loja').filter(slug__iexact=slug, is_active=True).first()
            if not loja:
                return Response({'error': 'Loja não encontrada'}, status=404)
            tipo = getattr(loja, 'tipo_loja', None)
            tipo_nome = tipo.nome if tipo else 'Loja'
            return Response({
                'id': loja.id,
                'nome': getattr(loja, 'nome', '') or '',
                'slug': getattr(loja, 'slug', '') or slug,
                'tipo_loja_nome': tipo_nome,
                'cor_primaria': getattr(loja, 'cor_primaria', None) or '#10B981',
                'cor_secundaria': getattr(loja, 'cor_secundaria', None) or '#059669',
                'logo': getattr(loja, 'logo', None) or '',
                'login_page_url': getattr(loja, 'login_page_url', None) or '',
                'senha_foi_alterada': getattr(loja, 'senha_foi_alterada', False),
            })
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
        """Permite ao proprietário alterar a senha no primeiro acesso (apenas proprietário ou superadmin)"""
        # Verificar se está autenticado
        if not request.user or not request.user.is_authenticated:
            return Response(
                {'error': 'Autenticação necessária'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        loja = self.get_object()
        
        # Verificar se o usuário é o proprietário
        if request.user != loja.owner:
            return Response(
                {'error': 'Apenas o proprietário pode alterar a senha'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Verificar se já alterou a senha
        if loja.senha_foi_alterada:
            return Response(
                {'error': 'A senha já foi alterada anteriormente'},
                status=status.HTTP_400_BAD_REQUEST
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
        
        # Alterar senha do usuário
        user = loja.owner
        user.set_password(nova_senha)
        user.save()
        
        # Marcar que a senha foi alterada
        loja.senha_foi_alterada = True
        loja.save()
        
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
        banco_removido = False
        asaas_deleted_payments = 0
        asaas_deleted_customer = False
        asaas_local_payments_removed = 0
        asaas_local_customers_removed = 0
        asaas_local_subscriptions_removed = 0
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
        
        # 2. Remover banco de dados físico se existir
        if database_created:
            try:
                db_path = settings.BASE_DIR / f'db_{database_name}.sqlite3'
                if database_name in settings.DATABASES:
                    del settings.DATABASES[database_name]
                    print(f"✅ Configuração do banco removida: {database_name}")
                if db_path.exists():
                    import os
                    os.remove(db_path)
                    banco_removido = True
                    print(f"✅ Arquivo do banco removido: {db_path}")
            except Exception as e:
                print(f"⚠️ Erro ao remover banco: {e}")
        
        # 3. Remover dados do Asaas (operação independente)
        try:
            from asaas_integration.deletion_service import AsaasDeletionService
            from asaas_integration.models import AsaasPayment, AsaasCustomer, LojaAssinatura
            
            deletion_service = AsaasDeletionService()
            if deletion_service.available:
                result = deletion_service.delete_loja_from_asaas(loja_slug)
                if result.get('success'):
                    asaas_deleted_payments = result.get('deleted_payments', 0)
                    asaas_deleted_customer = result.get('deleted_customer', False)
                    print(f"✅ Dados Asaas API removidos")
            
            # Remover dados locais do Asaas
            with transaction.atomic():
                try:
                    assinatura = LojaAssinatura.objects.get(loja_slug=loja_slug)
                    customer = assinatura.asaas_customer
                    payments = AsaasPayment.objects.filter(customer=customer)
                    asaas_local_payments_removed = payments.count()
                    payments.delete()
                    assinatura.delete()
                    asaas_local_subscriptions_removed = 1
                    customer.delete()
                    asaas_local_customers_removed = 1
                    print(f"✅ Dados Asaas locais removidos")
                except LojaAssinatura.DoesNotExist:
                    print(f"ℹ️ Nenhuma assinatura Asaas encontrada")
        except Exception as e:
            print(f"⚠️ Erro ao remover dados Asaas: {e}")
        
        # 4. Remover a loja (operação principal)
        try:
            with transaction.atomic():
                loja.delete()
                print(f"✅ Loja removida: {loja_nome}")
        except Exception as e:
            print(f"❌ Erro ao remover loja: {e}")
            return Response(
                {'error': f'Erro ao remover loja: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
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
        """Retorna informações da loja para o superadmin: tamanho do banco, espaço livre, senha, página de login."""
        import os
        loja = self.get_object()
        tamanho_banco_mb = None
        tamanho_banco_motivo = None
        if not loja.database_created or not loja.database_name:
            tamanho_banco_motivo = 'Banco isolado não criado para esta loja (dados no banco principal).'
        else:
            db_path = settings.BASE_DIR / f'db_{loja.database_name}.sqlite3'
            if db_path.exists():
                try:
                    tamanho_banco_mb = round(os.path.getsize(db_path) / (1024 * 1024), 2)
                except OSError:
                    tamanho_banco_motivo = 'Não foi possível ler o tamanho do arquivo.'
            else:
                tamanho_banco_motivo = 'Tamanho exato indisponível (disco efêmero no servidor).'
        # Quando não há tamanho real, usar estimativa padrão (512 MB) para exibição e cálculo de espaço livre
        tamanho_banco_estimativa_mb = self.TAMANHO_BANCO_ESTIMATIVA_MB
        espaco_plano_gb = loja.plano.espaco_storage_gb if loja.plano else None
        espaco_livre_gb = None
        if espaco_plano_gb is not None:
            uso_mb = tamanho_banco_mb if tamanho_banco_mb is not None else tamanho_banco_estimativa_mb
            espaco_livre_gb = round(espaco_plano_gb - (uso_mb / 1024), 2)
        return Response({
            'id': loja.id,
            'nome': loja.nome,
            'slug': loja.slug,
            'tamanho_banco_mb': tamanho_banco_mb,
            'tamanho_banco_estimativa_mb': tamanho_banco_estimativa_mb,
            'tamanho_banco_motivo': tamanho_banco_motivo,
            'database_created': loja.database_created,
            'espaco_plano_gb': espaco_plano_gb,
            'espaco_livre_gb': espaco_livre_gb,
            'senha_provisoria': loja.senha_provisoria or '',
            'login_page_url': loja.login_page_url or '',
            'owner_username': loja.owner.username,
            'owner_email': loja.owner.email,
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
        """Exclusão completa do usuário (UsuarioSistema + User do Django)"""
        usuario_sistema = self.get_object()
        user_django = usuario_sistema.user
        username = user_django.username
        
        try:
            with transaction.atomic():
                # 1. Excluir UsuarioSistema
                usuario_sistema.delete()
                logger.info(f"✅ UsuarioSistema excluído: {username}")
                
                # 2. Excluir User do Django
                user_django.delete()
                logger.info(f"✅ User Django excluído: {username}")
            
            return Response({
                'message': f'Usuário "{username}" foi completamente removido do sistema',
                'username': username
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"❌ Erro ao excluir usuário {username}: {e}")
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
