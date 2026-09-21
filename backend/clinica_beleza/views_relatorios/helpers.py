"""Helpers compartilhados das views de relatórios."""
from datetime import date, datetime

from django.http import HttpResponse


def float_or_zero(value) -> float:
    return float(value) if value is not None else 0.0


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def parse_filtros_comissoes(request):
    data_inicio = parse_date(request.query_params.get("data_inicio"))
    data_fim = parse_date(request.query_params.get("data_fim"))
    professional_id = request.query_params.get("professional_id")
    if professional_id:
        try:
            professional_id = int(professional_id)
        except (ValueError, TypeError):
            professional_id = None
    return data_inicio, data_fim, professional_id


def loja_atual():
    from superadmin.models import Loja
    from tenants.middleware import get_current_loja_id

    loja_id = get_current_loja_id()
    return Loja.objects.filter(id=loja_id).first()


def filename_periodo(prefix: str, data_inicio, data_fim, nome: str | None = None) -> str:
    parts = [prefix]
    if nome:
        safe = "".join(c if c.isalnum() or c in " -_" else "" for c in nome)[:40].strip()
        if safe:
            parts.append(safe.replace(" ", "_"))
    if data_inicio and data_fim:
        parts.append(f"{data_inicio}_{data_fim}")
    return "_".join(parts)


def pdf_response(pdf_buffer, filename: str) -> HttpResponse:
    response = HttpResponse(pdf_buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{filename}.pdf"'
    return response


def profissional_nome(professional_id) -> str | None:
    if not professional_id:
        return None
    from clinica_beleza.models import Professional

    prof = Professional.objects.filter(pk=professional_id).first()
    return prof.nome if prof else None


def parse_forma(request) -> str | None:
    from clinica_beleza.models import Payment

    forma = (request.query_params.get("forma") or "").strip().upper() or None
    metodos = {c[0] for c in Payment.PAYMENT_METHOD_CHOICES}
    if forma and forma not in metodos:
        return None
    return forma
