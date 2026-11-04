"use client";

import { ConsultasOperacionalGate } from "@/components/clinica-beleza/ConsultasOperacionalGate";
import { PdvPageContent } from "@/components/clinica-beleza/pdv/PdvPageContent";

export default function PdvPage() {
  return (
    <ConsultasOperacionalGate>
      <PdvPageContent />
    </ConsultasOperacionalGate>
  );
}
