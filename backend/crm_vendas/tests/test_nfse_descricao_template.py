from types import SimpleNamespace

from django.test import SimpleTestCase
from rest_framework.exceptions import ValidationError

from crm_vendas.serializers.config import CRMConfigSerializer
from crm_vendas.serializers.documentos import NfseDescricaoTemplateSerializer


class NfseDescricaoTemplateSerializerTest(SimpleTestCase):
    def test_template_novo_exige_prestadora(self):
        serializer = NfseDescricaoTemplateSerializer()
        with self.assertRaises(ValidationError):
            serializer.validate({})

    def test_nao_aceita_tirar_a_prestadora(self):
        serializer = NfseDescricaoTemplateSerializer()
        serializer.instance = SimpleNamespace(id=1)
        with self.assertRaises(ValidationError):
            serializer.validate({"prestadora": None})

    def test_mostra_a_razao_social_da_prestadora(self):
        template = SimpleNamespace(
            prestadora=SimpleNamespace(
                nome="ULTRASIS",
                razao_social="ULTRASIS INFORMATICA LTDA",
                cnpj="12.345.678/0001-90",
            ),
        )
        self.assertEqual(
            NfseDescricaoTemplateSerializer().get_prestadora_nome(template),
            "ULTRASIS INFORMATICA LTDA",
        )

    def test_texto_de_reserva_pode_ficar_vazio(self):
        field = CRMConfigSerializer().fields["descricao_servico_padrao"]
        self.assertEqual(field.run_validation(""), "")

    def test_sem_prestadora_fica_vazio(self):
        self.assertIsNone(
            NfseDescricaoTemplateSerializer().get_prestadora_nome(SimpleNamespace(prestadora=None)),
        )
