"use client";

import { CheckCircle2, DollarSign, AlertCircle, ExternalLink } from "lucide-react";
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
  const { mostrarReceber, mostrarPago, mostrarParcial, consultaFinalizada } = consultaPagamentoUi(consulta);
  const pad = size === "sm" ? "px-2 py-1 text-xs" : "px-3 py-1.5 text-sm";
  const iconSize = size === "sm" ? 14 : 16;

  // Parcial: badge laranja — se finalizada, aviso ao clicar
  if (mostrarParcial) {
    if (consultaFinalizada) {
      return (
        <button type="button"
          onClick={(e) => {
            e.stopPropagation();
            alert("Pagamento parcial — receber saldo na página Financeiro.");
          }}
          className={`inline-flex items-center gap-1 rounded-lg text-white font-medium bg-orange-500 ${pad}`}
          title="Pagamento parcial — receber saldo na página Financeiro"
        >
          <AlertCircle size={iconSize} />
          Parcial
        </button>
      );
    }
    if (onReceber) {
      return (
        <button type="button" onClick={(e) => { e.stopPropagation(); onReceber(consulta); }}
          disabled={loading}
          className={`inline-flex items-center gap-1 rounded-lg text-white font-medium disabled:opacity-50 bg-orange-500 hover:bg-orange-600 ${pad}`}
          title={`Parcial — saldo: R$ ${Number(consulta.valor_restante ?? 0).toFixed(2)}`}
        >
          <AlertCircle size={iconSize} />
          {loading ? "Registrando…" : "Parcial"}
        </button>
      );
    }
  }

  // Receber: se finalizada → aviso, senão → botão
  if (mostrarReceber) {
    if (consultaFinalizada) {
      return (
        <button type="button"
          onClick={(e) => {
            e.stopPropagation();
            alert("Pagamento pendente — receber na página Financeiro.");
          }}
          className={`inline-flex items-center gap-1 rounded-lg text-white font-medium bg-red-600 ${pad}`}
          title="Pagamento pendente — receber na página Financeiro"
        >
          <DollarSign size={iconSize} />
          Pendente
        </button>
      );
    }
    if (onReceber) {
      return (
        <button type="button" onClick={(e) => { e.stopPropagation(); onReceber(consulta); }}
          disabled={loading}
          className={`inline-flex items-center gap-1 rounded-lg text-white font-medium disabled:opacity-50 bg-red-600 hover:bg-red-700 ${pad}`}
        >
          <DollarSign size={iconSize} />
          {loading ? "Registrando…" : "Receber"}
        </button>
      );
    }
  }

  if (mostrarPago) {
    return (
      <span
        className={`inline-flex items-center gap-1 rounded-lg text-white font-medium bg-green-600 cursor-pointer hover:bg-green-700 ${pad}`}
        title="Pago — clique para reimprimir/reenviar recibo"
        onClick={(e) => {
          e.stopPropagation();
          if (onReceber) onReceber(consulta);
        }}
      >
        <CheckCircle2 size={iconSize} />
        Pago
      </span>
    );
  }

  return null;
}
