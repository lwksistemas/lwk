"""Busca de pacientes: nome por trecho e CPF com/sem pontuação."""
from django.test import SimpleTestCase

from clinica_beleza.models import Patient
from clinica_beleza.patient_search import apply_patient_search, digits_only, patient_search_rank
from clinica_beleza.tests.tenant_test_case import ClinicaBelezaIntegrationTestCase


class PatientSearchRankTest(SimpleTestCase):
    def test_prioriza_nome_que_comeca_com_o_termo(self):
        self.assertEqual(patient_search_rank("RENATA AMICCI", "renata"), 0)
        self.assertEqual(patient_search_rank("ELISETE PRIMA RENATA CLIENTE", "renata"), 1)
        self.assertEqual(patient_search_rank("LUIZ BOM", "luiz"), 0)
        self.assertEqual(patient_search_rank("ANA LUIZA JUSTINO", "luiz"), 1)


class PatientSearchTest(ClinicaBelezaIntegrationTestCase):
    def setUp(self):
        super().setUp()
        self.patient = Patient.objects.create(
            nome="MARIA SILVA SANTOS",
            telefone="11988887777",
            cpf="123.456.789-00",
            email="maria@exemplo.com",
            loja_id=self.loja.id,
        )
        Patient.objects.create(
            nome="JOAO PEREIRA",
            telefone="11911112222",
            cpf="987.654.321-00",
            loja_id=self.loja.id,
        )

    def _buscar(self, termo):
        return list(apply_patient_search(Patient.objects.all(), termo).values_list("nome", flat=True))

    def test_nome_por_sobrenome(self):
        self.assertIn("MARIA SILVA SANTOS", self._buscar("silva"))
        self.assertIn("MARIA SILVA SANTOS", self._buscar("MARIA"))

    def test_cpf_com_e_sem_ponto(self):
        self.assertEqual(self._buscar("123.456.789-00"), ["MARIA SILVA SANTOS"])
        self.assertEqual(self._buscar("12345678900"), ["MARIA SILVA SANTOS"])
        self.assertEqual(self._buscar("123.456"), ["MARIA SILVA SANTOS"])
        self.assertEqual(self._buscar("123456"), ["MARIA SILVA SANTOS"])

    def test_cpf_nao_confunde_outro_paciente(self):
        self.assertEqual(self._buscar("987.654.321-00"), ["JOAO PEREIRA"])
        self.assertEqual(self._buscar("98765432100"), ["JOAO PEREIRA"])

    def test_digits_only(self):
        self.assertEqual(digits_only("123.456.789-00"), "12345678900")
        self.assertEqual(digits_only("12345678900"), "12345678900")

    def test_busca_ordena_quem_comeca_com_o_termo(self):
        Patient.objects.create(nome="SILVA COSTA", loja_id=self.loja.id)
        nomes = self._buscar("silva")
        self.assertEqual(nomes[0], "SILVA COSTA")
        self.assertIn("MARIA SILVA SANTOS", nomes)
