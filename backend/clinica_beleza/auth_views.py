"""
Views de Autenticação para Clínica da Beleza
"""
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from .auth_serializers import ClinicaLoginSerializer, UserSerializer
from .permissions import IsAdmin


class ClinicaLoginView(TokenObtainPairView):
    """
    View de Login customizada
    POST /clinica-beleza/auth/login/
    Body: { "username": "user", "password": "pass" }
    """
    serializer_class = ClinicaLoginSerializer
    permission_classes = [AllowAny]


class ClinicaTokenRefreshView(TokenRefreshView):
    """
    View para refresh do token
    POST /clinica-beleza/auth/refresh/
    Body: { "refresh": "token" }
    """
    permission_classes = [AllowAny]


class MeView(APIView):
    """
    Retorna informações do usuário logado
    GET /clinica-beleza/auth/me/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class LogoutView(APIView):
    """
    Logout (blacklist do token)
    POST /clinica-beleza/auth/logout/
    Body: { "refresh": "token" }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            from rest_framework_simplejwt.tokens import RefreshToken
            
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response(
                    {"error": "Refresh token é obrigatório"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return Response(
                {"message": "Logout realizado com sucesso"},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class CheckPermissionsView(APIView):
    """
    Verifica permissões do usuário
    GET /clinica-beleza/auth/permissions/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        permissions = {
            'is_admin': user.is_admin if hasattr(user, 'is_admin') else False,
            'is_recepcao': user.is_recepcao if hasattr(user, 'is_recepcao') else False,
            'is_profissional': user.is_profissional if hasattr(user, 'is_profissional') else False,
            'cargo': user.cargo if hasattr(user, 'cargo') else None,
            'can_manage_appointments': user.cargo in ['admin', 'recepcao'] if hasattr(user, 'cargo') else False,
            'can_view_financial': user.cargo == 'admin' if hasattr(user, 'cargo') else False,
            'can_manage_users': user.cargo == 'admin' if hasattr(user, 'cargo') else False,
        }
        
        return Response(permissions)


class UserListView(APIView):
    """
    Listar e criar usuários (apenas Admin)
    GET /clinica-beleza/auth/users/
    POST /clinica-beleza/auth/users/
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get(self, request):
        from .user_models import ClinicaUser
        users = ClinicaUser.objects.all().order_by('username')
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        from .user_models import ClinicaUser
        
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            # Criar usuário
            user = ClinicaUser.objects.create_user(
                username=request.data.get('username'),
                email=request.data.get('email', ''),
                password=request.data.get('password'),
                first_name=request.data.get('first_name', ''),
                last_name=request.data.get('last_name', ''),
                cargo=request.data.get('cargo', 'recepcao'),
            )
            
            # Vincular profissional se fornecido
            professional_id = request.data.get('professional_id')
            if professional_id:
                from .models import Professional
                try:
                    professional = Professional.objects.get(id=professional_id)
                    user.professional = professional
                    user.save()
                except Professional.DoesNotExist:
                    pass
            
            return Response(
                UserSerializer(user).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
