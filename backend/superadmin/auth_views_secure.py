"""
Views de Autenticação com Isolamento Total e Validação de Grupo
"""
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from superadmin.session_manager import SessionManager
from superadmin.models import Loja, UsuarioSistema
import logging

logger = logging.getLogger(__name__)


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
        loja_slug = request.data.get('loja_slug')
        cpf_cnpj = request.data.get('cpf_cnpj', '').strip()
        
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
                'error': 'Usuário ou senha incorretos. Verifique suas credenciais e tente novamente.',
                'code': 'INVALID_CREDENTIALS',
                'detalhes': 'Se você esqueceu sua senha, clique em "Esqueci minha senha" para receber uma nova senha provisória por email.'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Se for loja e CPF/CNPJ foi fornecido, validar
        if user_type == 'loja' and cpf_cnpj:
            import re
            # Remover formatação do CPF/CNPJ
            cpf_cnpj_limpo = re.sub(r'[^0-9]', '', cpf_cnpj)
            
            # Buscar loja do usuário
            loja = Loja.objects.filter(owner=user, is_active=True).first()
            if loja and loja.cpf_cnpj:
                # Remover formatação do CPF/CNPJ da loja
                loja_cpf_cnpj_limpo = re.sub(r'[^0-9]', '', loja.cpf_cnpj)
                
                # Validar se o CPF/CNPJ corresponde
                if cpf_cnpj_limpo != loja_cpf_cnpj_limpo:
                    logger.critical(f"🚨 VIOLAÇÃO: CPF/CNPJ incorreto para usuário {username}")
                    return Response({
                        'error': 'CPF/CNPJ incorreto. Verifique os dados e tente novamente.',
                        'code': 'INVALID_CPF_CNPJ'
                    }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Se for superadmin ou suporte e CPF foi fornecido, validar
        if user_type in ['superadmin', 'suporte'] and cpf_cnpj:
            import re
            # Remover formatação do CPF
            cpf_limpo = re.sub(r'[^0-9]', '', cpf_cnpj)
            
            try:
                usuario_sistema = UsuarioSistema.objects.get(user=user, tipo=user_type, is_active=True)
                if usuario_sistema.cpf:
                    # Remover formatação do CPF do usuário
                    usuario_cpf_limpo = re.sub(r'[^0-9]', '', usuario_sistema.cpf)
                    
                    # Validar se o CPF corresponde
                    if cpf_limpo != usuario_cpf_limpo:
                        logger.critical(f"🚨 VIOLAÇÃO: CPF incorreto para usuário {username} ({user_type})")
                        return Response({
                            'error': 'CPF incorreto. Verifique os dados e tente novamente.',
                            'code': 'INVALID_CPF'
                        }, status=status.HTTP_401_UNAUTHORIZED)
            except UsuarioSistema.DoesNotExist:
                pass
        
        # Identificar tipo real do usuário
        real_user_type = self._get_user_type(user)
        
        # Validar se o tipo corresponde ao endpoint
        if user_type and real_user_type != user_type:
            logger.critical(
                f"🚨 VIOLAÇÃO: Usuário {username} (tipo: {real_user_type}) "
                f"tentou login no endpoint de {user_type}"
            )
            return Response({
                'error': 'Este usuário não pode fazer login aqui',
                'code': 'WRONG_LOGIN_ENDPOINT',
                'seu_tipo': real_user_type,
                'endpoint_correto': self._get_correct_endpoint(real_user_type)
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Se for loja, validar slug
        if real_user_type == 'loja':
            loja = Loja.objects.filter(owner=user, is_active=True).first()
            if not loja:
                return Response({
                    'error': 'Usuário não possui loja ativa',
                    'code': 'NO_ACTIVE_STORE'
                }, status=status.HTTP_403_FORBIDDEN)
            
            if loja_slug and loja.slug != loja_slug:
                logger.critical(f"🚨 VIOLAÇÃO: Usuário {username} tentou login na loja errada")
                return Response({
                    'error': 'Você não pode fazer login nesta loja',
                    'code': 'WRONG_STORE',
                    'sua_loja': loja.slug
                }, status=status.HTTP_403_FORBIDDEN)
        
        # Gerar tokens
        refresh = RefreshToken.for_user(user)
        refresh['user_type'] = real_user_type
        refresh['username'] = user.username
        refresh['email'] = user.email
        
        if real_user_type == 'loja':
            loja = Loja.objects.filter(owner=user, is_active=True).first()
            if loja:
                refresh['loja_id'] = loja.id
                refresh['loja_slug'] = loja.slug
        
        access_token = refresh.access_token
        access_token['user_type'] = real_user_type
        access_token['username'] = user.username
        access_token['email'] = user.email
        
        if real_user_type == 'loja':
            loja = Loja.objects.filter(owner=user, is_active=True).first()
            if loja:
                access_token['loja_id'] = loja.id
                access_token['loja_slug'] = loja.slug
        
        access = str(access_token)
        
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
        
        # Verificar se precisa trocar senha provisória
        precisa_trocar_senha = False
        if real_user_type == 'loja':
            loja = Loja.objects.filter(owner=user, is_active=True).first()
            if loja:
                # Verificar se tem senha provisória e não foi alterada
                precisa_trocar_senha = not loja.senha_foi_alterada and bool(loja.senha_provisoria)
                
                # LOG DETALHADO para debug
                logger.info(f"🔍 DEBUG SENHA - Loja: {loja.slug}")
                logger.info(f"   - senha_provisoria existe: {bool(loja.senha_provisoria)}")
                logger.info(f"   - senha_provisoria valor: {loja.senha_provisoria[:3] + '***' if loja.senha_provisoria else 'VAZIO'}")
                logger.info(f"   - senha_foi_alterada: {loja.senha_foi_alterada}")
                logger.info(f"   - precisa_trocar_senha: {precisa_trocar_senha}")
                
                response_data['loja'] = {
                    'id': loja.id,
                    'slug': loja.slug,
                    'nome': loja.nome,
                    'tipo_loja': loja.tipo_loja.nome if loja.tipo_loja else None
                }
                response_data['precisa_trocar_senha'] = precisa_trocar_senha
        elif real_user_type == 'suporte':
            # Verificar senha provisória do suporte
            try:
                usuario_sistema = UsuarioSistema.objects.get(user=user, tipo='suporte', is_active=True)
                precisa_trocar_senha = not usuario_sistema.senha_foi_alterada and bool(usuario_sistema.senha_provisoria)
                
                # LOG DETALHADO para debug
                logger.info(f"🔍 DEBUG SENHA SUPORTE - User: {usuario_sistema.user.username}")
                logger.info(f"   - senha_provisoria existe: {bool(usuario_sistema.senha_provisoria)}")
                logger.info(f"   - senha_foi_alterada: {usuario_sistema.senha_foi_alterada}")
                logger.info(f"   - precisa_trocar_senha: {precisa_trocar_senha}")
                
                response_data['precisa_trocar_senha'] = precisa_trocar_senha
            except UsuarioSistema.DoesNotExist:
                pass
        elif real_user_type == 'superadmin':
            # Verificar senha provisória do superadmin
            try:
                usuario_sistema = UsuarioSistema.objects.get(user=user, tipo='superadmin', is_active=True)
                precisa_trocar_senha = not usuario_sistema.senha_foi_alterada and bool(usuario_sistema.senha_provisoria)
                
                # LOG DETALHADO para debug
                logger.info(f"🔍 DEBUG SENHA SUPERADMIN - User: {usuario_sistema.user.username}")
                logger.info(f"   - senha_provisoria existe: {bool(usuario_sistema.senha_provisoria)}")
                logger.info(f"   - senha_foi_alterada: {usuario_sistema.senha_foi_alterada}")
                logger.info(f"   - precisa_trocar_senha: {precisa_trocar_senha}")
                
                response_data['precisa_trocar_senha'] = precisa_trocar_senha
            except UsuarioSistema.DoesNotExist:
                pass
        
        logger.info(f"✅ Login bem-sucedido: {username} (tipo: {real_user_type}, trocar senha: {precisa_trocar_senha})")
        
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


class BeaconLogoutView(APIView):
    """
    View de logout via sendBeacon (ao fechar aba do navegador)
    
    Esta view é especial porque:
    - Aceita requisições sem header de autenticação
    - Recebe o token no body da requisição
    - Usa navigator.sendBeacon() que não permite headers customizados
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Logout via beacon - aceita token no body
        """
        from rest_framework_simplejwt.tokens import AccessToken
        from rest_framework_simplejwt.exceptions import TokenError
        
        token_str = request.data.get('token')
        
        if not token_str:
            logger.warning("🚪 Beacon logout: token não fornecido")
            return Response({
                'error': 'Token não fornecido',
                'code': 'NO_TOKEN'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Decodificar token para obter user_id
            token = AccessToken(token_str)
            user_id = token['user_id']
            
            # Destruir sessão
            SessionManager.destroy_session(user_id)
            
            logger.info(f"🚪 Beacon logout: Usuário {user_id} deslogado (aba fechada)")
            
            return Response({
                'message': 'Logout via beacon realizado',
                'code': 'BEACON_LOGOUT_SUCCESS'
            }, status=status.HTTP_200_OK)
            
        except TokenError as e:
            logger.warning(f"🚪 Beacon logout: token inválido - {e}")
            return Response({
                'error': 'Token inválido',
                'code': 'INVALID_TOKEN'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"🚪 Beacon logout: erro - {e}")
            return Response({
                'error': 'Erro ao processar logout',
                'code': 'LOGOUT_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
