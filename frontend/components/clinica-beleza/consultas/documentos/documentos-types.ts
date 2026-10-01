import type { LucideIcon } from "lucide-react";
import { ClipboardCheck, File, FlaskConical, Pill } from "lucide-react";

/** Tipo de documento clínico — mapeia ao DocumentTemplate.TIPO_CHOICES do backend. */
export type DocumentoTipo = "receituario" | "pedido_exame" | "atestado" | "documento_personalizado";

export const DOCUMENTO_TIPO_LABEL: Record<DocumentoTipo, string> = {
  receituario: "Receituário",
  pedido_exame: "Pedido de Exame",
  atestado: "Atestado",
  documento_personalizado: "Documento Personalizado",
};

export function documentoTipoLabel(tipo: string): string {
  return DOCUMENTO_TIPO_LABEL[tipo as DocumentoTipo] ?? tipo;
}

/** Sub-opção ao clicar em um tipo de documento. */
export type DocumentoAcao = "memed" | "template" | "manual";

export interface DocumentoButtonConfig {
  tipo: DocumentoTipo;
  label: string;
  icon: LucideIcon;
  hasMemed: boolean;
}

export const DOCUMENTO_BUTTONS: DocumentoButtonConfig[] = [
  { tipo: "receituario", label: DOCUMENTO_TIPO_LABEL.receituario, icon: Pill, hasMemed: true },
  { tipo: "pedido_exame", label: DOCUMENTO_TIPO_LABEL.pedido_exame, icon: FlaskConical, hasMemed: true },
  { tipo: "atestado", label: DOCUMENTO_TIPO_LABEL.atestado, icon: ClipboardCheck, hasMemed: true },
  { tipo: "documento_personalizado", label: DOCUMENTO_TIPO_LABEL.documento_personalizado, icon: File, hasMemed: true },
];
