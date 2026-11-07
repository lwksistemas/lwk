"""Relatório de NFS-e emitidas: uma empresa ou o total."""
from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase
from django.utils import timezone

from crm_vendas.relatorios_nfse_pdf import agrupar_notas_por_empresa, gerar_pdf_nfse_emitidas


def _conta(conta_id, nome, cnpj, tipo="prestadora"):
    return SimpleNamespace(id=conta_id, nome=nome, razao_social=nome, cnpj=cnpj, tipo=tipo)


def _nota(numero, tomador, documento, valor, quando=None):
    return SimpleNamespace(
        numero_nf=numero,
        numero_rps=numero,
        tomador_nome=tomador,
        tomador_cpf_cnpj=documento,
        valor=Decimal(valor),
        data_emissao=quando or timezone.make_aware(datetime(2026, 11, 2, 10, 0)),
    )


class AgruparNotasNfseTests(SimpleTestCase):
    def setUp(self):
        self.ultrasys = _conta(1, "ULTRASIS", "12.345.678/0001-90")
        self.anadem = _conta(2, "ANADEM", "98.765.432/0001-10")
        self.cliente = _conta(3, "CLIENTE", "11.111.111/0001-11", tipo="cliente")
        self.notas = [
            _nota("10", "ULTRASIS", "12345678000190", "100.00"),
            _nota("11", "ULTRASIS INFORMATICA", "12.345.678/0001-90", "50.50"),
            _nota("12", "ANADEM", "98765432000110", "20.00"),
            _nota("13", "Pessoa avulsa", "12345678901", "7.00"),
        ]

    def test_total_agrupa_pelo_cnpj_da_prestadora(self):
        grupos = agrupar_notas_por_empresa(self.notas, [self.ultrasys, self.anadem, self.cliente])
        por_nome = {grupo["nome"]: grupo for grupo in grupos}
        self.assertEqual(len(por_nome["ULTRASIS"]["notas"]), 2)
        self.assertEqual(por_nome["ULTRASIS"]["total"], Decimal("150.50"))
        self.assertEqual(len(por_nome["ANADEM"]["notas"]), 1)
        self.assertEqual(por_nome["Pessoa avulsa"]["total"], Decimal("7.00"))
        self.assertNotIn("CLIENTE", por_nome)

    def test_uma_empresa_traz_so_as_notas_dela(self):
        grupos = agrupar_notas_por_empresa(self.notas, [self.ultrasys, self.anadem], 2)
        self.assertEqual(len(grupos), 1)
        self.assertEqual(grupos[0]["nome"], "ANADEM")
        self.assertEqual(len(grupos[0]["notas"]), 1)
        self.assertEqual(grupos[0]["total"], Decimal("20.00"))

    def test_empresa_sem_nota_no_periodo_fica_vazia(self):
        grupos = agrupar_notas_por_empresa([], [self.ultrasys], 1)
        self.assertEqual(grupos[0]["notas"], [])
        self.assertEqual(grupos[0]["total"], Decimal("0"))

    def test_pdf_sai_com_e_sem_nota(self):
        inicio = timezone.now().date().replace(day=1)
        fim = timezone.now().date()
        with patch("crm_vendas.relatorios_nfse_pdf._obter_logo_loja", return_value=None):
            vazio = gerar_pdf_nfse_emitidas(4, [], inicio, fim)
            cheio = gerar_pdf_nfse_emitidas(
                4,
                agrupar_notas_por_empresa(self.notas, [self.ultrasys, self.anadem]),
                inicio,
                fim,
                canceladas=2,
            )
        self.assertTrue(vazio.read().startswith(b"%PDF"))
        self.assertTrue(cheio.read().startswith(b"%PDF"))
