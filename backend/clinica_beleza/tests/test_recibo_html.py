"""Cupom HTML do recibo usa o mesmo contexto do PDF."""
from unittest.mock import MagicMock

from django.test import SimpleTestCase

from clinica_beleza.recibo.context import _buscar_procedimentos_recibo
from clinica_beleza.recibo.html import gerar_html_recibo


class GerarHtmlReciboTests(SimpleTestCase):
    def _ctx(self, **overrides):
        base = {
            "loja_nome": "HARMONIS",
            "loja_cnpj": "37302743000126",
            "loja_endereco": "Rua A, 1",
            "loja_telefone": "1633330000",
            "loja_email": "a@b.com",
            "loja_cep": "14000000",
            "paciente_nome": "Maria Silva",
            "profissional_nome": "Dra. Ana",
            "data_emissao": "20/09/2026 15:00",
            "data": "20/09/2026 14:00",
            "data_atendimento": "20/09/2026 14:00",
            "procedimentos": [{"nome": "CRIOGENIA", "valor": 200.0}],
            "taxa_consulta": 150.0,
            "desconto": 0.0,
            "desconto_retorno": 0.0,
            "retorno_gratuito": False,
            "subtotal": 350.0,
            "valor_total": 350.0,
            "valor_pago": 350.0,
            "saldo_devedor": 0.0,
            "vencimento": "",
            "metodo": "Dinheiro",
            "formas_pagamento": [{"metodo": "Dinheiro (20/09/2026)", "valor": 350.0}],
            "retorno_aviso": "",
        }
        base.update(overrides)
        return base

    def test_mostra_desconto_retorno_sem_prazo(self):
        html = gerar_html_recibo(
            self._ctx(
                retorno_gratuito=True,
                taxa_consulta=0.0,
                taxa_consulta_referencia=150.0,
                desconto_retorno=150.0,
                subtotal=350.0,
                valor_total=200.0,
                valor_pago=200.0,
            ),
        )
        self.assertNotIn("Desconto retorno", html)
        self.assertNotIn("Taxa de avaliação", html)
        self.assertNotIn("prazo", html)

    def test_escapa_html_do_nome(self):
        html = gerar_html_recibo(self._ctx(paciente_nome="<img src=x>"))
        self.assertIn("&lt;img src=x&gt;", html)
        self.assertNotIn("<img src=x>", html)

    def test_retorno_sem_valor_lista_procedimento_e_isento(self):
        html = gerar_html_recibo(
            self._ctx(
                retorno_gratuito=True,
                taxa_consulta=0.0,
                taxa_consulta_referencia=150.0,
                desconto_retorno=150.0,
                desconto=0.0,
                procedimentos=[{"nome": "LASER ETHEREA", "valor": 0.0}],
                subtotal=150.0,
                valor_total=0.0,
                valor_pago=0.0,
                saldo_devedor=0.0,
                formas_pagamento=[],
                metodo="",
            ),
        )
        self.assertIn("COMPROVANTE DE ATENDIMENTO", html)
        self.assertIn("Sem valor a pagar", html)
        self.assertNotIn("Sem saldo", html)
        self.assertNotIn("integralmente descontada", html)
        self.assertIn("Laser etherea", html)
        self.assertNotIn("Quitado", html)
        self.assertNotIn("Isento — retorno", html)
        self.assertNotIn("Desconto retorno", html)
        self.assertNotIn("Taxa de avaliação", html)
        self.assertNotIn(">Desconto<", html)

    def test_quitado_quando_sem_saldo(self):
        html = gerar_html_recibo(self._ctx())
        self.assertIn("Quitado", html)
        self.assertIn("RECIBO DE PAGAMENTO", html)

    def test_so_consulta_mostra_servico_local_e_convenio(self):
        html = gerar_html_recibo(
            self._ctx(
                procedimentos=[{"nome": "Consulta", "valor": 0.0}],
                taxa_consulta=0.0,
                subtotal=0.0,
                valor_total=0.0,
                valor_pago=0.0,
                saldo_devedor=0.0,
                formas_pagamento=[],
                metodo="",
                local_nome="CONSULTÓRIO",
                convenio_nome="PARTICULAR",
            ),
        )
        self.assertIn("Consulta", html)
        self.assertNotIn("Local", html)
        self.assertNotIn("CONSULTÓRIO", html)
        self.assertIn("Convênio PARTICULAR", html)

    def test_so_consulta_sem_retorno_usa_taxa_do_local(self):
        html = gerar_html_recibo(
            self._ctx(
                procedimentos=[{"nome": "Consulta", "valor": 0.0}],
                taxa_consulta=0.0,
                taxa_consulta_referencia=150.0,
                retorno_gratuito=False,
                subtotal=0.0,
                valor_total=0.0,
                valor_pago=0.0,
                saldo_devedor=0.0,
                formas_pagamento=[],
                metodo="",
            ),
        )
        self.assertIn("Taxa de avaliação", html)
        self.assertIn("150,00", html)
        self.assertNotIn("Desconto retorno", html)
        self.assertIn("SALDO A PAGAR", html)

    def test_procedimento_sem_retorno_mostra_taxa_do_local(self):
        html = gerar_html_recibo(
            self._ctx(
                procedimentos=[{"nome": "TIRZEPATIDA 2,5 MG", "valor": 150.0}],
                taxa_consulta=0.0,
                taxa_consulta_referencia=150.0,
                retorno_gratuito=False,
                subtotal=150.0,
                valor_total=300.0,
                valor_pago=300.0,
                desconto=0.0,
                formas_pagamento=[{"metodo": "Dinheiro (20/09/2026)", "valor": 300.0}],
            ),
        )
        self.assertIn("Taxa de avaliação", html)
        self.assertIn("Tirzepatida — 2,5 mg", html)
        self.assertIn("R$ 150,00", html)
        self.assertIn("R$ 300,00", html)
        self.assertNotIn("Desconto retorno", html)

    def test_procedimento_com_valor_nao_repete_local(self):
        html = gerar_html_recibo(
            self._ctx(local_nome="CONSULTÓRIO", convenio_nome="PARTICULAR"),
        )
        self.assertIn("Criogenia", html)
        self.assertNotIn(">Local<", html)
        self.assertNotIn("CONSULTÓRIO", html)

    def test_custeio_da_clinica_nao_parece_pagamento_do_cliente(self):
        html = gerar_html_recibo(
            self._ctx(
                metodo="Despesa (clínica)",
                formas_pagamento=[{"metodo": "Despesa (clínica) (18/09/2026)", "valor": 350.0}],
            ),
        )
        self.assertIn("COMPROVANTE DE ATENDIMENTO", html)
        self.assertIn("Custeado pela clínica", html)
        self.assertNotIn("RECIBO DE PAGAMENTO", html)
        self.assertNotIn("VALOR PAGO", html)
        self.assertNotIn("Quitado", html)
        self.assertNotIn("Despesa (clínica)", html)

    def test_saldo_sem_data_informa_que_nao_ha_vencimento(self):
        html = gerar_html_recibo(
            self._ctx(
                valor_pago=190.0,
                saldo_devedor=160.0,
                vencimento="",
                formas_pagamento=[{"metodo": "PIX (14/09/2026)", "valor": 190.0}],
            ),
        )
        self.assertIn("SALDO A PAGAR", html)
        self.assertIn("Sem vencimento", html)
        self.assertIn("• Taxa de avaliação", html)

    def test_sem_procedimento_cita_consulta(self):
        appointment = MagicMock()
        appointment.appointment_procedures.select_related.return_value.all.return_value = []
        appointment.procedure = None
        appointment.retorno_procedure = None
        appointment.consulta = None
        self.assertEqual(
            _buscar_procedimentos_recibo(appointment),
            [{"nome": "Consulta", "valor": 0.0}],
        )

    def _ctx_protocolo(self, **overrides):
        base = self._ctx(
            taxa_consulta=0,
            taxa_consulta_referencia=0,
            retorno_gratuito=False,
            desconto=0,
            desconto_retorno=0,
        )
        base.update(overrides)
        return base

    def test_pacote_mostra_valor_sem_e_com_desconto(self):
        html = gerar_html_recibo(
            self._ctx_protocolo(
                procedimentos=[
                    {"nome": "BOTOX", "valor": 150.0},
                    {"nome": "PREENCHIMENTO", "valor": 650.0},
                ],
                subtotal=800.0,
                valor_total=800.0,
                valor_pago=800.0,
                saldo_devedor=0.0,
                formas_pagamento=[{"metodo": "PIX", "valor": 800.0}],
                protocolo_valor_sem_desconto=1000.0,
                protocolo_valor_com_desconto=800.0,
                protocolo_procedimentos=[
                    {"nome": "BOTOX", "valor": 200.0},
                    {"nome": "PREENCHIMENTO", "valor": 800.0},
                ],
            ),
        )
        self.assertIn("Valor sem desconto", html)
        self.assertIn("R$ 1.000,00", html)
        self.assertIn("Desconto do protocolo", html)
        self.assertIn("- R$ 200,00", html)
        self.assertIn("Valor com desconto", html)
        self.assertIn("R$ 800,00", html)
        self.assertIn("R$ 200,00", html)
        self.assertNotIn("Abatimento", html)
        self.assertNotIn(">Total<", html)

    def test_parcela_mostra_os_dois_valores_do_protocolo(self):
        html = gerar_html_recibo(
            self._ctx_protocolo(
                procedimentos=[{"nome": "BOTOX", "valor": 200.0}],
                subtotal=200.0,
                valor_total=200.0,
                valor_pago=200.0,
                saldo_devedor=0.0,
                formas_pagamento=[{"metodo": "PIX", "valor": 200.0}],
                protocolo_valor_sem_desconto=1000.0,
                protocolo_valor_com_desconto=800.0,
            ),
        )
        self.assertIn("Protocolo", html)
        self.assertIn("Valor sem desconto", html)
        self.assertIn("R$ 1.000,00", html)
        self.assertIn("Valor com desconto", html)
        self.assertIn("R$ 800,00", html)
        self.assertIn(">Total<", html)
        self.assertIn("R$ 200,00", html)
        self.assertNotIn("Abatimento", html)
        self.assertNotIn("Desconto do protocolo", html)

    def test_sessao_zerada_nao_repete_o_desconto_do_pacote(self):
        html = gerar_html_recibo(
            self._ctx_protocolo(
                procedimentos=[{"nome": "BOTOX", "valor": 0.0}],
                subtotal=0.0,
                valor_total=0.0,
                valor_pago=0.0,
                saldo_devedor=0.0,
                formas_pagamento=[],
                protocolo_valor_sem_desconto=1000.0,
                protocolo_valor_com_desconto=800.0,
            ),
        )
        self.assertNotIn("Valor sem desconto", html)
        self.assertNotIn("Valor com desconto", html)
