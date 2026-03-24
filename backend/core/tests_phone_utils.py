"""
Testes para utilitários de telefone
"""
from django.test import TestCase
from .phone_utils import (
    limpar_telefone,
    formatar_telefone_brasileiro,
    validar_telefone_brasileiro,
    normalizar_telefone,
)


class PhoneUtilsTestCase(TestCase):
    """Testes para funções de padronização de telefone"""
    
    def test_limpar_telefone(self):
        """Testa remoção de caracteres não numéricos"""
        self.assertEqual(limpar_telefone("(11) 98765-4321"), "11987654321")
        self.assertEqual(limpar_telefone("11 9 8765-4321"), "11987654321")
        self.assertEqual(limpar_telefone("11987654321"), "11987654321")
        self.assertEqual(limpar_telefone(""), "")
        self.assertEqual(limpar_telefone(None), "")
    
    def test_formatar_celular_com_ddd(self):
        """Testa formatação de celular com DDD (11 dígitos)"""
        self.assertEqual(
            formatar_telefone_brasileiro("11987654321"),
            "(11) 98765-4321"
        )
        self.assertEqual(
            formatar_telefone_brasileiro("21987654321"),
            "(21) 98765-4321"
        )
    
    def test_formatar_fixo_com_ddd(self):
        """Testa formatação de telefone fixo com DDD (10 dígitos)"""
        self.assertEqual(
            formatar_telefone_brasileiro("1133334444"),
            "(11) 3333-4444"
        )
        self.assertEqual(
            formatar_telefone_brasileiro("2133334444"),
            "(21) 3333-4444"
        )
    
    def test_formatar_celular_sem_ddd(self):
        """Testa formatação de celular sem DDD (9 dígitos)"""
        self.assertEqual(
            formatar_telefone_brasileiro("987654321"),
            "98765-4321"
        )
    
    def test_formatar_fixo_sem_ddd(self):
        """Testa formatação de telefone fixo sem DDD (8 dígitos)"""
        self.assertEqual(
            formatar_telefone_brasileiro("33334444"),
            "3333-4444"
        )
    
    def test_formatar_telefone_ja_formatado(self):
        """Testa que telefone já formatado é reformatado corretamente"""
        self.assertEqual(
            formatar_telefone_brasileiro("(11) 98765-4321"),
            "(11) 98765-4321"
        )
        self.assertEqual(
            formatar_telefone_brasileiro("(11) 3333-4444"),
            "(11) 3333-4444"
        )
    
    def test_formatar_telefone_vazio(self):
        """Testa que telefone vazio retorna vazio"""
        self.assertEqual(formatar_telefone_brasileiro(""), "")
        self.assertEqual(formatar_telefone_brasileiro(None), "")
    
    def test_formatar_telefone_invalido(self):
        """Testa que telefone com quantidade inválida de dígitos retorna apenas números"""
        # Muito curto
        self.assertEqual(formatar_telefone_brasileiro("123"), "123")
        # Muito longo
        self.assertEqual(formatar_telefone_brasileiro("123456789012"), "123456789012")
    
    def test_validar_telefone_valido(self):
        """Testa validação de telefones válidos"""
        valido, msg = validar_telefone_brasileiro("(11) 98765-4321")
        self.assertTrue(valido)
        self.assertEqual(msg, "")
        
        valido, msg = validar_telefone_brasileiro("11987654321")
        self.assertTrue(valido)
        
        valido, msg = validar_telefone_brasileiro("1133334444")
        self.assertTrue(valido)
    
    def test_validar_telefone_vazio(self):
        """Testa que telefone vazio é válido (campo opcional)"""
        valido, msg = validar_telefone_brasileiro("")
        self.assertTrue(valido)
        
        valido, msg = validar_telefone_brasileiro(None)
        self.assertTrue(valido)
    
    def test_validar_telefone_quantidade_digitos_invalida(self):
        """Testa validação de telefone com quantidade inválida de dígitos"""
        valido, msg = validar_telefone_brasileiro("123")
        self.assertFalse(valido)
        self.assertIn("8, 9, 10 ou 11 dígitos", msg)
    
    def test_validar_ddd_invalido(self):
        """Testa validação de DDD inválido"""
        valido, msg = validar_telefone_brasileiro("0987654321")
        self.assertFalse(valido)
        self.assertIn("DDD inválido", msg)
        
        valido, msg = validar_telefone_brasileiro("9987654321")
        self.assertFalse(valido)
        self.assertIn("DDD inválido", msg)
    
    def test_validar_celular_sem_9(self):
        """Testa validação de celular que não começa com 9"""
        valido, msg = validar_telefone_brasileiro("11887654321")
        self.assertFalse(valido)
        self.assertIn("começar com 9", msg)
    
    def test_normalizar_telefone(self):
        """Testa função principal de normalização"""
        self.assertEqual(
            normalizar_telefone("11 9 8765-4321"),
            "(11) 98765-4321"
        )
        self.assertEqual(
            normalizar_telefone("(11) 98765-4321"),
            "(11) 98765-4321"
        )
        self.assertEqual(
            normalizar_telefone(""),
            ""
        )
        self.assertEqual(
            normalizar_telefone(None),
            ""
        )
