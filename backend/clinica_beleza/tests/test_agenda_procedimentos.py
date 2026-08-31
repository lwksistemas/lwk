from unittest.mock import MagicMock

from django.test import SimpleTestCase

from clinica_beleza.agenda_service import _aplicar_procedimentos
from clinica_beleza.serializers.appointments import AgendaEventSerializer


class AplicarProcedimentosTest(SimpleTestCase):
    def test_lista_vazia_remove_procedimentos(self):
        appointment = MagicMock()
        appointment.procedure_id = 4
        appointment.appointment_procedures.order_by.return_value.values_list.return_value = [4]

        changed = _aplicar_procedimentos(appointment, [])

        self.assertTrue(changed)
        appointment.appointment_procedures.all.return_value.delete.assert_called_once()
        self.assertIsNone(appointment.procedure)
        self.assertIsNone(appointment.duracao_minutos)

    def test_lista_igual_nao_altera(self):
        appointment = MagicMock()
        appointment.procedure_id = 4
        appointment.appointment_procedures.order_by.return_value.values_list.return_value = [1, 2]

        changed = _aplicar_procedimentos(appointment, [1, 2])

        self.assertFalse(changed)
        appointment.appointment_procedures.all.return_value.delete.assert_not_called()


class ProceduresListCategoriaTest(SimpleTestCase):
    def test_inclui_categoria_dos_procedimentos(self):
        proc = MagicMock(id=3, nome="BOTOX", duracao_minutos=30, preco=150, categoria="injetavel")
        linha = MagicMock(procedure_id=3, procedure=proc)
        linha.get_duracao.return_value = 30
        linha.get_valor.return_value = 150
        obj = MagicMock(procedure_id=3, procedure=proc)
        obj.appointment_procedures.all.return_value = [linha]

        data = AgendaEventSerializer().get_procedures_list(obj)

        self.assertEqual(data[0]["categoria"], "injetavel")
        self.assertEqual(data[0]["nome"], "BOTOX")
