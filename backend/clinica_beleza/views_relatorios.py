"""Views para Relatórios — Clínica da Beleza.
"""
from datetime import date, datetime

from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework.views import APIView

from .comissao_relatorio_service import calcular_comissoes
from .comissao_repasse_service import calcular_repasse_por_consulta
from .permissions import CLINICA_FINANCEIRO


def _float_or_zero(value) -> float:
    return float(value) if value is not None else 0.0


def _serialize_regra(regra: dict | None) -> dict | None:
    if not regra:
        return None
    return {
        "modo": regra.get("modo", ""),
        "regra": regra.get("regra", ""),
        "valor": _float_or_zero(regra.get("valor")),
    }


def _serialize_detalhe(d: dict) -> dict:
    return {
        "local_nome": d.get("local_nome", ""),
        "procedimento_nome": d["procedimento_nome"],
        "tipo_linha": d.get("tipo_linha", "procedimento"),
        "vinculado_consulta": bool(d.get("vinculado_consulta", True)),
        "qtd": d["qtd"],
        "valor_consulta": _float_or_zero(d.get("valor_consulta")),
        "valor_procedimento": _float_or_zero(d.get("valor_procedimento")),
        "valor_total": _float_or_zero(d.get("valor_total")),
        "comissao_consulta": _float_or_zero(d.get("comissao_consulta")),
        "comissao_procedimento": _float_or_zero(d.get("comissao_procedimento")),
        "comissao": _float_or_zero(d.get("comissao")),
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
        "valor_consulta": _float_or_zero(p.get("valor_consulta")),
        "valor_procedimento": _float_or_zero(p.get("valor_procedimento")),
        "valor_total": _float_or_zero(p.get("valor_total")),
        "comissao_consulta": _float_or_zero(p.get("comissao_consulta")),
        "comissao_procedimento": _float_or_zero(p.get("comissao_procedimento")),
        "comissao_total": _float_or_zero(p.get("comissao_total")),
        "comissao_consulta_regra": _serialize_regra(p.get("comissao_consulta_regra")),
        "comissao_consulta_regras_por_local": p.get("comissao_consulta_regras_por_local") or [],
        "detalhes": [_serialize_detalhe(d) for d in p["detalhes"]],
    }


def _parse_filtros_comissoes(request):
    data_inicio = RelatorioComissoesView._parse_date(request.query_params.get("data_inicio"))
    data_fim = RelatorioComissoesView._parse_date(request.query_params.get("data_fim"))
    professional_id = request.query_params.get("professional_id")
    if professional_id:
        try:
            professional_id = int(professional_id)
        except (ValueError, TypeError):
            professional_id = None
    return data_inicio, data_fim, professional_id


def _loja_atual():
    from superadmin.models import Loja
    from tenants.middleware import get_current_loja_id

    loja_id = get_current_loja_id()
    return Loja.objects.filter(id=loja_id).first()


def _filename_periodo(prefix: str, data_inicio, data_fim, nome: str | None = None) -> str:
    parts = [prefix]
    if nome:
        safe = "".join(c if c.isalnum() or c in " -_" else "" for c in nome)[:40].strip()
        if safe:
            parts.append(safe.replace(" ", "_"))
    if data_inicio and data_fim:
        parts.append(f"{data_inicio}_{data_fim}")
    return "_".join(parts)


def _pdf_response(pdf_buffer, filename: str) -> HttpResponse:
    response = HttpResponse(pdf_buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{filename}.pdf"'
    return response


def _profissional_nome(professional_id) -> str | None:
    if not professional_id:
        return None
    from .models import Professional

    prof = Professional.objects.filter(pk=professional_id).first()
    return prof.nome if prof else None


def _parse_forma(request) -> str | None:
    from .models import Payment

    forma = (request.query_params.get("forma") or "").strip().upper() or None
    metodos = {c[0] for c in Payment.PAYMENT_METHOD_CHOICES}
    if forma and forma not in metodos:
        return None
    return forma


class RelatorioComissoesView(APIView):
    """GET /clinica-beleza/relatorios/comissoes/"""

    permission_classes = CLINICA_FINANCEIRO

    def get(self, request):
        data_inicio, data_fim, professional_id = _parse_filtros_comissoes(request)

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
                "valor_consulta": _float_or_zero(totais.get("valor_consulta")),
                "valor_procedimento": _float_or_zero(totais.get("valor_procedimento")),
                "valor_total": _float_or_zero(totais.get("valor_total")),
                "comissao_consulta": _float_or_zero(totais.get("comissao_consulta")),
                "comissao_procedimento": _float_or_zero(totais.get("comissao_procedimento")),
                "comissao_total": _float_or_zero(totais.get("comissao_total")),
            },
        })

    @staticmethod
    def _parse_date(value: str | None) -> date | None:
        if not value:
            return None
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return None


class RelatorioComissoesPdfView(APIView):
    """GET /clinica-beleza/relatorios/comissoes/pdf/ — PDF com logo ou timbrado Memed."""

    permission_classes = CLINICA_FINANCEIRO

    def get(self, request):
        from .comissao_relatorio_pdf import gerar_pdf_comissoes

        data_inicio, data_fim, professional_id = _parse_filtros_comissoes(request)
        resultado = calcular_comissoes(
            data_inicio=data_inicio,
            data_fim=data_fim,
            professional_id=professional_id,
        )
        loja = _loja_atual()
        if not loja:
            return Response({"error": "Loja não encontrada."}, status=404)

        prof_nome = _profissional_nome(professional_id)
        agrupar = (request.query_params.get("agrupar") or "profissional").strip()
        if agrupar in ("local", "convenio"):
            from .relatorio_tabela_pdf import gerar_pdf_comissoes_agrupado

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

        return _pdf_response(pdf_buffer, _filename_periodo(prefix, data_inicio, data_fim, prof_nome))


def _serialize_procedimento_repasse(p: dict) -> dict:
    return {
        "procedure_id": p.get("procedure_id"),
        "nome": p.get("nome", ""),
        "valor": _float_or_zero(p.get("valor")),
        "comissao": _float_or_zero(p.get("comissao")),
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
        "valor_consulta": _float_or_zero(a.get("valor_consulta")),
        "comissao_consulta": _float_or_zero(a.get("comissao_consulta")),
        "modo_consulta": a.get("modo_consulta", ""),
        "regra_consulta": a.get("regra_consulta", ""),
        "procedimentos": [_serialize_procedimento_repasse(p) for p in a.get("procedimentos") or []],
        "valor_procedimentos": _float_or_zero(a.get("valor_procedimentos")),
        "comissao_procedimentos": _float_or_zero(a.get("comissao_procedimentos")),
        "valor_atendimento": _float_or_zero(a.get("valor_atendimento")),
        "comissao_atendimento": _float_or_zero(a.get("comissao_atendimento")),
    }


def _serialize_profissional_repasse(p: dict) -> dict:
    return {
        "professional_id": p["professional_id"],
        "nome": p["nome"],
        "total_atendimentos": p["total_atendimentos"],
        "valor_consulta": _float_or_zero(p.get("valor_consulta")),
        "valor_procedimento": _float_or_zero(p.get("valor_procedimento")),
        "valor_total": _float_or_zero(p.get("valor_total")),
        "comissao_consulta": _float_or_zero(p.get("comissao_consulta")),
        "comissao_procedimento": _float_or_zero(p.get("comissao_procedimento")),
        "comissao_total": _float_or_zero(p.get("comissao_total")),
        "atendimentos": [_serialize_atendimento_repasse(a) for a in p.get("atendimentos") or []],
    }


class RelatorioFaturamentoView(APIView):
    """GET /clinica-beleza/relatorios/faturamento/?data_inicio=&data_fim=&agrupar=profissional"""

    permission_classes = CLINICA_FINANCEIRO

    def get(self, request):
        from .faturamento_relatorio_service import calcular_faturamento

        data_inicio = RelatorioComissoesView._parse_date(request.query_params.get("data_inicio"))
        data_fim = RelatorioComissoesView._parse_date(request.query_params.get("data_fim"))
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
        from .faturamento_relatorio_service import calcular_faturamento
        from .relatorio_tabela_pdf import gerar_pdf_faturamento

        data_inicio = RelatorioComissoesView._parse_date(request.query_params.get("data_inicio"))
        data_fim = RelatorioComissoesView._parse_date(request.query_params.get("data_fim"))
        agrupar = request.query_params.get("agrupar", "profissional")
        if agrupar not in ("profissional", "procedimento", "local", "convenio"):
            agrupar = "profissional"

        loja = _loja_atual()
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
        return _pdf_response(pdf_buffer, _filename_periodo(f"faturamento_{agrupar}", data_inicio, data_fim))


class RelatorioLancamentosView(APIView):
    """GET /clinica-beleza/relatorios/lancamentos/?data_inicio=&data_fim=&forma=&professional_id="""

    permission_classes = CLINICA_FINANCEIRO

    def get(self, request):
        from .lancamentos_relatorio_service import calcular_lancamentos

        data_inicio, data_fim, professional_id = _parse_filtros_comissoes(request)
        forma = _parse_forma(request)
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
        from .lancamentos_relatorio_service import calcular_lancamentos
        from .models import Payment
        from .relatorio_tabela_pdf import gerar_pdf_lancamentos

        data_inicio, data_fim, professional_id = _parse_filtros_comissoes(request)
        forma = _parse_forma(request)
        loja = _loja_atual()
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
        return _pdf_response(
            pdf_buffer,
            _filename_periodo("lancamentos", data_inicio, data_fim, _profissional_nome(professional_id)),
        )


class RelatorioDescontosView(APIView):
    """GET /clinica-beleza/relatorios/descontos/?data_inicio=&data_fim=&professional_id="""

    permission_classes = CLINICA_FINANCEIRO

    def get(self, request):
        from .descontos_relatorio_service import calcular_descontos

        data_inicio, data_fim, professional_id = _parse_filtros_comissoes(request)
        return Response(calcular_descontos(
            data_inicio=data_inicio,
            data_fim=data_fim,
            professional_id=professional_id,
        ))


class RelatorioDescontosPdfView(APIView):
    """GET /clinica-beleza/relatorios/descontos/pdf/"""

    permission_classes = CLINICA_FINANCEIRO

    def get(self, request):
        from .descontos_relatorio_service import calcular_descontos
        from .relatorio_tabela_pdf import gerar_pdf_descontos

        data_inicio, data_fim, professional_id = _parse_filtros_comissoes(request)
        loja = _loja_atual()
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
        return _pdf_response(
            pdf_buffer,
            _filename_periodo("descontos", data_inicio, data_fim, _profissional_nome(professional_id)),
        )


class RelatorioRepasseConsultaView(APIView):
    """GET /clinica-beleza/relatorios/repasse-consultas/ — atendimento a atendimento."""

    permission_classes = CLINICA_FINANCEIRO

    def get(self, request):
        data_inicio, data_fim, professional_id = _parse_filtros_comissoes(request)
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
                "valor_consulta": _float_or_zero(totais.get("valor_consulta")),
                "valor_procedimento": _float_or_zero(totais.get("valor_procedimento")),
                "valor_total": _float_or_zero(totais.get("valor_total")),
                "comissao_consulta": _float_or_zero(totais.get("comissao_consulta")),
                "comissao_procedimento": _float_or_zero(totais.get("comissao_procedimento")),
                "comissao_total": _float_or_zero(totais.get("comissao_total")),
            },
        })


class RelatorioRepasseConsultaPdfView(APIView):
    """GET /clinica-beleza/relatorios/repasse-consultas/pdf/"""

    permission_classes = CLINICA_FINANCEIRO

    def get(self, request):
        from .comissao_repasse_pdf import gerar_pdf_repasse_consulta

        data_inicio, data_fim, professional_id = _parse_filtros_comissoes(request)
        resultado = calcular_repasse_por_consulta(
            data_inicio=data_inicio,
            data_fim=data_fim,
            professional_id=professional_id,
        )
        loja = _loja_atual()
        if not loja:
            return Response({"error": "Loja não encontrada."}, status=404)

        prof_nome = _profissional_nome(professional_id)
        pdf_buffer = gerar_pdf_repasse_consulta(
            resultado=resultado,
            loja=loja,
            data_inicio=data_inicio,
            data_fim=data_fim,
            profissional_filtro_nome=prof_nome,
        )
        prefix = "repasse" if prof_nome else "repasse_consultas"
        return _pdf_response(pdf_buffer, _filename_periodo(prefix, data_inicio, data_fim, prof_nome))
