"use client";

import { useRef, useState, type Dispatch, type ReactNode, type SetStateAction } from "react";
import { useConsultaDetailActions } from "@/hooks/clinica-beleza/useConsultaDetailActions";
import { useConsultaDetailLoader } from "@/hooks/clinica-beleza/useConsultaDetailLoader";
import { EMPTY_EVOLUCAO_FORM } from "@/hooks/clinica-beleza/consulta-detail-actions/consulta-detail-actions-types";
import type { Consulta, TabId } from "../consultas-types";
import { useConsultaDetailShellEffects } from "../useConsultaDetailShellEffects";
import { temHistoricoAnterior } from "./consulta-detail-shell-utils";

export interface UseConsultaDetailShellArgs {
  consulta: Consulta;
  detailPreloaded?: boolean;
  onBack: () => void;
  onSelectConsulta: (c: Consulta) => void;
  onListRefresh: () => void | Promise<void>;
}

export function useConsultaDetailShell({
  consulta,
  detailPreloaded = false,
  onBack,
  onSelectConsulta,
  onListRefresh,
}: UseConsultaDetailShellArgs) {
  const [fotosToolbar, setFotosToolbar] = useState<ReactNode | null>(null);
  const resetEditsRef = useRef<() => void>(() => {});

  const loader = useConsultaDetailLoader({
    consulta,
    detailPreloaded,
    onSelectConsulta,
    onListRefresh,
    onLoadStart: () => resetEditsRef.current(),
  });

  const actions = useConsultaDetailActions({
    ...loader,
    onBack,
    onListRefresh,
  });

  resetEditsRef.current = actions.resetEditsOnLoad;

  const historicoAnterior = temHistoricoAnterior(loader.historico);

  const resetTabEdits = () => {
    actions.setEditAtendimento(false);
    actions.setEditAnamnese(false);
    actions.setEditEvolucao(false);
    actions.setProtocoloPreview(null);
    actions.setProtocoloPendingId(null);
  };

  const handleTabChange = (id: TabId) => {
    loader.setTab(id);
    resetTabEdits();
  };

  useConsultaDetailShellEffects({
    tab: loader.tab,
    setTab: loader.setTab,
    temHistoricoAnterior: historicoAnterior,
    setFotosToolbar,
  });

  return {
    loader,
    actions,
    fotosToolbar,
    setFotosToolbar,
    historicoAnterior,
    handleTabChange,
  };
}

export type ConsultaDetailLoaderState = ReturnType<typeof useConsultaDetailLoader>;
export type ConsultaDetailActionsState = ReturnType<typeof useConsultaDetailActions>;

export function resetEvolucaoForm(
  setEvolucaoForm: Dispatch<SetStateAction<typeof EMPTY_EVOLUCAO_FORM>>,
) {
  setEvolucaoForm({ ...EMPTY_EVOLUCAO_FORM });
}
