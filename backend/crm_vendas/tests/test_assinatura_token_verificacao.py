"""Testes de verificação de token de assinatura digital."""
from datetime import timedelta
from unittest.mock import MagicMock, patch

from django.core.signing import dumps
from django.test import SimpleTestCase
from django.utils import timezone

from crm_vendas.assinatura_digital_token import (
    MSG_LINK_SUBSTITUIDO,
    _payload_assinatura_de_token,
    verificar_token_assinatura,
)


def _token_payload(*, exp=None, loja_id=4, doc_id=1, doc_type='proposta', tipo='cliente'):
    if exp is None:
        exp = int((timezone.now() + timedelta(days=1)).timestamp())
    return dumps({
        'doc_type': doc_type,
        'doc_id': doc_id,
        'tipo': tipo,
        'loja_id': loja_id,
        'exp': exp,
    })


class PayloadAssinaturaTokenTest(SimpleTestCase):
    def test_payload_valido(self):
        token = _token_payload()
        payload = _payload_assinatura_de_token(token)
        self.assertIsNotNone(payload)
        self.assertEqual(payload['loja_id'], 4)

    def test_payload_invalido(self):
        self.assertIsNone(_payload_assinatura_de_token('nao-é-token'))


class VerificarTokenAssinaturaTest(SimpleTestCase):
    def test_token_vazio(self):
        ass, err, lid, meta = verificar_token_assinatura('')
        self.assertIsNone(ass)
        self.assertIn('inválido', (err or '').lower())
        self.assertEqual(meta.get('error_code'), 'invalido')

    def test_token_expirado(self):
        token = _token_payload(exp=int((timezone.now() - timedelta(days=1)).timestamp()))
        ass, err, lid, meta = verificar_token_assinatura(token, loja_id=4)
        self.assertIsNone(ass)
        self.assertIn('expirou', (err or '').lower())
        self.assertEqual(meta.get('error_code'), 'expirado')

    def test_loja_id_divergente(self):
        token = _token_payload(loja_id=4)
        ass, err, lid, meta = verificar_token_assinatura(token, loja_id=99)
        self.assertIsNone(ass)
        self.assertEqual(meta.get('error_code'), 'invalido')

    @patch('crm_vendas.assinatura_digital_token._documento_aguarda_assinatura', return_value=True)
    @patch('crm_vendas.assinatura_digital_token._buscar_assinatura_pendente_por_payload', return_value=None)
    @patch('crm_vendas.models.AssinaturaDigital')
    def test_link_substituido_quando_doc_aguarda(self, mock_cls, _buscar, _aguarda):
        class DoesNotExist(Exception):
            pass

        mock_cls.DoesNotExist = DoesNotExist
        mock_cls.objects.select_related.return_value.get.side_effect = DoesNotExist()
        token = _token_payload()
        ass, err, lid, meta = verificar_token_assinatura(token, loja_id=4)
        self.assertIsNone(ass)
        self.assertEqual(err, MSG_LINK_SUBSTITUIDO)
        self.assertEqual(meta.get('error_code'), 'link_substituido')

    @patch('crm_vendas.models.AssinaturaDigital')
    def test_token_encontrado_no_banco(self, mock_cls):
        assinatura = MagicMock()
        assinatura.assinado = False
        assinatura.is_expirado.return_value = False
        assinatura.documento = MagicMock()
        mock_cls.objects.select_related.return_value.get.return_value = assinatura
        mock_cls.DoesNotExist = type('DoesNotExist', (Exception,), {})

        token = _token_payload()
        ass, err, lid, meta = verificar_token_assinatura(token, loja_id=4)
        self.assertIs(ass, assinatura)
        self.assertIsNone(err)

    @patch('crm_vendas.models.AssinaturaDigital')
    def test_documento_ja_assinado(self, mock_cls):
        assinatura = MagicMock()
        assinatura.assinado = True
        mock_cls.objects.select_related.return_value.get.return_value = assinatura
        mock_cls.DoesNotExist = type('DoesNotExist', (Exception,), {})

        token = _token_payload()
        ass, err, lid, meta = verificar_token_assinatura(token, loja_id=4)
        self.assertIsNone(ass)
        self.assertIn('assinado', (err or '').lower())
