import type { LucideIcon } from "lucide-react";
import {
  Activity,
  FileCheck,
  FileText,
  FlaskConical,
  FolderOpen,
  Pill,
} from "lucide-react";

/** Mapeamento de tab para seção da API */
export type ProntuarioTabId =
  | "receituario"
  | "pedido_exame"
  | "atestado"
  | "documento_personalizado"
  | "anamnese"
  | "evolucao";

export type ProntuarioDocTabId = Exclude<ProntuarioTabId, "anamnese" | "evolucao">;

export interface ProntuarioTabDef {
  id: ProntuarioTabId;
  label: string;
  icon: LucideIcon;
}

export const PRONTUARIO_TABS: ProntuarioTabDef[] = [
  { id: "receituario", label: "Receitas", icon: Pill },
  { id: "pedido_exame", label: "Exames", icon: FlaskConical },
  { id: "atestado", label: "Atestados", icon: FileCheck },
  { id: "documento_personalizado", label: "Atendimento", icon: FolderOpen },
  { id: "anamnese", label: "Anamnese", icon: FileText },
  { id: "evolucao", label: "Evolução", icon: Activity },
];

export const ANAMNESE_DISPLAY_FIELDS = [
  { key: "queixa_principal", label: "Queixa Principal" },
  { key: "historico_medico", label: "Histórico Médico" },
  { key: "medicamentos_uso", label: "Medicamentos em Uso" },
  { key: "alergias", label: "Alergias" },
  { key: "tipo_pele", label: "Tipo de Pele" },
  { key: "observacoes", label: "Observações" },
] as const;

export const EVOLUCAO_DISPLAY_FIELDS = [
  { key: "descricao", label: "Descrição" },
  { key: "procedimento_realizado", label: "Procedimento Realizado" },
  { key: "produtos_utilizados", label: "Produtos Utilizados" },
  { key: "orientacoes", label: "Orientações" },
] as const;
