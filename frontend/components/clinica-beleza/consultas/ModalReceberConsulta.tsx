"use client";

import { useEffect, useState } from "react";
import { X } from "lucide-react";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { CLINICA_FORMA_PAGAMENTO_LABEL } from "@/lib/clinica-beleza-constants";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import { formatApiErrorBody } from "@/lib/api-errors";
import { formatCurrency } from "@/lib/financeiro-helpers";
import {
  saldoReceberConsulta,
  valorPagamentoConsulta,
} from "@/hooks/clinica-beleza/consulta-detail-actions/consulta-detail-actions-utils";
import { consultaProcedimentosNomes, type Consulta } from "./consultas-types";

interface ModalReceberConsultaProps {
  open: boolean;
  consulta: Consulta;
  onClose: () => void;
  onSuccess: (consulta: Consulta) => void;
}

export function ModalReceberConsulta({
  open,
  consulta,
  onClose,
  onSuccess,
}: ModalReceberConsultaProps) {
  const saldo = saldoReceberConsulta(consulta);
  const total = valorPagamentoConsulta(consulta);
  const valorConsulta = Number(consulta.valor_consulta ?? 0);
  const valorProcedimentos = Number(consulta.valor_procedimentos ?? 0);
  const [paymentMethod, setPaymentMethod] = useState("CASH");
  const [markAsPaid, setMarkAsPaid] = useState(true);
  const [amount, setAmount] = useState(String(saldo || total || ""));
  const [desconto, setDesconto] = useState("");
  const [parcelas, setParcelas] = useState("1");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!open) return;
    const novoSaldo = saldoReceberConsulta(consulta);
    const novoTotal = valorPagamentoConsulta(consulta);
    setAmount(String(novoSaldo || novoTotal || ""));
    setDesconto("");
    setParcelas("1");
    setMarkAsPaid(true);
    setPaymentMethod("CASH");
    setError("");
  }, [open, consulta]);

  if (!open) return null;

  const valorBase = Number(amount) || 0;
  const valorDesconto = Number(desconto) || 0;
  const valorFinal = Math.max(0, valorBase - valorDesconto);
  const saldoAtual = saldoReceberConsulta(consulta);

  const handleConfirm = async () => {
    if (valorFinal <= 0) {
      setError("Informe um valor maior que zero.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const data = await ClinicaBelezaAPI.consultas.receber(consulta.id, {
        payment_method: paymentMethod,
        mark_as_paid: markAsPaid && valorFinal >= saldoAtual,
        amount: String(valorFinal),
        parcelas: paymentMethod === "CREDIT_CARD" ? Number(parcelas) : 1,
      });
      const atualizada = (data as { consulta?: Consulta }).consulta;
      if (!atualizada) throw new Error("Resposta inválida ao registrar recebimento.");
      onSuccess(atualizada);
      onClose();
    } catch (e: unknown) {
      setError(formatApiErrorBody(e) || "Erro ao registrar recebimento.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white dark:bg-neutral-800 rounded-2xl shadow-xl w-full max-w-md">
        <div className="flex items-center justify-between p-4 border-b dark:border-neutral-700">
          <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">Receber pagamento</h2>
          <button
            type="button"
            onClick={onClose}
            className="p-2 hover:bg-gray-100 dark:hover:bg-neutral-700 rounded-lg"
          >
            <X size={18} />
          </button>
        </div>
        <div className="p-4 space-y-4">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Registre o recebimento do atendimento. O início da consulta não depende do pagamento.
          </p>
          <div className="text-sm space-y-1">
            <p>
              <strong>Paciente:</strong> {consulta.patient_name}
            </p>
            <p>
              <strong>Procedimento:</strong> {consultaProcedimentosNomes(consulta)}
            </p>
            <p>
              <strong>Valor da consulta:</strong> {formatCurrency(valorConsulta)}
            </p>
            <p>
              <strong>Valor do procedimento:</strong> {formatCurrency(valorProcedimentos)}
            </p>
            <p className="font-semibold text-gray-800 dark:text-gray-200 pt-0.5">
              <strong>Total:</strong> {formatCurrency(total)}
            </p>
            {Number(consulta.valor_pago ?? 0) > 0 && (
              <p>
                <strong>Saldo em aberto:</strong> {formatCurrency(saldoAtual)}
              </p>
            )}
          </div>

          {error && (
            <div className="p-2 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 text-sm">
              {error}
            </div>
          )}

          <div className="space-y-2">
            <div>
              <label className="block text-sm font-medium mb-1">Valor (R$)</label>
              <input
                type="number"
                step="0.01"
                min="0"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                className="w-full px-3 py-2 border rounded-lg dark:bg-neutral-700 dark:border-neutral-600"
                placeholder="Valor a receber"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Desconto (R$)</label>
              <input
                type="number"
                step="0.01"
                min="0"
                value={desconto}
                onChange={(e) => setDesconto(e.target.value)}
                className="w-full px-3 py-2 border rounded-lg dark:bg-neutral-700 dark:border-neutral-600"
                placeholder="0,00"
              />
            </div>
            {valorDesconto > 0 && (
              <p className="text-sm font-semibold text-green-700 dark:text-green-400">
                Valor final a receber: {formatCurrency(valorFinal)}
              </p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Forma de pagamento</label>
            <select
              value={paymentMethod}
              onChange={(e) => setPaymentMethod(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg dark:bg-neutral-700 dark:border-neutral-600"
            >
              {Object.entries(CLINICA_FORMA_PAGAMENTO_LABEL).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>

          {paymentMethod === "CREDIT_CARD" && (
            <div>
              <label className="block text-sm font-medium mb-1">Parcelas no cartão</label>
              <select
                value={parcelas}
                onChange={(e) => setParcelas(e.target.value)}
                className="w-full px-3 py-2 border rounded-lg dark:bg-neutral-700 dark:border-neutral-600"
              >
                {Array.from({ length: 12 }, (_, i) => i + 1).map((n) => (
                  <option key={n} value={String(n)}>
                    {n}x de {formatCurrency(valorFinal / n)}
                    {n === 1 ? " (à vista)" : ""}
                  </option>
                ))}
              </select>
            </div>
          )}

          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={markAsPaid}
              onChange={(e) => setMarkAsPaid(e.target.checked)}
            />
            Quitar pagamento completo
          </label>

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
