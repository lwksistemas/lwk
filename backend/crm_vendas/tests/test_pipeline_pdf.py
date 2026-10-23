"""PDF do pipeline usa o cabeçalho da proposta e a razão social da prestadora."""
from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase


def _oportunidade(**extras):
    prestadora = extras.pop(
        "prestadora",
        SimpleNamespace(
            nome="ULTRASIS",
            razao_social="ULTRASIS INFORMATICA LTDA",
            cnpj="00000000000191",
            logo="https://media.example/ultrasys.png",
        ),
    )
    base = dict(
        id=1,
        lead=SimpleNamespace(nome="MARCELO ZUCHETTO KRUMEL"),
        titulo="ULTRASIS INFORMATICA LTDA",
        empresa_prestadora=prestadora,
        vendedor=SimpleNamespace(nome="LUIZ HENRIQUE FELIX"),
        valor=Decimal("1574.00"),
        etapa="prospecting",
        valor_comissao=Decimal("750.00"),
        data_fechamento_ganho=None,
        data_fechamento=None,
        data_fechamento_perdido=None,
        created_at=None,
    )
    base.update(extras)
    return SimpleNamespace(**base)


ETAPAS = [
    ("prospecting", "Prospecção"),
    ("proposal", "Proposta"),
    ("closed_won", "Fechado (ganho)"),
]


class PipelinePdfTests(SimpleTestCase):
    def test_prestadora_com_cnpj_usa_razao_social(self):
        from crm_vendas.relatorios_pipeline_pdf import _nome_prestadora

        self.assertEqual(_nome_prestadora(_oportunidade()), "ULTRASIS INFORMATICA LTDA")

    @patch("crm_vendas.pdf_proposta_contrato.sections._build_cabecalho")
    def test_uma_prestadora_leva_as_duas_logos(self, mock_cabecalho):
        from crm_vendas.relatorios_pipeline_pdf import gerar_pdf_pipeline

        loja = SimpleNamespace(logo="https://media.example/felix.png", login_logo="https://media.example/login.png")
        pdf = gerar_pdf_pipeline(
            [_oportunidade()],
            loja,
            data_inicio="2026-09-01",
            data_fim="2026-09-30",
            etapas=ETAPAS,
        )
        self.assertTrue(pdf.startswith(b"%PDF"))
        args = mock_cabecalho.call_args.args
        self.assertEqual(args[1], "https://media.example/felix.png")
        self.assertEqual(args[2], "PIPELINE DE VENDAS")
        self.assertEqual(args[3], "https://media.example/ultrasys.png")

    @patch("crm_vendas.pdf_proposta_contrato.sections._build_cabecalho")
    def test_prestadoras_diferentes_usam_a_logo_de_login(self, mock_cabecalho):
        from crm_vendas.relatorios_pipeline_pdf import gerar_pdf_pipeline

        outra = SimpleNamespace(
            nome="ANADEM",
            razao_social="ANADEM LTDA",
            cnpj="11111111000111",
            logo="https://media.example/anadem.png",
        )
        loja = SimpleNamespace(logo="https://media.example/felix.png", login_logo="https://media.example/login.png")
        gerar_pdf_pipeline(
            [
                _oportunidade(),
                _oportunidade(id=2, prestadora=outra, etapa="closed_won", data_fechamento_ganho=date(2026, 9, 10)),
            ],
            loja,
            etapas=ETAPAS,
        )
        self.assertEqual(mock_cabecalho.call_args.args[3], "https://media.example/login.png")

    def test_pdf_sem_logo_ainda_abre(self):
        from crm_vendas.relatorios_pipeline_pdf import gerar_pdf_pipeline

        loja = SimpleNamespace(logo="", login_logo="")
        pdf = gerar_pdf_pipeline([], loja, etapas=ETAPAS)
        self.assertTrue(pdf.startswith(b"%PDF"))
