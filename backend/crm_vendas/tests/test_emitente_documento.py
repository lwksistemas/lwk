"""
Testes unitários para emitente_documento.py — snapshot do emitente em propostas/contratos.
"""
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from crm_vendas.emitente_documento import (
    documento_tem_emitente_personalizado,
    limpar_emitente_se_vazio,
    obter_dados_emitente_documento,
)


class DocumentoTemEmitentePersonalizadoTests(SimpleTestCase):
    """Testa detecção de snapshot personalizado."""

    def test_com_emitente_nome_preenchido(self):
        doc = MagicMock()
        doc.emitente_nome = 'LWK Sistemas'
        self.assertTrue(documento_tem_emitente_personalizado(doc))

    def test_com_emitente_nome_vazio(self):
        doc = MagicMock()
        doc.emitente_nome = ''
        self.assertFalse(documento_tem_emitente_personalizado(doc))

    def test_com_emitente_nome_none(self):
        doc = MagicMock()
        doc.emitente_nome = None
        self.assertFalse(documento_tem_emitente_personalizado(doc))

    def test_com_emitente_nome_apenas_espacos(self):
        doc = MagicMock()
        doc.emitente_nome = '   '
        self.assertFalse(documento_tem_emitente_personalizado(doc))

    def test_sem_atributo_emitente_nome(self):
        """getattr com default '' deve retornar False."""
        doc = object()  # sem atributo emitente_nome
        self.assertFalse(documento_tem_emitente_personalizado(doc))


class LimparEmitenteSevazioTests(SimpleTestCase):
    """Testa limpeza do snapshot quando emitente_nome vier vazio."""

    def test_limpa_todos_campos_quando_nome_vazio(self):
        data = {
            'emitente_nome': '',
            'emitente_endereco': 'Rua A, 123',
            'emitente_cpf_cnpj': '12345678000195',
            'emitente_responsavel': 'João',
            'emitente_email': 'joao@test.com',
        }
        result = limpar_emitente_se_vazio(data)
        self.assertEqual(result['emitente_nome'], '')
        self.assertEqual(result['emitente_endereco'], '')
        self.assertEqual(result['emitente_cpf_cnpj'], '')
        self.assertEqual(result['emitente_responsavel'], '')
        self.assertEqual(result['emitente_email'], '')

    def test_preserva_campos_quando_nome_preenchido(self):
        data = {
            'emitente_nome': 'LWK Sistemas',
            'emitente_endereco': 'Rua B, 456',
            'emitente_cpf_cnpj': '99999999000199',
            'emitente_responsavel': 'Maria',
            'emitente_email': 'maria@test.com',
        }
        result = limpar_emitente_se_vazio(data)
        self.assertEqual(result['emitente_nome'], 'LWK Sistemas')
        self.assertEqual(result['emitente_endereco'], 'Rua B, 456')
        self.assertEqual(result['emitente_cpf_cnpj'], '99999999000199')

    def test_retorna_dict_mutado(self):
        """Deve modificar e retornar o mesmo dict (sem cópia)."""
        data = {'emitente_nome': '', 'emitente_endereco': 'X'}
        result = limpar_emitente_se_vazio(data)
        self.assertIs(result, data)

    def test_nome_none_limpa_campos(self):
        data = {'emitente_nome': None, 'emitente_endereco': 'Y'}
        result = limpar_emitente_se_vazio(data)
        self.assertEqual(result['emitente_nome'], '')
        self.assertEqual(result['emitente_endereco'], '')


class ObterDadosEmitenteDocumentoTests(SimpleTestCase):
    """Testa retorno correto de dados do emitente."""

    def test_retorna_snapshot_quando_personalizado(self):
        doc = MagicMock()
        doc.emitente_nome = 'Empresa Teste'
        doc.emitente_endereco = 'Rua C, 789'
        doc.emitente_cpf_cnpj = '12345678000195'
        doc.emitente_responsavel = 'Carlos'
        doc.emitente_email = 'carlos@test.com'

        result = obter_dados_emitente_documento(doc)

        self.assertEqual(result['nome'], 'Empresa Teste')
        self.assertEqual(result['endereco'], 'Rua C, 789')
        self.assertEqual(result['cpf_cnpj'], '12345678000195')
        self.assertEqual(result['admin_nome'], 'Carlos')
        self.assertEqual(result['admin_email'], 'carlos@test.com')
        self.assertIsNone(result['logo'])

    def test_retorna_dados_loja_quando_sem_snapshot(self):
        doc = MagicMock()
        doc.emitente_nome = ''
        doc.loja_id = 10

        dados_loja = {'nome': 'Loja Felix', 'endereco': 'Av X', 'logo': 'logo.png'}
        with patch('crm_vendas.pdf_proposta_contrato.formatters._obter_dados_loja', return_value=dados_loja) as mock_loja:
            result = obter_dados_emitente_documento(doc)
            mock_loja.assert_called_once_with(10)
            self.assertEqual(result['nome'], 'Loja Felix')

    def test_retorna_dict_vazio_sem_loja_id(self):
        doc = MagicMock()
        doc.emitente_nome = ''
        doc.loja_id = None

        result = obter_dados_emitente_documento(doc)
        self.assertEqual(result, {})

    def test_campos_vazios_retornam_none_no_snapshot(self):
        """Campos do snapshot com string vazia viram None no resultado."""
        doc = MagicMock()
        doc.emitente_nome = 'Empresa'
        doc.emitente_endereco = ''
        doc.emitente_cpf_cnpj = ''
        doc.emitente_responsavel = ''
        doc.emitente_email = ''

        result = obter_dados_emitente_documento(doc)
        self.assertIsNone(result['endereco'])
        self.assertIsNone(result['cpf_cnpj'])
        self.assertIsNone(result['admin_nome'])
        self.assertIsNone(result['admin_email'])
