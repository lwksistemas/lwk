/** Evento do FullCalendar na agenda da Clínica da Beleza. */
export interface AgendaEventData {
  id: string;
  title: string;
  start: string;
  end: string;
  /** FC7: cor principal do evento (temas Pulse/Classic usam isto). */
  color?: string;
  /** FC7: cor do texto sobre o evento. */
  contrastColor?: string;
  /** Compat / grade própria; FC7 prefere `color`. */
  backgroundColor: string;
  borderColor: string;
  textColor: string;
  /** FC7: classe CSS (ex.: bloqueio). Preferir isto a `classNames`. */
  className?: string;
  display?: "auto" | "block" | "list-item" | "background" | "inverse-background" | "none";
  constraint?: "businessHours";
  editable?: boolean;
  durationEditable?: boolean;
  startEditable?: boolean;
  allDay?: boolean;
  /** @deprecated FC6; use `className`. Mantido para leituras antigas. */
  classNames?: string[];
  extendedProps: {
    dbId?: number | string;
    status?: string;
    patient?: number;
    patient_name?: string;
    patient_phone?: string;
    professional_name?: string;
    procedure_name?: string;
    procedure_duration?: number;
    duracao_minutos?: number;
    procedure_price?: string;
    notes?: string;
    version?: number;
    updated_at?: string;
    isBloqueio?: boolean;
    isIntervalo?: boolean;
    bloqueioId?: number;
    motivo?: string;
    professional?: number | null;
    procedures_list?: { id: number; nome?: string; categoria?: string; valor?: number }[];
    retorno_gratuito?: boolean;
    protocolo?: {
      nome: string;
      sessao: number;
      sessoes: number;
      forma_cobranca: "" | "POR_CONSULTA" | "TOTAL";
      valor_total: number;
      valor_sessao: number;
    };
    intervalo_inicio?: string;
    intervalo_fim?: string;
    consulta_id?: number;
  };
}

export type AgendaConflictPayload = {
  status?: string;
  date?: string;
  duracao_minutos?: number;
  professional?: number;
  procedures_ids?: number[];
};
