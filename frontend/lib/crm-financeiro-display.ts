import type { LancamentoFinanceiro } from '@/lib/crm-financeiro-types';

/** IDs sintéticos para linhas agregadas de comissão (não existem na API). */
export const COMISSAO_AGREGADO_ID = {
  pendente: -1001,
  pago: -1002,
} as const;

export function isLancamentoComissaoAgregado(item: LancamentoFinanceiro): boolean {
  return item.id < 0 || (item.ids_agregados?.length ?? 0) > 0;
}

/**
 * Substitui lançamentos de comissão automática por uma linha total por status
 * (pendente / pago), mantendo despesas e receitas manuais linha a linha.
 */
export function prepararLancamentosParaTabela(itens: LancamentoFinanceiro[]): LancamentoFinanceiro[] {
  const manuais = itens.filter((i) => i.origem !== 'comissao_venda');
  const comissoes = itens.filter((i) => i.origem === 'comissao_venda');

  if (!comissoes.length) {
    return manuais;
  }

  const sinteticos: LancamentoFinanceiro[] = [];
  const base = comissoes[0];

  const agregar = (status: 'pendente' | 'pago', id: number, label: string) => {
    const subset = comissoes.filter((c) => c.status === status);
    if (!subset.length) return;
    const total = subset.reduce((s, c) => s + Number(c.valor), 0);
    const datasVenc = subset.map((c) => c.data_vencimento).filter(Boolean) as string[];
    const datasPag = subset.map((c) => c.data_pagamento).filter(Boolean) as string[];
    const dataVencimento = datasVenc.sort()[0] ?? base.data_vencimento;
    const dataPagamento =
      status === 'pago'
        ? (datasPag.sort().reverse()[0] ?? subset[0]?.data_pagamento ?? null)
        : null;
    const qtd = subset.length;
    sinteticos.push({
      ...base,
      id,
      descricao: qtd > 1 ? `${label} (${qtd} vendas)` : label,
      valor: total,
      status,
      status_display: status === 'pago' ? 'Pago' : 'Pendente',
      editavel: false,
      ids_agregados: subset.map((c) => c.id),
      data_vencimento: dataVencimento,
      data_pagamento: dataPagamento,
      oportunidade: null,
      oportunidade_titulo: '',
      observacoes:
        status === 'pago'
          ? 'Filtrado pelo mês em que o pagamento foi registrado (caixa).'
          : 'Filtrado pelo mês de vencimento (competência).',
    });
  };

  agregar('pendente', COMISSAO_AGREGADO_ID.pendente, 'Comissão de vendas');
  agregar('pago', COMISSAO_AGREGADO_ID.pago, 'Comissão de vendas');

  return [...sinteticos, ...manuais];
}
