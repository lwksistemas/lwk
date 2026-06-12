/**
 * Constantes compartilhadas da Clínica da Beleza (financeiro, agenda, consultas).
 */

export const CLINICA_FORMA_PAGAMENTO_LABEL: Record<string, string> = {
  CASH: 'Dinheiro',
  CREDIT_CARD: 'Crédito',
  DEBIT_CARD: 'Débito',
  PIX: 'PIX',
  TRANSFER: 'Transferência',
};

export const CLINICA_PAGAMENTO_STATUS_LABEL: Record<string, string> = {
  PENDING: 'Pendente',
  PAID: 'Pago',
  CANCELLED: 'Cancelado',
};

/** Status de agendamento na agenda (calendário, lista, conflito offline). */
export const CLINICA_AGENDA_STATUS_LABEL: Record<string, string> = {
  SCHEDULED: 'Aguardando confirmação',
  CONFIRMED: 'Confirmado',
  PENDING: 'Pendente',
  IN_PROGRESS: 'Em atendimento',
  COMPLETED: 'Concluído',
  CANCELLED: 'Cancelado',
  NO_SHOW: 'Faltou',
};

export const CLINICA_AGENDA_STATUS_COLORS: Record<string, { bg: string; border: string }> = {
  SCHEDULED: { bg: '#a855f7', border: '#9333ea' },
  CONFIRMED: { bg: '#22c55e', border: '#16a34a' },
  PENDING: { bg: '#f59e0b', border: '#d97706' },
  IN_PROGRESS: { bg: '#3b82f6', border: '#2563eb' },
  COMPLETED: { bg: '#0d9488', border: '#0f766e' },
  CANCELLED: { bg: '#dc2626', border: '#b91c1c' },
  NO_SHOW: { bg: '#b45309', border: '#92400e' },
};

export const CLINICA_AGENDA_BLOQUEIO_COLORS = { bg: '#4f46e5', border: '#4338ca' } as const;

/** Cores da legenda no header da agenda (usa CLINICA_AGENDA_STATUS_COLORS + intervalo). */
export const CLINICA_AGENDA_LEGEND_ITEMS: { key: string; label: string; bg: string }[] = [
  { key: 'SCHEDULED', label: CLINICA_AGENDA_STATUS_LABEL.SCHEDULED, bg: CLINICA_AGENDA_STATUS_COLORS.SCHEDULED.bg },
  { key: 'CONFIRMED', label: CLINICA_AGENDA_STATUS_LABEL.CONFIRMED, bg: CLINICA_AGENDA_STATUS_COLORS.CONFIRMED.bg },
  { key: 'NO_SHOW', label: CLINICA_AGENDA_STATUS_LABEL.NO_SHOW, bg: CLINICA_AGENDA_STATUS_COLORS.NO_SHOW.bg },
  { key: 'CANCELLED', label: CLINICA_AGENDA_STATUS_LABEL.CANCELLED, bg: CLINICA_AGENDA_STATUS_COLORS.CANCELLED.bg },
  { key: 'INTERVALO', label: 'Intervalo', bg: '#f59e0b' },
];

/** Opções de status editáveis na agenda (recepção). */
export const CLINICA_AGENDA_STATUS_OPCOES = [
  { value: 'SCHEDULED', label: '🟣 Aguardando confirmação' },
  { value: 'CONFIRMED', label: '🟢 Confirmado' },
  { value: 'PENDING', label: '🟠 Pendente' },
  { value: 'CANCELLED', label: '🔴 Cancelado' },
  { value: 'NO_SHOW', label: '⬜ Faltou' },
] as const;

/** Status da consulta clínica (fluxo em Consultas). */
export const CLINICA_CONSULTA_STATUS_LABEL: Record<string, string> = {
  SCHEDULED: 'AGUARDANDO INÍCIO',
  IN_PROGRESS: 'EM ATENDIMENTO',
  COMPLETED: 'CONCLUÍDA',
  CANCELLED: 'CANCELADA',
};

export const CLINICA_AGENDA_DURACAO_MIN_MIN = 5;
export const CLINICA_AGENDA_DURACAO_SNAP_MIN = 5;
