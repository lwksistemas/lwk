/**
 * Tipos partilhados entre formulários de proposta (lista, nova, modais).
 */

export interface CrmPropostaOportunidadeOption {
  id: number;
  titulo: string;
  lead: number;
  lead_nome: string;
  valor: string;
  etapa: string;
  conta_nome?: string | null;
  empresa_prestadora?: number | null;
  empresa_prestadora_nome?: string | null;
}

export interface CrmOportunidadeItem {
  id: number;
  produto_servico: number;
  produto_servico_nome: string;
  produto_servico_tipo: string;
  quantidade: string;
  preco_unitario: string;
  subtotal: number;
  observacao?: string;
}

export interface CrmPropostaTemplate {
  id: number;
  nome: string;
  conteudo: string;
  is_padrao: boolean;
  ativo: boolean;
}
