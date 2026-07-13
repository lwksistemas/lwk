"""Serializers de usuários do sistema."""
import logging

from django.contrib.auth.models import Group, User
from rest_framework import serializers

from core.logging_utils import mask_email
from core.serializer_mixins import UniqueDocumentoPerLojaMixin

from ..models import UsuarioSistema

logger = logging.getLogger(__name__)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_active']
        extra_kwargs = {'password': {'write_only': True}}
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user


class UsuarioSistemaSerializer(UniqueDocumentoPerLojaMixin, serializers.ModelSerializer):
    unique_documento_fields = ['cpf']
    unique_documento_entidade = 'usuário'
    unique_documento_global = True
    user = UserSerializer()
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    
    class Meta:
        model = UsuarioSistema
        fields = '__all__'
    
    def create(self, validated_data):
        
        user_data = validated_data.pop('user')
        
        # Gerar senha provisória automaticamente
        from core.password_validation import generate_provisional_password
        senha_provisoria = generate_provisional_password()
        
        # Criar usuário
        user = User.objects.create_user(
            username=user_data['username'],
            email=user_data.get('email', ''),
            password=senha_provisoria,
            first_name=user_data.get('first_name', ''),
            last_name=user_data.get('last_name', ''),
            is_staff=True
        )
        
        # Criar perfil com senha provisória
        perfil = UsuarioSistema.objects.create(
            user=user, 
            senha_provisoria=senha_provisoria,
            senha_foi_alterada=False,
            **validated_data
        )
        
        # Adicionar ao grupo
        if perfil.tipo == 'suporte':
            grupo, _ = Group.objects.get_or_create(name='suporte')
            user.groups.add(grupo)
        elif perfil.tipo == 'superadmin':
            user.is_superuser = True
            user.save()
        
        # Enviar email com senha provisória
        try:
            tipo_display = 'Super Admin' if perfil.tipo == 'superadmin' else 'Suporte'
            url_login = f"https://lwksistemas.com.br/{perfil.tipo}/login"
            
            assunto = f"Bem-vindo ao LWK Sistemas - {tipo_display}"
            mensagem = f"""
Olá {user.first_name or user.username}!

Sua conta foi criada no LWK Sistemas.

🔐 DADOS DE ACESSO:
• URL de Login: {url_login}
• Usuário: {user.username}
• Senha Provisória: {senha_provisoria}

⚠️ IMPORTANTE:
• Esta é uma senha provisória gerada automaticamente
• Você será solicitado a trocar a senha no primeiro acesso
• Por segurança, altere a senha assim que fizer login
• Mantenha seus dados de acesso em segurança

📋 INFORMAÇÕES DA CONTA:
• Nome: {user.first_name} {user.last_name}
• Email: {user.email}
• Tipo: {tipo_display}

---
Equipe LWK Sistemas
            """.strip()
            
            from core.email_delivery import send_system_mail
            send_system_mail(assunto, mensagem, [user.email], fail_silently=True)
            logger.info("Email com senha provisória enviado: email=%s", mask_email(user.email))
        except Exception as e:
            logger.warning("Erro ao enviar email com senha provisória: %s", e)
        
        # Armazenar senha provisória no contexto para retornar na resposta
        perfil._senha_provisoria_gerada = senha_provisoria
        
        return perfil
    
    def update(self, instance, validated_data):
        """
        Atualizar usuário do sistema
        
        IMPORTANTE:
        - Username NÃO pode ser alterado (ignorado se enviado)
        - Senha só é atualizada se fornecida
        - Tipo pode ser alterado (superadmin <-> suporte)
        """
        user_data = validated_data.pop('user', {})
        
        # Atualizar dados do User (exceto username)
        user = instance.user
        if 'email' in user_data:
            user.email = user_data['email']
        if 'first_name' in user_data:
            user.first_name = user_data['first_name']
        if 'last_name' in user_data:
            user.last_name = user_data['last_name']
        
        # Atualizar senha se fornecida
        if 'password' in user_data and user_data['password']:
            user.set_password(user_data['password'])
        
        user.save()
        
        # Atualizar tipo e permissões
        tipo_antigo = instance.tipo
        tipo_novo = validated_data.get('tipo', tipo_antigo)
        
        if tipo_antigo != tipo_novo:
            # Remover permissões antigas
            if tipo_antigo == 'superadmin':
                user.is_superuser = False
            elif tipo_antigo == 'suporte':
                grupo_suporte = Group.objects.filter(name='suporte').first()
                if grupo_suporte:
                    user.groups.remove(grupo_suporte)
            
            # Adicionar novas permissões
            if tipo_novo == 'superadmin':
                user.is_superuser = True
            elif tipo_novo == 'suporte':
                grupo_suporte, _ = Group.objects.get_or_create(name='suporte')
                user.groups.add(grupo_suporte)
            
            user.save()
        
        # Atualizar campos do UsuarioSistema
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        
        return instance

