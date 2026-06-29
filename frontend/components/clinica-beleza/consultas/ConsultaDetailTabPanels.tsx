"use client";

import dynamic from "next/dynamic";
import type { ReactNode, Dispatch, SetStateAction } from "react";
import type { ConsultaPrintMeta } from "@/lib/consulta-print";
import type { PrescricaoMemedItem } from "@/lib/clinica-beleza-api";
import { ConsultaAtendimentoTab } from "./ConsultaAtendimentoTab";
import { ConsultaProdutosTab } from "./ConsultaProdutosTab";
import { ConsultaAnamneseTab } from "./ConsultaAnamneseTab";
import { ConsultaEvolucaoTab } from "./ConsultaEvolucaoTab";
import type {
  Anamnese,
  Consulta,
  ConsultaProcedimento,
  Evolucao,
  Protocolo,
  TabId,
} from "./consultas-types";

const ConsultaHistoricoTab = dynamic(
  () => import("./ConsultaHistoricoTab").then((m) => ({ default: m.ConsultaHistoricoTab })),
  { loading: () => <div className="text-center py-12 text-gray-500 text-sm">Carregando histórico...</div> },
);

const ConsultaDocumentosTab = dynamic(
  () => import("./ConsultaDocumentosTab").then((m) => ({ default: m.ConsultaDocumentosTab })),
  { loading: () => <div className="text-center py-12 text-gray-500 text-sm">Carregando documentos...</div> },
);

const ConsultaFotosTab = dynamic(
  () => import("./ConsultaFotosTab").then((m) => ({ default: m.ConsultaFotosTab })),
  { loading: () => <div className="text-center py-12 text-gray-500 text-sm">Carregando fotos...</div> },
);

export interface EvolucaoFormState {
  descricao: string;
  procedimento_realizado: string;
  produtos_utilizados: string;
  orientacoes: string;
  satisfacao: string;
}

interface ConsultaDetailTabPanelsProps {
  tab: TabId;
  selected: Consulta;
  consultaAtiva: boolean;
  consultaFinalizada: boolean;
  protocolos: Protocolo[];
  protocoloPreview: Protocolo | null;
  editAtendimento: boolean;
  editAnamnese: boolean;
  editEvolucao: boolean;
  observacoes: string;
  observacoesDraft: string;
  anamnese: Anamnese;
  anamneseDraft: Anamnese;
  evolucoes: Evolucao[];
  evolucaoForm: EvolucaoFormState;
  historico: Consulta[];
  prescricoes: PrescricaoMemedItem[];
  saving: boolean;
  printMeta: ConsultaPrintMeta;
  procedimentosRealizados: ConsultaProcedimento[];
  prescricoesRefresh: number;
  formatData: (d?: string | null) => string;
  onSelectProtocolo: (id: number) => void;
  onConfirmProtocolo: () => void;
  onCancelProtocolo: () => void;
  onStartEditAtendimento: () => void;
  onCancelEditAtendimento: () => void;
  onChangeObservacoesDraft: (v: string) => void;
  onSaveAtendimento: () => void;
  onRefreshConsulta: () => void;
  onStartEditAnamnese: () => void;
  onCancelEditAnamnese: () => void;
  onChangeAnamneseDraft: Dispatch<SetStateAction<Anamnese>>;
  onSaveAnamnese: () => void;
  onStartEditEvolucao: () => void;
  onCancelEditEvolucao: () => void;
  onChangeEvolucaoForm: Dispatch<SetStateAction<EvolucaoFormState>>;
  onSaveEvolucao: () => void;
  onLoadDetalhes: (c: Consulta) => void;
  onUsarMemed: () => void;
  onToolbarChange: (node: ReactNode | null) => void;
}

export function ConsultaDetailTabPanels(props: ConsultaDetailTabPanelsProps) {
  const {
    tab,
    selected,
    consultaAtiva,
    consultaFinalizada,
    protocolos,
    protocoloPreview,
    editAtendimento,
    editAnamnese,
    editEvolucao,
    observacoes,
    observacoesDraft,
    anamnese,
    anamneseDraft,
    evolucoes,
    evolucaoForm,
    historico,
    prescricoes,
    saving,
    printMeta,
    procedimentosRealizados,
    prescricoesRefresh,
    formatData,
    onSelectProtocolo,
    onConfirmProtocolo,
    onCancelProtocolo,
    onStartEditAtendimento,
    onCancelEditAtendimento,
    onChangeObservacoesDraft,
    onSaveAtendimento,
    onRefreshConsulta,
    onStartEditAnamnese,
    onCancelEditAnamnese,
    onChangeAnamneseDraft,
    onSaveAnamnese,
    onStartEditEvolucao,
    onCancelEditEvolucao,
    onChangeEvolucaoForm,
    onSaveEvolucao,
    onLoadDetalhes,
    onUsarMemed,
    onToolbarChange,
  } = props;

  if (tab === "produtos") {
    return (
      <ConsultaProdutosTab
        consultaId={selected.id}
        somenteLeitura={consultaFinalizada}
        printMeta={printMeta}
        onItensChanged={onRefreshConsulta}
      />
    );
  }

  if (tab === "atendimento") {
    return (
      <ConsultaAtendimentoTab
        consultaId={selected.id}
        protocolos={consultaFinalizada ? [] : protocolos}
        protocoloPreview={protocoloPreview}
        editAtendimento={consultaFinalizada ? false : editAtendimento}
        observacoes={observacoes}
        observacoesDraft={observacoesDraft}
        saving={saving}
        printMeta={printMeta}
        protocolName={selected.protocol_name}
        procedimentosRealizados={procedimentosRealizados}
        consultaFinalizada={consultaFinalizada}
        onSelectProtocolo={consultaFinalizada ? () => {} : onSelectProtocolo}
        onConfirmProtocolo={onConfirmProtocolo}
        onCancelProtocolo={onCancelProtocolo}
        onStartEdit={consultaFinalizada ? () => {} : onStartEditAtendimento}
        onCancelEdit={onCancelEditAtendimento}
        onChangeDraft={onChangeObservacoesDraft}
        onSave={onSaveAtendimento}
        onProcedimentosChanged={onRefreshConsulta}
      />
    );
  }

  if (tab === "anamnese") {
    return (
      <ConsultaAnamneseTab
        anamnese={anamnese}
        anamneseDraft={anamneseDraft}
        editAnamnese={consultaFinalizada ? false : editAnamnese}
        saving={saving}
        printMeta={printMeta}
        onStartEdit={consultaFinalizada ? () => {} : onStartEditAnamnese}
        onCancelEdit={onCancelEditAnamnese}
        onChangeDraft={onChangeAnamneseDraft}
        onSave={onSaveAnamnese}
      />
    );
  }

  if (tab === "evolucao") {
    return (
      <ConsultaEvolucaoTab
        evolucoes={evolucoes}
        editEvolucao={consultaFinalizada ? false : editEvolucao}
        evolucaoForm={evolucaoForm}
        saving={saving}
        formatData={formatData}
        printMeta={printMeta}
        onStartEdit={consultaFinalizada ? () => {} : onStartEditEvolucao}
        onCancelEdit={onCancelEditEvolucao}
        onChangeForm={onChangeEvolucaoForm}
        onSave={onSaveEvolucao}
      />
    );
  }

  if (tab === "fotos") {
    return (
      <ConsultaFotosTab
        consultaId={selected.id}
        permiteEnviar={consultaAtiva}
        ativa={tab === "fotos" && consultaAtiva}
        onToolbarChange={onToolbarChange}
      />
    );
  }

  if (tab === "historico") {
    return (
      <ConsultaHistoricoTab
        historico={historico}
        selectedId={selected.id}
        consultaId={selected.id}
        anamnese={anamnese}
        prescricoes={prescricoes}
        observacoesAtual={observacoes}
        protocoloNotasAtual={selected.protocolo_notas}
        formatData={formatData}
        printMeta={printMeta}
        onSelect={onLoadDetalhes}
      />
    );
  }

  if (tab === "documentos") {
    return (
      <ConsultaDocumentosTab
        consultaId={selected.id}
        consultaAtiva={consultaAtiva}
        professionalId={selected.professional}
        onUsarMemed={onUsarMemed}
        refreshPrescricoes={prescricoesRefresh}
      />
    );
  }

  return null;
}
