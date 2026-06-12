from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from django.core.management import call_command
from django.conf import settings
from django.db import transaction
from django.utils import timezone
import logging

from drf_spectacular.utils import extend_schema_view, extend_schema
from core.logging_utils import mask_email
from ...api_docs import (
    TIPO_LOJA_LIST_SCHEMA,
    TIPO_LOJA_CREATE_SCHEMA,
    PLANO_LIST_SCHEMA,
    LOJA_LIST_SCHEMA,
    LOJA_CREATE_SCHEMA,
    LOJA_DELETE_SCHEMA,
)
from ...models import (
    TipoLoja, PlanoAssinatura, Loja, FinanceiroLoja, ProfissionalUsuario,
)
from ...serializers import (
    TipoLojaSerializer, PlanoAssinaturaSerializer, LojaSerializer, LojaCreateSerializer,
)
from ..permissions import IsOwnerOrSuperAdmin, IsSuperAdmin

logger = logging.getLogger(__name__)

from .backup_mixin import LojaBackupMixin

class LojaViewSet(LojaBackupMixin, viewsets.ModelViewSet):
    permission_classes = [IsSuperAdmin]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return LojaCreateSerializer
        return LojaSerializer
    
    def get_permissions(self):
        if self.action in ['info_publica', 'debug_auth', 'create', 'buscar_por_documento', 'por_atalho']:
            return []
        if self.action == 'heartbeat':
            return [permissions.IsAuthenticated()]
        return super().get_permissions()

    def get_throttles(self):
        from core.throttling import PublicLojaCreateThrottle, PublicLojaLookupThrottle

        if self.action == 'create':
            return [PublicLojaCreateThrottle()]
        if self.action == 'buscar_por_documento':
            return [PublicLojaLookupThrottle()]
        return super().get_throttles()
    
    def get_queryset(self):
        queryset = Loja.objects.select_related(
            'tipo_loja', 'plano', 'owner', 'financeiro'
        ).prefetch_related('pagamentos', 'usuarios_suporte')
        
        slug = self.request.query_params.get('slug')
        if slug:
            queryset = queryset.filter(slug=slug)
        
        return queryset
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny], authentication_classes=[])
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
        
        cache_key = f'loja_info_publica:{slug}'
        cached_data = cache.get(cache_key)
        if cached_data:
            logger.debug(f'✅ Cache HIT para loja {slug}')
            return Response(cached_data)
        
        from django.db import OperationalError
        import time
        
        max_retries = 3
        retry_delay = 1
        loja = None
        
        for attempt in range(max_retries):
            try:
                loja = Loja.objects.select_related('tipo_loja', 'owner').filter(slug__iexact=slug, is_active=True).first()
                if not loja:
                    loja = Loja.objects.select_related('tipo_loja', 'owner').filter(atalho__iexact=slug, is_active=True).first()
                break
                
            except OperationalError as e:
                if 'timeout' in str(e).lower() and attempt < max_retries - 1:
                    logger.warning(
                        f"⚠️ Timeout ao buscar loja {slug} (tentativa {attempt + 1}/{max_retries}). "
                        f"Tentando novamente em {retry_delay}s..."
                    )
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    logger.error(f"❌ Falha ao buscar loja {slug} após {max_retries} tentativas: {e}")
                    return Response(
                        {'error': 'Erro ao conectar ao banco de dados. Tente novamente.'},
                        status=503
                    )
        
        try:
            if not loja:
                return Response({'error': 'Loja não encontrada'}, status=404)
            tipo = getattr(loja, 'tipo_loja', None)
            tipo_nome = tipo.nome if tipo else 'Loja'

            cidade = getattr(loja, 'cidade', '') or ''
            uf = getattr(loja, 'uf', '') or ''
            cidade_uf = f"{cidade}/{uf}" if (cidade and uf) else (cidade or uf)
            endereco_parts = [
                getattr(loja, 'logradouro', '') or '',
                getattr(loja, 'numero', '') or '',
                getattr(loja, 'complemento', '') or '',
                getattr(loja, 'bairro', '') or '',
                cidade_uf,
                f"CEP {loja.cep}" if getattr(loja, 'cep', '') else '',
            ]
            endereco = ', '.join(p for p in endereco_parts if p).strip() or None

            data = {
                'id': loja.id,
                'nome': getattr(loja, 'nome', '') or '',
                'slug': getattr(loja, 'slug', '') or slug,
                'atalho': getattr(loja, 'atalho', '') or '',
                'tipo_loja_nome': tipo_nome,
                'cor_primaria': getattr(loja, 'cor_primaria', None) or '#10B981',
                'cor_secundaria': getattr(loja, 'cor_secundaria', None) or '#059669',
                'logo': getattr(loja, 'logo', None) or '',
                'login_background': getattr(loja, 'login_background', None) or '',
                'login_logo': getattr(loja, 'login_logo', None) or '',
                'login_page_url': getattr(loja, 'login_page_url', None) or '',
                'senha_foi_alterada': getattr(loja, 'senha_foi_alterada', False),
                'requer_cpf_cnpj': True,
                'endereco': endereco,
            }
            
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
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny], authentication_classes=[], url_path='buscar-por-documento')
    def buscar_por_documento(self, request):
        """
        Busca loja por CPF ou CNPJ (acesso público para facilitar login dos clientes).
        Retorna apenas slug e nome da loja para redirecionar para página de login.
        """
        documento = request.query_params.get('documento', '').strip()
        
        if not documento:
            return Response({'error': 'Documento (CPF ou CNPJ) é obrigatório'}, status=400)
        
        documento_limpo = ''.join(filter(str.isdigit, documento))
        
        if len(documento_limpo) not in [11, 14]:
            return Response({
                'error': 'Documento inválido. Digite um CPF (11 dígitos) ou CNPJ (14 dígitos)'
            }, status=400)
        
        try:
            logger.info(f"[buscar_por_documento] Buscando loja com documento: {documento_limpo}")
            
            from django.db.models import Q
            loja = Loja.objects.filter(
                Q(cpf_cnpj=documento_limpo) | Q(slug=documento_limpo),
                is_active=True
            ).first()
            
            if not loja:
                logger.warning(f"[buscar_por_documento] Nenhuma loja encontrada com documento: {documento_limpo}")
                return Response({
                    'error': 'Nenhuma loja encontrada com este CPF/CNPJ'
                }, status=404)
            
            logger.info(f"[buscar_por_documento] Loja encontrada: {loja.nome} (slug: {loja.slug})")
            
            return Response({
                'slug': loja.slug,
                'nome': loja.nome,
                'logo': loja.logo or None,
            })
            
        except Exception as e:
            logger.exception('buscar_por_documento erro para documento=%s: %s', documento_limpo, e)
            return Response({
                'error': 'Erro ao buscar loja. Tente novamente.'
            }, status=500)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny], authentication_classes=[], url_path='por-atalho')
    def por_atalho(self, request):
        """
        Busca loja por atalho (acesso público).
        Retorna slug e nome da loja para renderizar página de login mantendo URL amigável.
        """
        atalho = request.query_params.get('atalho', '').strip()
        
        if not atalho:
            return Response({'error': 'atalho é obrigatório'}, status=400)
        
        try:
            logger.info(f"[por_atalho] Buscando loja com atalho: {atalho}")
            
            loja = Loja.objects.filter(atalho=atalho, is_active=True).first()
            
            if not loja:
                logger.warning(f"[por_atalho] Nenhuma loja encontrada com atalho: {atalho}")
                return Response({
                    'error': 'Nenhuma loja encontrada com este atalho'
                }, status=404)
            
            logger.info(f"[por_atalho] Loja encontrada: {loja.nome} (slug: {loja.slug}, atalho: {loja.atalho})")
            
            return Response({
                'slug': loja.slug,
                'atalho': loja.atalho,
                'nome': loja.nome,
                'logo': loja.logo or None,
            })
            
        except Exception as e:
            logger.exception('por_atalho erro para atalho=%s: %s', atalho, e)
            return Response({
                'error': 'Erro ao buscar loja. Tente novamente.'
            }, status=500)
    
    @action(detail=False, methods=['get'])
    def heartbeat(self, request):
        """
        Mantém a sessão ativa. Se outro dispositivo fez login,
        o session_id no banco será diferente → retorna 401.
        """
        from ...session_manager import SessionManager
        from ...models import UserSession
        
        if not request.user or not request.user.is_authenticated:
            return Response({
                'error': 'Não autenticado',
                'code': 'NOT_AUTHENTICATED'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Verificar sessão única via session_id (query param OU header)
        client_sid = request.query_params.get('sid', '') or request.headers.get('X-Session-ID', '')
        if client_sid:
            try:
                db_session = UserSession.objects.filter(user_id=request.user.id).first()
                if db_session and db_session.session_id != client_sid:
                    return Response({
                        'error': 'Sessão encerrada — login realizado em outro dispositivo. Faça login novamente.',
                        'code': 'SESSION_REPLACED'
                    }, status=status.HTTP_401_UNAUTHORIZED)
            except Exception:
                pass
        
        SessionManager.update_activity(request.user.id)
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
        if not settings.DEBUG:
            return Response(
                {'error': 'Endpoint disponível apenas em modo DEBUG'},
                status=status.HTTP_403_FORBIDDEN
            )

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
        """Verifica se o usuário logado precisa trocar a senha provisória"""
        if not request.user or not request.user.is_authenticated:
            return Response({
                'precisa_trocar_senha': False,
                'mensagem': 'Usuário não autenticado'
            })
        
        try:
            slug = (request.query_params.get('slug') or '').strip()
            if slug:
                from ...loja_utils import resolve_loja_by_slug_or_atalho
                loja = resolve_loja_by_slug_or_atalho(slug, is_active=True)
                if not loja or loja.owner_id != request.user.id:
                    raise Loja.DoesNotExist
            else:
                loja = Loja.objects.get(owner=request.user)
            precisa_trocar = not loja.senha_foi_alterada and bool(loja.senha_provisoria)
            logger.debug(
                "Verificar senha provisória: loja=%s, senha_foi_alterada=%s, precisa_trocar=%s",
                loja.slug,
                loja.senha_foi_alterada,
                precisa_trocar,
            )
            
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
        if not settings.DEBUG:
            return Response(
                {'error': 'Endpoint disponível apenas em modo DEBUG'},
                status=status.HTTP_403_FORBIDDEN
            )

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
        from core.password_validation import validate_password_policy
        ok, msg = validate_password_policy(nova_senha)
        if not ok:
            return Response({'error': msg}, status=status.HTTP_400_BAD_REQUEST)

        loja = self.get_object()
        user = request.user

        # Caso 1: proprietário da loja
        if user == loja.owner:
            from superadmin.models import VendedorUsuario
            if loja.senha_foi_alterada:
                # Sincronizar flags órfãs (owner trocou senha mas vínculo CRM ficou pendente)
                ProfissionalUsuario.objects.filter(user=user, loja=loja).update(
                    precisa_trocar_senha=False
                )
                VendedorUsuario.objects.filter(user=user, loja=loja).update(
                    precisa_trocar_senha=False
                )
                return Response({
                    'message': 'Senha já foi alterada anteriormente',
                    'ja_alterada': True,
                    'loja': loja.nome,
                })
            user.set_password(nova_senha)
            user.save()
            loja.senha_foi_alterada = True
            loja.senha_provisoria = ''
            loja.save(update_fields=['senha_foi_alterada', 'senha_provisoria'])
            ProfissionalUsuario.objects.filter(user=user, loja=loja).update(
                precisa_trocar_senha=False
            )
            VendedorUsuario.objects.filter(user=user, loja=loja).update(
                precisa_trocar_senha=False
            )
            return Response({
                'message': 'Senha alterada com sucesso!',
                'loja': loja.nome
            })

        # Caso 2: profissional (ProfissionalUsuario) da Clínica da Beleza
        try:
            pu = ProfissionalUsuario.objects.get(user=user, loja=loja)
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
        except ProfissionalUsuario.DoesNotExist:
            pass

        # Caso 3: vendedor (VendedorUsuario) do CRM Vendas
        from superadmin.models import VendedorUsuario
        try:
            vu = VendedorUsuario.objects.get(user=user, loja=loja)
            if not vu.precisa_trocar_senha:
                return Response(
                    {'error': 'A senha já foi alterada anteriormente'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            user.set_password(nova_senha)
            user.save()
            vu.precisa_trocar_senha = False
            vu.save(update_fields=['precisa_trocar_senha'])
            return Response({
                'message': 'Senha alterada com sucesso!',
                'loja': loja.nome
            })
        except VendedorUsuario.DoesNotExist:
            return Response(
                {'error': 'Apenas o proprietário, um profissional ou vendedor desta loja pode alterar a senha aqui'},
                status=status.HTTP_403_FORBIDDEN
            )

    @action(detail=True, methods=['post'], permission_classes=[IsSuperAdmin])
    def resetar_senha_provisoria(self, request, pk=None):
        """Reseta a senha provisória de uma loja (apenas superadmin)"""
        import secrets
        import string
        from django.core.mail import send_mail
        
        loja = self.get_object()
        
        alphabet = string.ascii_letters + string.digits + "!@#$%&*"
        nova_senha = ''.join(secrets.choice(alphabet) for _ in range(8))
        
        user = loja.owner
        user.set_password(nova_senha)
        user.save()
        
        loja.senha_provisoria = nova_senha
        loja.senha_foi_alterada = False
        loja.save()
        
        logger.info(f"✅ Senha provisória resetada para loja {loja.slug}")
        
        email_enviado = False
        try:
            if hasattr(settings, 'DEFAULT_FROM_EMAIL') and settings.DEFAULT_FROM_EMAIL:
                from ...services.provisional_password_helpers import loja_login_absolute_url

                assunto = f"Nova Senha Provisória - {loja.nome}"
                mensagem = f"""
Olá!

Sua senha foi resetada para a loja "{loja.nome}".

🔐 NOVOS DADOS DE ACESSO:
• URL de Login: {loja_login_absolute_url(loja)}
• Usuário: {user.username}
• Senha Provisória: {nova_senha}

⚠️ IMPORTANTE:
• Esta é uma senha provisória
• Você será solicitado a trocar a senha no primeiro acesso

---
Equipe de Suporte
"""
                from core.email_delivery import send_system_mail
                send_system_mail(assunto, mensagem, [user.email], fail_silently=True)
                email_enviado = True
                logger.info("Email de senha provisória enviado: email=%s, loja=%s", mask_email(user.email), loja.slug)
        except Exception as e:
            logger.warning("Erro ao enviar email de senha provisória: loja=%s, erro=%s", loja.slug, e)
        
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
        from ...services import LojaCleanupService
        
        loja = self.get_object()
        cleanup_service = LojaCleanupService(loja)
        
        try:
            results = cleanup_service.cleanup_all()
            
            with transaction.atomic():
                try:
                    loja.delete()
                except Exception as del_err:
                    err_str = str(del_err)
                    if 'does not exist' in err_str.lower() or 'UndefinedTable' in err_str:
                        logger.warning(f"⚠️ Tabela inexistente durante CASCADE, forçando exclusão: {err_str}")
                        from django.db import connection
                        with connection.cursor() as cur:
                            cur.execute('DELETE FROM superadmin_loja WHERE id = %s', [loja.id])
                    else:
                        raise
                logger.info(f"✅ Loja removida: {results['loja_nome']}")
            
            return Response({
                'message': f'Loja "{results["loja_nome"]}" foi completamente removida do sistema',
                'detalhes': results
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"❌ Erro ao remover loja: {e}")
            transaction.set_rollback(True)
            return Response(
                {'error': f'Erro ao remover loja: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'], permission_classes=[IsOwnerOrSuperAdmin])
    def reenviar_senha(self, request, pk=None):
        """Gera nova senha provisória e envia por email (recuperação de senha)"""
        loja = self.get_object()
        
        if not request.user.is_superuser and request.user != loja.owner:
            return Response(
                {'error': 'Apenas o proprietário pode reenviar a senha'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            import random
            import string
            
            nova_senha_provisoria = ''.join(random.choices(string.ascii_letters + string.digits + '!@#$%', k=10))
            
            user = loja.owner
            user.set_password(nova_senha_provisoria)
            user.save()
            
            loja.senha_provisoria = nova_senha_provisoria
            loja.senha_foi_alterada = False
            loja.save()

            from ...services.provisional_password_helpers import loja_login_absolute_url
            from core.email_templates import email_senha_provisoria_html

            info_adicional = {
                "Nome da Loja": loja.nome,
                "Tipo de Sistema": loja.tipo_loja.nome,
                "Plano Contratado": loja.plano.nome,
                "Tipo de Assinatura": loja.get_tipo_assinatura_display(),
            }
            
            html_content, texto_plano = email_senha_provisoria_html(
                nome_destinatario="Administrador",
                usuario=loja.owner.username,
                senha=nova_senha_provisoria,
                url_login=loja_login_absolute_url(loja),
                titulo_principal="Nova Senha Provisória",
                subtitulo="Sua senha foi redefinida pelo suporte",
                info_adicional=info_adicional,
                nome_sistema=loja.nome
            )

            assunto = f"Nova Senha Provisória - {loja.nome}"
            
            from core.email_delivery import create_email_multipart
            email_msg = create_email_multipart(
                assunto,
                texto_plano,
                [loja.owner.email],
                html=html_content,
            )
            email_msg.send(fail_silently=False)
            
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
            
            call_command('migrate', '--database', db_name, verbosity=0)
            
            from django.contrib.auth.models import User as UserModel
            admin_loja = UserModel.objects.db_manager(db_name).create_user(
                username=loja.owner.username,
                email=loja.owner.email,
                password='senha123',
                is_staff=True
            )
            
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
    
    TAMANHO_BANCO_ESTIMATIVA_MB = 512

    @action(detail=True, methods=['get'])
    def info_loja(self, request, pk=None):
        """Retorna informações da loja para o superadmin: storage, senha, página de login."""
        loja = self.get_object()
        
        storage_usado_mb = float(loja.storage_usado_mb) if loja.storage_usado_mb else 0.0
        storage_limite_mb = loja.storage_limite_mb if loja.storage_limite_mb else (loja.plano.espaco_storage_gb * 1024 if loja.plano else 5120)
        storage_percentual = loja.get_storage_percentual()
        storage_livre_mb = storage_limite_mb - storage_usado_mb
        storage_livre_gb = round(storage_livre_mb / 1024, 2)
        
        ultima_verificacao = loja.storage_ultima_verificacao
        if ultima_verificacao:
            tempo_desde_verificacao = timezone.now() - ultima_verificacao
            horas_desde_verificacao = int(tempo_desde_verificacao.total_seconds() / 3600)
        else:
            horas_desde_verificacao = None
        
        if storage_percentual >= 100:
            storage_status = 'critical'
            storage_status_texto = 'Storage cheio'
        elif storage_percentual >= 80:
            storage_status = 'warning'
            storage_status_texto = 'Atingindo o limite'
        else:
            storage_status = 'ok'
            storage_status_texto = 'Normal'
        
        return Response({
            'id': loja.id,
            'nome': loja.nome,
            'slug': loja.slug,
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
            'espaco_plano_gb': loja.plano.espaco_storage_gb if loja.plano else 5,
            'plano_nome': loja.plano.nome if loja.plano else 'Sem plano',
            'senha_provisoria': loja.senha_provisoria or '',
            'login_page_url': loja.login_page_url or '',
            'owner_username': loja.owner.username,
            'owner_email': loja.owner.email,
            'database_created': loja.database_created,
            'tamanho_banco_mb': storage_usado_mb,
            'tamanho_banco_estimativa_mb': self.TAMANHO_BANCO_ESTIMATIVA_MB,
            'tamanho_banco_motivo': 'Dados reais do monitoramento de storage PostgreSQL',
            'espaco_livre_gb': storage_livre_gb,
        })
    
    @action(detail=False, methods=['get'])
    def estatisticas(self, request):
        """Estatísticas gerais do sistema"""
        from django.db.models import Sum
        
        total_lojas = Loja.objects.count()
        lojas_ativas = Loja.objects.filter(is_active=True).count()
        
        receita_mensal = FinanceiroLoja.objects.filter(
            status_pagamento='ativo'
        ).aggregate(total=Sum('valor_mensalidade'))['total'] or 0
        
        return Response({
            'total_lojas': total_lojas,
            'lojas_ativas': lojas_ativas,
            'lojas_inativas': total_lojas - lojas_ativas,
            'receita_mensal_estimada': float(receita_mensal),
        })
