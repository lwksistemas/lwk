"""Isolamento de orçamento entre lojas e PATCH/DELETE de status."""
from decimal import Decimal

from django.utils import timezone

from clinica_beleza.models import (
    Appointment,
    Consulta,
    ConsultaProdutoUtilizado,
    Patient,
    Procedure,
    ProdutoEstoque,
    Professional,
)
from clinica_beleza.models.orcamento import OrcamentoConsulta

from .tenant_test_case import ClinicaBelezaIntegrationTestCase


class OrcamentoIsolamentoTest(ClinicaBelezaIntegrationTestCase):
    def _criar_consulta_e_procedimento(self, loja):
        self.activate_loja(loja)
        patient = Patient.objects.create(nome="Paciente Orc", loja_id=loja.id)
        professional = Professional.objects.create(nome="Dr Orc", loja_id=loja.id)
        appt = Appointment.objects.create(
            date=timezone.now(),
            status="IN_PROGRESS",
            patient=patient,
            professional=professional,
            loja_id=loja.id,
        )
        consulta = Consulta.objects.create(
            appointment=appt,
            patient=patient,
            professional=professional,
            status="IN_PROGRESS",
            data_inicio=timezone.now(),
            loja_id=loja.id,
        )
        procedure = Procedure.objects.create(
            nome="Peeling",
            preco=Decimal("200.00"),
            duracao_minutos=30,
            loja_id=loja.id,
        )
        return consulta, procedure

    def test_loja_b_nao_acessa_orcamento_da_loja_a(self):
        consulta, procedure = self._criar_consulta_e_procedimento(self.loja)
        client = self.api_client_as_owner()
        created = client.post(
            "/api/clinica-beleza/orcamentos/",
            {
                "consulta_id": consulta.id,
                "itens": [{"procedure_id": procedure.id, "quantidade": 1, "valor_customizado": "200.00"}],
            },
            format="json",
            **self.tenant_headers(self.loja),
        )
        self.assertEqual(created.status_code, 201, created.content)
        orcamento_id = created.json()["id"]

        pdf_b = client.get(
            f"/api/clinica-beleza/orcamentos/{orcamento_id}/pdf/",
            **self.tenant_headers(self.loja_b),
        )
        self.assertEqual(pdf_b.status_code, 404)

        patch_b = client.patch(
            f"/api/clinica-beleza/orcamentos/{orcamento_id}/",
            {"status": "ACEITO"},
            format="json",
            **self.tenant_headers(self.loja_b),
        )
        self.assertEqual(patch_b.status_code, 404)

        lista_b = client.get(
            f"/api/clinica-beleza/orcamentos/?consulta_id={consulta.id}",
            **self.tenant_headers(self.loja_b),
        )
        self.assertEqual(lista_b.status_code, 200, lista_b.content)
        self.assertEqual(lista_b.json(), [])

        self.activate_loja(self.loja)
        self.assertEqual(OrcamentoConsulta.objects.filter(pk=orcamento_id).count(), 1)

    def test_patch_aceito_e_delete_bloqueado(self):
        consulta, procedure = self._criar_consulta_e_procedimento(self.loja)
        client = self.api_client_as_owner()
        created = client.post(
            "/api/clinica-beleza/orcamentos/",
            {
                "consulta_id": consulta.id,
                "itens": [{"procedure_id": procedure.id, "quantidade": 1}],
            },
            format="json",
            **self.tenant_headers(),
        )
        self.assertEqual(created.status_code, 201, created.content)
        orcamento_id = created.json()["id"]

        recusado_enviado = client.patch(
            f"/api/clinica-beleza/orcamentos/{orcamento_id}/",
            {"status": "ENVIADO"},
            format="json",
            **self.tenant_headers(),
        )
        self.assertEqual(recusado_enviado.status_code, 400)

        aceito = client.patch(
            f"/api/clinica-beleza/orcamentos/{orcamento_id}/",
            {"status": "ACEITO"},
            format="json",
            **self.tenant_headers(),
        )
        self.assertEqual(aceito.status_code, 200, aceito.content)
        self.assertEqual(aceito.json()["status"], "ACEITO")

        deleted = client.delete(
            f"/api/clinica-beleza/orcamentos/{orcamento_id}/",
            **self.tenant_headers(),
        )
        self.assertEqual(deleted.status_code, 400)


class ConsultaProdutoIdorTest(ClinicaBelezaIntegrationTestCase):
    def test_delete_produto_de_outra_consulta_404(self):
        self.activate_loja(self.loja)
        patient = Patient.objects.create(nome="Paciente Prod", loja_id=self.loja.id)
        professional = Professional.objects.create(nome="Dr Prod", loja_id=self.loja.id)
        produto = ProdutoEstoque.objects.create(nome="Toxina", loja_id=self.loja.id)

        def _consulta():
            appt = Appointment.objects.create(
                date=timezone.now(),
                status="IN_PROGRESS",
                patient=patient,
                professional=professional,
                loja_id=self.loja.id,
            )
            return Consulta.objects.create(
                appointment=appt,
                patient=patient,
                professional=professional,
                status="IN_PROGRESS",
                data_inicio=timezone.now(),
                loja_id=self.loja.id,
            )

        consulta_a = _consulta()
        consulta_b = _consulta()
        item = ConsultaProdutoUtilizado.objects.create(
            consulta=consulta_a,
            produto=produto,
            quantidade=Decimal("1"),
            loja_id=self.loja.id,
        )

        client = self.api_client_as_owner()
        resp = client.delete(
            f"/api/clinica-beleza/consultas/{consulta_b.id}/produtos/{item.id}/",
            **self.tenant_headers(),
        )
        self.assertEqual(resp.status_code, 404)
        self.assertTrue(ConsultaProdutoUtilizado.objects.filter(pk=item.id).exists())
