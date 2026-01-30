/** Tipos e interfaces do dashboard Restaurante */

export interface LojaInfo {
  id: number;
  nome: string;
  slug: string;
  tipo_loja_nome: string;
  cor_primaria: string;
  cor_secundaria: string;
  logo?: string;
}

export interface EstatisticasRestaurante {
  pedidos_hoje: number;
  mesas_ocupadas: string;
  cardapio: number;
  faturamento: number;
}

export interface Categoria {
  id: number;
  nome: string;
  ordem?: number;
}

export interface ItemCardapio {
  id: number;
  nome: string;
  descricao: string;
  categoria: number | null;
  preco: string;
  tempo_preparo: number;
  is_disponivel: boolean;
  is_destaque?: boolean;
}

export interface Mesa {
  id: number;
  numero: string;
  capacidade: number;
  localizacao?: string;
  status: string;
  is_active: boolean;
}

export interface Cliente {
  id: number;
  nome: string;
  email?: string;
  telefone?: string;
  endereco?: string;
}

export interface Pedido {
  id: number;
  tipo: string;
  status: string;
  total: string;
  mesa?: number | null;
  cliente?: number | null;
  endereco_entrega?: string | null;
  taxa_entrega?: string;
  created_at: string;
  itens?: { item_cardapio: { nome: string }; quantidade: number; preco_unitario: string }[];
}

export interface Funcionario {
  id: number;
  nome: string;
  email?: string;
  telefone?: string;
  cargo: string;
  is_admin?: boolean;
}

export interface Fornecedor {
  id: number;
  nome: string;
  cnpj?: string;
  email?: string;
  telefone?: string;
  endereco?: string;
}

export interface NotaFiscalEntrada {
  id: number;
  numero: string;
  fornecedor: number;
  fornecedor_nome?: string;
  data_emissao: string | null;
  data_entrada: string | null;
  valor_total: string;
  xml_file: string | null;
  aplicado_estoque: boolean;
  observacoes?: string | null;
  created_at: string;
}

export interface EstoqueItem {
  id: number;
  nome: string;
  unidade: string;
  quantidade_atual: string;
  quantidade_minima: string;
  observacoes?: string | null;
  is_active: boolean;
}

export interface MovimentoEstoque {
  id: number;
  estoque_item: number;
  estoque_item_nome?: string;
  quantidade: string;
  tipo: 'entrada' | 'saida';
  observacao?: string | null;
  created_at: string;
}

export interface RegistroPesoBalança {
  id: number;
  estoque_item: number;
  estoque_item_nome?: string;
  peso_kg: string;
  adicionar_ao_estoque: boolean;
  observacao?: string | null;
  created_at: string;
}

export const STATUS_MESA = [
  { value: 'livre', label: 'Livre' },
  { value: 'ocupada', label: 'Ocupada' },
  { value: 'reservada', label: 'Reservada' },
  { value: 'manutencao', label: 'Manutenção' },
] as const;

export const CARGO_FUNCIONARIO = [
  { value: 'garcom', label: 'Garçom' },
  { value: 'cozinheiro', label: 'Cozinheiro' },
  { value: 'gerente', label: 'Gerente' },
  { value: 'caixa', label: 'Caixa' },
  { value: 'outro', label: 'Outro' },
] as const;
