"use client";

import {
  CLINICA_CONSULTA_STATUS_COLORS,
  CLINICA_CONSULTA_STATUS_LABEL,
} from "@/lib/clinica-beleza-constants";
import { toUpperCase } from "@/lib/format-br";
import { consultaPagamentoUi } from "@/hooks/clinica-beleza/consulta-detail-actions/consulta-detail-actions-utils";
import type { Consulta } from "./consultas-types";

/** Mesma pílula do financeiro: retorno sem saldo é "Retorno"; o restante segue o atendimento. */
export function ConsultaStatusBadge({ consulta }: { consulta: Consulta }) {
  const { mostrarIsento } = consultaPagamentoUi(consulta);
  if (mostrarIsento) {
    return (
      <span className="inline-flex px-2 py-1 rounded-full text-xs font-medium bg-sky-100 text-sky-800 dark:bg-sky-900/30 dark:text-sky-300">
        Retorno
      </span>
    );
  }
  const colors =
    CLINICA_CONSULTA_STATUS_COLORS[consulta.status] ?? CLINICA_CONSULTA_STATUS_COLORS.SCHEDULED;
  return (
    <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium uppercase ${colors.bg} ${colors.text}`}>
      {CLINICA_CONSULTA_STATUS_LABEL[consulta.status] || toUpperCase(consulta.status)}
    </span>
  );
}
