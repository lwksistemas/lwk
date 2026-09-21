"""Faturamento, lançamentos, descontos e inadimplentes."""
from rest_framework.response import Response
from rest_framework.views import APIView

from clinica_beleza.permissions import CLINICA_FINANCEIRO

from .helpers import (
    filename_periodo,
    loja_atual,
    parse_date,
    parse_filtros_comissoes,
    parse_forma,
    pdf_response,
    profissional_nome,
)


class RelatorioFaturamentoView(APIView):
    """GET /clinica-beleza/relatorios/faturamento/?data_inicio=&data_fim=&agrupar=profissional"""

    permission_classes = CLINICA_FINANCEIRO

    def get(self, request):
        from clinica_beleza.faturamento_relatorio_service import calcular_faturamento

        data_inicio = parse_date(request.query_params.get("data_inicio"))
        data_fim = parse_date(request.query_params.get("data_fim"))
        agrupar = request.query_params.get("agrupar", "profissional")
        if agrupar not in ("profissional", "procedimento", "local", "convenio"):
            agrupar = "profissional"

        resultado = calcular_faturamento(
            data_inicio=data_inicio,
            data_fim=data_fim,
            agrupar=agrupar,
        )

        return Response(resultado)


class RelatorioFaturamentoPdfView(APIView):
    """GET /clinica-beleza/relatorios/faturamento/pdf/?data_inicio=&data_fim=&agrupar="""

    permission_classes = CLINICA_FINANCEIRO

    def get(self, request):
        from clinica_beleza.faturamento_relatorio_service import calcular_faturamento
        from clinica_beleza.relatorio_tabela_pdf import gerar_pdf_faturamento

        data_inicio = parse_date(request.query_params.get("data_inicio"))
        data_fim = parse_date(request.query_params.get("data_fim"))
        agrupar = request.query_params.get("agrupar", "profissional")
        if agrupar not in ("profissional", "procedimento", "local", "convenio"):
            agrupar = "profissional"

        loja = loja_atual()
        if not loja:
            return Response({"error": "Loja não encontrada."}, status=404)

        resultado = calcular_faturamento(
            data_inicio=data_inicio,
            data_fim=data_fim,
            agrupar=agrupar,
        )
        pdf_buffer = gerar_pdf_faturamento(
            resultado=resultado,
            loja=loja,
            data_inicio=data_inicio,
            data_fim=data_fim,
            agrupar=agrupar,
        )
        return pdf_response(pdf_buffer, filename_periodo(f"faturamento_{agrupar}", data_inicio, data_fim))


class RelatorioLancamentosView(APIView):
    """GET /clinica-beleza/relatorios/lancamentos/?data_inicio=&data_fim=&forma=&professional_id="""

    permission_classes = CLINICA_FINANCEIRO

    def get(self, request):
        from clinica_beleza.lancamentos_relatorio_service import calcular_lancamentos

        data_inicio, data_fim, professional_id = parse_filtros_comissoes(request)
        forma = parse_forma(request)
        return Response(calcular_lancamentos(
            data_inicio=data_inicio,
            data_fim=data_fim,
            professional_id=professional_id,
            forma=forma,
        ))


class RelatorioLancamentosPdfView(APIView):
    """GET /clinica-beleza/relatorios/lancamentos/pdf/"""

    permission_classes = CLINICA_FINANCEIRO

    def get(self, request):
        from clinica_beleza.lancamentos_relatorio_service import calcular_lancamentos
        from clinica_beleza.models import Payment
        from clinica_beleza.relatorio_tabela_pdf import gerar_pdf_lancamentos

        data_inicio, data_fim, professional_id = parse_filtros_comissoes(request)
        forma = parse_forma(request)
        loja = loja_atual()
        if not loja:
            return Response({"error": "Loja não encontrada."}, status=404)

        resultado = calcular_lancamentos(
            data_inicio=data_inicio,
            data_fim=data_fim,
            professional_id=professional_id,
            forma=forma,
        )
        forma_label = dict(Payment.PAYMENT_METHOD_CHOICES).get(forma) if forma else None
        pdf_buffer = gerar_pdf_lancamentos(
            resultado=resultado,
            loja=loja,
            data_inicio=data_inicio,
            data_fim=data_fim,
            forma_label=forma_label,
        )
        return pdf_response(
            pdf_buffer,
            filename_periodo("lancamentos", data_inicio, data_fim, profissional_nome(professional_id)),
        )


class RelatorioDescontosView(APIView):
    """GET /clinica-beleza/relatorios/descontos/?data_inicio=&data_fim=&professional_id="""

    permission_classes = CLINICA_FINANCEIRO

    def get(self, request):
        from clinica_beleza.descontos_relatorio_service import calcular_descontos

        data_inicio, data_fim, professional_id = parse_filtros_comissoes(request)
        return Response(calcular_descontos(
            data_inicio=data_inicio,
            data_fim=data_fim,
            professional_id=professional_id,
        ))


class RelatorioDescontosPdfView(APIView):
    """GET /clinica-beleza/relatorios/descontos/pdf/"""

    permission_classes = CLINICA_FINANCEIRO

    def get(self, request):
        from clinica_beleza.descontos_relatorio_service import calcular_descontos
        from clinica_beleza.relatorio_tabela_pdf import gerar_pdf_descontos

        data_inicio, data_fim, professional_id = parse_filtros_comissoes(request)
        loja = loja_atual()
        if not loja:
            return Response({"error": "Loja não encontrada."}, status=404)

        resultado = calcular_descontos(
            data_inicio=data_inicio,
            data_fim=data_fim,
            professional_id=professional_id,
        )
        pdf_buffer = gerar_pdf_descontos(
            resultado=resultado,
            loja=loja,
            data_inicio=data_inicio,
            data_fim=data_fim,
        )
        return pdf_response(
            pdf_buffer,
            filename_periodo("descontos", data_inicio, data_fim, profissional_nome(professional_id)),
        )


class RelatorioInadimplentesView(APIView):
    """GET /clinica-beleza/relatorios/inadimplentes/ — pagamentos a prazo vencidos em aberto."""

    permission_classes = CLINICA_FINANCEIRO

    def get(self, request):
        from clinica_beleza.inadimplentes_relatorio_service import calcular_inadimplentes

        return Response(calcular_inadimplentes())


class RelatorioInadimplentesPdfView(APIView):
    """GET /clinica-beleza/relatorios/inadimplentes/pdf/"""

    permission_classes = CLINICA_FINANCEIRO

    def get(self, request):
        from clinica_beleza.inadimplentes_relatorio_service import calcular_inadimplentes
        from clinica_beleza.relatorio_tabela_pdf import gerar_pdf_inadimplentes

        loja = loja_atual()
        if not loja:
            return Response({"error": "Loja não encontrada."}, status=404)

        resultado = calcular_inadimplentes()
        pdf_buffer = gerar_pdf_inadimplentes(resultado=resultado, loja=loja)
        return pdf_response(pdf_buffer, "inadimplentes")
