/**
 * Constantes centralizadas do CRM Vendas.
 */

export const ETAPAS_OPORTUNIDADE = [
  { value: 'prospecting', label: 'Prospecção' },
  { value: 'qualification', label: 'Qualificação' },
  { value: 'proposal', label: 'Proposta' },
  { value: 'negotiation', label: 'Negociação' },
  { value: 'closed_won', label: 'Fechado ganho (venda)' },
  { value: 'closed_lost', label: 'Fechado perdido' },
] as const;

export const STATUS_LEAD_OPCOES = [
  { value: 'novo', label: 'Novo' },
  { value: 'contato', label: 'Contato feito' },
  { value: 'qualificado', label: 'Qualificado' },
  { value: 'perdido', label: 'Perdido' },
] as const;

/** Etapas padrão do pipeline (em andamento, excluindo fechadas) */
export const ETAPAS_DEFAULT = [
  'prospecting',
  'qualification',
  'proposal',
  'negotiation',
] as const;
