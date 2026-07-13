"""
Service layer para o Dashboard do CRM Vendas.
Extraído de views.dashboard_data (refatoração #4 — SRP).
"""
import logging
from datetime import timedelta

from django.db.models import Count, Q, Sum
from django.utils import timezone

from .periodo import (
    PERIODOS_PIPELINE_CRIACAO_ESTRITA,
    calcular_intervalo_datas,
)
from .periodo import (
    filtro_fechamento_no_periodo as _filtro_fechamento_no_periodo,
)
from .utils import get_vendedor_destino_merge_loja

logger = logging.getLogger(__name__)

ETAPAS_EM_ANDAMENTO = ['prospecting', 'qualification', 'proposal', 'negotiation']
ETAPAS_PIPELINE = ['prospecting', 'qualification', 'proposal', 'negotiation', 'closed_won', 'closed_lost']


def _filtro_oportunidades_abertas_periodo(periodo, data_inicio, data_fim):
    """Etapas abertas no dashboard conforme o tipo de período."""
    base = Q(etapa__in=ETAPAS_EM_ANDAMENTO)
    if periodo in PERIODOS_PIPELINE_CRIACAO_ESTRITA:
        return base & Q(created_at__date__gte=data_inicio, created_at__date__lte=data_fim)
    return base

_ATIVIDADE_VALUES = (
    'id', 'titulo', 'tipo', 'data', 'concluido', 'observacoes', 'lead__nome',
)


def _filtro_atividades_vendedor(vendedor_id):
    """Mesma visibilidade do calendário: oportunidade, lead ou atividade avulsa do vendedor."""
    return (
        Q(oportunidade__vendedor_id=vendedor_id)
        | Q(lead__oportunidades__vendedor_id=vendedor_id)
        | Q(lead__vendedor_id=vendedor_id)
        | Q(oportunidade__isnull=True, lead__isnull=True, criado_por_vendedor_id=vendedor_id)
    )


def _serializar_atividades_dashboard(rows):
    out = []
    for a in rows:
        item = dict(a)
        item['lead_nome'] = (item.pop('lead__nome', None) or '').strip()
        if item.get('data'):
            data_val = item['data']
            item['data'] = data_val.isoformat() if hasattr(data_val, 'isoformat') else str(data_val)
        out.append(item)
    return out


def _fetch_proximas_atividades(atividades_qs, limit=10):
    """
    Próximas tarefas pendentes a partir de hoje (mesma lógica do calendário).
    Não inclui tarefas antigas nem fallback sem filtro de data.
    """
    agora = timezone.now()
    inicio_hoje = agora.replace(hour=0, minute=0, second=0, microsecond=0)
    fim_janela = inicio_hoje + timedelta(days=60)

    proximas = list(
        atividades_qs.filter(
            concluido=False,
            data__gte=inicio_hoje,
            data__lte=fim_janela,
        )
        .order_by('data')
        .values(*_ATIVIDADE_VALUES)[:limit]
    )
    return _serializar_atividades_dashboard(proximas)


def empty_dashboard_response():
    return {
        'leads': 0,
        'oportunidades': 0,
        'receita': 0,
        'pipeline_aberto': 0,
        'oportunidades_em_andamento': 0,
        'valor_perdido': 0,
        'meta_vendas': 0,
        'taxa_conversao': 0,
        'pipeline_por_etapa': [],
        'atividades_hoje': [],
        'performance_vendedores': [],
        'comissao_total_mes': 0,
    }


def build_dashboard_payload(loja_id, vendedor_id, periodo, data_inicio_param,
                            data_fim_param, vendedor_id_filtro, status_filtro, is_owner):
    """
    Constrói o payload do dashboard. Lógica pura sem HTTP.
    Raises em caso de erro de banco (ProgrammingError, OperationalError).
    """
    from .models import Atividade, Lead, Oportunidade, Vendedor

    leads_qs = Lead.objects.all()
    opp_qs = Oportunidade.objects.all()
    atividades_qs = Atividade.objects.all()
    vendedores_qs = Vendedor.objects.filter(is_active=True)

    # Filtro por vendedor logado (não-owner)
    if vendedor_id is not None:
        leads_qs = leads_qs.filter(
            Q(oportunidades__vendedor_id=vendedor_id) | Q(vendedor_id=vendedor_id)
        ).distinct()
        opp_qs = opp_qs.filter(vendedor_id=vendedor_id)
        atividades_qs = atividades_qs.filter(_filtro_atividades_vendedor(vendedor_id)).distinct()
        vendedores_qs = vendedores_qs.filter(id=vendedor_id)

    # Filtro por vendedor específico (owner filtrando por vendedor)
    if is_owner and vendedor_id_filtro and vendedor_id_filtro != 'todos':
        try:
            vid = int(vendedor_id_filtro)
            leads_qs = leads_qs.filter(
                Q(oportunidades__vendedor_id=vid) | Q(vendedor_id=vid)
            ).distinct()
            opp_qs = opp_qs.filter(vendedor_id=vid)
            atividades_qs = atividades_qs.filter(_filtro_atividades_vendedor(vid)).distinct()
            vendedores_qs = vendedores_qs.filter(id=vid)
        except (ValueError, TypeError):
            pass

    data_inicio, data_fim = calcular_intervalo_datas(periodo, data_inicio_param, data_fim_param)

    # Filtro de status
    if status_filtro == 'abertas':
        opp_qs = opp_qs.filter(etapa__in=ETAPAS_EM_ANDAMENTO)
    elif status_filtro == 'fechadas':
        opp_qs = opp_qs.filter(etapa__in=['closed_won', 'closed_lost'])

    filtro_opp_mes = _filtro_fechamento_no_periodo(data_inicio, data_fim)
    filtro_abertas_periodo = _filtro_oportunidades_abertas_periodo(periodo, data_inicio, data_fim)

    # Agregações principais (1 query)
    agg = opp_qs.aggregate(
        total_oportunidades=Count('id'),
        receita=Sum('valor', filter=Q(etapa='closed_won') & filtro_opp_mes),
        pipeline_aberto=Sum('valor', filter=filtro_abertas_periodo),
        oportunidades_em_andamento=Count('id', filter=filtro_abertas_periodo),
        total_fechados=Count('id', filter=Q(etapa__in=['closed_won', 'closed_lost']) & (filtro_opp_mes | Q(etapa='closed_lost', data_fechamento_perdido__gte=data_inicio, data_fechamento_perdido__lte=data_fim))),
        total_ganhos=Count('id', filter=Q(etapa='closed_won') & filtro_opp_mes),
        valor_perdido=Sum('valor', filter=Q(etapa='closed_lost') & Q(data_fechamento_perdido__gte=data_inicio, data_fechamento_perdido__lte=data_fim)),
    )
    total_fechados = agg['total_fechados'] or 0
    total_ganhos = agg['total_ganhos'] or 0
    taxa_conversao = round((total_ganhos / total_fechados * 100), 1) if total_fechados else 0

    # Pipeline por etapa (1 query)
    # Etapas abertas: criadas no período selecionado
    # Etapas fechadas (ganho/perdido): filtra pela data de fechamento no período
    pipeline_aberto_map = {
        row['etapa']: {'valor': float(row['valor'] or 0), 'quantidade': row['qtd'] or 0}
        for row in opp_qs.filter(filtro_abertas_periodo)
        .values('etapa')
        .annotate(valor=Sum('valor'), qtd=Count('id'))
    }
    # Fechadas: filtra por data_fechamento_ganho, data_fechamento_perdido ou data_fechamento
    _filtro_fechado_periodo = (
        Q(data_fechamento_ganho__gte=data_inicio, data_fechamento_ganho__lte=data_fim)
        | Q(data_fechamento_perdido__gte=data_inicio, data_fechamento_perdido__lte=data_fim)
        | (
            Q(data_fechamento_ganho__isnull=True, data_fechamento_perdido__isnull=True)
            & Q(data_fechamento__gte=data_inicio, data_fechamento__lte=data_fim)
        )
    )
    pipeline_fechado_map = {
        row['etapa']: {'valor': float(row['valor'] or 0), 'quantidade': row['qtd'] or 0}
        for row in opp_qs.filter(etapa__in=['closed_won', 'closed_lost'])
        .filter(_filtro_fechado_periodo)
        .values('etapa')
        .annotate(valor=Sum('valor'), qtd=Count('id'))
    }
    pipeline_map = {**pipeline_aberto_map, **pipeline_fechado_map}
    pipeline_por_etapa = [
        {'etapa': e, **(pipeline_map.get(e, {'valor': 0, 'quantidade': 0}))}
        for e in ETAPAS_PIPELINE
    ]

    atividades_data = _fetch_proximas_atividades(atividades_qs, limit=10)

    # Performance vendedores (usa período selecionado pelo filtro)
    filtro_perf = _filtro_fechamento_no_periodo(data_inicio, data_fim, prefix='oportunidades')
    perf_qs = vendedores_qs.annotate(
        receita_mes=Sum('oportunidades__valor', filter=Q(oportunidades__etapa='closed_won') & filtro_perf),
        comissao_mes=Sum('oportunidades__valor_comissao', filter=Q(oportunidades__etapa='closed_won') & filtro_perf),
    )
    performance_vendedores = [
        {'id': v.id, 'nome': v.nome, 'receita_mes': float(v.receita_mes or 0), 'comissao_mes': float(v.comissao_mes or 0)}
        for v in perf_qs
    ]

    filtro_opp_mes_direto = _filtro_fechamento_no_periodo(data_inicio, data_fim)
    comissao_total_mes = opp_qs.filter(etapa='closed_won').filter(filtro_opp_mes_direto).aggregate(
        total=Sum('valor_comissao')
    )['total'] or 0

    # Merge vendas sem vendedor / vendedor inativo no administrador
    base_fechadas = opp_qs.filter(etapa='closed_won').filter(filtro_opp_mes_direto)
    extras_agg = base_fechadas.filter(
        Q(vendedor_id__isnull=True) | Q(vendedor__is_active=False)
    ).aggregate(receita=Sum('valor'), comissao=Sum('valor_comissao'))
    rec_sem = float(extras_agg['receita'] or 0)
    com_sem = float(extras_agg['comissao'] or 0)
    if rec_sem > 0 or com_sem > 0:
        admin_v = get_vendedor_destino_merge_loja(loja_id)
        if admin_v:
            merged = False
            for row in performance_vendedores:
                if row['id'] == admin_v.id:
                    row['receita_mes'] += rec_sem
                    row['comissao_mes'] += com_sem
                    merged = True
                    break
            if not merged:
                performance_vendedores.append({'id': admin_v.id, 'nome': admin_v.nome, 'receita_mes': rec_sem, 'comissao_mes': com_sem})
        else:
            performance_vendedores.append({'id': None, 'nome': 'Sem vendedor', 'receita_mes': rec_sem, 'comissao_mes': com_sem})
    performance_vendedores.sort(key=lambda x: -x['receita_mes'])

    return {
        'leads': leads_qs.filter(created_at__date__gte=data_inicio, created_at__date__lte=data_fim).count(),
        'oportunidades': agg['total_oportunidades'] or 0,
        'receita': float(agg['receita'] or 0),
        'pipeline_aberto': float(agg['pipeline_aberto'] or 0),
        'oportunidades_em_andamento': agg['oportunidades_em_andamento'] or 0,
        'valor_perdido': float(agg.get('valor_perdido') or 0),
        'meta_vendas': 0,
        'taxa_conversao': taxa_conversao,
        'pipeline_por_etapa': pipeline_por_etapa,
        'atividades_hoje': atividades_data,
        'performance_vendedores': performance_vendedores,
        'comissao_total_mes': float(comissao_total_mes),
    }
