"use client";

import { useParams } from "next/navigation";
import { AgendamentoOnlineWizard } from "@/components/agendamento-online-publico/AgendamentoOnlineWizard";

/** Página pública (sem login) de agendamento online da clínica. */
export default function AgendamentoOnlinePublicoPage() {
  const slug = (useParams()?.slug as string) ?? "";
  return <AgendamentoOnlineWizard slug={slug} />;
}
