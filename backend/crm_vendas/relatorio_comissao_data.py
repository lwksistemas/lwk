"""
Dados e consultas para Relatório de Comissão (CRM).
"""
from decimal import Decimal

from django.db.models import Count, Q, Sum


def fmt_cpf_cnpj(valor: str) -> str:
    """Formata CPF (000.000.000-00) ou CNPJ (00.000.000/0001-00) a partir de string com ou sem máscara."""
    digits = ''.join(c for c in (valor or '') if c.isdigit())
    if len(digits) == 11:
        return f'{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}'
    if len(digits) == 14:
        return f'{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}'
    return valor


def resolver_periodo_relatorio(
    periodo: str = 'mes_atual',
    data_inicio_str: str | None = None,
    data_fim_str: str | None = None,
):
    """
    Retorna (periodo_inicio, periodo_fim, periodo_descricao, erro).
    erro é str quando inválido.
    """
    from datetime import date as date_type

    from .relatorios import calcular_periodo

    if data_inicio_str and data_fim_str:
        try:
            periodo_inicio = date_type.fromisoformat(data_inicio_str)
            periodo_fim = date_type.fromisoformat(data_fim_str)
        except ValueError:
            return None, None, None, 'Datas inválidas.'
        periodo_descricao = (
            f'{periodo_inicio.strftime("%d/%m/%Y")} a {periodo_fim.strftime("%d/%m/%Y")}'
        )
        return periodo_inicio, periodo_fim, periodo_descricao, None

    periodo_inicio, periodo_fim = calcular_periodo(periodo)
    periodo_descricao = periodo.replace('_', ' ').title()
    return periodo_inicio, periodo_fim, periodo_descricao, None


def queryset_oportunidades_comissao(
    loja_id: int,
    empresa_prestadora_id: int,
    vendedor_id: int | None,
    periodo_inicio,
    periodo_fim,
):
    """Oportunidades closed_won no período para uma empresa prestadora."""
    from .models import Oportunidade
    from .relatorios import _filtro_datas_fechamento_ganho

    qs = Oportunidade.objects.filter(
        loja_id=loja_id,
        etapa='closed_won',
    ).filter(
        Q(empresa_prestadora_id=empresa_prestadora_id)
        | Q(empresa_prestadora_id__isnull=True)
    ).filter(
        _filtro_datas_fechamento_ganho(periodo_inicio, periodo_fim)
    ).select_related('lead', 'lead__conta', 'vendedor')

    if vendedor_id:
        from .utils import get_vendedor_destino_merge_loja

        destino = get_vendedor_destino_merge_loja(loja_id)
        if destino and destino.id == vendedor_id:
            qs = qs.filter(
                Q(vendedor_id=vendedor_id)
                | Q(vendedor_id__isnull=True)
                | Q(vendedor__is_active=False)
            )
        else:
            qs = qs.filter(vendedor_id=vendedor_id)

    return qs


def agregar_totais_oportunidades(qs):
    return qs.aggregate(
        total_vendas=Sum('valor'),
        total_comissao=Sum('valor_comissao'),
        qtd=Count('id'),
    )


def resumo_relatorio_comissao(
    loja_id: int,
    empresa_prestadora_id: int,
    vendedor_id: int | None,
    periodo: str = 'mes_atual',
    data_inicio_str: str | None = None,
    data_fim_str: str | None = None,
) -> tuple[dict | None, str | None]:
    """Resumo das vendas que entrarão no relatório (preview antes do PDF)."""
    from .models import Conta

    ep = Conta.objects.filter(id=empresa_prestadora_id, loja_id=loja_id).first()
    if not ep:
        return None, 'Empresa prestadora não encontrada.'

    periodo_inicio, periodo_fim, periodo_descricao, err = resolver_periodo_relatorio(
        periodo, data_inicio_str, data_fim_str
    )
    if err:
        return None, err

    qs = queryset_oportunidades_comissao(
        loja_id, empresa_prestadora_id, vendedor_id, periodo_inicio, periodo_fim
    )
    totais = agregar_totais_oportunidades(qs)
    vendas = []
    for op in qs.order_by('-data_fechamento_ganho', '-data_fechamento')[:50]:
        data = op.data_fechamento_ganho or op.data_fechamento
        cliente = op.lead.conta.nome if op.lead and op.lead.conta_id else (
            op.lead.nome if op.lead else op.titulo
        )
        vendas.append({
            'id': op.id,
            'titulo': op.titulo,
            'cliente': cliente,
            'data': data.isoformat() if data else None,
            'valor': float(op.valor or 0),
            'comissao': float(op.valor_comissao or 0),
            'empresa_prestadora_id': op.empresa_prestadora_id,
            'empresa_prestadora_nome': (
                op.empresa_prestadora.nome if op.empresa_prestadora_id else None
            ),
        })

    return {
        'empresa_prestadora_id': ep.id,
        'empresa_prestadora_nome': ep.nome,
        'periodo_descricao': periodo_descricao,
        'quantidade_vendas': totais['qtd'] or 0,
        'valor_total_vendas': float(totais['total_vendas'] or 0),
        'valor_total_comissao': float(totais['total_comissao'] or 0),
        'vendas': vendas,
    }, None


def montar_dados_oportunidades_snapshot(qs, *, incluir_id: bool = True) -> list[dict]:
    dados_ops = []
    for op in qs.order_by('-data_fechamento_ganho', '-data_fechamento'):
        data = op.data_fechamento_ganho or op.data_fechamento
        cliente = ''
        cpf_cnpj = ''
        if op.lead:
            if op.lead.conta_id:
                cliente = op.lead.conta.nome
                cpf_cnpj = op.lead.conta.cnpj or ''
            else:
                cliente = op.lead.nome
                cpf_cnpj = op.lead.cpf_cnpj or ''
        item = {
            'data': data.strftime('%d/%m/%Y') if data else '—',
            'cliente': (
                f'{fmt_cpf_cnpj(cpf_cnpj)} {cliente}'.strip()
                if cpf_cnpj
                else (cliente or op.titulo)
            ),
            'valor': float(op.valor or 0),
            'comissao': float(op.valor_comissao or 0),
        }
        if incluir_id:
            item['id'] = op.id
            item['titulo'] = op.titulo
        dados_ops.append(item)
    return dados_ops


def nome_arquivo_pdf_comissao(empresa_nome: str, vendedor_nome: str, numero: str = '') -> str:
    nome_empresa = (empresa_nome or 'empresa').replace(' ', '_')[:30]
    nome_vend = (vendedor_nome or 'vendedor').replace(' ', '_')[:30]
    sufixo = f'_{numero}' if numero else ''
    return f'comissao_{nome_empresa}_{nome_vend}{sufixo}.pdf'


def serializar_relatorio_lista(relatorio) -> dict:
    return {
        'id': relatorio.id,
        'numero': relatorio.numero,
        'titulo': relatorio.titulo,
        'status': relatorio.status,
        'status_display': relatorio.get_status_display(),
        'empresa_prestadora_nome': (
            relatorio.empresa_prestadora.nome if relatorio.empresa_prestadora else ''
        ),
        'vendedor_nome': relatorio.vendedor.nome if relatorio.vendedor else '',
        'periodo_descricao': relatorio.periodo_descricao,
        'valor_total_vendas': str(relatorio.valor_total_vendas),
        'valor_total_comissao': str(relatorio.valor_total_comissao),
        'quantidade_vendas': relatorio.quantidade_vendas,
        'boleto_url': relatorio.boleto_url,
        'nfse_numero': relatorio.nfse_numero,
        'created_at': relatorio.created_at.isoformat() if relatorio.created_at else None,
    }


def gerar_preview_pdf_comissao(
    loja_id: int,
    empresa_prestadora_id: int,
    vendedor_id: int | None,
    periodo: str = 'mes_atual',
    data_inicio_str: str | None = None,
    data_fim_str: str | None = None,
):
    """
    Gera PDF de preview sem persistir relatório.
    Retorna (pdf_bytes, filename, erro).
    """
    from superadmin.models import Loja

    from .models import Conta, Vendedor
    from .models_relatorio_comissao import RelatorioComissao
    from .pdf_relatorio_comissao import gerar_pdf_relatorio_comissao

    ep = Conta.objects.filter(id=empresa_prestadora_id, loja_id=loja_id).first()
    if not ep:
        return None, None, 'Empresa prestadora não encontrada.'

    periodo_inicio, periodo_fim, periodo_descricao, err = resolver_periodo_relatorio(
        periodo, data_inicio_str, data_fim_str
    )
    if err:
        return None, None, err

    qs = queryset_oportunidades_comissao(
        loja_id, empresa_prestadora_id, vendedor_id, periodo_inicio, periodo_fim
    )
    totais = agregar_totais_oportunidades(qs)
    if not totais['qtd']:
        return None, None, 'Nenhuma venda encontrada no período para esta empresa.'

    dados_ops = montar_dados_oportunidades_snapshot(qs, incluir_id=False)
    vendedor = (
        Vendedor.objects.filter(id=int(vendedor_id), loja_id=loja_id).first()
        if vendedor_id
        else None
    )

    fake_relatorio = RelatorioComissao(
        loja_id=loja_id,
        numero='PREVIEW',
        titulo=f'Comissões {periodo_descricao} — {ep.nome}',
        empresa_prestadora=ep,
        vendedor=vendedor,
        periodo_inicio=periodo_inicio,
        periodo_fim=periodo_fim,
        periodo_descricao=periodo_descricao,
        valor_total_vendas=Decimal(str(totais['total_vendas'] or 0)),
        valor_total_comissao=Decimal(str(totais['total_comissao'] or 0)),
        quantidade_vendas=totais['qtd'] or 0,
        dados_oportunidades=dados_ops,
    )

    loja = Loja.objects.using('default').filter(id=loja_id).first()
    pdf_buffer = gerar_pdf_relatorio_comissao(fake_relatorio, loja)
    filename = nome_arquivo_pdf_comissao(
        ep.nome,
        vendedor.nome if vendedor else 'vendedor',
    )
    return pdf_buffer.read(), filename, None
