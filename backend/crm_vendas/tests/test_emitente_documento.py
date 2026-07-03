"""Testes do snapshot de emitente em proposta/contrato."""
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from crm_vendas.emitente_documento import (
    documento_tem_emitente_personalizado,
    limpar_emitente_se_vazio,
    obter_dados_emitente_documento,
)


class EmitenteDocumentoTest(SimpleTestCase):
    def test_sem_personalizacao_usa_loja(self):
        doc = MagicMock()
        doc.emitente_nome = ''
        doc.loja_id = 7
        with patch(
            'crm_vendas.pdf_proposta_contrato.formatters._obter_dados_loja',
            return_value={'nome': 'Loja Felix', 'logo': 'http://x/logo.png'},
        ):
            data = obter_dados_emitente_documento(doc)
        self.assertEqual(data['nome'], 'Loja Felix')
        self.assertFalse(documento_tem_emitente_personalizado(doc))

    def test_com_personalizacao_usa_snapshot(self):
        doc = MagicMock()
        doc.emitente_nome = 'Empresa Parceira'
        doc.emitente_endereco = 'Rua B, 10'
        doc.emitente_cpf_cnpj = '12.345.678/0001-90'
        doc.emitente_responsavel = 'João'
        doc.emitente_email = 'joao@exemplo.com'
        doc.loja_id = 7
        data = obter_dados_emitente_documento(doc)
        self.assertEqual(data['nome'], 'Empresa Parceira')
        self.assertEqual(data['admin_nome'], 'João')
        self.assertTrue(documento_tem_emitente_personalizado(doc))

    def test_limpar_emitente_quando_nome_vazio(self):
        attrs = {
            'emitente_nome': '  ',
            'emitente_endereco': 'x',
            'emitente_cpf_cnpj': '1',
            'emitente_responsavel': 'a',
            'emitente_email': 'b@c.com',
        }
        out = limpar_emitente_se_vazio(attrs)
        self.assertEqual(out['emitente_nome'], '')
        self.assertEqual(out['emitente_endereco'], '')
