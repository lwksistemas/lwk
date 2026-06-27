"use client";

import { useParams } from "next/navigation";
import { ProcedimentosPageContent } from "@/components/clinica-beleza/ProcedimentosPageContent";
import { CLINICA_MODULO_PROCEDIMENTOS } from "@/lib/clinica-beleza-module-config";

export function ModuloProcedimentosPage({ modulo }: { modulo: "estetica" | "soroterapia" }) {
  const slug = useParams().slug as string;
  const config = CLINICA_MODULO_PROCEDIMENTOS[modulo](slug);
  return (
    <ProcedimentosPageContent
      {...config}
      backHref={`/loja/${slug}/dashboard`}
    />
  );
}
