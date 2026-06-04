"""
Views para Relatórios — Clínica da Beleza.
"""
from datetime import date, datetime

from rest_framework.views import APIView
from rest_framework.response import Response

from .permissions import CLINICA_FINANCEIRO
from .comissao_relatorio_service import calcular_comissoes


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

        # Serializar Decimal para float no response
        return Response({
            'profissionais': [
                {
                    **p,
                    'valor_total': float(p['valor_total']),
                    'comissao_total': float(p['comissao_total']),
                }
                for p in resultado['profissionais']
            ],
            'totais': {
                'total_atendimentos': resultado['totais']['total_atendimentos'],
                'valor_total': float(resultado['totais']['valor_total']),
                'comissao_total': float(resultado['totais']['comissao_total']),
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
