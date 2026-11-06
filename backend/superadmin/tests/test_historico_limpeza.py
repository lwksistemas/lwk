"""Leitura clínica fica 6 meses. O restante do histórico sai em 90 dias."""
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from superadmin.historico_limpeza import limpar_historico_acesso
from superadmin.models import HistoricoAcessoGlobal


def _linha(acao, dias):
    linha = HistoricoAcessoGlobal.objects.create(
        usuario_email="ana@clinica.test",
        usuario_nome="Ana",
        acao=acao,
        ip_address="127.0.0.1",
    )
    HistoricoAcessoGlobal.objects.filter(pk=linha.pk).update(
        created_at=timezone.now() - timedelta(days=dias),
    )
    return linha.pk


class HistoricoLimpezaTests(TestCase):
    def test_separa_leitura_e_operacao(self):
        leitura_velha = _linha("visualizar", 200)
        leitura_no_prazo = _linha("visualizar", 100)
        operacao_velha = _linha("criar", 100)
        operacao_nova = _linha("editar", 10)

        resultado = limpar_historico_acesso()

        self.assertGreaterEqual(resultado["operacao"], 1)
        self.assertGreaterEqual(resultado["leitura"], 1)
        restantes = set(HistoricoAcessoGlobal.objects.values_list("id", flat=True))
        self.assertNotIn(leitura_velha, restantes)
        self.assertIn(leitura_no_prazo, restantes)
        self.assertNotIn(operacao_velha, restantes)
        self.assertIn(operacao_nova, restantes)
