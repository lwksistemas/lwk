from types import SimpleNamespace

from django.test import SimpleTestCase

from crm_vendas.serializers.documentos import PropostaSerializer


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

    def test_sem_prestadora_fica_vazio(self):
        proposta = SimpleNamespace(
            oportunidade=SimpleNamespace(empresa_prestadora_id=None),
        )
        self.assertIsNone(PropostaSerializer().get_prestador_nome(proposta))
