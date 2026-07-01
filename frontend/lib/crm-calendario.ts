export const API_CRM_CALENDARIO = '/crm-vendas';
export const API_GOOGLE_STATUS = `${API_CRM_CALENDARIO}/google-calendar/status/`;
export const API_GOOGLE_AUTH = `${API_CRM_CALENDARIO}/google-calendar/auth/`;
export const API_GOOGLE_SYNC = `${API_CRM_CALENDARIO}/google-calendar/sync/`;
export const API_GOOGLE_DISCONNECT = `${API_CRM_CALENDARIO}/google-calendar/disconnect/`;
export const SYNC_RESULT_DISPLAY_MS = 5000;
export const MOBILE_BREAKPOINT = 640;

export interface Atividade {
  id: number;
  titulo: string;
  tipo: 'call' | 'meeting' | 'email' | 'task';
  oportunidade: number | null;
  lead: number | null;
  lead_nome?: string;
  conta: number | null;
  conta_nome?: string;
  data: string;
  duracao_minutos?: number;
  concluido: boolean;
  observacoes: string;
  lembrete_whatsapp?: boolean;
  lembrete_whatsapp_telefone?: string;
  created_at: string;
  updated_at: string;
}

export interface CalendarEvent {
  id: string;
  title: string;
  start: string;
  end: string;
  backgroundColor: string;
  borderColor: string;
  extendedProps: { atividade: Atividade };
}

export const TIPO_LABEL: Record<string, string> = {
  call: 'Ligação',
  meeting: 'Reunião',
  email: 'Email',
  task: 'Tarefa',
};

export const TIPO_COR: Record<string, { bg: string; border: string }> = {
  call: { bg: '#0ea5e9', border: '#0284c7' },
  meeting: { bg: '#6366f1', border: '#4f46e5' },
  email: { bg: '#8b5cf6', border: '#7c3aed' },
  task: { bg: '#22c55e', border: '#16a34a' },
};

export function toISO(date: Date): string {
  return date.toISOString().slice(0, 19) + 'Z';
}

export function atividadeToEvent(a: Atividade): CalendarEvent {
  const d = new Date(a.data);
  const end = new Date(d);
  const duracao = a.duracao_minutos ?? 60;
  end.setMinutes(end.getMinutes() + duracao);
  const cor = TIPO_COR[a.tipo] ?? TIPO_COR.task;
  return {
    id: String(a.id),
    title: a.concluido ? `✓ ${a.titulo}` : a.titulo,
    start: a.data,
    end: toISO(end),
    backgroundColor: a.concluido ? '#94a3b8' : cor.bg,
    borderColor: a.concluido ? '#64748b' : cor.border,
    extendedProps: { atividade: a },
  };
}

export type AtividadeFormState = {
  titulo: string;
  tipo: Atividade['tipo'];
  data: string;
  duracao_minutos: number;
  observacoes: string;
  conta: number | null;
  lead: number | null;
  lembrete_whatsapp: boolean;
  lembrete_whatsapp_telefone: string;
};

export const EMPTY_ATIVIDADE_FORM: AtividadeFormState = {
  titulo: '',
  tipo: 'task',
  data: '',
  duracao_minutos: 60,
  observacoes: '',
  conta: null,
  lead: null,
  lembrete_whatsapp: false,
  lembrete_whatsapp_telefone: '',
};

/** Formato `datetime-local` a partir de Date no fuso local. */
export function localDateTimeInputFromDate(d: Date): string {
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  const hours = String(d.getHours()).padStart(2, '0');
  const minutes = String(d.getMinutes()).padStart(2, '0');
  return `${year}-${month}-${day}T${hours}:${minutes}`;
}

export function emptyAtividadeForm(whatsappAtivo: boolean): AtividadeFormState {
  return {
    ...EMPTY_ATIVIDADE_FORM,
    lembrete_whatsapp: whatsappAtivo,
  };
}
