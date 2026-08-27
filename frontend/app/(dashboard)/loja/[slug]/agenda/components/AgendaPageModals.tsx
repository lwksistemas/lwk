import { ModalBloqueioHorario } from "@/components/clinica-beleza/modal-bloqueio-horario/ModalBloqueioHorario";
import { ModalConflitoAgenda } from "@/components/clinica-beleza/ModalConflitoAgenda";
import { ModalCriarAgendamento } from "@/components/clinica-beleza/ModalCriarAgendamento";
import type { AgendaEventData } from "@/lib/clinica-beleza-agenda-types";
import type { PatientQuickOption } from "@/components/clinica-beleza/patient-quick-register/patient-quick-register-types";
import type { ConsultaFormProcedure } from "@/hooks/clinica-beleza/useNovaConsultaForm";
import type { LocalAtendimentoItem, NomeAgendaItem } from "@/lib/clinica-beleza-api";
import { ModalBloqueio } from "./ModalBloqueio";
import { ModalDetalheAgendamento } from "./ModalDetalheAgendamento";

export function AgendaPageModals({
  selectedBloqueio,
  onCloseBloqueio,
  showModal,
  selectedEvent,
  onCloseDetalhe,
  onReload,
  onUpdateStatus,
  onSalvarDetalhe,
  onDelete,
  onReenviarWhatsApp,
  updatingStatus,
  salvandoDetalhe,
  reenviandoMensagem,
  showCreateModal,
  onCloseCreate,
  selectedDate,
  defaultProfessionalId,
  professionals,
  patients,
  procedures,
  nomesAgenda,
  locaisAtendimento,
  onPatientsChange,
  onSearchPatients,
  onOfflineEventCreated,
  showModalBloqueio,
  onCloseModalBloqueio,
  conflictData,
  onCloseConflict,
  onUseServer,
  onUseLocal,
  conflictResolving,
}: {
  selectedBloqueio: { id: number; motivo: string; professional_name: string } | null;
  onCloseBloqueio: () => void;
  showModal: boolean;
  selectedEvent: AgendaEventData | null;
  onCloseDetalhe: () => void;
  onReload: () => void;
  onUpdateStatus: (status: string) => Promise<void>;
  onSalvarDetalhe: (payload: {
    date?: string;
    professional?: number;
    procedures_ids?: number[];
  }) => Promise<void>;
  onDelete: () => Promise<void>;
  onReenviarWhatsApp: () => Promise<void>;
  updatingStatus: boolean;
  salvandoDetalhe: boolean;
  reenviandoMensagem: boolean;
  showCreateModal: boolean;
  onCloseCreate: () => void;
  selectedDate: Date | null;
  defaultProfessionalId: string;
  professionals: { id: number; nome?: string; name?: string }[];
  patients: PatientQuickOption[];
  procedures: ConsultaFormProcedure[];
  nomesAgenda: NomeAgendaItem[];
  locaisAtendimento: LocalAtendimentoItem[];
  onPatientsChange: (patients: PatientQuickOption[]) => void;
  onSearchPatients: (query: string) => Promise<PatientQuickOption[]>;
  onOfflineEventCreated: (evt: unknown) => void;
  showModalBloqueio: boolean;
  onCloseModalBloqueio: () => void;
  conflictData: unknown;
  onCloseConflict: () => void;
  onUseServer: () => void;
  onUseLocal: () => void;
  conflictResolving: boolean;
}) {
  return (
    <>
      <ModalBloqueio
        open={selectedBloqueio != null}
        onClose={onCloseBloqueio}
        onSuccess={onReload}
        bloqueio={selectedBloqueio}
      />
      <ModalDetalheAgendamento
        open={showModal && selectedEvent != null}
        onClose={onCloseDetalhe}
        event={selectedEvent!}
        professionals={professionals}
        procedures={procedures}
        onUpdateStatus={onUpdateStatus}
        onSalvarDetalhe={onSalvarDetalhe}
        onDelete={onDelete}
        onReenviarWhatsApp={onReenviarWhatsApp}
        updatingStatus={updatingStatus}
        salvandoDetalhe={salvandoDetalhe}
        reenviandoMensagem={reenviandoMensagem}
      />
      <ModalCriarAgendamento
        open={showCreateModal}
        onClose={onCloseCreate}
        onSuccess={onReload}
        selectedDate={selectedDate}
        defaultProfessionalId={defaultProfessionalId}
        professionals={professionals}
        patients={patients}
        procedures={procedures}
        nomesAgenda={nomesAgenda}
        locaisAtendimento={locaisAtendimento}
        onPatientsChange={onPatientsChange}
        onSearchPatients={onSearchPatients}
        onOfflineEventCreated={onOfflineEventCreated}
      />
      <ModalBloqueioHorario
        isOpen={showModalBloqueio}
        onClose={onCloseModalBloqueio}
        onSuccess={onReload}
        professionals={professionals}
        defaultProfessionalId={defaultProfessionalId}
      />
      <ModalConflitoAgenda
        open={conflictData != null}
        onClose={onCloseConflict}
        data={conflictData as never}
        onUseServer={onUseServer}
        onUseLocal={onUseLocal}
        resolving={conflictResolving}
      />
    </>
  );
}
