export const rosa = "var(--cb-primary, #8B3D52)";

export type ProdutoLinha = {
  id: number;
  produto: number;
  produto_nome: string;
  quantidade: number | string;
  preco_unitario?: number | string;
  desconto?: number | string;
  finalidade?: string;
};

export type ProdutoOpcao = {
  id: number;
  nome: string;
  preco_venda?: number | string;
  vende_ao_cliente?: boolean;
  is_active?: boolean;
};

export type VendaLinha = { produto: number; nome: string; quantidade: string; preco: string; desconto: string };

export type EntregaRecibo = {
  paymentId: number;
  cliente: string;
  numero: number;
  total: string;
  forma: string;
  quando: string;
  telefone: string;
  email: string;
};

export type VendaHistorico = {
  id: number;
  payment_id: number;
  cliente: string;
  total: string;
  status: string;
  operador: string;
  telefone?: string;
  email?: string;
  forma?: string;
  criada_em?: string;
};

export type FechamentoCaixa = {
  id: number;
  nome: string;
  operador: string;
  aberta_em: string;
  fechada_em: string;
  vendas_produtos: number;
  recebido: number;
  a_receber: number;
  vendas: VendaHistorico[];
};

export function listaDe<T>(corpo: unknown): T[] {
  if (Array.isArray(corpo)) return corpo as T[];
  if (corpo && typeof corpo === "object" && Array.isArray((corpo as { results?: T[] }).results)) {
    return (corpo as { results: T[] }).results;
  }
  return [];
}

export function mensagemErro(erro: unknown, fallback: string): string {
  if (erro && typeof erro === "object" && "error" in erro) return String((erro as { error?: string }).error || fallback);
  if (erro instanceof Error && erro.message) return erro.message;
  return fallback;
}
