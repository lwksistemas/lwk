"use client";

import type { Consulta } from "../consultas-types";
import { ConsultaProfessionalSelectModal } from "../ConsultaProfessionalSelectModal";
import { textoModalProfissional } from "../consulta-acesso";
import { ModalReceberConsulta } from "../ModalReceberConsulta";
import type { ConsultaDetailActionsState } from "./useConsultaDetailShell";

interface ConsultaDetailShellModalsProps {
  selected: Consulta;
  actions: ConsultaDetailActionsState;
}

export function ConsultaDetailShellModals({ selected, actions }: ConsultaDetailShellModalsProps) {
  return (
    <>
      <ModalReceberConsulta
        open={actions.showReceberModal}
        consulta={selected}
        onClose={() => actions.setShowReceberModal(false)}
        onSuccess={(c) => void actions.aposRecebimento(c)}
      />

      <ConsultaProfessionalSelectModal
        open={actions.showProfessionalModal}
        profissionais={actions.profissionaisDisponiveis}
        titulo={textoModalProfissional(selected).titulo}
        descricao={textoModalProfissional(selected).descricao}
        onSelect={(id) => {
          actions.setShowProfessionalModal(false);
          void actions.iniciarConsulta(id);
        }}
        onClose={() => actions.setShowProfessionalModal(false)}
      />
    </>
  );
}
