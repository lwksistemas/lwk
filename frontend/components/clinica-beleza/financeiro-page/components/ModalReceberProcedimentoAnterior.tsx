"use client";

import { useEffect, useState } from "react";
import { X } from "lucide-react";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import { formatApiErrorBody } from "@/lib/api-errors";
import { formatCurrency } from "@/lib/financeiro-helpers";
import type { FinanceiroPayment } from "../types";

const FORMAS = [
  { id: "PIX", label: "PIX" },
  { id: "CASH", label: "Dinheiro" },
  { id: "CREDIT_CARD", label: "Cartão de crédito" },
  { id: "DEBIT_CARD", label: "Cartão de débito" },
  { id: "TRANSFER", label: "Transferência" },
];

interface ModalReceberProcedimentoAnteriorProps {
  payment: FinanceiroPayment | null;
  onClose: () => void;
  onSuccess: () => void;
}

export function ModalReceberProcedimentoAnterior({
  payment,
  onClose,
  onSuccess,
}: ModalReceberProcedimentoAnteriorProps) {
  const [valor, setValor] = useState("");
  const [data, setData] = useState("");
  const [forma, setForma] = useState("PIX");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!payment) return;
    setValor(String(payment.saldo_devedor || ""));
    setData(new Date().toISOString().slice(0, 10));
    setForma("PIX");
    setError("");
  }, [payment]);

  if (!payment?.patient_id) return null;

  const confirmar = async () => {
    setSaving(true);
    setError("");
    try {
      await ClinicaBelezaAPI.patients.procedimentosAnteriores.receber(payment.patient_id as number, payment.id, {
        valor: valor.replace(",", "."),
        data,
        payment_method: forma,
      });
      onSuccess();
      onClose();
    } catch (erro) {
      setError(formatApiErrorBody(erro) || "Não foi possível receber.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-md rounded-2xl bg-white p-5 shadow-xl dark:bg-neutral-800">
        <div className="mb-3 flex items-start justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Receber</h2>
            <p className="text-sm text-gray-500">{payment.paciente_nome}</p>
            <p className="text-sm text-gray-700 dark:text-gray-200">{payment.procedimento_nome}</p>
          </div>
          <button type="button" onClick={onClose} aria-label="Fechar"><X size={18} /></button>
        </div>
        <p className="mb-3 text-sm">Saldo {formatCurrency(payment.saldo_devedor)}</p>
        <div className="space-y-2">
          <input
            inputMode="decimal"
            value={valor}
            onChange={(e) => setValor(e.target.value)}
            aria-label="Valor recebido"
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-neutral-600 dark:bg-neutral-700"
          />
          <input
            type="date"
            value={data}
            onChange={(e) => setData(e.target.value)}
            aria-label="Data do recebimento"
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-neutral-600 dark:bg-neutral-700"
          />
          <select
            value={forma}
            onChange={(e) => setForma(e.target.value)}
            aria-label="Forma de pagamento"
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-neutral-600 dark:bg-neutral-700"
          >
            {FORMAS.map((item) => (
              <option key={item.id} value={item.id}>{item.label}</option>
            ))}
          </select>
        </div>
        {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
        <button
          type="button"
          disabled={saving}
          onClick={() => void confirmar()}
          className="mt-4 w-full rounded-lg px-3 py-2 text-sm font-medium text-white disabled:opacity-50"
          style={{ backgroundColor: "var(--cb-primary, #8B3D52)" }}
        >
          {saving ? "Recebendo..." : "Confirmar recebimento"}
        </button>
      </div>
    </div>
  );
}
