"use client";

import { useParams } from "next/navigation";
import { ProtocolosPageContent } from "@/components/clinica-beleza/protocolos-page/ProtocolosPageContent";
import { CLINICA_MODULO_PROTOCOLOS } from "@/lib/clinica-beleza-module-config";

export function ModuloProtocolosPage({ modulo }: { modulo: "estetica" | "soroterapia" }) {
  const slug = useParams().slug as string;
  const config = CLINICA_MODULO_PROTOCOLOS[modulo](slug);
  return (
    <ProtocolosPageContent
      {...config}
      backHref={`/loja/${slug}/dashboard`}
    />
  );
}
