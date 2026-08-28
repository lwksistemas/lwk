"use client";

import { ModalCriarAgendamento } from "@/components/clinica-beleza/ModalCriarAgendamento";
import { AgendaConfigModals } from "@/components/clinica-beleza/consultas/AgendaConfigModals";
import type { ConsultasAgendaModalsApi, ConsultasAgendamentoCadastros } from "./consultas-page-types";

interface ConsultasPageModalsProps {
  showNovaConsultaModal: boolean;
  novaConsultaDate: Date | null;
  onFecharNovaConsulta: () => void;
  onConsultaCreated: (consultaId: number) => void;
  onAgendamentoSuccess: () => void;
  cadastros: ConsultasAgendamentoCadastros;
  agendaModals: ConsultasAgendaModalsApi;
}

export function ConsultasPageModals({
  showNovaConsultaModal,
  novaConsultaDate,
  onFecharNovaConsulta,
  onConsultaCreated,
  onAgendamentoSuccess,
  cadastros,
  agendaModals,
}: ConsultasPageModalsProps) {
  return (
    <>
      <ModalCriarAgendamento
        open={showNovaConsultaModal}
        onClose={onFecharNovaConsulta}
        mode="consulta"
        selectedDate={novaConsultaDate}
        professionals={cadastros.professionals}
        patients={cadastros.patients}
        procedures={cadastros.procedures}
        nomesAgenda={cadastros.nomesAgenda}
        locaisAtendimento={cadastros.locaisAtendimento}
        onPatientsChange={cadastros.setPatients}
        onSearchPatients={cadastros.searchPatients}
        onSuccess={onAgendamentoSuccess}
        onConsultaCreated={onConsultaCreated}
      />
      <AgendaConfigModals agendaModals={agendaModals} />
    </>
  );
}
