"use client";

import dynamic from "next/dynamic";
import { ModalCriarAgendamento } from "@/components/clinica-beleza/ModalCriarAgendamento";
import type { ConsultasAgendaModalsApi, ConsultasAgendamentoCadastros } from "./consultas-page-types";

const ConfiguracaoAgendaMenuModal = dynamic(
  () =>
    import("@/components/clinica-beleza/consultas/ConfiguracaoAgendaMenuModal").then((m) => ({
      default: m.ConfiguracaoAgendaMenuModal,
    })),
);

const LocaisAtendimentoModal = dynamic(
  () =>
    import("@/components/clinica-beleza/consultas/LocaisAtendimentoModal").then((m) => ({
      default: m.LocaisAtendimentoModal,
    })),
);

const NomesAgendaModal = dynamic(
  () =>
    import("@/components/clinica-beleza/consultas/NomesAgendaModal").then((m) => ({
      default: m.NomesAgendaModal,
    })),
);

const MensagensWhatsAppAgendaModal = dynamic(
  () =>
    import("@/components/clinica-beleza/consultas/MensagensWhatsAppAgendaModal").then((m) => ({
      default: m.MensagensWhatsAppAgendaModal,
    })),
);

const NovoConvenioModal = dynamic(
  () =>
    import("@/components/clinica-beleza/consultas/NovoConvenioModal").then((m) => ({
      default: m.NovoConvenioModal,
    })),
);

const RetornoAgendaModal = dynamic(
  () =>
    import("@/components/clinica-beleza/consultas/RetornoAgendaModal").then((m) => ({
      default: m.RetornoAgendaModal,
    })),
);

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
  const {
    showConfigAgendaMenu,
    setShowConfigAgendaMenu,
    showLocaisModal,
    setShowLocaisModal,
    showNomesAgendaModal,
    setShowNomesAgendaModal,
    showMensagensWhatsAppModal,
    setShowMensagensWhatsAppModal,
    showNovoConvenioModal,
    setShowNovoConvenioModal,
    showRetornoModal,
    setShowRetornoModal,
  } = agendaModals;

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

      {showConfigAgendaMenu && (
        <ConfiguracaoAgendaMenuModal
          open={showConfigAgendaMenu}
          onClose={() => setShowConfigAgendaMenu(false)}
          onLocais={() => setShowLocaisModal(true)}
          onNomesAgenda={() => setShowNomesAgendaModal(true)}
          onMensagensWhatsApp={() => setShowMensagensWhatsAppModal(true)}
          onNovoConvenio={() => setShowNovoConvenioModal(true)}
          onRetorno={() => setShowRetornoModal(true)}
        />
      )}
      {showLocaisModal && (
        <LocaisAtendimentoModal open={showLocaisModal} onClose={() => setShowLocaisModal(false)} />
      )}
      {showNomesAgendaModal && (
        <NomesAgendaModal open={showNomesAgendaModal} onClose={() => setShowNomesAgendaModal(false)} />
      )}
      {showMensagensWhatsAppModal && (
        <MensagensWhatsAppAgendaModal
          open={showMensagensWhatsAppModal}
          onClose={() => setShowMensagensWhatsAppModal(false)}
        />
      )}
      {showNovoConvenioModal && (
        <NovoConvenioModal open={showNovoConvenioModal} onClose={() => setShowNovoConvenioModal(false)} />
      )}
      {showRetornoModal && (
        <RetornoAgendaModal open={showRetornoModal} onClose={() => setShowRetornoModal(false)} />
      )}
    </>
  );
}
