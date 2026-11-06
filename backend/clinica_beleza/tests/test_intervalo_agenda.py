from django.test import SimpleTestCase
from rest_framework.exceptions import ValidationError

from clinica_beleza.serializers.professionals import ProfessionalSerializer


class IntervaloAgendaSerializerTest(SimpleTestCase):
    def test_aceita_intervalos_da_lista_e_vazio(self):
        serializer = ProfessionalSerializer()
        self.assertIsNone(serializer.validate_intervalo_agenda_minutos(None))
        self.assertEqual(serializer.validate_intervalo_agenda_minutos(30), 30)

    def test_rejeita_intervalo_fora_da_lista(self):
        serializer = ProfessionalSerializer()
        with self.assertRaises(ValidationError):
            serializer.validate_intervalo_agenda_minutos(7)
