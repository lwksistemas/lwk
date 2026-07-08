"use client";

import { CheckCircle2, DollarSign } from "lucide-react";
import { consultaPagamentoUi } from "@/hooks/clinica-beleza/consulta-detail-actions/consulta-detail-actions-utils";
import type { Consulta } from "./consultas-types";

interface ConsultaPagamentoButtonProps {
  consulta: Consulta;
  onReceber?: (consulta: Consulta) => void;
  size?: "sm" | "md";
  loading?: boolean;
}

export function ConsultaPagamentoButton({
  consulta,
  onReceber,
  size = "sm",
  loading = false,
}: ConsultaPagamentoButtonProps) {
  const { mostrarReceber, mostrarPago } = consultaPagamentoUi(consulta);
  const pad = size === "sm" ? "px-2 py-1 text-xs" : "px-3 py-1.5 text-sm";
  const iconSize = size === "sm" ? 14 : 16;

  if (mostrarReceber && onReceber) {
    return (
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation();
          onReceber(consulta);
        }}
        disabled={loading}
        className={`inline-flex items-center gap-1 rounded-lg text-white font-medium disabled:opacity-50 bg-amber-600 hover:bg-amber-700 ${pad}`}
      >
        <DollarSign size={iconSize} />
        {loading ? "Registrando…" : "Receber"}
      </button>
    );
  }

  if (mostrarPago) {
    return (
      <span
        className={`inline-flex items-center gap-1 rounded-lg text-white font-medium bg-green-600 ${pad}`}
        title="Pagamento quitado"
      >
        <CheckCircle2 size={iconSize} />
        Pago
      </span>
    );
  }

  return null;
}
