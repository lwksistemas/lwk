export interface OrcamentoItem {
  id: number;
  procedure_id: number | null;
  nome_procedimento: string;
  valor_original: string;
  valor_customizado: string;
  quantidade: number;
  observacao_item: string;
  subtotal: string;
}

export interface Orcamento {
  id: number;
  consulta_id: number;
  patient_name: string;
  professional_name: string;
  observacoes: string;
  valor_total: string;
  validade_dias: number;
  status: string;
  enviado_email: boolean;
  enviado_whatsapp: boolean;
  data_envio: string | null;
  created_at: string;
  itens: OrcamentoItem[];
}

export interface Procedure {
  id: number;
  nome: string;
  preco: string;
  categoria: string;
}

export interface ItemForm {
  procedure_id: number;
  nome: string;
  valor: string;
  qtd: number;
}
