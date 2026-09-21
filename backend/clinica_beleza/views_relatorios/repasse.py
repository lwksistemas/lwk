"""GET /clinica-beleza/relatorios/repasse-consultas/"""
from rest_framework.response import Response
from rest_framework.views import APIView

from clinica_beleza.comissao_repasse_service import calcular_repasse_por_consulta
from clinica_beleza.permissions import CLINICA_FINANCEIRO

from .helpers import (
    filename_periodo,
    float_or_zero,
    loja_atual,
    parse_filtros_comissoes,
    pdf_response,
    profissional_nome,
)


def _serialize_procedimento_repasse(p: dict) -> dict:
    return {
        "procedure_id": p.get("procedure_id"),
        "nome": p.get("nome", ""),
        "valor": float_or_zero(p.get("valor")),
        "comissao": float_or_zero(p.get("comissao")),
        "modo": p.get("modo", ""),
        "regra": p.get("regra", ""),
    }


def _serialize_atendimento_repasse(a: dict) -> dict:
    return {
        "appointment_id": a.get("appointment_id"),
        "data_atendimento": a.get("data_atendimento", ""),
        "hora_atendimento": a.get("hora_atendimento", ""),
        "paciente_nome": a.get("paciente_nome", ""),
        "local_nome": a.get("local_nome", ""),
        "forma_pagamento": a.get("forma_pagamento", ""),
        "valor_consulta": float_or_zero(a.get("valor_consulta")),
        "comissao_consulta": float_or_zero(a.get("comissao_consulta")),
        "modo_consulta": a.get("modo_consulta", ""),
        "regra_consulta": a.get("regra_consulta", ""),
        "procedimentos": [_serialize_procedimento_repasse(p) for p in a.get("procedimentos") or []],
        "valor_procedimentos": float_or_zero(a.get("valor_procedimentos")),
        "comissao_procedimentos": float_or_zero(a.get("comissao_procedimentos")),
        "valor_atendimento": float_or_zero(a.get("valor_atendimento")),
        "comissao_atendimento": float_or_zero(a.get("comissao_atendimento")),
    }


def _serialize_profissional_repasse(p: dict) -> dict:
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
        "atendimentos": [_serialize_atendimento_repasse(a) for a in p.get("atendimentos") or []],
    }


class RelatorioRepasseConsultaView(APIView):
    """GET /clinica-beleza/relatorios/repasse-consultas/ — atendimento a atendimento."""

    permission_classes = CLINICA_FINANCEIRO

    def get(self, request):
        data_inicio, data_fim, professional_id = parse_filtros_comissoes(request)
        resultado = calcular_repasse_por_consulta(
            data_inicio=data_inicio,
            data_fim=data_fim,
            professional_id=professional_id,
        )
        totais = resultado["totais"]
        return Response({
            "profissionais": [_serialize_profissional_repasse(p) for p in resultado["profissionais"]],
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


class RelatorioRepasseConsultaPdfView(APIView):
    """GET /clinica-beleza/relatorios/repasse-consultas/pdf/"""

    permission_classes = CLINICA_FINANCEIRO

    def get(self, request):
        from clinica_beleza.comissao_repasse_pdf import gerar_pdf_repasse_consulta

        data_inicio, data_fim, professional_id = parse_filtros_comissoes(request)
        resultado = calcular_repasse_por_consulta(
            data_inicio=data_inicio,
            data_fim=data_fim,
            professional_id=professional_id,
        )
        loja = loja_atual()
        if not loja:
            return Response({"error": "Loja não encontrada."}, status=404)

        prof_nome = profissional_nome(professional_id)
        pdf_buffer = gerar_pdf_repasse_consulta(
            resultado=resultado,
            loja=loja,
            data_inicio=data_inicio,
            data_fim=data_fim,
            profissional_filtro_nome=prof_nome,
        )
        prefix = "repasse" if prof_nome else "repasse_consultas"
        return pdf_response(pdf_buffer, filename_periodo(prefix, data_inicio, data_fim, prof_nome))
