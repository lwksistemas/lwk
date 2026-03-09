import logging
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.conf import settings

from .models import Vendedor, Conta, Lead, Contato, Oportunidade, Atividade

logger = logging.getLogger(__name__)


class VendedorSerializer(serializers.ModelSerializer):
    criar_acesso = serializers.BooleanField(write_only=True, default=False, required=False)
    tem_acesso = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Vendedor
        fields = [
            'id', 'nome', 'email', 'telefone', 'cargo', 'is_admin', 'is_active',
            'criar_acesso', 'tem_acesso',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_tem_acesso(self, obj):
        if not obj or not obj.email:
            return False
        from tenants.middleware import get_current_loja_id
        from superadmin.models import VendedorUsuario
        loja_id = get_current_loja_id()
        if not loja_id:
            return False
        return VendedorUsuario.objects.filter(
            loja_id=loja_id,
            vendedor_id=obj.id,
        ).exists()

    def create(self, validated_data):
        criar_acesso = validated_data.pop('criar_acesso', False)
        vendedor = super().create(validated_data)
        if criar_acesso and vendedor.email:
            try:
                self._criar_acesso_e_enviar_email(vendedor)
            except serializers.ValidationError:
                vendedor.delete()
                raise
        return vendedor

    def _criar_acesso_e_enviar_email(self, vendedor):
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
        senha_provisoria = get_random_string(8)
        user = None

        existing_user = User.objects.using('default').filter(username=email).first()
        if existing_user:
            if VendedorUsuario.objects.using('default').filter(
                user=existing_user,
                loja_id=loja_id,
            ).exists():
                raise serializers.ValidationError({
                    'email': 'Este e-mail já possui acesso a esta loja. Use outro ou cadastre sem "Criar acesso".',
                    'detail': 'Este e-mail já possui acesso a esta loja.',
                })
            if existing_user.lojas_owned.exists():
                raise serializers.ValidationError({
                    'email': 'Já existe um usuário (proprietário de loja) com este e-mail. Use outro ou não marque "Criar acesso".',
                    'detail': 'E-mail já utilizado como proprietário.',
                })
            user = existing_user
            user.set_password(senha_provisoria)
            user.first_name = vendedor.nome or user.first_name or ''
            user.save(update_fields=['password', 'first_name'])
            VendedorUsuario.objects.using('default').create(
                user=user,
                loja=loja,
                vendedor_id=vendedor.id,
                precisa_trocar_senha=True,
            )
        else:
            user = User.objects.db_manager('default').create_user(
                username=email,
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

        site_url = getattr(settings, 'SITE_URL', 'https://lwksistemas.com.br').rstrip('/')
        login_url = f"{site_url}/loja/{loja.slug}/login"
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or 'noreply@lwksistemas.com.br'
        try:
            send_mail(
                subject='Acesso ao sistema - CRM Vendas',
                message=(
                    f"Olá, {vendedor.nome or 'Vendedor'}!\n\n"
                    f"Seu acesso ao sistema foi criado.\n\n"
                    f"Login: {email}\n"
                    f"Senha provisória: {senha_provisoria}\n\n"
                    f"Acesse: {login_url}\n\n"
                    f"Por segurança, altere sua senha no primeiro acesso."
                ),
                from_email=from_email,
                recipient_list=[email],
                fail_silently=True,
            )
        except Exception as mail_err:
            logger.warning('Envio de e-mail ao criar vendedor falhou: %s', mail_err)


class ContaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conta
        fields = [
            'id', 'nome', 'segmento', 'telefone', 'email', 'cidade', 'endereco',
            'observacoes', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class LeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = [
            'id', 'nome', 'empresa', 'email', 'telefone', 'origem', 'status',
            'valor_estimado', 'conta', 'observacoes', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class LeadListSerializer(serializers.ModelSerializer):
    conta_nome = serializers.CharField(source='conta.nome', read_only=True)

    class Meta:
        model = Lead
        fields = [
            'id', 'nome', 'empresa', 'email', 'origem', 'status', 'valor_estimado',
            'conta', 'conta_nome', 'created_at',
        ]


class ContatoSerializer(serializers.ModelSerializer):
    conta_nome = serializers.CharField(source='conta.nome', read_only=True)

    class Meta:
        model = Contato
        fields = [
            'id', 'nome', 'email', 'telefone', 'cargo', 'conta', 'conta_nome',
            'observacoes', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class OportunidadeSerializer(serializers.ModelSerializer):
    lead_nome = serializers.CharField(source='lead.nome', read_only=True)
    vendedor_nome = serializers.CharField(source='vendedor.nome', read_only=True)

    class Meta:
        model = Oportunidade
        fields = [
            'id', 'titulo', 'lead', 'lead_nome', 'valor', 'etapa', 'vendedor', 'vendedor_nome',
            'probabilidade', 'data_fechamento_prevista', 'data_fechamento', 'observacoes',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class AtividadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Atividade
        fields = [
            'id', 'titulo', 'tipo', 'oportunidade', 'lead', 'data', 'duracao_minutos',
            'concluido', 'observacoes', 'google_event_id', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class AtividadeListSerializer(serializers.ModelSerializer):
    """Serializer para listagem sem google_event_id (compatível com schemas antigos)."""
    class Meta:
        model = Atividade
        fields = [
            'id', 'titulo', 'tipo', 'oportunidade', 'lead', 'data', 'duracao_minutos',
            'concluido', 'observacoes', 'created_at', 'updated_at',
        ]
