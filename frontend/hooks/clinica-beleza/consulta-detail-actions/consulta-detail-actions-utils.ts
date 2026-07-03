import {
  consultaEstaConcluida,
  consultaProcedimentos,
  consultaProcedimentosNomes,
  type Consulta,
} from "@/components/clinica-beleza/consultas/consultas-types";
import type { ConsultaPrintMeta } from "@/lib/consulta-print";
import { formatClinicaDateTime } from "@/lib/clinica-beleza-datetime";

export function formatConsultaData(d?: string | null): string {
  return d ? formatClinicaDateTime(new Date(d)) : "—";
}

export function valorPagamentoConsulta(c: Consulta): number {
  const total = Number(c.valor_pagamento ?? 0);
  if (total > 0) return total;
  const taxa = Number(c.valor_consulta ?? 0);
  const procs = Number(c.valor_procedimentos ?? 0);
  return taxa + procs;
}

export function buildConsultaPrintMeta(selected: Consulta): ConsultaPrintMeta {
  return {
    patientName: selected.patient_name,
    professionalName: selected.professional_name,
    procedureName: consultaProcedimentosNomes(selected),
    consultaId: selected.id,
    dataConsulta: formatConsultaData(selected.data_inicio),
  };
}

export function computeConsultaFlags(selected: Consulta, historico: Consulta[]) {
  const outraConsultaEmAndamento = historico.find(
    (c) => c.id !== selected.id && c.status === "IN_PROGRESS",
  );
  const consultaConcluida = consultaEstaConcluida(selected);
  return {
    outraConsultaEmAndamento,
    podeIniciar: selected.status === "SCHEDULED" && !outraConsultaEmAndamento,
    podeFinalizar: selected.status === "IN_PROGRESS",
    podeExcluir: !consultaConcluida,
    consultaAtiva: selected.status === "IN_PROGRESS",
    consultaFinalizada: consultaConcluida,
  };
}

export { consultaProcedimentos };
