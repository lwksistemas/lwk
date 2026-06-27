"""Testes de validação do LocalAtendimentoSerializer (property-style)."""
import random
import string
from decimal import Decimal
from unittest import TestCase

from clinica_beleza.serializers import LocalAtendimentoSerializer


def _random_nome_valido(rng: random.Random) -> str:
    chars = string.ascii_letters + string.digits + ' '
    while True:
        raw = ''.join(rng.choice(chars) for _ in range(rng.randint(1, 80)))
        stripped = raw.strip()
        if stripped:
            return stripped


class LocalAtendimentoSerializerPropertyTest(TestCase):
    def setUp(self):
        self.rng = random.Random(20260620)

    def test_round_trip_validacao_nome_e_valor(self):
        """Property 1: nomes válidos e valores >= 0 passam na validação."""
        for _ in range(40):
            nome = _random_nome_valido(self.rng)
            valor = Decimal(str(round(self.rng.uniform(0, 9999.99), 2)))
            serializer = LocalAtendimentoSerializer(data={'nome': nome, 'valor_consulta': valor})
            self.assertTrue(serializer.is_valid(), serializer.errors)
            self.assertEqual(serializer.validated_data['nome'], nome.upper())
            self.assertEqual(serializer.validated_data['valor_consulta'], valor)

    def test_rejeita_nome_whitespace(self):
        """Property 3: strings só com whitespace são rejeitadas."""
        whitespace_samples = [' ', '\t', '\n', '   ', '\t \n', ' \r\n ']
        for sample in whitespace_samples:
            serializer = LocalAtendimentoSerializer(
                data={'nome': sample, 'valor_consulta': Decimal('100.00')},
            )
            self.assertFalse(serializer.is_valid())
            self.assertIn('nome', serializer.errors)

    def test_rejeita_valor_negativo(self):
        """Property 4: valores negativos são rejeitados."""
        for _ in range(20):
            valor = Decimal(str(round(self.rng.uniform(-9999, -0.01), 2)))
            serializer = LocalAtendimentoSerializer(
                data={'nome': 'Consultório', 'valor_consulta': valor},
            )
            self.assertFalse(serializer.is_valid())
            self.assertIn('valor_consulta', serializer.errors)

    def test_tempo_consulta_fora_do_intervalo(self):
        serializer = LocalAtendimentoSerializer(
            data={'nome': 'Sala', 'valor_consulta': '100', 'tempo_consulta_minutos': 0},
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('tempo_consulta_minutos', serializer.errors)

        serializer = LocalAtendimentoSerializer(
            data={'nome': 'Sala', 'valor_consulta': '100', 'tempo_consulta_minutos': 481},
        )
        self.assertFalse(serializer.is_valid())
