from rest_framework import serializers
from .models import HeroSection, Funcionalidade, ModuloSistema


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
        fields = ['id', 'titulo', 'descricao', 'icone', 'ordem', 'ativo']
        extra_kwargs = {
            'icone': {'allow_blank': True, 'required': False},
        }


class ModuloSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModuloSistema
        fields = ['id', 'nome', 'descricao', 'slug', 'icone', 'ordem', 'ativo']
