export interface CrmOportunidadeLeadOption {
  id: number;
  nome: string;
  empresa?: string;
  conta?: number | null;
}

export interface CrmOportunidadeContaOption {
  id: number;
  nome: string;
  cnpj?: string;
  tipo?: string;
}

export interface CrmOportunidadeProdutoOption {
  id: number;
  nome: string;
  tipo: string;
  preco: string;
  codigo?: string;
  categoria_nome?: string;
}

export interface CrmOportunidadeItemForm {
  produto_servico_id: number;
  quantidade: string;
  preco_unitario: string;
}

export interface CrmOportunidadeFormState {
  lead_id: string;
  titulo: string;
  empresa_prestadora_id: string;
  valor: string;
  etapa: string;
  valor_comissao: string;
  itens: CrmOportunidadeItemForm[];
}

export const CRM_OPORTUNIDADE_FORM_INICIAL: CrmOportunidadeFormState = {
  lead_id: '',
  titulo: '',
  empresa_prestadora_id: '',
  valor: '0',
  etapa: 'prospecting',
  valor_comissao: '',
  itens: [],
};
