"""Testes de validação de envio de campanhas."""

from datetime import timedelta
from unittest import TestCase
from unittest.mock import MagicMock

from django.utils import timezone

from clinica_beleza.views_whatsapp import _validar_campanha_para_envio


class CampanhaValidacaoTest(TestCase):
    def _campanha(self, **kwargs):
        c = MagicMock()
        c.ativa = kwargs.get('ativa', True)
        c.data_inicio = kwargs.get('data_inicio')
        c.data_fim = kwargs.get('data_fim')
        c.mensagem = kwargs.get('mensagem', 'Promoção válida')
        return c

    def test_rejeita_inativa(self):
        err = _validar_campanha_para_envio(self._campanha(ativa=False))
        self.assertIn('inativa', err or '')

    def test_rejeita_antes_da_vigencia(self):
        amanha = timezone.localdate() + timedelta(days=1)
        err = _validar_campanha_para_envio(self._campanha(data_inicio=amanha))
        self.assertIn('a partir', err or '')

    def test_rejeita_apos_vigencia(self):
        ontem = timezone.localdate() - timedelta(days=1)
        err = _validar_campanha_para_envio(self._campanha(data_fim=ontem))
        self.assertIn('expirou', err or '')

    def test_aceita_campanha_valida(self):
        hoje = timezone.localdate()
        err = _validar_campanha_para_envio(
            self._campanha(data_inicio=hoje - timedelta(days=1), data_fim=hoje + timedelta(days=1))
        )
        self.assertIsNone(err)

    def test_rejeita_mensagem_vazia(self):
        err = _validar_campanha_para_envio(self._campanha(mensagem='   '))
        self.assertIn('vazia', err or '')
