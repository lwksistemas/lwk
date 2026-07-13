"""
CRM: busca global (leads, oportunidades, contas, propostas).
"""
from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from tenants.middleware import get_current_loja_id

from .utils import get_current_vendedor_id, is_owner


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def crm_busca(request):
    """
    Busca global no CRM: Leads, Oportunidades e Contas.
    GET /crm-vendas/busca/?q=termo&limit=5
    Respeita isolamento por loja e filtro por vendedor.
    """
    loja_id = get_current_loja_id()
    if not loja_id:
        return Response({'leads': [], 'oportunidades': [], 'contas': []})

    q = (request.GET.get('q') or '').strip()
    if len(q) < 2:
        return Response({'leads': [], 'oportunidades': [], 'contas': []})

    limit = min(int(request.GET.get('limit', 5) or 5), 10)
    term = q
    # Versão só com dígitos para buscar CPF/CNPJ sem formatação
    term_digits = ''.join(c for c in q if c.isdigit())
    vendedor_id = get_current_vendedor_id(request)

    from core.text_search import q_icontains_sem_acento

    from .models import Conta, Lead, Oportunidade, Proposta

    q_filter = (
        q_icontains_sem_acento(term, 'nome', 'empresa', 'email')
        | Q(telefone__icontains=term)
        | Q(cpf_cnpj__icontains=term)
    )
    # Buscar CPF/CNPJ sem formatação (dígitos puros)
    if term_digits and len(term_digits) >= 3:
        q_filter |= Q(cpf_cnpj__icontains=term_digits)
    leads_qs = Lead.objects.filter(q_filter)
    if vendedor_id is not None and not is_owner(request):
        leads_qs = leads_qs.filter(
            Q(oportunidades__vendedor_id=vendedor_id)
            | Q(vendedor_id=vendedor_id)
        ).distinct()
    leads_qs = list(leads_qs.values('id', 'nome', 'empresa', 'status', 'cpf_cnpj')[:limit])

    opp_filter = (
        q_icontains_sem_acento(
            term,
            'titulo',
            'lead__nome',
            'lead__empresa',
            'lead__conta__nome',
            'lead__conta__razao_social',
        )
        | Q(lead__cpf_cnpj__icontains=term)
        | Q(lead__conta__cnpj__icontains=term)
    )
    if term_digits and len(term_digits) >= 3:
        opp_filter |= Q(lead__cpf_cnpj__icontains=term_digits)
        opp_filter |= Q(lead__conta__cnpj__icontains=term_digits)
    opp_qs = Oportunidade.objects.filter(opp_filter)
    if vendedor_id is not None and not is_owner(request):
        opp_qs = opp_qs.filter(vendedor_id=vendedor_id)
    opp_qs = list(opp_qs.values('id', 'titulo', 'valor', 'etapa', 'lead__nome', 'lead__empresa')[:limit])

    conta_filter = (
        q_icontains_sem_acento(term, 'nome', 'razao_social', 'email')
        | Q(telefone__icontains=term)
        | Q(cnpj__icontains=term)
    )
    if term_digits and len(term_digits) >= 3:
        conta_filter |= Q(cnpj__icontains=term_digits)
    contas_qs = Conta.objects.filter(conta_filter)
    if vendedor_id is not None and not is_owner(request):
        contas_qs = contas_qs.filter(vendedor_id=vendedor_id)
    contas_qs = list(contas_qs.values('id', 'nome', 'segmento', 'cnpj')[:limit])

    prop_filter = (
        q_icontains_sem_acento(
            term,
            'titulo',
            'numero',
            'oportunidade__titulo',
            'oportunidade__lead__nome',
            'oportunidade__lead__empresa',
        )
        | Q(oportunidade__lead__cpf_cnpj__icontains=term)
    )
    if term_digits and len(term_digits) >= 3:
        prop_filter |= Q(oportunidade__lead__cpf_cnpj__icontains=term_digits)
    prop_qs = Proposta.objects.filter(prop_filter)
    if vendedor_id is not None and not is_owner(request):
        prop_qs = prop_qs.filter(oportunidade__vendedor_id=vendedor_id)
    prop_qs = list(
        prop_qs.values(
            'id', 'titulo', 'numero', 'status',
            'oportunidade__titulo', 'oportunidade__lead__nome',
        )[:limit]
    )

    def lead_item(r):
        return {'id': r['id'], 'nome': r['nome'], 'empresa': r['empresa'] or '', 'status': r['status'], 'cpf_cnpj': r.get('cpf_cnpj') or ''}

    def opp_item(r):
        return {
            'id': r['id'],
            'titulo': r['titulo'],
            'valor': str(r['valor']),
            'etapa': r['etapa'],
            'lead_nome': r['lead__nome'] or '',
            'lead_empresa': r['lead__empresa'] or '',
        }

    def conta_item(r):
        return {'id': r['id'], 'nome': r['nome'], 'segmento': r['segmento'] or '', 'cnpj': r.get('cnpj') or ''}

    def prop_item(r):
        lead_nome = r.get('oportunidade__lead__nome') or ''
        return {
            'id': r['id'],
            'titulo': r['titulo'],
            'numero': r.get('numero') or '',
            'status': r.get('status') or '',
            'oportunidade_titulo': r.get('oportunidade__titulo') or '',
            'lead_nome': lead_nome,
        }

    return Response({
        'leads': [lead_item(r) for r in leads_qs],
        'oportunidades': [opp_item(r) for r in opp_qs],
        'contas': [conta_item(r) for r in contas_qs],
        'propostas': [prop_item(r) for r in prop_qs],
    })
