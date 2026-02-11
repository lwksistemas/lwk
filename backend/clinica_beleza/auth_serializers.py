"""
Serializers de Autenticação para Clínica da Beleza
"""
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from .user_models import ClinicaUser


class ClinicaLoginSerializer(TokenObtainPairSerializer):
    """
    Serializer customizado para login
    Adiciona informações do cargo no token JWT
    """
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Adicionar informações customizadas ao token
        token['cargo'] = user.cargo
        token['username'] = user.username
        token['email'] = user.email
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name
        token['is_admin'] = user.is_admin
        token['is_recepcao'] = user.is_recepcao
        token['is_profissional'] = user.is_profissional
        
        # Se for profissional, adicionar ID do profissional
        if user.professional:
            token['professional_id'] = user.professional.id
            token['professional_name'] = user.professional.name
        
        return token
    
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Adicionar informações do usuário na resposta
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'cargo': self.user.cargo,
            'cargo_display': self.user.get_cargo_display(),
            'is_admin': self.user.is_admin,
            'is_recepcao': self.user.is_recepcao,
            'is_profissional': self.user.is_profissional,
        }
        
        if self.user.professional:
            data['user']['professional'] = {
                'id': self.user.professional.id,
                'name': self.user.professional.name,
                'specialty': self.user.professional.specialty,
            }
        
        return data


class UserSerializer(serializers.ModelSerializer):
    """Serializer para informações do usuário"""
    cargo_display = serializers.CharField(source='get_cargo_display', read_only=True)
    professional_info = serializers.SerializerMethodField()
    
    class Meta:
        model = ClinicaUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'cargo', 'cargo_display', 'is_admin', 'is_recepcao', 
            'is_profissional', 'professional_info'
        ]
        read_only_fields = ['id', 'is_admin', 'is_recepcao', 'is_profissional']
    
    def get_professional_info(self, obj):
        if obj.professional:
            return {
                'id': obj.professional.id,
                'name': obj.professional.name,
                'specialty': obj.professional.specialty,
            }
        return None
