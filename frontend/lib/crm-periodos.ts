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
