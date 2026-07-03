import type { LucideIcon } from "lucide-react";
import { ClipboardCheck, File, FlaskConical, Pill } from "lucide-react";

/** Tipo de documento clínico — mapeia ao DocumentTemplate.TIPO_CHOICES do backend. */
export type DocumentoTipo = "receituario" | "pedido_exame" | "atestado" | "documento_personalizado";

/** Sub-opção ao clicar em um tipo de documento. */
export type DocumentoAcao = "memed" | "template" | "manual";

export interface DocumentoButtonConfig {
  tipo: DocumentoTipo;
  label: string;
  icon: LucideIcon;
  hasMemed: boolean;
}

export const DOCUMENTO_BUTTONS: DocumentoButtonConfig[] = [
  { tipo: "receituario", label: "Receituário", icon: Pill, hasMemed: true },
  { tipo: "pedido_exame", label: "Exames", icon: FlaskConical, hasMemed: true },
  { tipo: "atestado", label: "Atestado", icon: ClipboardCheck, hasMemed: false },
  { tipo: "documento_personalizado", label: "Documento", icon: File, hasMemed: false },
];
