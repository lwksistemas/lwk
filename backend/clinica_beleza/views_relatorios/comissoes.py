"""GET /clinica-beleza/relatorios/comissoes/"""
from rest_framework.response import Response
from rest_framework.views import APIView

from clinica_beleza.comissao_relatorio_service import calcular_comissoes
from clinica_beleza.permissions import CLINICA_FINANCEIRO

from .helpers import (
    filename_periodo,
    float_or_zero,
    loja_atual,
    parse_date,
    parse_filtros_comissoes,
    pdf_response,
    profissional_nome,
)


def _serialize_regra(regra: dict | None) -> dict | None:
    if not regra:
        return None
    return {
        "modo": regra.get("modo", ""),
        "regra": regra.get("regra", ""),
        "valor": float_or_zero(regra.get("valor")),
    }


def _serialize_detalhe(d: dict) -> dict:
    return {
        "local_nome": d.get("local_nome", ""),
        "procedimento_nome": d["procedimento_nome"],
        "tipo_linha": d.get("tipo_linha", "procedimento"),
        "vinculado_consulta": bool(d.get("vinculado_consulta", True)),
        "qtd": d["qtd"],
        "valor_consulta": float_or_zero(d.get("valor_consulta")),
        "valor_procedimento": float_or_zero(d.get("valor_procedimento")),
        "valor_total": float_or_zero(d.get("valor_total")),
        "comissao_consulta": float_or_zero(d.get("comissao_consulta")),
        "comissao_procedimento": float_or_zero(d.get("comissao_procedimento")),
        "comissao": float_or_zero(d.get("comissao")),
        "modo_consulta": d.get("modo_consulta", ""),
        "regra_consulta": d.get("regra_consulta", ""),
        "modo_procedimento": d.get("modo_procedimento", ""),
        "regra_procedimento": d.get("regra_procedimento", ""),
        "convenio_nome": d.get("convenio_nome", ""),
        "forma_pagamento": d.get("forma_pagamento", ""),
    }


def _serialize_profissional(p: dict) -> dict:
    return {
        "professional_id": p["professional_id"],
        "nome": p["nome"],
        "total_atendimentos": p["total_atendimentos"],
        "valor_consulta": float_or_zero(p.get("valor_consulta")),
        "valor_procedimento": float_or_zero(p.get("valor_procedimento")),
        "valor_total": float_or_zero(p.get("valor_total")),
        "comissao_consulta": float_or_zero(p.get("comissao_consulta")),
        "comissao_procedimento": float_or_zero(p.get("comissao_procedimento")),
        "comissao_total": float_or_zero(p.get("comissao_total")),
        "comissao_consulta_regra": _serialize_regra(p.get("comissao_consulta_regra")),
        "comissao_consulta_regras_por_local": p.get("comissao_consulta_regras_por_local") or [],
        "detalhes": [_serialize_detalhe(d) for d in p["detalhes"]],
    }


class RelatorioComissoesView(APIView):
    """GET /clinica-beleza/relatorios/comissoes/"""

    permission_classes = CLINICA_FINANCEIRO

    def get(self, request):
        data_inicio, data_fim, professional_id = parse_filtros_comissoes(request)

        resultado = calcular_comissoes(
            data_inicio=data_inicio,
            data_fim=data_fim,
            professional_id=professional_id,
        )

        totais = resultado["totais"]
        return Response({
            "profissionais": [_serialize_profissional(p) for p in resultado["profissionais"]],
            "totais": {
                "total_atendimentos": totais["total_atendimentos"],
                "valor_consulta": float_or_zero(totais.get("valor_consulta")),
                "valor_procedimento": float_or_zero(totais.get("valor_procedimento")),
                "valor_total": float_or_zero(totais.get("valor_total")),
                "comissao_consulta": float_or_zero(totais.get("comissao_consulta")),
                "comissao_procedimento": float_or_zero(totais.get("comissao_procedimento")),
                "comissao_total": float_or_zero(totais.get("comissao_total")),
            },
        })

    @staticmethod
    def _parse_date(value: str | None):
        return parse_date(value)


class RelatorioComissoesPdfView(APIView):
    """GET /clinica-beleza/relatorios/comissoes/pdf/ — PDF com logo ou timbrado Memed."""

    permission_classes = CLINICA_FINANCEIRO

    def get(self, request):
        from clinica_beleza.comissao_relatorio_pdf import gerar_pdf_comissoes

        data_inicio, data_fim, professional_id = parse_filtros_comissoes(request)
        resultado = calcular_comissoes(
            data_inicio=data_inicio,
            data_fim=data_fim,
            professional_id=professional_id,
        )
        loja = loja_atual()
        if not loja:
            return Response({"error": "Loja não encontrada."}, status=404)

        prof_nome = profissional_nome(professional_id)
        agrupar = (request.query_params.get("agrupar") or "profissional").strip()
        if agrupar in ("local", "convenio"):
            from clinica_beleza.relatorio_tabela_pdf import gerar_pdf_comissoes_agrupado

            pdf_buffer = gerar_pdf_comissoes_agrupado(
                resultado=resultado,
                loja=loja,
                data_inicio=data_inicio,
                data_fim=data_fim,
                agrupar=agrupar,
            )
            prefix = f"comissoes_{agrupar}"
        else:
            pdf_buffer = gerar_pdf_comissoes(
                resultado=resultado,
                loja=loja,
                data_inicio=data_inicio,
                data_fim=data_fim,
                profissional_filtro_nome=prof_nome,
            )
            prefix = "comissoes"

        return pdf_response(pdf_buffer, filename_periodo(prefix, data_inicio, data_fim, prof_nome))
