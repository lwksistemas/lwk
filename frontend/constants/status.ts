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

/** Status de agendamento para clínica de estética (dashboard + calendário). Fonte única para labels, cores e classes Tailwind. */
export const STATUS_AGENDAMENTO_CLINICA = [
  { value: 'agendado', label: 'Agendado', color: '#3B82F6', bg: 'bg-blue-100 dark:bg-blue-900/30', text: 'text-blue-800 dark:text-blue-300' },
  { value: 'confirmado', label: 'Confirmado', color: '#10B981', bg: 'bg-green-100 dark:bg-green-900/30', text: 'text-green-800 dark:text-green-300' },
  { value: 'em_atendimento', label: 'Em Atendimento', color: '#10B981', bg: 'bg-yellow-100 dark:bg-yellow-900/30', text: 'text-yellow-800 dark:text-yellow-300' },
  { value: 'concluido', label: 'Concluído', color: '#8B5CF6', bg: 'bg-purple-100 dark:bg-purple-900/30', text: 'text-purple-800 dark:text-purple-300' },
  { value: 'faltou', label: 'Faltou', color: '#F97316', bg: 'bg-orange-100 dark:bg-orange-900/30', text: 'text-orange-800 dark:text-orange-300' },
  { value: 'cancelado', label: 'Cancelado', color: '#EF4444', bg: 'bg-red-100 dark:bg-red-900/30', text: 'text-red-800 dark:text-red-300' },
] as const;

export type StatusAgendamentoClinica = typeof STATUS_AGENDAMENTO_CLINICA[number]['value'];

/** Retorna cor hex, label e emoji para um status (uso no calendário). */
export function getStatusClinicaInfo(status: string) {
  const item = STATUS_AGENDAMENTO_CLINICA.find(s => s.value === status);
  const labels: Record<string, string> = { agendado: '🔵', confirmado: '🟢', em_atendimento: '🟢', concluido: '✅', faltou: '🔴', cancelado: '⚪' };
  return {
    color: item?.color ?? '#6B7280',
    label: item?.label ?? status,
    emoji: labels[status] ?? '⚫',
  };
}

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
