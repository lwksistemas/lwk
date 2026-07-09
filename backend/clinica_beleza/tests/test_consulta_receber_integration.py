"""Integração — POST /consultas/<id>/receber/ (total, parcial, procedimento extra)."""
from decimal import Decimal

from django.utils import timezone

from clinica_beleza.consulta_service import registrar_recebimento_consulta
from clinica_beleza.consulta_service.payment import _sincronizar_recebimento_apos_procedimento
from clinica_beleza.models import Appointment, Consulta, Patient, Payment, Professional

from .tenant_test_case import ClinicaBelezaIntegrationTestCase


class ConsultaReceberIntegrationTests(ClinicaBelezaIntegrationTestCase):
    def _criar_consulta_receber(self, *, valor=Decimal('200.00')):
        patient = Patient.objects.create(nome='Paciente Receber', loja_id=self.loja.id)
        professional = Professional.objects.create(nome='Dr. Receber', loja_id=self.loja.id)
        appt = Appointment.objects.create(
            date=timezone.now(),
            status='CONFIRMED',
            patient=patient,
            professional=professional,
            loja_id=self.loja.id,
        )
        consulta = Consulta.objects.create(
            appointment=appt,
            patient=patient,
            professional=professional,
            status='RECEBER',
            valor_consulta=valor,
            loja_id=self.loja.id,
        )
        return consulta

    def test_api_receber_total_vai_para_scheduled(self):
        consulta = self._criar_consulta_receber()
        client = self.api_client_as_owner()
        response = client.post(
            f'/api/clinica-beleza/consultas/{consulta.id}/receber/',
            {'payment_method': 'PIX', 'amount': '200', 'mark_as_paid': True},
            format='json',
            **self.tenant_headers(),
        )
        self.assertEqual(response.status_code, 201, response.content)
        body = response.json()
        self.assertEqual(body['payment']['status'], 'PAID')
        self.assertEqual(body['consulta']['status'], 'SCHEDULED')

        consulta.refresh_from_db()
        self.assertEqual(consulta.status, 'SCHEDULED')
        payment = Payment.objects.get(appointment=consulta.appointment)
        self.assertEqual(payment.status, 'PAID')
        self.assertTrue(payment.parcelas.exists())
        self.assertEqual(payment.saldo_devedor, Decimal('0'))

    def test_api_receber_parcial_mantem_receber(self):
        consulta = self._criar_consulta_receber()
        client = self.api_client_as_owner()
        response = client.post(
            f'/api/clinica-beleza/consultas/{consulta.id}/receber/',
            {'payment_method': 'CASH', 'amount': '80', 'mark_as_paid': False},
            format='json',
            **self.tenant_headers(),
        )
        self.assertEqual(response.status_code, 201, response.content)
        body = response.json()
        self.assertEqual(body['payment']['status'], 'PARTIAL')
        self.assertEqual(body['consulta']['status'], 'RECEBER')

        consulta.refresh_from_db()
        self.assertEqual(consulta.status, 'RECEBER')

    def test_procedimento_extra_reabre_receber(self):
        consulta = self._criar_consulta_receber(valor=Decimal('100.00'))
        registrar_recebimento_consulta(
            consulta,
            payment_method='CASH',
            amount=Decimal('100'),
            mark_as_paid=True,
        )
        consulta.refresh_from_db()
        self.assertEqual(consulta.status, 'SCHEDULED')

        # Simula aumento do total (procedimento extra) via valor_consulta
        consulta.valor_consulta = Decimal('180.00')
        consulta.save(update_fields=['valor_consulta', 'updated_at'])
        _sincronizar_recebimento_apos_procedimento(consulta)

        consulta.refresh_from_db()
        self.assertEqual(consulta.status, 'RECEBER')
        payment = Payment.objects.get(appointment=consulta.appointment)
        self.assertEqual(payment.status, 'PARTIAL')
        self.assertGreater(payment.saldo_devedor, Decimal('0'))
