/** Evento do FullCalendar na agenda da Clínica da Beleza. */
export interface AgendaEventData {
  id: string;
  title: string;
  start: string;
  end: string;
  backgroundColor: string;
  borderColor: string;
  textColor: string;
  constraint?: "businessHours";
  editable?: boolean;
  durationEditable?: boolean;
  startEditable?: boolean;
  allDay?: boolean;
  classNames?: string[];
  extendedProps: {
    dbId?: number | string;
    status?: string;
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
    intervalo_inicio?: string;
    intervalo_fim?: string;
    consulta_id?: number;
  };
}

export type AgendaConflictPayload = {
  status?: string;
  date?: string;
  duracao_minutos?: number;
};
