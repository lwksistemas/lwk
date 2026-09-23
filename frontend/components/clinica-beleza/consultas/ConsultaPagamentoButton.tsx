"use client";

import { CheckCircle2, DollarSign, AlertCircle, Printer } from "lucide-react";
import { useToast } from "@/components/ui/Toast";
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
  const toast = useToast();
  const { mostrarReceber, mostrarPago, mostrarParcial, mostrarRecibo, mostrarPrazo, consultaFinalizada } = consultaPagamentoUi(consulta);
  const pad = size === "sm" ? "px-2 py-1 text-xs" : "px-3 py-1.5 text-sm";
  const iconSize = size === "sm" ? 14 : 16;

  // Parcial: badge laranja — se finalizada, aviso ao clicar
  if (mostrarParcial) {
    if (consultaFinalizada) {
      // Finalizada e parcial: abre o comprovante (imprimir/enviar); saldo se recebe no Financeiro.
      return (
        <button type="button"
          onClick={(e) => {
            e.stopPropagation();
            if (onReceber) onReceber(consulta);
          }}
          className={`inline-flex items-center gap-1 rounded-lg text-white font-medium bg-orange-500 hover:bg-orange-600 ${pad}`}
          title="Parcial — clique para ver/enviar o comprovante (saldo se recebe no Financeiro)"
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
          aria-label={`Receber pagamento parcial de ${consulta.patient_name}`}
          className={`inline-flex items-center gap-1 rounded-lg text-white font-medium disabled:opacity-50 bg-orange-500 hover:bg-orange-600 ${pad}`}
          title={`Parcial — saldo: R$ ${Number(consulta.valor_restante ?? 0).toFixed(2)}`}
        >
          <AlertCircle size={iconSize} />
          {loading ? "Registrando…" : "Parcial"}
        </button>
      );
    }
  }

  if (mostrarPrazo) {
    if (consultaFinalizada) {
      // Finalizada a prazo: abre o comprovante (imprimir/enviar) ao clicar.
      return (
        <button type="button"
          onClick={(e) => {
            e.stopPropagation();
            if (onReceber) onReceber(consulta);
          }}
          className={`inline-flex items-center gap-1 rounded-lg text-white font-medium bg-slate-600 hover:bg-slate-700 ${pad}`}
          title="A prazo — clique para ver/enviar o comprovante"
        >
          <DollarSign size={iconSize} />
          A prazo
        </button>
      );
    }
    return (
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation();
          toast.info("O comprovante fica disponível após finalizar a consulta.");
        }}
        aria-label={`Pagamento a prazo de ${consulta.patient_name}`}
        className={`inline-flex items-center gap-1 rounded-lg text-white font-medium bg-slate-600 ${pad}`}
        title="A prazo — o comprovante fica disponível após finalizar a consulta"
      >
        <DollarSign size={iconSize} />
        A prazo
      </button>
    );
  }

  // Receber: se finalizada → aviso, senão → botão
  if (mostrarReceber) {
    if (consultaFinalizada) {
      return (
        <button type="button"
          onClick={(e) => {
            e.stopPropagation();
            toast.info("Pagamento pendente — receber na página Financeiro.");
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
          aria-label={`Receber pagamento de ${consulta.patient_name}`}
          className={`inline-flex items-center gap-1 rounded-lg text-white font-medium disabled:opacity-50 bg-red-600 hover:bg-red-700 ${pad}`}
        >
          <DollarSign size={iconSize} />
          {loading ? "Registrando…" : "Receber"}
        </button>
      );
    }
  }

  if (mostrarPago) {
    // Comprovante só disponível após finalizar a consulta.
    const podeComprovante = consultaFinalizada && onReceber;
    return (
      <span
        className={`inline-flex items-center gap-1 rounded-lg text-white font-medium bg-green-600 ${pad} ${
          podeComprovante ? "cursor-pointer hover:bg-green-700" : "cursor-default opacity-90"
        }`}
        title={
          podeComprovante
            ? "Pago — clique para reimprimir/reenviar recibo"
            : "Pago — o comprovante fica disponível após finalizar a consulta"
        }
        onClick={(e) => {
          e.stopPropagation();
          if (podeComprovante) {
            onReceber(consulta);
          } else if (!consultaFinalizada) {
            toast.info("O comprovante fica disponível após finalizar a consulta.");
          }
        }}
      >
        <CheckCircle2 size={iconSize} />
        Pago
      </span>
    );
  }

  if (mostrarRecibo) {
    // Recibo (retorno gratuito) já pressupõe consulta finalizada.
    return (
      <span
        className={`inline-flex items-center gap-1 rounded-lg text-white font-medium bg-green-600 cursor-pointer hover:bg-green-700 ${pad}`}
        title="Retorno gratuito — clique para imprimir/enviar recibo"
        onClick={(e) => {
          e.stopPropagation();
          if (onReceber) onReceber(consulta);
        }}
      >
        <Printer size={iconSize} />
        Recibo
      </span>
    );
  }

  return null;
}
