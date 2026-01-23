"""
Views de Autenticação com Isolamento Total e Validação de Grupo
"""
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.response import Response
from rest_framework import status, serializers
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate
from superadmin.session_manager import SessionManager
from superadmin.models import Loja, UsuarioSistema
import logging

logger = logging.getLogger(__name__)


class SecureTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializer customizado com validação de grupo e loja
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Adicionar campos opcionais
        self.fields['user_type'] = serializers.CharField(required=False, allow_blank=True)
        self.fields['loja_slug'] = serializers.CharField(required=False, allow_blank=True)
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Adicionar informações básicas
        token['username'] = user.username
        token['email'] = user.email
        token['is_superuser'] = user.is_superuser
        
        # Identificar grupo do usuário
        user_type = cls._get_user_type(user)
        token['user_type'] = user_type
        
        # Se for loja, adicionar loja_id e slug
        if user_type == 'loja':
            try:
                loja = Loja.objects.filter(owner=user, is_active=True).first()
                if loja:
                    token['loja_id'] = loja.id
                    token['loja_slug'] = loja.slug
            except Exception as e:
                logger.error(f"Erro ao buscar loja do usuário {user.username}: {e}")
        
        return token
    
    @staticmethod
    def _get_user_type(user):
        """Identifica o tipo de usuário"""
        if user.is_superuser:
            return 'superadmin'
        
        # Verificar se é usuário de sistema (suporte)
        try:
            usuario_sistema = UsuarioSistema.objects.filter(user=user, is_active=True).first()
            if usuario_sistema:
                return usuario_sistema.tipo  # 'suporte' ou 'superadmin'
        except:
            pass
        
        # Verificar se é proprietário de loja
        try:
            if Loja.objects.filter(owner=user, is_active=True).exists():
                return 'loja'
        except:
            pass
        
        return 'unknown'
    
    def validate(self, attrs):
        """Validação customizada com verificação de grupo"""
        # Autenticar usuário
        data = super().validate(attrs)
        
        user = self.user
        user_type = self._get_user_type(user)
        
        # Adicionar informações do usuário na resposta
        data['user_type'] = user_type
        data['user'] = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_superuser': user.is_superuser,
            'user_type': user_type
        }
        
        # Se for loja, adicionar informações da loja
        if user_type == 'loja':
            try:
                loja = Loja.objects.filter(owner=user, is_active=True).first()
                if loja:
                    data['loja'] = {
                        'id': loja.id,
                        'slug': loja.slug,
                        'nome': loja.nome,
                        'tipo_loja': loja.tipo_loja.nome if loja.tipo_loja else None
                    }
                else:
                    raise serializers.ValidationError({
                        'detail': 'Usuário não possui loja ativa',
                        'code': 'NO_ACTIVE_STORE'
                    })
            except Loja.DoesNotExist:
                raise serializers.ValidationError({
                    'detail': 'Usuário não possui loja ativa',
                    'code': 'NO_ACTIVE_STORE'
                })
        
        return data


class SecureLoginView(APIView):
    """
    View de login segura com validação de grupo e endpoint
    
    REGRAS:
    - /api/auth/superadmin/login/ - Apenas superadmin
    - /api/auth/suporte/login/ - Apenas suporte
    - /api/auth/loja/login/ - Apenas proprietários de loja
    """
    permission_classes = [AllowAny]
    
    def post(self, request, user_type=None):
        username = request.data.get('username')
        password = request.data.get('password')
        loja_slug = request.data.get('loja_slug')  # Apenas para lojas
        
        if not username or not password:
            return Response({
                'error': 'Username e password são obrigatórios',
                'code': 'MISSING_CREDENTIALS'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Autenticar usuário
        user = authenticate(username=username, password=password)
        
        if not user:
            logger.warning(f"❌ Tentativa de login falhou: {username}")
            return Response({
                'error': 'Credenciais inválidas',
                'code': 'INVALID_CREDENTIALS'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Identificar tipo real do usuário
        real_user_type = self._get_user_type(user)
        
        # VALIDAÇÃO CRÍTICA: Verificar se o tipo de usuário corresponde ao endpoint
        if user_type and real_user_type != user_type:
            logger.critical(
                f"🚨 VIOLAÇÃO DE SEGURANÇA: Usuário {username} (tipo: {real_user_type}) "
                f"tentou fazer login no endpoint de {user_type}"
            )
            return Response({
                'error': f'Este usuário não pode fazer login aqui',
                'code': 'WRONG_LOGIN_ENDPOINT',
                'seu_tipo': real_user_type,
                'endpoint_correto': self._get_correct_endpoint(real_user_type),
                'mensagem': f'Use o endpoint correto para seu tipo de usuário'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Se for loja, validar slug
        if real_user_type == 'loja':
            try:
                loja = Loja.objects.filter(owner=user, is_active=True).first()
                if not loja:
                    return Response({
                        'error': 'Usuário não possui loja ativa',
                        'code': 'NO_ACTIVE_STORE'
                    }, status=status.HTTP_403_FORBIDDEN)
                
                # Se slug foi fornecido, validar
                if loja_slug and loja.slug != loja_slug:
                    logger.critical(
                        f"🚨 VIOLAÇÃO: Usuário {username} (loja: {loja.slug}) "
                        f"tentou fazer login na loja: {loja_slug}"
                    )
                    return Response({
                        'error': 'Você não pode fazer login nesta loja',
                        'code': 'WRONG_STORE',
                        'sua_loja': loja.slug,
                        'loja_solicitada': loja_slug
                    }, status=status.HTTP_403_FORBIDDEN)
                
            except Exception as e:
                logger.error(f"Erro ao validar loja: {e}")
                return Response({
                    'error': 'Erro ao validar loja',
                    'code': 'STORE_VALIDATION_ERROR'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Gerar tokens
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        access = str(refresh.access_token)
        
        # Adicionar claims customizados
        refresh['user_type'] = real_user_type
        refresh['username'] = user.username
        refresh['email'] = user.email
        
        if real_user_type == 'loja':
            loja = Loja.objects.filter(owner=user, is_active=True).first()
            if loja:
                refresh['loja_id'] = loja.id
                refresh['loja_slug'] = loja.slug
        
        # Criar sessão única
        session_id = SessionManager.create_session(user.id, access)
        
        # Preparar resposta
        response_data = {
            'access': access,
            'refresh': str(refresh),
            'session_id': session_id,
            'session_timeout_minutes': SessionManager.SESSION_TIMEOUT_MINUTES,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_superuser': user.is_superuser,
                'user_type': real_user_type
            }
        }
        
        # Se for loja, adicionar informações da loja
        if real_user_type == 'loja':
            loja = Loja.objects.filter(owner=user, is_active=True).first()
            if loja:
                response_data['loja'] = {
                    'id': loja.id,
                    'slug': loja.slug,
                    'nome': loja.nome,
                    'tipo_loja': loja.tipo_loja.nome if loja.tipo_loja else None
                }
        
        logger.info(f"✅ Login bem-sucedido: {username} (tipo: {real_user_type})")
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    def _get_user_type(self, user):
        """Identifica o tipo de usuário"""
        if user.is_superuser:
            return 'superadmin'
        
        try:
            usuario_sistema = UsuarioSistema.objects.filter(user=user, is_active=True).first()
            if usuario_sistema:
                return usuario_sistema.tipo
        except:
            pass
        
        try:
            if Loja.objects.filter(owner=user, is_active=True).exists():
                return 'loja'
        except:
            pass
        
        return 'unknown'
    
    def _get_correct_endpoint(self, user_type):
        """Retorna o endpoint correto para o tipo de usuário"""
        endpoints = {
            'superadmin': '/api/auth/superadmin/login/',
            'suporte': '/api/auth/suporte/login/',
            'loja': '/api/auth/loja/login/'
        }
        return endpoints.get(user_type, '/api/auth/token/')


class SecureLogoutView(APIView):
    """View de logout segura"""
    
    def post(self, request):
        if request.user and request.user.is_authenticated:
            user_id = request.user.id
            username = request.user.username
            
            # Destruir sessão
            SessionManager.destroy_session(user_id)
            
            logger.info(f"👋 Logout: {username} (ID: {user_id})")
            
            return Response({
                'message': 'Logout realizado com sucesso',
                'code': 'LOGOUT_SUCCESS'
            }, status=status.HTTP_200_OK)
        
        return Response({
            'error': 'Usuário não autenticado',
            'code': 'NOT_AUTHENTICATED'
        }, status=status.HTTP_401_UNAUTHORIZED)
