"""CRM: busca global (leads, oportunidades, contas, propostas).
"""
from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from tenants.middleware import get_current_loja_id

from .utils import get_current_vendedor_id, is_owner


def _aplicar_filtro_vendedor(qs, vendedor_id, request, vendedor_field="vendedor_id"):
    """Filtra queryset pelo vendedor se não for owner."""
    if vendedor_id is not None and not is_owner(request):
        return qs.filter(**{vendedor_field: vendedor_id})
    return qs


def _busca_leads(term, term_digits, vendedor_id, request, limit, q_icontains_sem_acento, Lead, Q):
    """Busca leads por nome/empresa/email/cpf."""
    f = q_icontains_sem_acento(term, "nome", "empresa", "email") | Q(telefone__icontains=term) | Q(cpf_cnpj__icontains=term)
    if term_digits and len(term_digits) >= 3:
        f |= Q(cpf_cnpj__icontains=term_digits)
    if vendedor_id is not None and not is_owner(request):
        qs = Lead.objects.filter(f).filter(
            Q(oportunidades__vendedor_id=vendedor_id) | Q(vendedor_id=vendedor_id),
        ).distinct()
    else:
        qs = Lead.objects.filter(f)
    return list(qs.values("id", "nome", "empresa", "status", "cpf_cnpj")[:limit])


def _busca_oportunidades(term, term_digits, vendedor_id, request, limit, q_icontains_sem_acento, Oportunidade, Q):
    """Busca oportunidades por título/lead/conta."""
    f = (
        q_icontains_sem_acento(term, "titulo", "lead__nome", "lead__empresa", "lead__conta__nome", "lead__conta__razao_social")
        | Q(lead__cpf_cnpj__icontains=term)
        | Q(lead__conta__cnpj__icontains=term)
    )
    if term_digits and len(term_digits) >= 3:
        f |= Q(lead__cpf_cnpj__icontains=term_digits) | Q(lead__conta__cnpj__icontains=term_digits)
    qs = _aplicar_filtro_vendedor(Oportunidade.objects.filter(f), vendedor_id, request)
    return list(qs.values("id", "titulo", "valor", "etapa", "lead__nome", "lead__empresa")[:limit])


def _busca_contas(term, term_digits, vendedor_id, request, limit, q_icontains_sem_acento, Conta, Q):
    """Busca contas por nome/razão social/cnpj."""
    f = q_icontains_sem_acento(term, "nome", "razao_social", "email") | Q(telefone__icontains=term) | Q(cnpj__icontains=term)
    if term_digits and len(term_digits) >= 3:
        f |= Q(cnpj__icontains=term_digits)
    qs = _aplicar_filtro_vendedor(Conta.objects.filter(f), vendedor_id, request)
    return list(qs.values("id", "nome", "segmento", "cnpj")[:limit])


def _busca_propostas(term, term_digits, vendedor_id, request, limit, q_icontains_sem_acento, Proposta, Q):
    """Busca propostas por título/número/oportunidade/lead."""
    f = (
        q_icontains_sem_acento(term, "titulo", "numero", "oportunidade__titulo", "oportunidade__lead__nome", "oportunidade__lead__empresa")
        | Q(oportunidade__lead__cpf_cnpj__icontains=term)
    )
    if term_digits and len(term_digits) >= 3:
        f |= Q(oportunidade__lead__cpf_cnpj__icontains=term_digits)
    qs = _aplicar_filtro_vendedor(Proposta.objects.filter(f), vendedor_id, request, vendedor_field="oportunidade__vendedor_id")
    return list(qs.values("id", "titulo", "numero", "status", "oportunidade__titulo", "oportunidade__lead__nome")[:limit])


def _serializar_lead(r):
    return {"id": r["id"], "nome": r["nome"], "empresa": r["empresa"] or "", "status": r["status"], "cpf_cnpj": r.get("cpf_cnpj") or ""}


def _serializar_oportunidade(r):
    return {"id": r["id"], "titulo": r["titulo"], "valor": str(r["valor"]), "etapa": r["etapa"], "lead_nome": r["lead__nome"] or "", "lead_empresa": r["lead__empresa"] or ""}


def _serializar_conta(r):
    return {"id": r["id"], "nome": r["nome"], "segmento": r["segmento"] or "", "cnpj": r.get("cnpj") or ""}


def _serializar_proposta(r):
    return {"id": r["id"], "titulo": r["titulo"], "numero": r.get("numero") or "", "status": r.get("status") or "", "oportunidade_titulo": r.get("oportunidade__titulo") or "", "lead_nome": r.get("oportunidade__lead__nome") or ""}


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def crm_busca(request):
    """Busca global no CRM: Leads, Oportunidades e Contas.
    GET /crm-vendas/busca/?q=termo&limit=5
    Respeita isolamento por loja e filtro por vendedor.
    """
    loja_id = get_current_loja_id()
    if not loja_id:
        return Response({"leads": [], "oportunidades": [], "contas": []})

    q = (request.GET.get("q") or "").strip()
    if len(q) < 2:
        return Response({"leads": [], "oportunidades": [], "contas": []})

    limit = min(int(request.GET.get("limit", 5) or 5), 10)
    term = q
    # Versão só com dígitos para buscar CPF/CNPJ sem formatação
    term_digits = "".join(c for c in q if c.isdigit())
    vendedor_id = get_current_vendedor_id(request)

    from core.text_search import q_icontains_sem_acento

    from .models import Conta, Lead, Oportunidade, Proposta

    bargs = (term, term_digits, vendedor_id, request, limit, q_icontains_sem_acento)
    leads_qs = _busca_leads(*bargs, Lead, Q)
    opp_qs = _busca_oportunidades(*bargs, Oportunidade, Q)
    contas_qs = _busca_contas(*bargs, Conta, Q)
    prop_qs = _busca_propostas(*bargs, Proposta, Q)

    return Response({
        "leads": list(map(_serializar_lead, leads_qs)),
        "oportunidades": list(map(_serializar_oportunidade, opp_qs)),
        "contas": list(map(_serializar_conta, contas_qs)),
        "propostas": list(map(_serializar_proposta, prop_qs)),
    })
