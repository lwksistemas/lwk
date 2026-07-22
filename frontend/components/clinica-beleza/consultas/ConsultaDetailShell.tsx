"use client";

import dynamic from "next/dynamic";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { PacienteAvatar } from "@/components/clinica-beleza/PacienteAvatar";
import { toUpperCase } from "@/lib/format-br";
import { type Consulta, consultaProcedimentosNomes } from "./consultas-types";
import { ConsultaDetailHeaderActions } from "./ConsultaDetailHeaderActions";
import { ConsultaDetailStatusBar } from "./ConsultaDetailStatusBar";
import { ConsultaDetailTabBar } from "./ConsultaDetailTabBar";
import { ConsultaDetailShellContent } from "./consulta-detail-shell/ConsultaDetailShellContent";
import { ConsultaDetailShellModals } from "./consulta-detail-shell/ConsultaDetailShellModals";
import { useConsultaDetailShell } from "./consulta-detail-shell/useConsultaDetailShell";

const MemedPrescricao = dynamic(() => import("./MemedPrescricao"), { ssr: false });

interface ConsultaDetailShellProps {
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
}: ConsultaDetailShellProps) {
  const {
    loader,
    actions,
    fotosToolbar,
    setFotosToolbar,
    historicoAnterior,
    handleTabChange,
  } = useConsultaDetailShell({
    consulta,
    detailPreloaded,
    onBack,
    onSelectConsulta,
    onListRefresh,
  });

  const { selected, tab, refreshConsulta } = loader;

  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title={
          selected.numero
            ? `Nº ${selected.numero} · ${toUpperCase(selected.patient_name)}`
            : toUpperCase(selected.patient_name)
        }
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
        extraActions={
          <ConsultaDetailHeaderActions
            consultaAtiva={actions.consultaAtiva}
            podeExcluir={actions.podeExcluir}
            onFinalizar={actions.abrirFinalizarModal}
            onExcluir={actions.excluirConsulta}
          />
        }
      />
      <div className="min-h-full bg-[var(--cb-page-bg,#f7f2f4)] dark:bg-gray-950 flex flex-col">
        <div className="px-4 md:px-6 pt-2 pb-4 border-b border-gray-200 dark:border-neutral-800 bg-white/80 dark:bg-neutral-900/80">
          <ConsultaDetailStatusBar
            selected={selected}
            procedimentosRealizados={actions.procedimentosRealizados}
            formatData={actions.formatData}
            valorPagamentoConsulta={actions.valorPagamentoConsulta}
            outraConsultaEmAndamento={actions.outraConsultaEmAndamento}
            podeIniciar={actions.podeIniciar}
            podeFinalizar={actions.podeFinalizar}
            podeExcluir={actions.podeExcluir}
            consultaAtiva={actions.consultaAtiva}
            recebendo={actions.recebendo}
            emitindoNfse={actions.emitindoNfse}
            iniciando={actions.iniciando}
            onIniciar={() => actions.iniciarConsulta()}
            onReceber={actions.abrirReceberModal}
            onEmitirNfse={actions.emitirNfseConsulta}
            onFinalizar={actions.abrirFinalizarModal}
            onExcluir={actions.excluirConsulta}
            onRefreshConsulta={refreshConsulta}
          />
          <ConsultaDetailTabBar
            tab={tab}
            selected={selected}
            consultaAtiva={actions.consultaAtiva}
            consultaFinalizada={actions.consultaFinalizada}
            temHistoricoAnterior={historicoAnterior}
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
          <ConsultaDetailShellContent
            loader={loader}
            actions={actions}
            onToolbarChange={setFotosToolbar}
          />
        </div>
      </div>

      <ConsultaDetailShellModals selected={selected} actions={actions} />
    </>
  );
}
