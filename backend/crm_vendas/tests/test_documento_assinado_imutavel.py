"""Documento assinado pelas duas partes não aceita alteração."""
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase
from rest_framework.exceptions import ValidationError

from clinica_beleza.consentimento_service import congelar_termo_assinado
from crm_vendas.serializers.documentos import ContratoSerializer, PropostaSerializer


class DocumentoAssinadoImutavelTest(SimpleTestCase):
    def test_proposta_assinada_recusa_alteracao(self):
        proposta = MagicMock(status_assinatura="concluido")
        with self.assertRaises(ValidationError):
            PropostaSerializer().update(proposta, {"titulo": "Outro título"})

    def test_contrato_assinado_recusa_alteracao(self):
        contrato = MagicMock(status_assinatura="concluido")
        with self.assertRaises(ValidationError):
            ContratoSerializer().update(contrato, {"titulo": "Outro título"})

    @patch("clinica_beleza.termos_consentimento_service.template_do_procedimento", return_value=None)
    def test_termo_assinado_guarda_o_texto_e_ignora_mudanca_depois(self, _tpl):
        termo = MagicMock()
        termo.procedure = None
        termo.consulta = MagicMock()
        termo.conteudo_termo = "Texto que as duas partes assinaram"
        termo.respostas_interativo = {}
        termo.status_assinatura_termo = "concluido"

        texto = congelar_termo_assinado(termo)

        self.assertEqual(texto, "Texto que as duas partes assinaram")
        termo.conteudo_termo = "Texto alterado depois da assinatura"
        self.assertEqual(congelar_termo_assinado(termo), "Texto que as duas partes assinaram")
