import type { Dispatch, ReactNode, SetStateAction } from "react";
import type { PrescricaoMemedItem } from "@/lib/clinica-beleza-api";
import type { ConsultaPrintMeta } from "@/lib/consulta-print";
import type {
  Anamnese,
  Consulta,
  ConsultaProcedimento,
  Evolucao,
  Protocolo,
  TabId,
} from "../consultas-types";

export interface EvolucaoFormState {
  descricao: string;
  procedimento_realizado: string;
  produtos_utilizados: string;
  orientacoes: string;
  satisfacao: string;
}

export interface ConsultaDetailTabPanelsProps {
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
