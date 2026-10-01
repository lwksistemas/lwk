"""Testes unitários do service de dashboard."""
from datetime import date, datetime
from decimal import Decimal

from django.test import SimpleTestCase
from django.utils import timezone

from clinica_beleza.dashboard_service import (
    consulta_realizada_no_periodo_q,
    dashboard_filter_meta,
    next_appointments_limit,
    parse_dashboard_period,
    parse_next_appointments_period,
    parse_professional_id,
    procedimentos_realizados_lista,
    top_procedures_realizados_periodo,
)
from clinica_beleza.models import (
    Appointment,
    AppointmentProcedure,
    Consulta,
    Patient,
    Procedure,
    Professional,
)

from .tenant_test_case import ClinicaBelezaIntegrationTestCase


class ParseDashboardPeriodTests(SimpleTestCase):
    def test_mes_atual_termina_em_hoje(self):
        today = date(2026, 6, 20)
        start, end, mes, ano = parse_dashboard_period(mes=6, ano=2026, today=today)
        self.assertEqual(start, date(2026, 6, 1))
        self.assertEqual(end, today)
        self.assertEqual(mes, 6)
        self.assertEqual(ano, 2026)

    def test_mes_passado_usa_ultimo_dia(self):
        today = date(2026, 6, 20)
        start, end, mes, ano = parse_dashboard_period(mes=3, ano=2026, today=today)
        self.assertEqual(start, date(2026, 3, 1))
        self.assertEqual(end, date(2026, 3, 31))
        self.assertEqual(mes, 3)

    def test_mes_invalido_cai_no_mes_atual(self):
        today = date(2026, 6, 20)
        start, end, mes, ano = parse_dashboard_period(mes=99, ano=2026, today=today)
        self.assertEqual(mes, today.month)
        self.assertEqual(ano, today.year)
        self.assertEqual(start, date(2026, 6, 1))
        self.assertEqual(end, today)


class DashboardFilterMetaTests(SimpleTestCase):
    def test_label_mes_ano(self):
        meta = dashboard_filter_meta(
            filter_mes=6,
            filter_ano=2026,
            today=date(2026, 6, 15),
            period_start=date(2026, 6, 1),
            period_end=date(2026, 6, 15),
        )
        self.assertEqual(meta["label"], "Junho/2026")
        self.assertTrue(meta["is_current_month"])
        self.assertEqual(meta["period_start"], "2026-06-01")


class ConsultaRealizadaNoPeriodoTests(SimpleTestCase):
    def test_conta_pelo_dia_do_agendamento(self):
        texto = str(consulta_realizada_no_periodo_q(date(2026, 10, 1), date(2026, 10, 1)))
        self.assertIn("appointment__date__date", texto)
        self.assertNotIn("updated_at", texto)
        self.assertNotIn("data_fim", texto)


class DashboardQueryParamParsingTests(SimpleTestCase):
    def test_period_default(self):
        self.assertEqual(parse_next_appointments_period(None), "proximos")

    def test_professional_id_invalido(self):
        self.assertIsNone(parse_professional_id("abc"))

    def test_next_appointments_limit(self):
        self.assertEqual(next_appointments_limit("hoje"), 10)
        self.assertEqual(next_appointments_limit("semana"), 15)


class TopProceduresRealizadosTests(ClinicaBelezaIntegrationTestCase):
    def test_conta_todos_procedimentos_da_consulta_finalizada(self):
        patient = Patient.objects.create(nome="Paciente Dash", loja_id=self.loja.id)
        professional = Professional.objects.create(nome="Dr Dash", loja_id=self.loja.id)
        tirzepatida = Procedure.objects.create(
            nome="TIRZEPATIDA (DOSE MINIMA)",
            preco=Decimal("300.00"),
            duracao_minutos=20,
            loja_id=self.loja.id,
        )
        depilacao = Procedure.objects.create(
            nome="DEPILAÇÃO A LASER FAIXA DA BARBA",
            preco=Decimal("130.00"),
            duracao_minutos=20,
            loja_id=self.loja.id,
        )
        now = timezone.now()
        appt = Appointment.objects.create(
            date=now,
            status="COMPLETED",
            patient=patient,
            professional=professional,
            procedure=tirzepatida,
            loja_id=self.loja.id,
        )
        AppointmentProcedure.objects.create(
            appointment=appt, procedure=tirzepatida, ordem=0, valor=Decimal("300.00"), loja_id=self.loja.id,
        )
        AppointmentProcedure.objects.create(
            appointment=appt, procedure=depilacao, ordem=1, valor=Decimal("130.00"), loja_id=self.loja.id,
        )
        Consulta.objects.create(
            appointment=appt,
            patient=patient,
            professional=professional,
            procedure=tirzepatida,
            status="COMPLETED",
            data_inicio=now,
            data_fim=now,
            loja_id=self.loja.id,
        )

        today = timezone.localdate()
        rows = top_procedures_realizados_periodo(today.replace(day=1), today)
        counts = {row["name"]: row["count"] for row in rows}
        self.assertEqual(counts.get("TIRZEPATIDA (DOSE MINIMA)"), 1)
        self.assertEqual(counts.get("DEPILAÇÃO A LASER FAIXA DA BARBA"), 1)

    def test_lista_cada_procedimento_da_consulta_finalizada(self):
        patient = Patient.objects.create(nome="Paciente Lista", loja_id=self.loja.id)
        professional = Professional.objects.create(nome="Dra Lista", loja_id=self.loja.id)
        laser = Procedure.objects.create(
            nome="LASER ETHEREA",
            preco=Decimal("400.00"),
            duracao_minutos=30,
            loja_id=self.loja.id,
        )
        detox = Procedure.objects.create(
            nome="DETOX",
            preco=Decimal("250.00"),
            duracao_minutos=20,
            loja_id=self.loja.id,
        )
        now = timezone.now()
        appt = Appointment.objects.create(
            date=now,
            status="COMPLETED",
            patient=patient,
            professional=professional,
            procedure=laser,
            loja_id=self.loja.id,
        )
        AppointmentProcedure.objects.create(
            appointment=appt, procedure=laser, ordem=0, valor=Decimal("400.00"), loja_id=self.loja.id,
        )
        AppointmentProcedure.objects.create(
            appointment=appt, procedure=detox, ordem=1, valor=Decimal("250.00"), loja_id=self.loja.id,
        )
        consulta = Consulta.objects.create(
            appointment=appt,
            patient=patient,
            professional=professional,
            procedure=laser,
            status="COMPLETED",
            data_inicio=now,
            data_fim=now,
            loja_id=self.loja.id,
        )

        today = timezone.localdate()
        linhas = procedimentos_realizados_lista(today.replace(day=1), today)
        nomes = [linha["nome"] for linha in linhas]
        self.assertEqual(nomes, ["LASER ETHEREA", "DETOX"])
        self.assertTrue(all(linha["paciente"] == "Paciente Lista" for linha in linhas))
        self.assertTrue(all(linha["profissional"] == "Dra Lista" for linha in linhas))
        self.assertTrue(all(linha["consulta_id"] == consulta.id for linha in linhas))

    def test_visita_de_setembro_nao_entra_em_outubro(self):
        patient = Patient.objects.create(nome="Paciente Setembro", loja_id=self.loja.id)
        professional = Professional.objects.create(nome="Dra Setembro", loja_id=self.loja.id)
        proc = Procedure.objects.create(
            nome="TIRZEPATIDA 2,5 MG",
            preco=Decimal("300.00"),
            duracao_minutos=20,
            loja_id=self.loja.id,
        )
        visita = timezone.make_aware(datetime(2026, 9, 30, 17, 0))
        fechamento = timezone.make_aware(datetime(2026, 10, 1, 0, 4))
        appt = Appointment.objects.create(
            date=visita,
            status="COMPLETED",
            patient=patient,
            professional=professional,
            procedure=proc,
            loja_id=self.loja.id,
        )
        AppointmentProcedure.objects.create(
            appointment=appt, procedure=proc, ordem=0, valor=Decimal("300.00"), loja_id=self.loja.id,
        )
        Consulta.objects.create(
            appointment=appt,
            patient=patient,
            professional=professional,
            procedure=proc,
            status="COMPLETED",
            data_inicio=visita,
            data_fim=fechamento,
            loja_id=self.loja.id,
        )

        outubro = top_procedures_realizados_periodo(date(2026, 10, 1), date(2026, 10, 1))
        self.assertEqual(outubro, [])
        setembro = top_procedures_realizados_periodo(date(2026, 9, 1), date(2026, 9, 30))
        self.assertEqual(setembro, [{"name": "TIRZEPATIDA 2,5 MG", "count": 1}])
