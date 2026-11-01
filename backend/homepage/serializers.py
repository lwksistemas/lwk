from rest_framework import serializers

from core.serializer_mixins import PhoneNormalizationMixin

from .models import (
    EmpresaConfig,
    Funcionalidade,
    HeroSection,
    ItemMenu,
    ModuloSistema,
    PaginaSite,
    SolicitacaoContato,
    WhyUsBenefit,
)


class HeroSerializer(serializers.ModelSerializer):
    class Meta:
        model = HeroSection
        fields = [
            "id",
            "titulo",
            "subtitulo",
            "selo",
            "botao_texto",
            "botao_url",
            "botao_principal_ativo",
            "botao_secundario_texto",
            "botao_secundario_url",
            "botao_secundario_ativo",
            "intervalo_carrossel",
            "titulo_destaque",
            "fonte_familia",
            "fonte_tamanho",
            "ordem",
            "ativo",
        ]
        extra_kwargs = {
            "botao_principal_ativo": {"required": False, "default": True},
            "titulo_destaque": {"required": False, "allow_blank": True},
            "fonte_familia": {"required": False},
            "fonte_tamanho": {"required": False},
        }


class FuncionalidadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Funcionalidade
        fields = ["id", "titulo", "descricao", "icone", "link", "imagem", "ordem", "ativo"]
        extra_kwargs = {
            "icone": {"allow_blank": True, "required": False},
            "link": {"allow_blank": True, "required": False},
            "imagem": {"required": False, "allow_blank": True, "allow_null": True},
        }


class ModuloSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModuloSistema
        fields = ["id", "nome", "descricao", "slug", "icone", "imagem", "ordem", "ativo"]
        extra_kwargs = {
            "imagem": {"required": False, "allow_blank": True, "allow_null": True},
        }

    def validate_slug(self, value):
        """Valida se o slug é único (exceto para o próprio registro em edição)"""
        if not value:
            return value

        # Verifica se já existe outro módulo com o mesmo slug
        queryset = ModuloSistema.objects.filter(slug=value)

        # Se estamos editando, excluir o próprio registro da verificação
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError(f'Já existe um módulo com o slug "{value}". Escolha outro.')

        return value


class WhyUsBenefitSerializer(serializers.ModelSerializer):
    class Meta:
        model = WhyUsBenefit
        fields = ["id", "titulo", "descricao", "icone", "ordem", "ativo"]
        extra_kwargs = {
            "descricao": {"required": False, "allow_blank": True},
            "icone": {"required": False, "allow_blank": True, "default": "✓"},
        }


class EmpresaConfigSerializer(PhoneNormalizationMixin, serializers.ModelSerializer):
    phone_fields = ["telefone_whatsapp"]

    class Meta:
        model = EmpresaConfig
        fields = ["id", "nome_empresa", "cnpj", "endereco", "telefone_whatsapp", "mensagem_whatsapp", "email_contato", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {
            "cnpj": {"required": False, "allow_blank": True},
            "endereco": {"required": False, "allow_blank": True},
            "telefone_whatsapp": {"required": False, "allow_blank": True},
            "mensagem_whatsapp": {"required": False, "allow_blank": True},
            "email_contato": {"required": False, "allow_blank": True},
        }


class ItemMenuSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemMenu
        fields = ["id", "grupo", "rotulo", "url", "ordem", "ativo"]


class PaginaSiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaginaSite
        fields = ["id", "slug", "titulo", "resumo", "corpo", "itens", "mensagem_whatsapp", "imagem", "ativo"]
        extra_kwargs = {
            "imagem": {"required": False, "allow_blank": True},
        }


PRODUTOS_CONTATO = {"crm-vendas", "clinicas-estetica", "personalizados", "outros", "geral"}


class SolicitacaoContatoSerializer(serializers.ModelSerializer):
    aceite_lgpd = serializers.BooleanField(write_only=True)

    class Meta:
        model = SolicitacaoContato
        fields = ["nome", "empresa", "whatsapp", "produto", "mensagem", "origem", "aceite_lgpd"]
        extra_kwargs = {
            "empresa": {"required": False, "allow_blank": True},
            "origem": {"required": False},
        }

    def validate_aceite_lgpd(self, value):
        if value is not True:
            raise serializers.ValidationError("É preciso aceitar o aviso de privacidade.")
        return value

    def validate_produto(self, value):
        if value not in PRODUTOS_CONTATO:
            raise serializers.ValidationError("Escolha o produto de interesse.")
        return value

    def validate_whatsapp(self, value):
        digitos = "".join(ch for ch in (value or "") if ch.isdigit())
        if len(digitos) < 10 or len(digitos) > 13:
            raise serializers.ValidationError("Informe um WhatsApp com DDD.")
        return digitos

    def create(self, validated_data):
        validated_data.pop("aceite_lgpd", None)
        return super().create(validated_data)
