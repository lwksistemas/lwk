"use client";

import { useState } from "react";
import { X } from "lucide-react";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { CLINICA_FORMA_PAGAMENTO_LABEL } from "@/lib/clinica-beleza-constants";
import { formatCurrency } from "@/lib/financeiro-helpers";
import { clinicaBelezaFetch } from "@/lib/clinica-beleza-api/fetch";

interface ModalPagamentoAgendaProps {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
  appointmentId: number;
  patientName: string;
  procedureName: string;
  procedurePrice: number | string;
}

export function ModalPagamentoAgenda({
  open,
  onClose,
  onSuccess,
  appointmentId,
  patientName,
  procedureName,
  procedurePrice,
}: ModalPagamentoAgendaProps) {
  const [paymentMethod, setPaymentMethod] = useState("CASH");
  const [markAsPaid, setMarkAsPaid] = useState(true);
  const [amount, setAmount] = useState(String(procedurePrice || ""));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  if (!open) return null;

  const handleConfirm = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await clinicaBelezaFetch(`/agenda/${appointmentId}/pagamento/`, {
        method: "POST",
        body: JSON.stringify({
          payment_method: paymentMethod,
          mark_as_paid: markAsPaid,
          amount: amount || undefined,
        }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.error || "Erro ao registrar pagamento.");
      }
      onSuccess();
      onClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao registrar pagamento.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white dark:bg-neutral-800 rounded-2xl shadow-xl w-full max-w-md">
        <div className="flex items-center justify-between p-4 border-b dark:border-neutral-700">
          <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">Registrar Pagamento</h2>
          <button type="button" onClick={onClose} className="p-2 hover:bg-gray-100 dark:hover:bg-neutral-700 rounded-lg">
            <X size={18} />
          </button>
        </div>
        <div className="p-4 space-y-4">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Cliente presente. Registre o pagamento <strong>antes</strong> do atendimento.
          </p>
          <div className="text-sm space-y-1">
            <p><strong>Paciente:</strong> {patientName}</p>
            <p><strong>Procedimento:</strong> {procedureName}</p>
            {Number(procedurePrice) > 0 && (
              <p><strong>Valor sugerido:</strong> {formatCurrency(Number(procedurePrice))}</p>
            )}
          </div>

          {error && (
            <div className="p-2 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 text-sm">
              {error}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium mb-1">Valor (R$)</label>
            <input
              type="number"
              step="0.01"
              min="0"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg dark:bg-neutral-700 dark:border-neutral-600"
              placeholder="Valor do atendimento"
            />
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

          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={markAsPaid}
              onChange={(e) => setMarkAsPaid(e.target.checked)}
            />
            Registrar como pago agora
          </label>

          <div className="flex gap-2 pt-2">
            <button type="button" onClick={onClose} className="flex-1 py-2 rounded-lg border border-gray-300 dark:border-neutral-600">
              Cancelar
            </button>
            <button
              type="button"
              onClick={handleConfirm}
              disabled={loading}
              className="flex-1 py-2 rounded-lg text-white disabled:opacity-50"
              style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
            >
              {loading ? "Registrando..." : "Confirmar"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
