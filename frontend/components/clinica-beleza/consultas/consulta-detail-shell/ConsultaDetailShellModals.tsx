"use client";

import dynamic from "next/dynamic";
import type { Consulta } from "../consultas-types";
import { ConsultaProfessionalSelectModal } from "../ConsultaProfessionalSelectModal";
import type { ConsultaDetailActionsState } from "./useConsultaDetailShell";

const ConsultaFinalizarModal = dynamic(
  () => import("../ConsultaFinalizarModal").then((m) => ({ default: m.ConsultaFinalizarModal })),
);

interface ConsultaDetailShellModalsProps {
  selected: Consulta;
  actions: ConsultaDetailActionsState;
}

export function ConsultaDetailShellModals({ selected, actions }: ConsultaDetailShellModalsProps) {
  return (
    <>
      <ConsultaFinalizarModal
        open={actions.showFinalizarModal}
        finalizando={actions.finalizando}
        form={actions.finalizarForm}
        valorConsulta={selected.valor_consulta}
        valorProcedimentos={selected.valor_procedimentos}
        locais={actions.locaisAtendimento}
        onClose={() => actions.setShowFinalizarModal(false)}
        onChange={actions.setFinalizarForm}
        onConfirm={actions.finalizarConsulta}
      />

      <ConsultaProfessionalSelectModal
        open={actions.showProfessionalModal}
        profissionais={actions.profissionaisDisponiveis}
        onSelect={(id) => {
          actions.setShowProfessionalModal(false);
          void actions.iniciarConsulta(id);
        }}
        onClose={() => actions.setShowProfessionalModal(false)}
      />
    </>
  );
}
