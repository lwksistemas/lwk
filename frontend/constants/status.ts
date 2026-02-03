/**
 * Constantes de status compartilhadas entre os dashboards
 */

export const STATUS_AGENDAMENTO = [
  { value: 'agendado', label: 'Agendado', color: '#3B82F6' },
  { value: 'confirmado', label: 'Confirmado', color: '#10B981' },
  { value: 'em_andamento', label: 'Em Andamento', color: '#F59E0B' },
  { value: 'concluido', label: 'Concluído', color: '#059669' },
  { value: 'cancelado', label: 'Cancelado', color: '#EF4444' }
] as const;

export const STATUS_OS = [
  { value: 'aberta', label: 'Aberta', color: '#3B82F6' },
  { value: 'em_andamento', label: 'Em Andamento', color: '#F59E0B' },
  { value: 'aguardando_peca', label: 'Aguardando Peça', color: '#8B5CF6' },
  { value: 'concluida', label: 'Concluída', color: '#059669' },
  { value: 'cancelada', label: 'Cancelada', color: '#EF4444' }
] as const;

export const STATUS_LEAD = [
  { value: 'novo', label: 'Novo Lead' },
  { value: 'contato_inicial', label: 'Contato Inicial' },
  { value: 'qualificado', label: 'Qualificado' },
  { value: 'proposta_enviada', label: 'Proposta Enviada' },
  { value: 'negociacao', label: 'Negociação' },
  { value: 'fechado', label: 'Fechado' },
  { value: 'perdido', label: 'Perdido' }
] as const;

export const ORIGENS_CRM = [
  { value: 'site', label: 'Site' },
  { value: 'indicacao', label: 'Indicação' },
  { value: 'redes_sociais', label: 'Redes Sociais' },
  { value: 'email_marketing', label: 'Email Marketing' },
  { value: 'evento', label: 'Evento' },
  { value: 'telefone', label: 'Telefone' },
  { value: 'outro', label: 'Outro' }
] as const;

export const STATUS_PEDIDO = [
  { value: 'pendente', label: 'Pendente', color: '#6B7280' },
  { value: 'confirmado', label: 'Confirmado', color: '#3B82F6' },
  { value: 'preparando', label: 'Preparando', color: '#F59E0B' },
  { value: 'pronto', label: 'Pronto', color: '#10B981' },
  { value: 'entregue', label: 'Entregue', color: '#059669' },
  { value: 'cancelado', label: 'Cancelado', color: '#EF4444' }
] as const;

export const STATUS_MESA = [
  { value: 'livre', label: 'Livre', color: '#10B981' },
  { value: 'ocupada', label: 'Ocupada', color: '#EF4444' },
  { value: 'reservada', label: 'Reservada', color: '#F59E0B' }
] as const;
