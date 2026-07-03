import type { useAgendamentoCadastros } from "@/hooks/clinica-beleza/useAgendamentoCadastros";
import type { useConsultasAgendaModals } from "./useConsultasPage";

export type ConsultasAgendamentoCadastros = Pick<
  ReturnType<typeof useAgendamentoCadastros>,
  | "patients"
  | "professionals"
  | "procedures"
  | "nomesAgenda"
  | "locaisAtendimento"
  | "setPatients"
  | "searchPatients"
>;

export type ConsultasAgendaModalsApi = ReturnType<typeof useConsultasAgendaModals>;
