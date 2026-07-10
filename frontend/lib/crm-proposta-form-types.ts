/**
 * Tipos partilhados entre formulários de proposta (lista, nova, modais).
 */

import type { EmitenteLojaFields } from '@/lib/crm-emitente-loja';
import { EMPTY_EMITENTE_LOJA } from '@/lib/crm-emitente-loja';

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

export interface OportunidadeItem {
  id: number;
  produto_servico: number;
  produto_servico_nome: string;
  produto_servico_tipo: string;
  produto_servico_recorrencia?: string;
  quantidade: string;
  preco_unitario: string;
  subtotal: number;
  observacao?: string;
}

/** Alias de compatibilidade com o nome anterior. */
export type CrmOportunidadeItem = OportunidadeItem;

export interface FormDataProposta extends EmitenteLojaFields {
  oportunidade_id: string;
  titulo: string;
  conteudo: string;
  valor_total: string;
  desconto_tipo: 'percentual' | 'valor';
  desconto_valor: string;
  status: string;
  nome_vendedor_assinatura?: string;
  nome_cliente_assinatura?: string;
}

export const EMPTY_FORM_PROPOSTA: FormDataProposta = {
  oportunidade_id: '',
  titulo: '',
  conteudo: '',
  valor_total: '',
  desconto_tipo: 'percentual',
  desconto_valor: '',
  status: 'rascunho',
  nome_vendedor_assinatura: '',
  nome_cliente_assinatura: '',
  ...EMPTY_EMITENTE_LOJA,
};

export interface CrmPropostaTemplate {
  id: number;
  nome: string;
  conteudo: string;
  is_padrao: boolean;
  ativo: boolean;
}
