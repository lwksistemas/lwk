from rest_framework import serializers
from .models import HeroSection, Funcionalidade, ModuloSistema, WhyUsBenefit


class HeroSerializer(serializers.ModelSerializer):
    class Meta:
        model = HeroSection
        fields = ['id', 'titulo', 'subtitulo', 'botao_texto', 'botao_principal_ativo', 'ordem', 'ativo']
        extra_kwargs = {
            'botao_principal_ativo': {'required': False, 'default': True},
        }


class FuncionalidadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Funcionalidade
        fields = ['id', 'titulo', 'descricao', 'icone', 'imagem', 'ordem', 'ativo']
        extra_kwargs = {
            'icone': {'allow_blank': True, 'required': False},
            'imagem': {'required': False, 'allow_blank': True, 'allow_null': True},
        }


class ModuloSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModuloSistema
        fields = ['id', 'nome', 'descricao', 'slug', 'icone', 'imagem', 'ordem', 'ativo']
        extra_kwargs = {
            'imagem': {'required': False, 'allow_blank': True, 'allow_null': True},
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
        fields = ['id', 'titulo', 'descricao', 'icone', 'ordem', 'ativo']
        extra_kwargs = {
            'descricao': {'required': False, 'allow_blank': True},
            'icone': {'required': False, 'allow_blank': True, 'default': '✓'},
        }
