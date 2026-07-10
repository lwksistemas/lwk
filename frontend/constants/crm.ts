/**
 * Constantes centralizadas do CRM Vendas.
 */

export const STATUS_LEAD_OPCOES = [
  { value: 'novo', label: 'Novo' },
  { value: 'contato', label: 'Contato feito' },
  { value: 'qualificado', label: 'Qualificado' },
  { value: 'perdido', label: 'Perdido' },
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
