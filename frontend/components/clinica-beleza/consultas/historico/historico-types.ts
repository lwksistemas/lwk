import type { LucideIcon } from "lucide-react";
import {
  Activity,
  Camera,
  ClipboardList,
  FileText,
  FolderOpen,
} from "lucide-react";

export type HistoricoSection =
  | "atendimentos"
  | "anamnese"
  | "fotos"
  | "documentos"
  | "evolucoes";

export type HistoricoSectionConfig = {
  id: HistoricoSection;
  label: string;
  icon: LucideIcon;
  count: number;
};

export const HISTORICO_SECTION_ICONS = {
  atendimentos: ClipboardList,
  anamnese: FileText,
  fotos: Camera,
  documentos: FolderOpen,
  evolucoes: Activity,
} as const;
