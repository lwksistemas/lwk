import type { Dispatch, SetStateAction } from "react";
import type {
  Anamnese,
  Consulta,
  Evolucao,
  Protocolo,
  TabId,
} from "@/components/clinica-beleza/consultas/consultas-types";
import type { EvolucaoFormState } from "@/components/clinica-beleza/consultas/tab-panels/tab-panels-types";

export type ConsultaDetailLoaderSlice = {
  selected: Consulta;
  setSelected: (c: Consulta | ((prev: Consulta) => Consulta)) => void;
  setTab: (tab: TabId) => void;
  protocolos: Protocolo[];
  anamnese: Anamnese;
  setAnamnese: (a: Anamnese) => void;
  anamneseDraft: Anamnese;
  setAnamneseDraft: Dispatch<SetStateAction<Anamnese>>;
  evolucoes: Evolucao[];
  setEvolucoes: (e: Evolucao[]) => void;
  historico: Consulta[];
  setHistorico: (h: Consulta[]) => void;
  observacoes: string;
  setObservacoes: (v: string) => void;
  observacoesDraft: string;
  setObservacoesDraft: Dispatch<SetStateAction<string>>;
  loadDetalhes: (c: Consulta, opts?: { detailPreloaded?: boolean }) => Promise<void>;
  refreshConsulta: (patch?: Partial<Consulta>) => Promise<void>;
  recarregarPrescricoes: () => Promise<void>;
};

export type UseConsultaDetailActionsArgs = ConsultaDetailLoaderSlice & {
  onBack: () => void;
  onListRefresh: () => void | Promise<void>;
};

export const EMPTY_EVOLUCAO_FORM: EvolucaoFormState = {
  descricao: "",
  procedimento_realizado: "",
  produtos_utilizados: "",
  orientacoes: "",
  satisfacao: "",
};

