import { fetchAllPaginatedResults } from '@/lib/crm-utils';

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
  /** IDs reais quando a linha é comissão agregada na tabela. */
  ids_agregados?: number[];
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
  | { type: 'receber_comissoes'; item: LancamentoFinanceiro; ids: number[] }
  | { type: 'cancelar_comissoes'; item: LancamentoFinanceiro; ids: number[] }
  | null;

export async function fetchLancamentosPorTipo(
  tipo: TipoFinanceiro,
  vendedorFiltro: string,
  periodo: string,
  dataInicio: string,
  dataFim: string,
): Promise<LancamentoFinanceiro[]> {
  const params: Record<string, string | number> = { tipo, periodo };
  if (vendedorFiltro) params.vendedor_id = vendedorFiltro;
  if (periodo === 'personalizado' && dataInicio && dataFim) {
    params.data_inicio = dataInicio;
    params.data_fim = dataFim;
  }
  return fetchAllPaginatedResults<LancamentoFinanceiro>(
    '/crm-vendas/financeiro-lancamentos/',
    params,
  );
}
