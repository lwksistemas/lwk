"use client";

import { ProntuarioPageContent } from "@/components/clinica-beleza/prontuario/ProntuarioPageContent";

/**
 * Prontuário do Paciente — Clínica da Beleza.
 * Cada aba carrega GET /patients/<id>/prontuario/?secao=X
 */
export default function ProntuarioPage() {
  return <ProntuarioPageContent />;
}
