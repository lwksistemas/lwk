/** Opções de período compartilhadas no CRM Vendas. */

export type CrmPeriodoOption = { value: string; label: string };

export const CRM_PERIODO_RELATORIO: CrmPeriodoOption[] = [
  { value: 'hoje', label: 'Hoje' },
  { value: 'ontem', label: 'Ontem' },
  { value: 'semana_atual', label: 'Esta Semana' },
  { value: 'semana_passada', label: 'Semana Passada' },
  { value: 'mes_atual', label: 'Este Mês' },
  { value: 'mes_passado', label: 'Mês Passado' },
  { value: 'trimestre_atual', label: 'Este Trimestre' },
  { value: 'ano_atual', label: 'Este Ano' },
  { value: 'personalizado', label: 'Período Personalizado' },
];

export const CRM_PERIODO_PADRAO: CrmPeriodoOption[] = [
  { value: 'mes_atual', label: 'Este mês' },
  { value: 'mes_passado', label: 'Mês passado' },
  { value: 'trimestre_atual', label: 'Este trimestre' },
  { value: 'ano_atual', label: 'Este ano' },
  { value: 'personalizado', label: 'Personalizado' },
];

export const CRM_PERIODO_FINANCEIRO: CrmPeriodoOption[] = [
  { value: 'mes_atual', label: 'Mês atual' },
  { value: 'mes_passado', label: 'Mês passado' },
  { value: 'trimestre_atual', label: 'Trimestre atual' },
  { value: 'ano_atual', label: 'Ano atual' },
  { value: 'personalizado', label: 'Personalizado' },
];

export const CRM_PERIODO_COMISSAO: CrmPeriodoOption[] = [
  { value: 'mes_atual', label: 'Este Mês' },
  { value: 'mes_passado', label: 'Mês Passado' },
  { value: 'trimestre_atual', label: 'Este Trimestre' },
  { value: 'personalizado', label: 'Personalizado' },
];

export const CRM_PERIODO_DASHBOARD_FILTRO: CrmPeriodoOption[] = [
  { value: 'mes_atual', label: 'Este mês' },
  { value: 'mes_passado', label: 'Mês passado' },
  { value: 'trimestre_atual', label: 'Este trimestre' },
  { value: 'ano_atual', label: 'Este ano' },
];

export const CRM_PERIODO_NOME: Record<string, string> = {
  mes_atual: 'Este mês',
  mes_passado: 'Mês passado',
  trimestre_atual: 'Este trimestre',
  ano_atual: 'Este ano',
};

export const CRM_PERIODO_CARD_LABELS: Record<
  string,
  { receita: string; comissao: string; leads: string; comissaoSub: string }
> = {
  mes_atual: {
    receita: 'Receita do mês',
    comissao: 'Comissão do mês',
    leads: 'Novos leads',
    comissaoSub: 'Vendas ganhas neste mês',
  },
  mes_passado: {
    receita: 'Receita do mês passado',
    comissao: 'Comissão do mês passado',
    leads: 'Novos leads',
    comissaoSub: 'Vendas ganhas no mês passado',
  },
  trimestre_atual: {
    receita: 'Receita do trimestre',
    comissao: 'Comissão do trimestre',
    leads: 'Novos leads no trimestre',
    comissaoSub: 'Vendas ganhas no trimestre (últimos 3 meses)',
  },
  ano_atual: {
    receita: 'Receita do ano',
    comissao: 'Comissão do ano',
    leads: 'Novos leads no ano',
    comissaoSub: 'Vendas ganhas neste ano',
  },
};

export function crmLabelsPeriodo(periodo: string) {
  return CRM_PERIODO_CARD_LABELS[periodo] ?? CRM_PERIODO_CARD_LABELS.mes_atual;
}

function fmtDataLocal(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

/** Intervalo de datas para filtros no frontend (espelha lógica do backend). */
export function crmDatasPeriodo(
  periodo: string,
  ref: Date = new Date(),
): { dataInicio: string; dataFim: string } | null {
  const hoje = ref;

  if (periodo === 'mes_atual') {
    const inicio = new Date(hoje.getFullYear(), hoje.getMonth(), 1);
    const fim = new Date(hoje.getFullYear(), hoje.getMonth() + 1, 0);
    return { dataInicio: fmtDataLocal(inicio), dataFim: fmtDataLocal(fim) };
  }

  if (periodo === 'mes_passado') {
    const primeiroMesAtual = new Date(hoje.getFullYear(), hoje.getMonth(), 1);
    const ultimoMesPassado = new Date(primeiroMesAtual.getTime() - 86400000);
    const inicio = new Date(ultimoMesPassado.getFullYear(), ultimoMesPassado.getMonth(), 1);
    const fim = new Date(inicio.getFullYear(), inicio.getMonth() + 1, 0);
    return { dataInicio: fmtDataLocal(inicio), dataFim: fmtDataLocal(fim) };
  }

  if (periodo === 'trimestre_atual') {
    const inicio = new Date(hoje.getFullYear(), hoje.getMonth() - 2, 1);
    return { dataInicio: fmtDataLocal(inicio), dataFim: fmtDataLocal(hoje) };
  }

  if (periodo === 'ano_atual') {
    const inicio = new Date(hoje.getFullYear(), 0, 1);
    return { dataInicio: fmtDataLocal(inicio), dataFim: fmtDataLocal(hoje) };
  }

  return null;
}

/** Período padrão ao abrir o pipeline de vendas. */
export const CRM_PIPELINE_PERIODO_PADRAO = 'mes_atual';

export const CRM_PERIODO_PIPELINE: CrmPeriodoOption[] = [
  { value: 'mes_atual', label: 'Este mês' },
  { value: 'mes_passado', label: 'Mês passado' },
  { value: 'trimestre_atual', label: 'Este trimestre' },
  { value: 'ano_atual', label: 'Este ano' },
  { value: 'todos', label: 'Todas as oportunidades' },
  { value: 'personalizado', label: 'Personalizado' },
];

/** Período anterior para comparação de tendência no dashboard. */
export function crmPeriodoAnteriorComparavel(
  periodo: string,
): { periodo: string; data_inicio?: string; data_fim?: string } | null {
  const fmt = (d: Date) => d.toISOString().slice(0, 10);
  const hoje = new Date();

  if (periodo === 'mes_atual') {
    return { periodo: 'mes_passado' };
  }

  if (periodo === 'mes_passado') {
    const primeiroMesAtual = new Date(hoje.getFullYear(), hoje.getMonth(), 1);
    const ultimoMesAnterior = new Date(primeiroMesAtual.getTime() - 86400000);
    const inicio = new Date(ultimoMesAnterior.getFullYear(), ultimoMesAnterior.getMonth(), 1);
    const fim = new Date(inicio.getFullYear(), inicio.getMonth() + 1, 0);
    return { periodo: 'personalizado', data_inicio: fmt(inicio), data_fim: fmt(fim) };
  }

  if (periodo === 'trimestre_atual') {
    const fimAtual = hoje;
    const inicioAtual = new Date(hoje.getFullYear(), hoje.getMonth() - 2, 1);
    const dias = Math.round((fimAtual.getTime() - inicioAtual.getTime()) / 86400000);
    const fimAnterior = new Date(inicioAtual.getTime() - 86400000);
    const inicioAnterior = new Date(fimAnterior.getTime() - dias * 86400000);
    return { periodo: 'personalizado', data_inicio: fmt(inicioAnterior), data_fim: fmt(fimAnterior) };
  }

  if (periodo === 'ano_atual') {
    const inicioAnoPassado = new Date(hoje.getFullYear() - 1, 0, 1);
    const fimAnoPassado = new Date(hoje.getFullYear() - 1, hoje.getMonth(), hoje.getDate());
    return { periodo: 'personalizado', data_inicio: fmt(inicioAnoPassado), data_fim: fmt(fimAnoPassado) };
  }

  return null;
}

export function calcularVariacaoPct(
  atual: number,
  anterior: number,
): { trend?: 'up' | 'down'; trendValue?: string } {
  if (anterior === 0) {
    if (atual > 0) return { trend: 'up', trendValue: 'novo' };
    return {};
  }
  const pct = ((atual - anterior) / Math.abs(anterior)) * 100;
  const rounded = Math.round(pct * 10) / 10;
  const sign = rounded > 0 ? '+' : '';
  return {
    trend: rounded >= 0 ? 'up' : 'down',
    trendValue: `${sign}${rounded}%`,
  };
}
