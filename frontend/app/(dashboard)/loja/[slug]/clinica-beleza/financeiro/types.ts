export interface FinanceiroResumo {
  caixa_diario: number;
  total_mes: number;
  contas_a_receber: number;
  comissao_mes: number;
  despesas_operacionais?: number;
  despesas_pendentes?: number;
  despesas: number;
  lucro: number;
}

export interface FinanceiroPayment {
  id: number;
  appointment: number;
  amount: string;
  payment_method: string;
  status: string;
  payment_date: string | null;
  comissao_percentual: number;
  comissao_valor: string;
  paciente_nome: string;
  profissional_nome: string;
  procedimento_nome: string;
  data_atendimento: string;
  created_at: string;
}

export interface FinanceiroProfessional {
  id: number;
  name?: string;
  nome?: string;
}

export type FinanceiroTab = "receitas" | "despesas";
