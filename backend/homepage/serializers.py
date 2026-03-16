from rest_framework import serializers
from .models import HeroSection, Funcionalidade, ModuloSistema


class HeroSerializer(serializers.ModelSerializer):
    class Meta:
        model = HeroSection
        fields = ['id', 'titulo', 'subtitulo', 'botao_texto', 'ordem']


class FuncionalidadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Funcionalidade
        fields = ['id', 'titulo', 'descricao', 'icone', 'ordem']


class ModuloSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModuloSistema
        fields = ['id', 'nome', 'descricao', 'slug', 'icone', 'ordem']
