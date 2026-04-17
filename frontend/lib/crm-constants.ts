/**
 * Rótulos e constantes compartilhadas do CRM Vendas (evita duplicar entre páginas).
 */

/** Status comercial da proposta */
export const CRM_PROPOSTA_STATUS_LABEL: Record<string, string> = {
  rascunho: 'Rascunho',
  enviada: 'Enviada',
  aceita: 'Aceita',
  rejeitada: 'Rejeitada',
  cancelada: 'Cancelada',
};

/** Status comercial do contrato */
export const CRM_CONTRATO_STATUS_LABEL: Record<string, string> = {
  rascunho: 'Rascunho',
  enviado: 'Enviado',
  assinado: 'Assinado',
  cancelado: 'Cancelado',
};

/** Workflow de assinatura digital (proposta/contrato) */
export const CRM_STATUS_ASSINATURA_LABEL: Record<string, string> = {
  rascunho: 'Rascunho',
  aguardando_cliente: 'Aguardando Cliente',
  aguardando_vendedor: 'Aguardando Vendedor',
  concluido: 'Concluído',
};
