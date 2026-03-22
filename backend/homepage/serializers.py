from rest_framework import serializers
from .models import HeroSection, Funcionalidade, ModuloSistema


class HeroSerializer(serializers.ModelSerializer):
    class Meta:
        model = HeroSection
        fields = ['id', 'titulo', 'subtitulo', 'botao_texto', 'botao_principal_ativo', 'imagem', 'ordem', 'ativo']
        extra_kwargs = {
            'botao_principal_ativo': {'required': False, 'default': True},
            'imagem': {'required': False, 'allow_blank': True, 'allow_null': True},
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
