/**
 * Tipos do formulário de contrato CRM.
 */

import type { EmitenteLojaFields } from '@/lib/crm-emitente-loja';
import { EMPTY_EMITENTE_LOJA } from '@/lib/crm-emitente-loja';

export interface FormDataContrato extends EmitenteLojaFields {
  oportunidade_id: string;
  numero: string;
  titulo: string;
  conteudo: string;
  valor_total: string;
  desconto_tipo: 'percentual' | 'valor';
  desconto_valor: string;
  status: string;
  nome_vendedor_assinatura?: string;
  nome_cliente_assinatura?: string;
}

export const EMPTY_FORM_CONTRATO: FormDataContrato = {
  oportunidade_id: '',
  numero: '',
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
