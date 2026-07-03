"use client";

import type { Dispatch, ReactNode, SetStateAction } from "react";
import { ConsultaDetailTabPanels } from "../ConsultaDetailTabPanels";
import {
  resetEvolucaoForm,
  type ConsultaDetailActionsState,
  type ConsultaDetailLoaderState,
} from "./useConsultaDetailShell";
import {
  deveExibirAguardandoInicio,
  loadingConsultaLabel,
} from "./consulta-detail-shell-utils";

interface ConsultaDetailTabPanelsBridgeProps {
  loader: ConsultaDetailLoaderState;
  actions: ConsultaDetailActionsState;
  onToolbarChange: Dispatch<SetStateAction<ReactNode | null>>;
}

export function ConsultaDetailTabPanelsBridge({
  loader,
  actions,
  onToolbarChange,
}: ConsultaDetailTabPanelsBridgeProps) {
  const {
    tab,
    selected,
    protocolos,
    evolucoes,
    historico,
    prescricoes,
    refreshConsulta,
    loadDetalhes,
  } = loader;

  return (
    <ConsultaDetailTabPanels
      tab={tab}
      selected={selected}
      consultaAtiva={actions.consultaAtiva}
      consultaFinalizada={actions.consultaFinalizada}
      protocolos={protocolos}
      protocoloPreview={actions.protocoloPreview}
      editAtendimento={actions.editAtendimento}
      editAnamnese={actions.editAnamnese}
      editEvolucao={actions.editEvolucao}
      observacoes={actions.observacoes}
      observacoesDraft={actions.observacoesDraft}
      anamnese={actions.anamnese}
      anamneseDraft={actions.anamneseDraft}
      evolucoes={evolucoes}
      evolucaoForm={actions.evolucaoForm}
      historico={historico}
      prescricoes={prescricoes}
      saving={actions.saving}
      printMeta={actions.printMeta}
      procedimentosRealizados={actions.procedimentosRealizados}
      prescricoesRefresh={actions.prescricoesRefresh}
      formatData={actions.formatData}
      onSelectProtocolo={actions.selecionarProtocolo}
      onConfirmProtocolo={actions.confirmarProtocolo}
      onCancelProtocolo={() => {
        actions.setProtocoloPreview(null);
        actions.setProtocoloPendingId(null);
      }}
      onStartEditAtendimento={() => {
        actions.setObservacoesDraft(actions.observacoes);
        actions.setEditAtendimento(true);
      }}
      onCancelEditAtendimento={() => {
        actions.setObservacoesDraft(actions.observacoes);
        actions.setEditAtendimento(false);
      }}
      onChangeObservacoesDraft={actions.setObservacoesDraft}
      onSaveAtendimento={actions.salvarObservacoes}
      onRefreshConsulta={refreshConsulta}
      onStartEditAnamnese={() => {
        actions.setAnamneseDraft(actions.anamnese);
        actions.setEditAnamnese(true);
      }}
      onCancelEditAnamnese={() => {
        actions.setAnamneseDraft(actions.anamnese);
        actions.setEditAnamnese(false);
      }}
      onChangeAnamneseDraft={actions.setAnamneseDraft}
      onSaveAnamnese={actions.salvarAnamnese}
      onStartEditEvolucao={() => actions.setEditEvolucao(true)}
      onCancelEditEvolucao={() => {
        actions.setEditEvolucao(false);
        resetEvolucaoForm(actions.setEvolucaoForm);
      }}
      onChangeEvolucaoForm={actions.setEvolucaoForm}
      onSaveEvolucao={actions.salvarEvolucao}
      onLoadDetalhes={loadDetalhes}
      onUsarMemed={actions.abrirMemed}
      onToolbarChange={onToolbarChange}
    />
  );
}

interface ConsultaDetailShellContentProps {
  loader: ConsultaDetailLoaderState;
  actions: ConsultaDetailActionsState;
  onToolbarChange: Dispatch<SetStateAction<ReactNode | null>>;
}

export function ConsultaDetailShellContent({
  loader,
  actions,
  onToolbarChange,
}: ConsultaDetailShellContentProps) {
  const { loadingDetalhe, tabLoading, tab } = loader;

  if (loadingDetalhe || tabLoading) {
    return (
      <div className="text-center py-16 text-gray-500">
        {loadingConsultaLabel(loadingDetalhe)}
      </div>
    );
  }

  if (deveExibirAguardandoInicio(actions.consultaAtiva, actions.consultaFinalizada, tab)) {
    return (
      <div className="text-center py-16">
        <p className="text-gray-500 dark:text-gray-400 text-sm">
          Consulta aguardando início. O profissional deve clicar em{" "}
          <strong>&quot;Iniciar consulta&quot;</strong> para habilitar o atendimento.
        </p>
      </div>
    );
  }

  return (
    <ConsultaDetailTabPanelsBridge
      loader={loader}
      actions={actions}
      onToolbarChange={onToolbarChange}
    />
  );
}
