"use client";

import { X } from "lucide-react";
import { CLINICA_FORMA_PAGAMENTO_LABEL } from "@/lib/clinica-beleza-constants";
import { formatCurrency } from "@/lib/financeiro-helpers";
import { valorPagamentoConsulta } from "@/hooks/clinica-beleza/consulta-detail-actions/consulta-detail-actions-utils";
import { consultaProcedimentosNomes, type Consulta } from "../consultas-types";
import {
  formatEntradasResumo,
  type EntradaPagamentoLinha,
} from "../modal-receber-consulta-utils";
import { ReceberReciboActions } from "./ReceberReciboActions";

interface ReceberSucessoPanelProps {
  consultaExibida: Consulta;
  consultaStatus: string;
  precisaComplementar: boolean;
  saldoAposRecebimento: number;
  reciboSnapshot: {
    desconto: number;
    totalLiquido: number;
    entradas: EntradaPagamentoLinha[];
  } | null;
  error: string;
  loading: boolean;
  onClose: () => void;
  onComplementar: () => void;
  onEstornar: () => void;
  onImprimir: () => void;
  onEmail: () => void;
  onWhatsApp: () => void;
}

export function ReceberSucessoPanel({
  consultaExibida,
  consultaStatus,
  precisaComplementar,
  saldoAposRecebimento,
  reciboSnapshot,
  error,
  loading,
  onClose,
  onComplementar,
  onEstornar,
  onImprimir,
  onEmail,
  onWhatsApp,
}: ReceberSucessoPanelProps) {
  const snap = reciboSnapshot;
  const resumoFormas = snap
    ? formatEntradasResumo(snap.entradas, CLINICA_FORMA_PAGAMENTO_LABEL as Record<string, string>)
    : "";
  const valorTotalConsulta = valorPagamentoConsulta(consultaExibida);

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white dark:bg-neutral-800 rounded-2xl shadow-xl w-full max-w-2xl">
        <div className="flex items-center justify-between p-4 border-b dark:border-neutral-700">
          <h2
            className={`text-lg font-bold ${
              precisaComplementar
                ? "text-orange-700 dark:text-orange-400"
                : "text-green-700 dark:text-green-400"
            }`}
          >
            {precisaComplementar ? "✓ Pagamento parcial registrado" : "✓ Pagamento registrado"}
          </h2>
          <button type="button" onClick={onClose} className="p-2 hover:bg-gray-100 dark:hover:bg-neutral-700 rounded-lg">
            <X size={18} />
          </button>
        </div>
        <div className="p-6 space-y-4">
          <div
            className={`text-sm space-y-1 rounded-lg p-4 ${
              precisaComplementar
                ? "bg-orange-50 dark:bg-orange-900/20"
                : "bg-green-50 dark:bg-green-900/20"
            }`}
          >
            <p>
              <strong>Paciente:</strong> {consultaExibida.patient_name}
            </p>
            <p>
              <strong>Procedimento:</strong> {consultaProcedimentosNomes(consultaExibida)}
            </p>
            {valorTotalConsulta > 0 && (
              <p>
                <strong>Valor:</strong> {formatCurrency(valorTotalConsulta)}
              </p>
            )}
            {snap && snap.desconto > 0 && (
              <p>
                <strong>Desconto:</strong> {formatCurrency(snap.desconto)}
              </p>
            )}
            {Boolean(consultaExibida.retorno_gratuito) && snap && snap.desconto <= 0 && (
              <p>
                <strong>Desconto retorno:</strong> {formatCurrency(valorTotalConsulta)}
              </p>
            )}
            <p>
              <strong>Valor recebido nesta operação:</strong>{" "}
              {formatCurrency(snap?.totalLiquido ?? Number(consultaExibida.valor_pago ?? 0))}
            </p>
            {resumoFormas && (
              <p>
                <strong>Formas nesta operação:</strong> {resumoFormas}
              </p>
            )}
            {Number(consultaExibida.valor_pago ?? 0) > 0 && (
              <p>
                <strong>Total já pago:</strong> {formatCurrency(Number(consultaExibida.valor_pago))}
              </p>
            )}
            <p className="text-xs text-gray-500 dark:text-gray-400 pt-1">
              O recibo impresso/WhatsApp/e-mail lista todas as formas e o total já pago.
            </p>              {precisaComplementar && (
              <p className="font-semibold text-orange-800 dark:text-orange-300 pt-1">
                Saldo em aberto: {formatCurrency(saldoAposRecebimento)} — inclua outras formas para
                complementar.
              </p>
            )}
          </div>

          {precisaComplementar && (
            <button
              type="button"
              onClick={onComplementar}
              className="w-full py-2.5 rounded-lg text-white text-sm font-medium"
              style={{ backgroundColor: "var(--cb-primary, #8B3D52)" }}
            >
              Complementar saldo (várias formas)
            </button>
          )}

          <p className="text-sm text-gray-600 dark:text-gray-400">
            Envie o recibo de pagamento para o cliente:
          </p>
          <ReceberReciboActions
            onImprimir={onImprimir}
            onEmail={onEmail}
            onWhatsApp={onWhatsApp}
          />

          {error && (
            <div className="p-2 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 text-sm">
              {error}
            </div>
          )}

          <div className="flex justify-between items-center pt-2 gap-2">
            {consultaStatus !== "COMPLETED" && (
              <button
                type="button"
                onClick={onEstornar}
                disabled={loading}
                className="px-4 py-2 rounded-lg border border-red-300 text-red-600 hover:bg-red-50 text-sm disabled:opacity-50"
              >
                {loading ? "Corrigindo..." : "Corrigir pagamento"}
              </button>
            )}
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-lg text-white ml-auto"
              style={{ backgroundColor: 'var(--cb-primary, #8B3D52)' }}
            >
              Fechar
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
