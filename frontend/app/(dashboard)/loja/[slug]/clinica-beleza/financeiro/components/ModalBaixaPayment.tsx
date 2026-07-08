"use client";

import { useState } from "react";
import { X } from "lucide-react";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { CLINICA_FORMA_PAGAMENTO_LABEL } from "@/lib/clinica-beleza-constants";
import { formatCurrency } from "@/lib/financeiro-helpers";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import type { FinanceiroPayment } from "../types";

interface ModalBaixaPaymentProps {
  payment: FinanceiroPayment | null;
  onClose: () => void;
  onSuccess: () => void;
}

export function ModalBaixaPayment({ payment, onClose, onSuccess }: ModalBaixaPaymentProps) {
  const [amount, setAmount] = useState("");
  const [paymentMethod, setPaymentMethod] = useState("CASH");
  const [paymentDate, setPaymentDate] = useState(new Date().toISOString().slice(0, 10));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  if (!payment) return null;

  const valorOriginal = Number(payment.amount) || 0;
  const valorBaixa = Number(amount) || valorOriginal;

  const handleConfirm = async () => {
    setLoading(true);
    setError("");
    try {
      await ClinicaBelezaAPI.financeiro.payments.baixa(payment.id, {
        amount: valorBaixa,
        payment_method: paymentMethod,
        payment_date: paymentDate,
      });
      onSuccess();
      onClose();
    } catch {
      setError("Erro ao registrar baixa. Tente novamente.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[70] flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white dark:bg-neutral-800 rounded-2xl shadow-xl w-full max-w-md">
        <div className="flex items-center justify-between p-4 border-b dark:border-neutral-700">
          <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">Dar Baixa no Pagamento</h2>
          <button type="button" onClick={onClose} className="p-2 hover:bg-gray-100 dark:hover:bg-neutral-700 rounded-lg">
            <X size={18} />
          </button>
        </div>
        <div className="p-4 space-y-4">
          <div className="text-sm space-y-1">
            <p><strong>Paciente:</strong> {payment.paciente_nome || "—"}</p>
            <p><strong>Procedimento:</strong> {payment.procedimento_nome || "—"}</p>
            <p><strong>Valor original:</strong> {formatCurrency(valorOriginal)}</p>
          </div>

          {error && (
            <div className="p-2 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 text-sm">
              {error}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium mb-1">Valor recebido (R$)</label>
            <input
              type="number"
              step="0.01"
              min="0"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder={String(valorOriginal)}
              className="w-full px-3 py-2 border rounded-lg dark:bg-neutral-700 dark:border-neutral-600"
            />
            <p className="text-xs text-gray-500 mt-1">
              Deixe em branco para usar o valor original ({formatCurrency(valorOriginal)}).
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Forma de pagamento</label>
            <select
              value={paymentMethod}
              onChange={(e) => setPaymentMethod(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg dark:bg-neutral-700 dark:border-neutral-600"
            >
              {Object.entries(CLINICA_FORMA_PAGAMENTO_LABEL).map(([value, label]) => (
                <option key={value} value={value}>{label}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Data do pagamento</label>
            <input
              type="date"
              value={paymentDate}
              onChange={(e) => setPaymentDate(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg dark:bg-neutral-700 dark:border-neutral-600"
            />
          </div>

          <div className="flex gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-2 rounded-lg border border-gray-300 dark:border-neutral-600"
            >
              Cancelar
            </button>
            <button
              type="button"
              onClick={handleConfirm}
              disabled={loading}
              className="flex-1 py-2 rounded-lg text-white disabled:opacity-50 font-medium"
              style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
            >
              {loading ? "Registrando..." : "Confirmar Baixa"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
