from types import SimpleNamespace

from django.test import SimpleTestCase
from rest_framework.exceptions import ValidationError

from crm_vendas.serializers.documentos import PropostaSerializer, PropostaTemplateSerializer


class PrestadorNomePropostaTest(SimpleTestCase):
    def test_devolve_o_nome_da_empresa_prestadora(self):
        proposta = SimpleNamespace(
            oportunidade=SimpleNamespace(
                empresa_prestadora_id=3,
                empresa_prestadora=SimpleNamespace(nome="ULTRASIS INFORMATICA LTDA"),
            ),
        )
        self.assertEqual(
            PropostaSerializer().get_prestador_nome(proposta),
            "ULTRASIS INFORMATICA LTDA",
        )

    def test_template_novo_exige_prestadora(self):
        serializer = PropostaTemplateSerializer()
        with self.assertRaises(ValidationError):
            serializer.validate({})

    def test_template_mostra_a_razao_social_da_prestadora(self):
        template = SimpleNamespace(
            prestadora=SimpleNamespace(
                nome="ULTRASIS",
                razao_social="ULTRASIS INFORMATICA LTDA",
                cnpj="12.345.678/0001-90",
            ),
        )
        self.assertEqual(
            PropostaTemplateSerializer().get_prestadora_nome(template),
            "ULTRASIS INFORMATICA LTDA",
        )

    def test_sem_prestadora_fica_vazio(self):
        proposta = SimpleNamespace(
            oportunidade=SimpleNamespace(empresa_prestadora_id=None),
        )
        self.assertIsNone(PropostaSerializer().get_prestador_nome(proposta))
