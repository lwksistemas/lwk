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
  DRAFT: 'Rascunho (consulta)',
  PAID: 'Pago',
  PARTIAL: 'Parcial',
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
  COMPLETED: 'Finalizada',
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
  COMPLETED: { bg: '#047857', border: '#065f46' },
  CANCELLED: { bg: '#dc2626', border: '#b91c1c' },
  NO_SHOW: { bg: '#b45309', border: '#92400e' },
};

export type AgendaStatusColor = { bg: string; border: string };
export type AgendaStatusColorMap = Record<string, AgendaStatusColor>;

/** Status editáveis na identidade visual (PENDING = SCHEDULED). */
export const CLINICA_AGENDA_STATUS_COLOR_EDITABLE = [
  'SCHEDULED',
  'CLIENT_CONFIRMED',
  'PHONE_CONFIRMED',
  'CONFIRMED',
  'IN_PROGRESS',
  'COMPLETED',
  'CANCELLED',
  'NO_SHOW',
] as const;

export function mergeAgendaStatusColors(
  overrides?: Record<string, { bg?: string; border?: string }> | null,
): AgendaStatusColorMap {
  const merged: AgendaStatusColorMap = { ...CLINICA_AGENDA_STATUS_COLORS };
  if (!overrides || typeof overrides !== 'object') return merged;
  for (const key of CLINICA_AGENDA_STATUS_COLOR_EDITABLE) {
    const entry = overrides[key];
    if (!entry) continue;
    const bg = typeof entry.bg === 'string' ? entry.bg.trim() : '';
    const border = typeof entry.border === 'string' ? entry.border.trim() : '';
    if (/^#[0-9A-Fa-f]{6}$/.test(bg) && /^#[0-9A-Fa-f]{6}$/.test(border)) {
      merged[key] = { bg: bg.toLowerCase(), border: border.toLowerCase() };
      if (key === 'SCHEDULED') {
        merged.PENDING = merged.SCHEDULED;
      }
    }
  }
  return merged;
}

export function getAgendaStatusColor(
  status: string,
  colors: AgendaStatusColorMap = CLINICA_AGENDA_STATUS_COLORS,
): AgendaStatusColor {
  const key = normalizeAgendaStatus(status);
  return colors[key] || colors.SCHEDULED || { bg: '#a855f7', border: '#9333ea' };
}

export const CLINICA_AGENDA_BLOQUEIO_COLORS = { bg: '#4f46e5', border: '#4338ca' } as const;

/** Opções de status no modal Detalhes do Agendamento. */
export const CLINICA_AGENDA_STATUS_OPCOES_MODAL = [
  { value: 'SCHEDULED', label: '🟣 Aguardando confirmação' },
  { value: 'CLIENT_CONFIRMED', label: '💬 Confirmado pelo WhatsApp' },
  { value: 'PHONE_CONFIRMED', label: '📞 Confirmado por ligação' },
  { value: 'CONFIRMED', label: '🟢 Cliente presente' },
  { value: 'NO_SHOW', label: '⬜ Faltou' },
  { value: 'CANCELLED', label: '🔴 Cancelado' },
] as const;

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
  RECEBER: 'INICIAR CONSULTA',
  SCHEDULED: 'AGUARDANDO INÍCIO',
  IN_PROGRESS: 'EM ATENDIMENTO',
  COMPLETED: 'FINALIZADA',
  CANCELLED: 'CANCELADA',
};

export const CLINICA_CONSULTA_STATUS_COLORS: Record<string, { bg: string; text: string }> = {
  RECEBER: { bg: 'bg-amber-100 dark:bg-amber-900/30', text: 'text-amber-800 dark:text-amber-300' },
  SCHEDULED: { bg: 'bg-gray-100 dark:bg-neutral-800', text: 'text-gray-700 dark:text-gray-300' },
  IN_PROGRESS: { bg: 'bg-violet-100 dark:bg-violet-900/30', text: 'text-violet-800 dark:text-violet-300' },
  COMPLETED: { bg: 'bg-emerald-100 dark:bg-emerald-900/30', text: 'text-emerald-800 dark:text-emerald-300' },
  CANCELLED: { bg: 'bg-red-100 dark:bg-red-900/30', text: 'text-red-800 dark:text-red-300' },
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
