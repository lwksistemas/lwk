"""Serializers de vendedores CRM."""
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from rest_framework import serializers

from core.serializer_mixins import (
    TextNormalizationMixin,
)

from ..models import Vendedor
from ..vendedor_permissoes_service import (
    aplicar_permissoes_usuario_crm,
    normalizar_config_acesso,
    permissoes_ids_grupo,
    permissoes_ids_usuario_crm,
)

logger = logging.getLogger(__name__)


class VendedorSerializer(TextNormalizationMixin, serializers.ModelSerializer):
    criar_acesso = serializers.BooleanField(write_only=True, default=False, required=False)
    username = serializers.CharField(write_only=True, max_length=150, required=False, allow_blank=True)
    tem_acesso = serializers.SerializerMethodField(read_only=True)
    grupo_id = serializers.IntegerField(required=False, allow_null=True)
    grupo_nome = serializers.SerializerMethodField(read_only=True)
    permissoes_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True,
    )
    
    phone_fields = ['telefone']
    uppercase_fields = ['nome', 'cargo']

    class Meta:
        model = Vendedor
        fields = [
            'id', 'nome', 'email', 'telefone', 'cargo', 'comissao_padrao', 'is_admin', 'is_active',
            'criar_acesso', 'username', 'tem_acesso', 'grupo_id', 'grupo_nome', 'permissoes_ids',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_tem_acesso(self, obj):
        """✅ OTIMIZAÇÃO: Usa anotação do queryset para evitar N+1"""
        # Se tem anotação (vem do ViewSet otimizado), usa ela
        if hasattr(obj, 'tem_acesso_anotado'):
            return obj.tem_acesso_anotado
        
        # Fallback para casos sem anotação (detail view, etc)
        if not obj or not obj.email:
            return False
        from superadmin.models import VendedorUsuario
        from tenants.middleware import get_current_loja_id
        loja_id = get_current_loja_id()
        if not loja_id:
            return False
        return VendedorUsuario.objects.filter(
            loja_id=loja_id,
            vendedor_id=obj.id,
        ).exists()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        cfg = normalizar_config_acesso(getattr(instance, 'config_acesso', None))
        data['grupo_id'] = cfg.get('grupo_id')
        data['permissoes_ids'] = cfg.get('permissoes_ids') or []
        if not data['permissoes_ids']:
            user = self._get_vendedor_user(instance)
            if user:
                data['permissoes_ids'] = permissoes_ids_usuario_crm(user)
                if not data['grupo_id']:
                    grupo = user.groups.filter(name__in=['Gerente de Vendas', 'Vendedor']).first()
                    data['grupo_id'] = grupo.id if grupo else None
        return data

    def _get_vendedor_user(self, obj):
        if not obj or not obj.id:
            return None
        from superadmin.models import VendedorUsuario
        from tenants.middleware import get_current_loja_id

        loja_id = get_current_loja_id()
        if not loja_id:
            return None
        try:
            vu = VendedorUsuario.objects.using('default').select_related('user').get(
                loja_id=loja_id,
                vendedor_id=obj.id,
            )
            return vu.user
        except VendedorUsuario.DoesNotExist:
            return None

    def _persistir_config_acesso(self, vendedor, grupo_id, permissoes_ids):
        cfg = normalizar_config_acesso({'grupo_id': grupo_id, 'permissoes_ids': permissoes_ids})
        vendedor.config_acesso = cfg
        vendedor.save(update_fields=['config_acesso', 'updated_at'])
        return cfg

    def _aplicar_config_acesso_usuario(self, vendedor, cfg):
        user = self._get_vendedor_user(vendedor)
        if not user:
            return
        aplicar_permissoes_usuario_crm(user, cfg.get('grupo_id'), cfg.get('permissoes_ids') or [])

    def get_grupo_nome(self, obj):
        cfg = normalizar_config_acesso(getattr(obj, 'config_acesso', None))
        grupo_id = cfg.get('grupo_id')
        if grupo_id:
            from django.contrib.auth.models import Group
            try:
                return Group.objects.using('default').get(id=grupo_id).name
            except Group.DoesNotExist:
                pass
        user = self._get_vendedor_user(obj)
        if user:
            grupo = user.groups.filter(name__in=['Gerente de Vendas', 'Vendedor']).first()
            return grupo.name if grupo else None
        return None

    def create(self, validated_data):
        criar_acesso = validated_data.pop('criar_acesso', False)
        username = validated_data.pop('username', '') or ''
        grupo_id = validated_data.pop('grupo_id', None)
        permissoes_ids = validated_data.pop('permissoes_ids', None)
        if permissoes_ids is None and grupo_id:
            permissoes_ids = permissoes_ids_grupo(grupo_id)
        permissoes_ids = permissoes_ids or []

        vendedor = super().create(validated_data)
        cfg = self._persistir_config_acesso(vendedor, grupo_id, permissoes_ids)
        if criar_acesso and vendedor.email:
            try:
                self._criar_acesso_e_enviar_email(vendedor, cfg.get('grupo_id'), username, cfg.get('permissoes_ids'))
            except serializers.ValidationError:
                vendedor.delete()
                raise
        return vendedor

    def update(self, instance, validated_data):
        criar_acesso = validated_data.pop('criar_acesso', False)
        username = validated_data.pop('username', '') or ''
        grupo_id = validated_data.pop('grupo_id', None)
        permissoes_ids = validated_data.pop('permissoes_ids', None)

        vendedor = super().update(instance, validated_data)

        cfg_atual = normalizar_config_acesso(vendedor.config_acesso)
        if grupo_id is not None:
            cfg_atual['grupo_id'] = grupo_id
        if permissoes_ids is not None:
            cfg_atual['permissoes_ids'] = permissoes_ids
        elif grupo_id is not None and permissoes_ids is None:
            cfg_atual['permissoes_ids'] = permissoes_ids_grupo(grupo_id)

        cfg = self._persistir_config_acesso(vendedor, cfg_atual.get('grupo_id'), cfg_atual.get('permissoes_ids') or [])

        if criar_acesso and vendedor.email:
            try:
                self._criar_acesso_e_enviar_email(vendedor, cfg.get('grupo_id'), username, cfg.get('permissoes_ids'))
            except serializers.ValidationError:
                raise
        else:
            self._aplicar_config_acesso_usuario(vendedor, cfg)
        return vendedor

    def _criar_acesso_e_enviar_email(self, vendedor, grupo_id=None, username='', permissoes_ids=None):
        User = get_user_model()

        from superadmin.models import Loja, VendedorUsuario
        from tenants.middleware import get_current_loja_id

        loja_id = get_current_loja_id()
        if not loja_id:
            return
        try:
            loja = Loja.objects.using('default').get(id=loja_id)
        except Loja.DoesNotExist:
            return

        email = vendedor.email.strip().lower()
        login_username = (username.strip().lower() if username else email).strip()
        senha_provisoria = get_random_string(8)

        # Se já tem VendedorUsuario: apenas reenviar senha e atualizar grupo
        vu_existente = VendedorUsuario.objects.using('default').filter(
            loja_id=loja_id,
            vendedor_id=vendedor.id,
        ).select_related('user').first()
        if vu_existente:
            user = vu_existente.user
            user.set_password(senha_provisoria)
            user.first_name = vendedor.nome or user.first_name or ''
            user.save(update_fields=['password', 'first_name'])
            vu_existente.precisa_trocar_senha = True
            vu_existente.save(update_fields=['precisa_trocar_senha'])

            aplicar_permissoes_usuario_crm(user, grupo_id, permissoes_ids or [])

            _enviar_email_senha(loja, vendedor, email, senha_provisoria, assunto='Nova senha provisória - CRM Vendas', reenviar=True)
            return

        existing_user = User.objects.using('default').filter(username=login_username).first()
        if existing_user:
            if VendedorUsuario.objects.using('default').filter(
                user=existing_user,
                loja_id=loja_id,
            ).exists():
                raise serializers.ValidationError({
                    'username': f'O usuário "{login_username}" já possui acesso a esta loja.',
                    'detail': f'O usuário "{login_username}" já possui acesso a esta loja.',
                })
            if existing_user.lojas_owned.exists():
                raise serializers.ValidationError({
                    'username': f'O usuário "{login_username}" já existe no sistema. Escolha outro.',
                    'detail': f'Usuário "{login_username}" já utilizado.',
                })
            existing_user.set_password(senha_provisoria)
            existing_user.first_name = vendedor.nome or existing_user.first_name or ''
            existing_user.email = email
            existing_user.save(update_fields=['password', 'first_name', 'email'])
            VendedorUsuario.objects.using('default').create(
                user=existing_user,
                loja=loja,
                vendedor_id=vendedor.id,
                precisa_trocar_senha=True,
            )

            aplicar_permissoes_usuario_crm(existing_user, grupo_id, permissoes_ids or [])
        else:
            user = User.objects.db_manager('default').create_user(
                username=login_username,
                email=email,
                password=senha_provisoria,
                first_name=vendedor.nome or '',
            )
            VendedorUsuario.objects.using('default').create(
                user=user,
                loja=loja,
                vendedor_id=vendedor.id,
                precisa_trocar_senha=True,
            )

            aplicar_permissoes_usuario_crm(user, grupo_id, permissoes_ids or [])

        _enviar_email_senha(loja, vendedor, email, senha_provisoria, assunto='Acesso ao sistema - CRM Vendas')

    def _atualizar_grupo(self, vendedor, grupo_id):
        """Compatibilidade: delega para config de acesso."""
        cfg = normalizar_config_acesso(vendedor.config_acesso)
        cfg['grupo_id'] = grupo_id
        cfg['permissoes_ids'] = permissoes_ids_grupo(grupo_id)
        self._persistir_config_acesso(vendedor, cfg.get('grupo_id'), cfg.get('permissoes_ids'))
        self._aplicar_config_acesso_usuario(vendedor, cfg)

    def _atualizar_grupo_usuario(self, user, grupo_id):
        aplicar_permissoes_usuario_crm(user, grupo_id, permissoes_ids_grupo(grupo_id))


def _enviar_email_senha(loja, vendedor, email, senha_provisoria, assunto='Acesso ao Sistema - CRM Vendas', reenviar=False):
    site_url = getattr(settings, 'SITE_URL', 'https://lwksistemas.com.br').rstrip('/')
    login_url = f"{site_url}/loja/{loja.slug}/login"
    if reenviar:
        titulo = "Senha Redefinida"
        subtitulo = "Sua senha foi redefinida com sucesso"
    else:
        titulo = "Bem-vindo ao CRM"
        subtitulo = "Seu acesso foi criado com sucesso!"
    
    try:
        from core.email_delivery import create_email_multipart
        from core.email_templates import email_senha_provisoria_html
        
        info_adicional = {
            "Loja": loja.nome,
            "Sistema": "CRM de Vendas",
            "Seu Cargo": vendedor.cargo,
            "Comissão Padrão": f"{vendedor.comissao_padrao}%",
        }
        
        html_content, texto_plano = email_senha_provisoria_html(
            nome_destinatario=vendedor.nome or 'Vendedor',
            usuario=email,
            senha=senha_provisoria,
            url_login=login_url,
            titulo_principal=titulo,
            subtitulo=subtitulo,
            info_adicional=info_adicional,
            nome_sistema=loja.nome
        )
        
        email_msg = create_email_multipart(
            assunto,
            texto_plano,
            [email],
            html=html_content,
        )
        email_msg.send(fail_silently=True)
    except Exception as mail_err:
        logger.warning('Envio de e-mail ao criar vendedor falhou: %s', mail_err)

