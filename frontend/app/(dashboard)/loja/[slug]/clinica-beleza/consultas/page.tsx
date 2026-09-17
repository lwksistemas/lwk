"use client";

/**
 * Consultas — Clínica da Beleza
 * Lista em tela cheia; detalhe da consulta selecionada em shell dedicado.
 */

import { ClinicaConsultaAccessGate } from "@/components/clinica-beleza/ClinicaConsultaAccessGate";
import { ConsultasPageContent } from "@/components/clinica-beleza/consultas-page/ConsultasPageContent";

export default function ConsultasPage() {
  return (
    <ClinicaConsultaAccessGate>
      <ConsultasPageContent />
    </ClinicaConsultaAccessGate>
  );
}
