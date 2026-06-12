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
  CLIENT_CONFIRMED: 'Confirmado pelo WhatsApp',
  PHONE_CONFIRMED: 'Confirmado por ligação',
  CONFIRMED: 'Cliente presente',
  PENDING: 'Aguardando confirmação',
  IN_PROGRESS: 'Em atendimento',
  COMPLETED: 'Concluído',
  CANCELLED: 'Cancelado',
  NO_SHOW: 'Faltou',
};

export const CLINICA_AGENDA_STATUS_COLORS: Record<string, { bg: string; border: string }> = {
  SCHEDULED: { bg: '#a855f7', border: '#9333ea' },
  CLIENT_CONFIRMED: { bg: '#06b6d4', border: '#0891b2' },
  PHONE_CONFIRMED: { bg: '#3b82f6', border: '#2563eb' },
  CONFIRMED: { bg: '#22c55e', border: '#16a34a' },
  PENDING: { bg: '#a855f7', border: '#9333ea' },
  IN_PROGRESS: { bg: '#8b5cf6', border: '#7c3aed' },
  COMPLETED: { bg: '#0d9488', border: '#0f766e' },
  CANCELLED: { bg: '#dc2626', border: '#b91c1c' },
  NO_SHOW: { bg: '#b45309', border: '#92400e' },
};

export const CLINICA_AGENDA_BLOQUEIO_COLORS = { bg: '#4f46e5', border: '#4338ca' } as const;

/** Cores da legenda no header da agenda (usa CLINICA_AGENDA_STATUS_COLORS + intervalo). */
export const CLINICA_AGENDA_LEGEND_ITEMS: { key: string; label: string; bg: string }[] = [
  { key: 'SCHEDULED', label: CLINICA_AGENDA_STATUS_LABEL.SCHEDULED, bg: CLINICA_AGENDA_STATUS_COLORS.SCHEDULED.bg },
  { key: 'CLIENT_CONFIRMED', label: CLINICA_AGENDA_STATUS_LABEL.CLIENT_CONFIRMED, bg: CLINICA_AGENDA_STATUS_COLORS.CLIENT_CONFIRMED.bg },
  { key: 'PHONE_CONFIRMED', label: CLINICA_AGENDA_STATUS_LABEL.PHONE_CONFIRMED, bg: CLINICA_AGENDA_STATUS_COLORS.PHONE_CONFIRMED.bg },
  { key: 'CONFIRMED', label: CLINICA_AGENDA_STATUS_LABEL.CONFIRMED, bg: CLINICA_AGENDA_STATUS_COLORS.CONFIRMED.bg },
  { key: 'NO_SHOW', label: CLINICA_AGENDA_STATUS_LABEL.NO_SHOW, bg: CLINICA_AGENDA_STATUS_COLORS.NO_SHOW.bg },
  { key: 'CANCELLED', label: CLINICA_AGENDA_STATUS_LABEL.CANCELLED, bg: CLINICA_AGENDA_STATUS_COLORS.CANCELLED.bg },
  { key: 'INTERVALO', label: 'Intervalo', bg: '#f59e0b' },
];

/** Opções de status no modal Detalhes do Agendamento (mesma ordem da legenda). */
export const CLINICA_AGENDA_STATUS_OPCOES_MODAL = [
  { value: 'SCHEDULED', label: '🟣 Aguardando confirmação' },
  { value: 'CLIENT_CONFIRMED', label: '💬 Confirmado pelo WhatsApp' },
  { value: 'PHONE_CONFIRMED', label: '📞 Confirmado por ligação' },
  { value: 'CONFIRMED', label: '🟢 Cliente presente' },
  { value: 'NO_SHOW', label: '⬜ Faltou' },
  { value: 'CANCELLED', label: '🔴 Cancelado' },
] as const;

/** @deprecated Use CLINICA_AGENDA_STATUS_OPCOES_MODAL */
export const CLINICA_AGENDA_STATUS_OPCOES_SECRETARIA = CLINICA_AGENDA_STATUS_OPCOES_MODAL;
export const CLINICA_AGENDA_STATUS_OPCOES = CLINICA_AGENDA_STATUS_OPCOES_MODAL;

/** PENDING legado equivale a SCHEDULED na exibição. */
export function normalizeAgendaStatus(status: string): string {
  return status === 'PENDING' ? 'SCHEDULED' : status;
}

export function getAgendaStatusLabel(status: string): string {
  return CLINICA_AGENDA_STATUS_LABEL[normalizeAgendaStatus(status)] || status;
}

/** Opções do select — lista completa + status atual se for só leitura (ex.: em atendimento). */
export function getAgendaStatusOpcoesModal(currentStatus: string) {
  const normalized = normalizeAgendaStatus(currentStatus);
  const base = [...CLINICA_AGENDA_STATUS_OPCOES_MODAL];
  if (base.some((o) => o.value === normalized)) {
    return base;
  }
  return [
    { value: currentStatus, label: getAgendaStatusLabel(currentStatus) },
    ...base,
  ];
}

/** Status da consulta clínica (fluxo em Consultas). */
export const CLINICA_CONSULTA_STATUS_LABEL: Record<string, string> = {
  SCHEDULED: 'AGUARDANDO INÍCIO',
  IN_PROGRESS: 'EM ATENDIMENTO',
  COMPLETED: 'CONCLUÍDA',
  CANCELLED: 'CANCELADA',
};

export const CLINICA_AGENDA_DURACAO_MIN_MIN = 5;
export const CLINICA_AGENDA_DURACAO_SNAP_MIN = 5;
/** Intervalo visual da grade e dos rótulos de horário (apenas exibição). */
export const CLINICA_AGENDA_SLOT_LABEL_MIN = 15;
export const CLINICA_AGENDA_SLOT_VISUAL_MIN = 15;

function padDurationMinutes(min: number): string {
  return `00:${String(min).padStart(2, '0')}:00`;
}

/** Grade/labels da agenda (visual mais limpa — a cada 15 min). */
export const CLINICA_AGENDA_SLOT_DURATION = padDurationMinutes(CLINICA_AGENDA_SLOT_VISUAL_MIN);
export const CLINICA_AGENDA_SLOT_LABEL_INTERVAL = padDurationMinutes(CLINICA_AGENDA_SLOT_LABEL_MIN);
/** Snap ao clicar, arrastar e redimensionar (mínimo 5 min). */
export const CLINICA_AGENDA_SNAP_DURATION = padDurationMinutes(CLINICA_AGENDA_DURACAO_SNAP_MIN);
