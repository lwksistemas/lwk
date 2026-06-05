"""
Views para Relatórios — Clínica da Beleza.
"""
from datetime import date, datetime

from rest_framework.views import APIView
from rest_framework.response import Response

from .permissions import CLINICA_FINANCEIRO
from .comissao_relatorio_service import calcular_comissoes


def _float_or_zero(value) -> float:
    return float(value) if value is not None else 0.0


def _serialize_regra(regra: dict | None) -> dict | None:
    if not regra:
        return None
    return {
        'modo': regra.get('modo', ''),
        'regra': regra.get('regra', ''),
        'valor': _float_or_zero(regra.get('valor')),
    }


def _serialize_detalhe(d: dict) -> dict:
    return {
        'local_nome': d.get('local_nome', ''),
        'procedimento_nome': d['procedimento_nome'],
        'tipo_linha': d.get('tipo_linha', 'procedimento'),
        'vinculado_consulta': bool(d.get('vinculado_consulta', True)),
        'qtd': d['qtd'],
        'valor_consulta': _float_or_zero(d.get('valor_consulta')),
        'valor_procedimento': _float_or_zero(d.get('valor_procedimento')),
        'valor_total': _float_or_zero(d.get('valor_total')),
        'comissao_consulta': _float_or_zero(d.get('comissao_consulta')),
        'comissao_procedimento': _float_or_zero(d.get('comissao_procedimento')),
        'comissao': _float_or_zero(d.get('comissao')),
        'modo_consulta': d.get('modo_consulta', ''),
        'regra_consulta': d.get('regra_consulta', ''),
        'modo_procedimento': d.get('modo_procedimento', ''),
        'regra_procedimento': d.get('regra_procedimento', ''),
    }


def _serialize_profissional(p: dict) -> dict:
    return {
        'professional_id': p['professional_id'],
        'nome': p['nome'],
        'total_atendimentos': p['total_atendimentos'],
        'valor_consulta': _float_or_zero(p.get('valor_consulta')),
        'valor_procedimento': _float_or_zero(p.get('valor_procedimento')),
        'valor_total': _float_or_zero(p.get('valor_total')),
        'comissao_consulta': _float_or_zero(p.get('comissao_consulta')),
        'comissao_procedimento': _float_or_zero(p.get('comissao_procedimento')),
        'comissao_total': _float_or_zero(p.get('comissao_total')),
        'comissao_consulta_regra': _serialize_regra(p.get('comissao_consulta_regra')),
        'detalhes': [_serialize_detalhe(d) for d in p['detalhes']],
    }


class RelatorioComissoesView(APIView):
    """GET /clinica-beleza/relatorios/comissoes/"""
    permission_classes = CLINICA_FINANCEIRO

    def get(self, request):
        data_inicio = self._parse_date(request.query_params.get('data_inicio'))
        data_fim = self._parse_date(request.query_params.get('data_fim'))
        professional_id = request.query_params.get('professional_id')

        if professional_id:
            try:
                professional_id = int(professional_id)
            except (ValueError, TypeError):
                professional_id = None

        resultado = calcular_comissoes(
            data_inicio=data_inicio,
            data_fim=data_fim,
            professional_id=professional_id,
        )

        totais = resultado['totais']
        return Response({
            'profissionais': [_serialize_profissional(p) for p in resultado['profissionais']],
            'totais': {
                'total_atendimentos': totais['total_atendimentos'],
                'valor_consulta': _float_or_zero(totais.get('valor_consulta')),
                'valor_procedimento': _float_or_zero(totais.get('valor_procedimento')),
                'valor_total': _float_or_zero(totais.get('valor_total')),
                'comissao_consulta': _float_or_zero(totais.get('comissao_consulta')),
                'comissao_procedimento': _float_or_zero(totais.get('comissao_procedimento')),
                'comissao_total': _float_or_zero(totais.get('comissao_total')),
            },
        })

    @staticmethod
    def _parse_date(value: str | None) -> date | None:
        if not value:
            return None
        try:
            return datetime.strptime(value, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return None
