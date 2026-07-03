import type { HorarioTrabalho } from "@/lib/clinica-beleza-work-hours";
import type { UseCriarAgendamentoOptions } from "./criar-agendamento-types";

export interface CriarAgendamentoSubmitContext {
  isConsulta: boolean;
  validateBase: () => string | null;
  resetForm: () => void;
  patientId: number | "";
  professionalId: number | "";
  convenioId: number | "";
  selectedProcedures: number[];
  resumo: { duracao: number; valor: number };
  dateInput: string;
  time: string;
  notes: string;
  nomeAgendaId: number | "";
  localAtendimentoId: number | "";
  retornoProcedureId: number | "";
  horariosProfissional: HorarioTrabalho[];
  setCreateLoading: (v: boolean) => void;
  setCreateError: (v: string) => void;
  setTime: (v: string) => void;
  setDateInput: (v: string) => void;
  setNotes: (v: string) => void;
  setNomeAgendaId: (v: number | "") => void;
  setLocalAtendimentoId: (v: number | "") => void;
}

export type CriarAgendamentoSubmitOptions = UseCriarAgendamentoOptions;
