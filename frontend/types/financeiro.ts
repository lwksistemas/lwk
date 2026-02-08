/**
 * Types para o sistema financeiro
 * Centralizado para reutilização (DRY)
 */

export interface Categoria {
  id: number;
  nome: string;
  tipo: 'receita' | 'despesa';
  descricao?: string;
  cor: string;
  is_active: boolean;
  created_at: string;
}

export interface Transacao {
  id: number;
  tipo: 'receita' | 'despesa';
  descricao: string;
  categoria: number;
  categoria_nome: string;
  categoria_cor: string;
  valor: number;
  valor_pago: number;
  valor_pendente: number;
  data_vencimento: string;
  data_pagamento?: string;
  status: 'pendente' | 'pago' | 'cancelado' | 'atrasado';
  forma_pagamento?: string;
  cliente?: number;
  cliente_nome?: string;
  agendamento?: number;
  observacoes?: string;
  is_recorrente: boolean;
  recorrencia_tipo?: string;
  esta_atrasado: boolean;
  created_at: string;
  updated_at: string;
  created_by?: string;
}

export interface ResumoFinanceiro {
  total_receitas: number;
  total_despesas: number;
  saldo: number;
  receitas_pendentes: number;
  despesas_pendentes: number;
  receitas_pagas: number;
  despesas_pagas: number;
  transacoes_atrasadas: number;
  valor_atrasado: number;
}

export interface TransacaoFormData {
  tipo: 'receita' | 'despesa';
  descricao: string;
  categoria: string;
  valor: string;
  data_vencimento: string;
  status: 'pendente' | 'pago';
  forma_pagamento: string;
  observacoes: string;
}

export type TabFinanceiro = 'resumo' | 'receitas' | 'despesas' | 'categorias';
