"use client";

import { useParams } from "next/navigation";
import { SimulacaoConfigPage } from "@/components/clinica-beleza/simulacao-config/SimulacaoConfigPage";

export default function ClinicaBelezaSimulacaoConfigPage() {
  const slug = (useParams()?.slug as string) ?? "";
  return <SimulacaoConfigPage voltarHref={`/loja/${slug}/clinica-beleza/configuracoes`} />;
}
