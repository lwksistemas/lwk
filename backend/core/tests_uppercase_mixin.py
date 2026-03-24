"""
Testes para mixin de conversão para maiúsculas
"""
from django.test import TestCase
from rest_framework import serializers
from core.serializer_mixins import UpperCaseNormalizationMixin, TextNormalizationMixin


# Mock model para testes
class MockModel:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


# Serializer de teste com UpperCaseNormalizationMixin
class TestUpperCaseSerializer(UpperCaseNormalizationMixin, serializers.Serializer):
    nome = serializers.CharField()
    empresa = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False)
    
    uppercase_fields = ['nome', 'empresa']


# Serializer de teste com TextNormalizationMixin (telefone + maiúsculas)
class TestTextNormalizationSerializer(TextNormalizationMixin, serializers.Serializer):
    nome = serializers.CharField()
    telefone = serializers.CharField(required=False, allow_blank=True)
    cidade = serializers.CharField(required=False, allow_blank=True)
    
    phone_fields = ['telefone']
    uppercase_fields = ['nome', 'cidade']


class UpperCaseNormalizationMixinTestCase(TestCase):
    """Testes para UpperCaseNormalizationMixin"""
    
    def test_converte_nome_para_maiusculas(self):
        """Testa conversão de nome para maiúsculas"""
        serializer = TestUpperCaseSerializer(data={
            'nome': 'joão silva',
            'email': 'joao@example.com'
        })
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['nome'], 'JOÃO SILVA')
    
    def test_converte_empresa_para_maiusculas(self):
        """Testa conversão de empresa para maiúsculas"""
        serializer = TestUpperCaseSerializer(data={
            'nome': 'maria',
            'empresa': 'empresa teste ltda'
        })
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['empresa'], 'EMPRESA TESTE LTDA')
    
    def test_nao_converte_email(self):
        """Testa que email não é convertido (não está em uppercase_fields)"""
        serializer = TestUpperCaseSerializer(data={
            'nome': 'pedro',
            'email': 'Pedro@Example.COM'
        })
        self.assertTrue(serializer.is_valid())
        # Email deve permanecer como foi digitado
        self.assertEqual(serializer.validated_data['email'], 'Pedro@Example.COM')
    
    def test_campo_vazio_nao_causa_erro(self):
        """Testa que campo vazio não causa erro"""
        serializer = TestUpperCaseSerializer(data={
            'nome': 'ana',
            'empresa': ''
        })
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['nome'], 'ANA')
        self.assertEqual(serializer.validated_data['empresa'], '')
    
    def test_remove_espacos_extras(self):
        """Testa que espaços extras são removidos"""
        serializer = TestUpperCaseSerializer(data={
            'nome': '  carlos santos  ',
            'empresa': '  empresa  '
        })
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['nome'], 'CARLOS SANTOS')
        self.assertEqual(serializer.validated_data['empresa'], 'EMPRESA')
    
    def test_ja_maiuscula_permanece_igual(self):
        """Testa que texto já em maiúsculas permanece igual"""
        serializer = TestUpperCaseSerializer(data={
            'nome': 'FERNANDO SILVA',
            'empresa': 'EMPRESA LTDA'
        })
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['nome'], 'FERNANDO SILVA')
        self.assertEqual(serializer.validated_data['empresa'], 'EMPRESA LTDA')
    
    def test_caracteres_especiais_preservados(self):
        """Testa que caracteres especiais são preservados"""
        serializer = TestUpperCaseSerializer(data={
            'nome': 'josé & maria',
            'empresa': 'empresa (teste) - ltda'
        })
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['nome'], 'JOSÉ & MARIA')
        self.assertEqual(serializer.validated_data['empresa'], 'EMPRESA (TESTE) - LTDA')


class TextNormalizationMixinTestCase(TestCase):
    """Testes para TextNormalizationMixin (telefone + maiúsculas)"""
    
    def test_normaliza_telefone_e_maiusculas(self):
        """Testa que normaliza telefone E converte para maiúsculas"""
        serializer = TestTextNormalizationSerializer(data={
            'nome': 'lucas santos',
            'telefone': '11987654321',
            'cidade': 'são paulo'
        })
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['nome'], 'LUCAS SANTOS')
        self.assertEqual(serializer.validated_data['telefone'], '(11) 98765-4321')
        self.assertEqual(serializer.validated_data['cidade'], 'SÃO PAULO')
    
    def test_telefone_formatado_e_nome_maiusculo(self):
        """Testa formatação de telefone com nome em maiúsculas"""
        serializer = TestTextNormalizationSerializer(data={
            'nome': 'beatriz',
            'telefone': '21 9 8765-4321'
        })
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['nome'], 'BEATRIZ')
        self.assertEqual(serializer.validated_data['telefone'], '(21) 98765-4321')
    
    def test_campos_opcionais_vazios(self):
        """Testa que campos opcionais vazios não causam erro"""
        serializer = TestTextNormalizationSerializer(data={
            'nome': 'rafael',
            'telefone': '',
            'cidade': ''
        })
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['nome'], 'RAFAEL')
        self.assertEqual(serializer.validated_data['telefone'], '')
        self.assertEqual(serializer.validated_data['cidade'], '')
