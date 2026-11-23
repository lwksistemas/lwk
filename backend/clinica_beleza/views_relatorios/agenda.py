"""Relatórios de agenda / equipe (folgas, bloqueios, dias trabalhados)."""
from rest_framework.response import Response
from rest_framework.views import APIView

from clinica_beleza.permissions import CLINICA_AGENDA

from .helpers import (
    filename_periodo,
    loja_atual,
    parse_filtros_comissoes,
    pdf_response,
    profissional_nome,
)


class RelatorioFolgasBloqueiosView(APIView):
    """GET /clinica-beleza/relatorios/folgas-bloqueios/?data_inicio=&data_fim=&professional_id="""

    permission_classes = CLINICA_AGENDA

    def get(self, request):
        from clinica_beleza.folga_bloqueio_relatorio_service import calcular_folgas_bloqueios

        data_inicio, data_fim, professional_id = parse_filtros_comissoes(request)
        return Response(
            calcular_folgas_bloqueios(
                data_inicio=data_inicio,
                data_fim=data_fim,
                professional_id=professional_id,
            )
        )


class RelatorioFolgasBloqueiosPdfView(APIView):
    """GET /clinica-beleza/relatorios/folgas-bloqueios/pdf/"""

    permission_classes = CLINICA_AGENDA

    def get(self, request):
        from clinica_beleza.folga_bloqueio_relatorio_service import calcular_folgas_bloqueios
        from clinica_beleza.relatorio_tabela_pdf import gerar_pdf_folgas_bloqueios

        data_inicio, data_fim, professional_id = parse_filtros_comissoes(request)
        loja = loja_atual()
        if not loja:
            return Response({"error": "Loja não encontrada."}, status=404)

        resultado = calcular_folgas_bloqueios(
            data_inicio=data_inicio,
            data_fim=data_fim,
            professional_id=professional_id,
        )
        pdf_buffer = gerar_pdf_folgas_bloqueios(
            resultado=resultado,
            loja=loja,
            data_inicio=data_inicio,
            data_fim=data_fim,
        )
        return pdf_response(
            pdf_buffer,
            filename_periodo(
                "folgas_bloqueios",
                data_inicio,
                data_fim,
                profissional_nome(professional_id),
            ),
        )
