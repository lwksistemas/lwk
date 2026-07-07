"""Testes unitários para serializers da clinica_estetica."""
import pytest
from unittest.mock import patch, MagicMock

from rest_framework.test import APIRequestFactory

from clinica_estetica.serializers import (
    ClienteSerializer,
    ProfissionalSerializer,
    ProcedimentoSerializer,
    AgendamentoSerializer,
    BloqueioAgendaSerializer,
    CategoriaFinanceiraSerializer,
    TransacaoSerializer,
    TransacaoResumoSerializer,
)


class TestClienteSerializer:
    """Testes do ClienteSerializer."""

    def test_fields_existem(self):
        """Verifica que o serializer declara os campos esperados."""
        s = ClienteSerializer()
        field_names = set(s.fields.keys())
        assert 'nome' in field_names
        assert 'telefone' in field_names
        assert 'cpf' in field_names
        assert 'email' in field_names
        assert 'loja_id' in field_names

    def test_loja_id_read_only(self):
        """loja_id deve ser read-only (preenchido automaticamente)."""
        s = ClienteSerializer()
        assert s.fields['loja_id'].read_only is True

    def test_total_agendamentos_read_only(self):
        """total_agendamentos é campo calculado."""
        s = ClienteSerializer()
        assert 'total_agendamentos' in s.fields
        assert s.fields['total_agendamentos'].read_only is True


class TestProcedimentoSerializer:
    """Testes do ProcedimentoSerializer."""

    def test_duracao_alias(self):
        """to_internal_value deve aceitar 'duracao' como alias de 'duracao_minutos'."""
        s = ProcedimentoSerializer()
        data = {
            'nome': 'Limpeza de Pele',
            'preco': '150.00',
            'duracao': '60',
        }
        # to_internal_value transforma duracao → duracao_minutos
        internal = s.to_internal_value(data)
        assert internal.get('duracao_minutos') == 60

    def test_duracao_minutos_direto(self):
        """Se duracao_minutos é fornecido diretamente, não usa alias."""
        s = ProcedimentoSerializer()
        data = {
            'nome': 'Peeling',
            'preco': '200.00',
            'duracao_minutos': 45,
        }
        internal = s.to_internal_value(data)
        assert internal.get('duracao_minutos') == 45


class TestBloqueioAgendaSerializer:
    """Testes de segurança do BloqueioAgendaSerializer."""

    def test_validate_profissional_schema_injection(self):
        """validate_profissional deve rejeitar schema_name com caracteres perigosos."""
        s = BloqueioAgendaSerializer()

        # Mock do contexto para simular loja com schema malicioso
        with patch('clinica_estetica.serializers.agenda.get_current_loja_id', return_value=1):
            mock_loja = MagicMock()
            mock_loja.database_name = "loja; DROP TABLE --"
            with patch('superadmin.models.Loja.objects') as mock_loja_qs:
                mock_loja_qs.get.return_value = mock_loja

                from rest_framework import serializers as drf_serializers
                with pytest.raises(drf_serializers.ValidationError, match="schema inválido"):
                    s.validate_profissional(999)


class TestTransacaoResumoSerializer:
    """Testes do TransacaoResumoSerializer (DTO)."""

    def test_serializa_resumo(self):
        """Deve serializar dados do resumo financeiro."""
        data = {
            'total_receitas': 5000.00,
            'total_despesas': 2000.00,
            'saldo': 3000.00,
            'receitas_pendentes': 1000.00,
            'despesas_pendentes': 500.00,
            'receitas_pagas': 4000.00,
            'despesas_pagas': 1500.00,
            'transacoes_atrasadas': 3,
            'valor_atrasado': 750.00,
        }
        s = TransacaoResumoSerializer(data)
        assert s.data['saldo'] == '3000.00'
        assert s.data['transacoes_atrasadas'] == 3

    def test_campos_obrigatorios(self):
        """Todos os campos são obrigatórios para validação."""
        s = TransacaoResumoSerializer(data={})
        assert not s.is_valid()
        assert 'total_receitas' in s.errors
