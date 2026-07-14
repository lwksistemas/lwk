"use client";

import { useCallback, useEffect, useState } from "react";
import { X } from "lucide-react";
import { CLINICA_FORMA_PAGAMENTO_LABEL } from "@/lib/clinica-beleza-constants";
import { formatCurrency } from "@/lib/financeiro-helpers";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import type { FinanceiroPayment } from "../types";

interface Parcela {
  id: number;
  valor: string | number;
  payment_method: string;
  payment_method_label?: string;
  payment_date: string;
  observacoes?: string;
  created_at: string;
}

interface ParcelasData {
  valor_total: number;
  valor_pago: number;
  saldo_devedor: number;
  status: string;
  parcelas: Parcela[];
}

interface ModalBaixaPaymentProps {
  payment: FinanceiroPayment | null;
  onClose: () => void;
  onSuccess: () => void;
}

export function ModalBaixaPayment({ payment, onClose, onSuccess }: ModalBaixaPaymentProps) {
  const [parcelasData, setParcelasData] = useState<ParcelasData | null>(null);
  const [loadingParcelas, setLoadingParcelas] = useState(false);
  const [valor, setValor] = useState("");
  const [paymentMethod, setPaymentMethod] = useState("CASH");
  const [paymentDate, setPaymentDate] = useState(new Date().toISOString().slice(0, 10));
  const [observacoes, setObservacoes] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const carregarParcelas = useCallback(async (id: number) => {
    setLoadingParcelas(true);
    try {
      const data = await ClinicaBelezaAPI.financeiro.payments.parcelas.list(id) as ParcelasData;
      setParcelasData(data);
    } catch {
      setParcelasData(null);
    } finally {
      setLoadingParcelas(false);
    }
  }, []);

  useEffect(() => {
    if (!payment) return;
    setValor("");
    setPaymentMethod("CASH");
    setPaymentDate(new Date().toISOString().slice(0, 10));
    setObservacoes("");
    setError("");
    setParcelasData(null);
    void carregarParcelas(payment.id);
  }, [payment, carregarParcelas]);

  if (!payment) return null;

  const valorTotal = parcelasData?.valor_total ?? Number(payment.amount) ?? 0;
  const saldoDevedor = parcelasData?.saldo_devedor ?? valorTotal;
  const valorPago = parcelasData?.valor_pago ?? 0;
  const parcelas = parcelasData?.parcelas ?? [];

  const valorEntrada = Number(valor) || 0;
  const saldoAposEntrada = Math.max(0, saldoDevedor - valorEntrada);
  const quitaTotal = valorEntrada > 0 && valorEntrada >= saldoDevedor;

  const handleConfirm = async () => {
    if (!valor || Number(valor) <= 0) {
      setError("Informe o valor recebido.");
      return;
    }
    setSaving(true);
    setError("");
    try {
      await ClinicaBelezaAPI.financeiro.payments.parcelas.add(payment.id, {
        valor: Number(valor),
        payment_method: paymentMethod,
        payment_date: paymentDate,
        observacoes,
      });
      if (quitaTotal) {
        onSuccess();
        onClose();
      } else {
        await carregarParcelas(payment.id);
        setValor("");
        setObservacoes("");
      }
    } catch {
      setError("Erro ao registrar pagamento. Tente novamente.");
    } finally {
      setSaving(false);
    }
  };

  const inputClass =
    "w-full px-3 py-2 border rounded-lg dark:bg-neutral-700 dark:border-neutral-600";

  return (
    <div className="fixed inset-0 z-[70] flex items-center justify-center bg-black/50 p-3 sm:p-4">
      <div className="bg-white dark:bg-neutral-800 rounded-2xl shadow-xl w-full max-w-4xl max-h-[92vh] flex flex-col overflow-hidden">
        <div className="flex items-center justify-between px-4 py-3 sm:px-5 border-b dark:border-neutral-700 shrink-0">
          <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">Registrar Pagamento</h2>
          <button
            type="button"
            onClick={onClose}
            className="p-2 hover:bg-gray-100 dark:hover:bg-neutral-700 rounded-lg"
            aria-label="Fechar"
          >
            <X size={18} />
          </button>
        </div>

        <div className="overflow-y-auto flex-1 p-4 sm:p-5">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5 md:gap-6 md:items-start">
            {/* Coluna esquerda — contexto + saldo + histórico */}
            <div className="space-y-4 min-w-0">
              <div className="text-sm space-y-1">
                <p>
                  <strong>Paciente:</strong> {payment.paciente_nome || "—"}
                </p>
                <p>
                  <strong>Procedimento:</strong> {payment.procedimento_nome || "—"}
                </p>
              </div>

              <div
                className={`p-3 rounded-xl text-sm border ${
                  saldoDevedor <= 0
                    ? "bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-700"
                    : "bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-700"
                }`}
              >
                <div className="flex justify-between mb-1">
                  <span className="text-gray-600 dark:text-gray-400">Valor total:</span>
                  <span className="font-semibold">{formatCurrency(valorTotal)}</span>
                </div>
                <div className="flex justify-between mb-1">
                  <span className="text-gray-600 dark:text-gray-400">Já pago:</span>
                  <span className="font-semibold text-green-700 dark:text-green-400">
                    {formatCurrency(valorPago)}
                  </span>
                </div>
                <div className="flex justify-between border-t dark:border-neutral-600 pt-1 mt-1">
                  <span className="font-semibold">Saldo devedor:</span>
                  <span
                    className={`font-bold text-base ${
                      saldoDevedor <= 0
                        ? "text-green-700 dark:text-green-400"
                        : "text-amber-700 dark:text-amber-300"
                    }`}
                  >
                    {saldoDevedor <= 0 ? "Quitado" : formatCurrency(saldoDevedor)}
                  </span>
                </div>
              </div>

              {loadingParcelas && (
                <p className="text-xs text-gray-500 text-center">Carregando histórico...</p>
              )}
              {parcelas.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase mb-2">
                    Histórico de pagamentos
                  </p>
                  <div className="space-y-1 max-h-48 md:max-h-[min(40vh,280px)] overflow-y-auto pr-1">
                    {parcelas.map((p) => (
                      <div
                        key={p.id}
                        className="flex justify-between items-center text-sm bg-gray-50 dark:bg-neutral-700/50 rounded-lg px-3 py-2 gap-2"
                      >
                        <div className="min-w-0">
                          <span className="font-medium">{formatCurrency(Number(p.valor))}</span>
                          <span className="text-gray-500 dark:text-gray-400 ml-2 text-xs">
                            {p.payment_method_label ||
                              CLINICA_FORMA_PAGAMENTO_LABEL[p.payment_method] ||
                              p.payment_method}
                          </span>
                        </div>
                        <span className="text-xs text-gray-500 dark:text-gray-400 shrink-0">
                          {new Date(p.payment_date + "T12:00:00").toLocaleDateString("pt-BR")}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Coluna direita — formulário */}
            <div className="min-w-0 md:border-l md:border-neutral-200 dark:md:border-neutral-700 md:pl-6">
              {saldoDevedor > 0 ? (
                <div className="space-y-3">
                  <p className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                    Registrar novo pagamento
                  </p>

                  {error && (
                    <div className="p-2 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 text-sm">
                      {error}
                    </div>
                  )}

                  <div>
                    <label className="block text-sm font-medium mb-1">
                      Valor recebido (R$){" "}
                      <span className="text-gray-400 font-normal text-xs">
                        — saldo: {formatCurrency(saldoDevedor)}
                      </span>
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      max={saldoDevedor}
                      value={valor}
                      onChange={(e) => setValor(e.target.value)}
                      placeholder={String(saldoDevedor.toFixed(2))}
                      className={inputClass}
                    />
                    {valorEntrada > 0 && (
                      <p
                        className={`text-xs mt-1 font-medium ${
                          quitaTotal
                            ? "text-green-600 dark:text-green-400"
                            : "text-amber-600 dark:text-amber-400"
                        }`}
                      >
                        {quitaTotal
                          ? "Quita o saldo completo"
                          : `Restará ${formatCurrency(saldoAposEntrada)} após este pagamento`}
                      </p>
                    )}
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <label className="block text-sm font-medium mb-1">Forma de pagamento</label>
                      <select
                        value={paymentMethod}
                        onChange={(e) => setPaymentMethod(e.target.value)}
                        className={inputClass}
                      >
                        {Object.entries(CLINICA_FORMA_PAGAMENTO_LABEL).map(([v, label]) => (
                          <option key={v} value={v}>
                            {label}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">Data do pagamento</label>
                      <input
                        type="date"
                        value={paymentDate}
                        onChange={(e) => setPaymentDate(e.target.value)}
                        className={inputClass}
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-1">
                      Observações <span className="text-gray-400 font-normal">(opcional)</span>
                    </label>
                    <input
                      type="text"
                      value={observacoes}
                      onChange={(e) => setObservacoes(e.target.value)}
                      placeholder="Ex: 1ª parcela, cheque nº 123..."
                      className={inputClass}
                    />
                  </div>
                </div>
              ) : (
                <div className="h-full flex items-center justify-center text-sm text-green-700 dark:text-green-400 font-medium py-8 md:py-12">
                  Este atendimento já está quitado.
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="px-4 py-3 sm:px-5 border-t dark:border-neutral-700 flex gap-2 shrink-0 md:justify-end">
          <button
            type="button"
            onClick={onClose}
            className="flex-1 md:flex-none md:min-w-[120px] py-2 px-4 rounded-lg border border-gray-300 dark:border-neutral-600"
          >
            {saldoDevedor <= 0 ? "Fechar" : "Cancelar"}
          </button>
          {saldoDevedor > 0 && (
            <button
              type="button"
              onClick={handleConfirm}
              disabled={saving || !valor || Number(valor) <= 0}
              className="flex-1 md:flex-none md:min-w-[160px] py-2 px-4 rounded-lg text-white disabled:opacity-50 font-medium"
              style={{ backgroundColor: "var(--cb-primary, #8B3D52)" }}
            >
              {saving ? "Registrando..." : quitaTotal ? "Quitar Tudo" : "Registrar Entrada"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
