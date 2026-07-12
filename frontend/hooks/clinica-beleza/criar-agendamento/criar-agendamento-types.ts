import type { PatientQuickOption } from "@/components/clinica-beleza/patient-quick-register/patient-quick-register-types";
import type {
  CriarAgendamentoProfessional,
  ModalCriarAgendamentoMode,
} from "@/components/clinica-beleza/criar-agendamento/criar-agendamento-utils";
import type { ConsultaFormProcedure } from "@/hooks/clinica-beleza/useNovaConsultaForm";
import type { LocalAtendimentoItem, NomeAgendaItem } from "@/lib/clinica-beleza-api";

export interface UseCriarAgendamentoOptions {
  open: boolean;
  mode?: ModalCriarAgendamentoMode;
  selectedDate: Date | null;
  defaultProfessionalId?: string;
  professionals: CriarAgendamentoProfessional[];
  patients: PatientQuickOption[];
  procedures: ConsultaFormProcedure[];
  nomesAgenda: NomeAgendaItem[];
  locaisAtendimento: LocalAtendimentoItem[];
  onClose: () => void;
  onSuccess: () => void;
  onPatientsChange: (patients: PatientQuickOption[]) => void;
  onConsultaCreated?: (consultaId: number) => void;
  onOfflineEventCreated?: (event: unknown) => void;
}
