import apiClient from '@/lib/api-client';

export type TipoFinanceiro = 'receita' | 'despesa';

export interface GrupoFinanceiro {
  id: number;
  nome: string;
  tipo: TipoFinanceiro;
  is_active: boolean;
  ordem: number;
}

export interface LancamentoFinanceiro {
  id: number;
  vendedor: number;
  vendedor_nome: string;
  grupo: number | null;
  grupo_nome: string;
  tipo: TipoFinanceiro;
  tipo_display: string;
  origem: string;
  origem_display: string;
  descricao: string;
  valor: number;
  status: string;
  status_display: string;
  data_vencimento: string;
  data_pagamento: string | null;
  oportunidade: number | null;
  oportunidade_titulo: string;
  observacoes: string;
  editavel: boolean;
}

export interface ResumoFinanceiro {
  receitas_pagas: number;
  receitas_pendentes: number;
  despesas_pagas: number;
  despesas_pendentes: number;
  saldo_realizado: number;
  saldo_previsto: number;
  comissao_vendas_total: number;
}

export interface VendedorOption {
  id: number;
  nome: string;
}

export type FinanceiroConfirmAction =
  | { type: 'excluir_lancamento'; item: LancamentoFinanceiro }
  | { type: 'excluir_grupo'; grupo: GrupoFinanceiro }
  | { type: 'sync_comissoes' }
  | null;

export async function fetchLancamentosPorTipo(
  tipo: TipoFinanceiro,
  vendedorFiltro: string,
  periodo: string,
  dataInicio: string,
  dataFim: string,
): Promise<LancamentoFinanceiro[]> {
  const params = new URLSearchParams({ tipo, page_size: '100', periodo });
  if (vendedorFiltro) params.set('vendedor_id', vendedorFiltro);
  if (periodo === 'personalizado' && dataInicio && dataFim) {
    params.set('data_inicio', dataInicio);
    params.set('data_fim', dataFim);
  }
  const { data } = await apiClient.get<{ results?: LancamentoFinanceiro[] } | LancamentoFinanceiro[]>(
    `crm-vendas/financeiro-lancamentos/?${params}`,
  );
  return Array.isArray(data) ? data : data.results ?? [];
}
