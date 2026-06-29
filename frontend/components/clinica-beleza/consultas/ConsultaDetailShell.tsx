"use client";

import dynamic from "next/dynamic";
import { useEffect, useRef, useState, type ReactNode } from "react";
import { CheckCircle2, Trash2 } from "lucide-react";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { PacienteAvatar } from "@/components/clinica-beleza/PacienteAvatar";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { useConsultaDetailLoader } from "@/hooks/clinica-beleza/useConsultaDetailLoader";
import { useConsultaDetailActions } from "@/hooks/clinica-beleza/useConsultaDetailActions";
import { toUpperCase } from "@/lib/format-br";
import {
  type Consulta,
  consultaProcedimentosNomes,
  type TabId,
} from "./consultas-types";
import { ConsultaDetailStatusBar } from "./ConsultaDetailStatusBar";
import { ConsultaDetailTabBar } from "./ConsultaDetailTabBar";
import { ConsultaDetailTabPanels } from "./ConsultaDetailTabPanels";
import { ConsultaProfessionalSelectModal } from "./ConsultaProfessionalSelectModal";

const ConsultaFinalizarModal = dynamic(
  () => import("./ConsultaFinalizarModal").then((m) => ({ default: m.ConsultaFinalizarModal })),
);

const MemedPrescricao = dynamic(() => import("./MemedPrescricao"), { ssr: false });

interface Props {
  consulta: Consulta;
  detailPreloaded?: boolean;
  onBack: () => void;
  onSelectConsulta: (c: Consulta) => void;
  onListRefresh: () => void | Promise<void>;
}

export function ConsultaDetailShell({
  consulta,
  detailPreloaded = false,
  onBack,
  onSelectConsulta,
  onListRefresh,
}: Props) {
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

  const {
    selected,
    tab,
    setTab,
    loadingDetalhe,
    tabLoading,
    protocolos,
    evolucoes,
    historico,
    prescricoes,
    refreshConsulta,
    loadDetalhes,
  } = loader;

  const temHistoricoAnterior = historico.length > 1;

  const resetTabEdits = () => {
    actions.setEditAtendimento(false);
    actions.setEditAnamnese(false);
    actions.setEditEvolucao(false);
    actions.setProtocoloPreview(null);
    actions.setProtocoloPendingId(null);
  };

  const handleTabChange = (id: TabId) => {
    setTab(id);
    resetTabEdits();
  };

  useEffect(() => {
    if (tab !== "fotos") setFotosToolbar(null);
  }, [tab]);

  useEffect(() => {
    if (tab === "historico" && !temHistoricoAnterior) {
      setTab("atendimento");
    }
  }, [tab, temHistoricoAnterior, setTab]);

  const headerExtraActions = actions.consultaAtiva ? (
    <>
      <button
        type="button"
        onClick={actions.abrirFinalizarModal}
        className="inline-flex items-center gap-1 px-2.5 sm:px-3 py-1.5 rounded-lg text-white text-xs sm:text-sm font-medium"
        style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
      >
        <CheckCircle2 size={15} />
        <span className="hidden sm:inline">Finalizar consulta</span>
        <span className="sm:hidden">Finalizar</span>
      </button>
      {actions.podeExcluir && (
        <button
          type="button"
          onClick={actions.excluirConsulta}
          className="inline-flex items-center gap-1 px-2.5 sm:px-3 py-1.5 rounded-lg text-xs sm:text-sm font-medium border border-red-300 dark:border-red-700 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20"
        >
          <Trash2 size={15} />
          <span className="hidden sm:inline">Excluir</span>
        </button>
      )}
    </>
  ) : null;

  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title={toUpperCase(selected.patient_name)}
        subtitle={`${consultaProcedimentosNomes(selected)} · ${toUpperCase(selected.professional_name)}`}
        onBack={onBack}
        leadingContent={
          <PacienteAvatar
            fotoUrl={selected.patient_foto_url}
            name={selected.patient_name}
            size="sm"
          />
        }
        toolbarActions={tab === "fotos" ? fotosToolbar : undefined}
        extraActions={headerExtraActions}
      />
      <div className="min-h-full bg-[#f7f2f4] dark:bg-gray-950 flex flex-col">
        <div className="px-4 md:px-6 pt-2 pb-4 border-b border-gray-200 dark:border-neutral-800 bg-white/80 dark:bg-neutral-900/80">
          {!actions.consultaAtiva && (
            <ConsultaDetailStatusBar
              selected={selected}
              procedimentosRealizados={actions.procedimentosRealizados}
              formatData={actions.formatData}
              valorPagamentoConsulta={actions.valorPagamentoConsulta}
              outraConsultaEmAndamento={actions.outraConsultaEmAndamento}
              podeIniciar={actions.podeIniciar}
              podeFinalizar={actions.podeFinalizar}
              podeExcluir={actions.podeExcluir}
              iniciando={actions.iniciando}
              onIniciar={() => actions.iniciarConsulta()}
              onFinalizar={actions.abrirFinalizarModal}
              onExcluir={actions.excluirConsulta}
            />
          )}
          <ConsultaDetailTabBar
            tab={tab}
            selected={selected}
            consultaAtiva={actions.consultaAtiva}
            consultaFinalizada={actions.consultaFinalizada}
            temHistoricoAnterior={temHistoricoAnterior}
            onTabChange={handleTabChange}
            onRefreshConsulta={refreshConsulta}
          />
        </div>

        {actions.consultaAtiva && (
          <MemedPrescricao
            ref={actions.memedRef}
            consultaId={selected.id}
            professionalId={selected.professional ?? null}
            patientId={selected.patient}
            patientName={selected.patient_name}
            onPrescricaoRegistrada={actions.recarregarPrescricoes}
          />
        )}

        <div className="flex-1 p-4 md:p-6 lg:p-8 w-full">
          {loadingDetalhe || tabLoading ? (
            <div className="text-center py-16 text-gray-500">
              {loadingDetalhe ? "Carregando consulta..." : "Carregando aba..."}
            </div>
          ) : !actions.consultaAtiva && !actions.consultaFinalizada && tab !== "historico" ? (
            <div className="text-center py-16">
              <p className="text-gray-500 dark:text-gray-400 text-sm">
                Consulta aguardando início. O profissional deve clicar em{" "}
                <strong>&quot;Iniciar consulta&quot;</strong> para habilitar o atendimento.
              </p>
            </div>
          ) : (
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
                actions.setEvolucaoForm({
                  descricao: "",
                  procedimento_realizado: "",
                  produtos_utilizados: "",
                  orientacoes: "",
                  satisfacao: "",
                });
              }}
              onChangeEvolucaoForm={actions.setEvolucaoForm}
              onSaveEvolucao={actions.salvarEvolucao}
              onLoadDetalhes={loadDetalhes}
              onUsarMemed={actions.abrirMemed}
              onToolbarChange={setFotosToolbar}
            />
          )}
        </div>
      </div>

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
