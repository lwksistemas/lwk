"""
Views para Relatórios — Clínica da Beleza.
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
        'convenio_nome': d.get('convenio_nome', ''),
        'forma_pagamento': d.get('forma_pagamento', ''),
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
        'comissao_consulta_regras_por_local': p.get('comissao_consulta_regras_por_local') or [],
        'detalhes': [_serialize_detalhe(d) for d in p['detalhes']],
    }


def _parse_filtros_comissoes(request):
    data_inicio = RelatorioComissoesView._parse_date(request.query_params.get('data_inicio'))
    data_fim = RelatorioComissoesView._parse_date(request.query_params.get('data_fim'))
    professional_id = request.query_params.get('professional_id')
    if professional_id:
        try:
            professional_id = int(professional_id)
        except (ValueError, TypeError):
            professional_id = None
    return data_inicio, data_fim, professional_id


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


class RelatorioComissoesPdfView(APIView):
    """GET /clinica-beleza/relatorios/comissoes/pdf/ — PDF com logo ou timbrado Memed."""
    permission_classes = CLINICA_FINANCEIRO

    def get(self, request):
        from superadmin.models import Loja
        from tenants.middleware import get_current_loja_id

        from .comissao_relatorio_pdf import gerar_pdf_comissoes
        from .models import Professional

        data_inicio, data_fim, professional_id = _parse_filtros_comissoes(request)

        resultado = calcular_comissoes(
            data_inicio=data_inicio,
            data_fim=data_fim,
            professional_id=professional_id,
        )

        loja_id = get_current_loja_id()
        loja = Loja.objects.filter(id=loja_id).first()
        if not loja:
            return Response({'error': 'Loja não encontrada.'}, status=404)

        prof_nome = None
        if professional_id:
            prof = Professional.objects.filter(pk=professional_id).first()
            prof_nome = prof.nome if prof else None

        pdf_buffer = gerar_pdf_comissoes(
            resultado=resultado,
            loja=loja,
            data_inicio=data_inicio,
            data_fim=data_fim,
            profissional_filtro_nome=prof_nome,
        )

        filename = 'comissoes'
        if prof_nome:
            safe = ''.join(c if c.isalnum() or c in ' -_' else '' for c in prof_nome)[:40].strip()
            filename = f'comissoes_{safe.replace(" ", "_")}'
        if data_inicio and data_fim:
            filename += f'_{data_inicio}_{data_fim}'

        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
        return response


def _serialize_procedimento_repasse(p: dict) -> dict:
    return {
        'procedure_id': p.get('procedure_id'),
        'nome': p.get('nome', ''),
        'valor': _float_or_zero(p.get('valor')),
        'comissao': _float_or_zero(p.get('comissao')),
        'modo': p.get('modo', ''),
        'regra': p.get('regra', ''),
    }


def _serialize_atendimento_repasse(a: dict) -> dict:
    return {
        'appointment_id': a.get('appointment_id'),
        'data_atendimento': a.get('data_atendimento', ''),
        'hora_atendimento': a.get('hora_atendimento', ''),
        'paciente_nome': a.get('paciente_nome', ''),
        'local_nome': a.get('local_nome', ''),
        'forma_pagamento': a.get('forma_pagamento', ''),
        'valor_consulta': _float_or_zero(a.get('valor_consulta')),
        'comissao_consulta': _float_or_zero(a.get('comissao_consulta')),
        'modo_consulta': a.get('modo_consulta', ''),
        'regra_consulta': a.get('regra_consulta', ''),
        'procedimentos': [_serialize_procedimento_repasse(p) for p in a.get('procedimentos') or []],
        'valor_procedimentos': _float_or_zero(a.get('valor_procedimentos')),
        'comissao_procedimentos': _float_or_zero(a.get('comissao_procedimentos')),
        'valor_atendimento': _float_or_zero(a.get('valor_atendimento')),
        'comissao_atendimento': _float_or_zero(a.get('comissao_atendimento')),
    }


def _serialize_profissional_repasse(p: dict) -> dict:
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
        'atendimentos': [_serialize_atendimento_repasse(a) for a in p.get('atendimentos') or []],
    }


class RelatorioFaturamentoView(APIView):
    """GET /clinica-beleza/relatorios/faturamento/?data_inicio=&data_fim=&agrupar=profissional"""
    permission_classes = CLINICA_FINANCEIRO

    def get(self, request):
        from .faturamento_relatorio_service import calcular_faturamento

        data_inicio = RelatorioComissoesView._parse_date(request.query_params.get('data_inicio'))
        data_fim = RelatorioComissoesView._parse_date(request.query_params.get('data_fim'))
        agrupar = request.query_params.get('agrupar', 'profissional')
        if agrupar not in ('profissional', 'procedimento', 'local', 'convenio'):
            agrupar = 'profissional'

        resultado = calcular_faturamento(
            data_inicio=data_inicio,
            data_fim=data_fim,
            agrupar=agrupar,
        )

        return Response(resultado)


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
        totais = resultado['totais']
        return Response({
            'profissionais': [_serialize_profissional_repasse(p) for p in resultado['profissionais']],
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


class RelatorioRepasseConsultaPdfView(APIView):
    """GET /clinica-beleza/relatorios/repasse-consultas/pdf/"""

    permission_classes = CLINICA_FINANCEIRO

    def get(self, request):
        from superadmin.models import Loja
        from tenants.middleware import get_current_loja_id

        from .comissao_repasse_pdf import gerar_pdf_repasse_consulta
        from .models import Professional

        data_inicio, data_fim, professional_id = _parse_filtros_comissoes(request)
        resultado = calcular_repasse_por_consulta(
            data_inicio=data_inicio,
            data_fim=data_fim,
            professional_id=professional_id,
        )

        loja_id = get_current_loja_id()
        loja = Loja.objects.filter(id=loja_id).first()
        if not loja:
            return Response({'error': 'Loja não encontrada.'}, status=404)

        prof_nome = None
        if professional_id:
            prof = Professional.objects.filter(pk=professional_id).first()
            prof_nome = prof.nome if prof else None

        pdf_buffer = gerar_pdf_repasse_consulta(
            resultado=resultado,
            loja=loja,
            data_inicio=data_inicio,
            data_fim=data_fim,
            profissional_filtro_nome=prof_nome,
        )

        filename = 'repasse_consultas'
        if prof_nome:
            safe = ''.join(c if c.isalnum() or c in ' -_' else '' for c in prof_nome)[:40].strip()
            filename = f'repasse_{safe.replace(" ", "_")}'
        if data_inicio and data_fim:
            filename += f'_{data_inicio}_{data_fim}'

        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
        return response
