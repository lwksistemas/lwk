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

/** Etapas completas do pipeline (config + Kanban) — fonte única no frontend */
export const ETAPAS_PIPELINE_PADRAO = [
  { key: 'prospecting', label: 'Prospecção', ordem: 1, ativo: true },
  { key: 'qualification', label: 'Qualificação', ordem: 2, ativo: true },
  { key: 'proposal', label: 'Proposta', ordem: 3, ativo: true },
  { key: 'negotiation', label: 'Negociação', ordem: 4, ativo: true },
  { key: 'closed_won', label: 'Fechado ganho', ordem: 5, ativo: true },
  { key: 'closed_lost', label: 'Fechado perdido', ordem: 6, ativo: true },
] as const;

export type CrmEtapaPipeline = { key: string; label: string; ordem: number };
