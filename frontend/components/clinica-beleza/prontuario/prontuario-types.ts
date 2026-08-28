import type { LucideIcon } from "lucide-react";
import {
  Activity,
  Camera,
  ClipboardList,
  FileCheck,
  FileText,
  FlaskConical,
  FolderOpen,
  Pill,
} from "lucide-react";

/** Mapeamento de tab para seção da API (resumo e fotos são só front). */
export type ProntuarioTabId =
  | "resumo"
  | "fotos"
  | "receituario"
  | "pedido_exame"
  | "atestado"
  | "documento_personalizado"
  | "anamnese"
  | "evolucao";

export type ProntuarioDocTabId = Exclude<
  ProntuarioTabId,
  "resumo" | "fotos" | "anamnese" | "evolucao"
>;

export interface ProntuarioTabDef {
  id: ProntuarioTabId;
  label: string;
  icon: LucideIcon;
}

export const PRONTUARIO_TABS: ProntuarioTabDef[] = [
  { id: "resumo", label: "Resumo", icon: ClipboardList },
  { id: "fotos", label: "Fotos", icon: Camera },
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
