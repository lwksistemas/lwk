"use client";

/**
 * Consultas — Clínica da Beleza
 * Lista em tela cheia; detalhe da consulta selecionada em shell dedicado.
 */

import { ConsultasOperacionalGate } from "@/components/clinica-beleza/ConsultasOperacionalGate";
import { ConsultasPageContent } from "@/components/clinica-beleza/consultas-page/ConsultasPageContent";

export default function ConsultasPage() {
  return (
    <ConsultasOperacionalGate>
      <ConsultasPageContent />
    </ConsultasOperacionalGate>
  );
}
