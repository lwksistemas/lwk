"use client";

import { useEffect, useState } from "react";
import { X } from "lucide-react";
import {
  CLINICA_FORMA_PAGAMENTO_CORRIGIVEL,
  CLINICA_FORMA_PAGAMENTO_LABEL,
} from "@/lib/clinica-beleza-constants";
import { formatCurrency, formatDate } from "@/lib/financeiro-helpers";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import { formatApiErrorBody } from "@/lib/api-errors";
import type { FinanceiroPayment } from "../types";

interface ParcelaForma {
  id: number;
  valor: string | number;
  payment_method: string;
  payment_date: string;
}

interface ModalCorrigirFormaProps {
  payment: FinanceiroPayment | null;
  onClose: () => void;
  onSuccess: () => void;
}

export function ModalCorrigirForma({ payment, onClose, onSuccess }: ModalCorrigirFormaProps) {
  const [parcelas, setParcelas] = useState<ParcelaForma[]>([]);
  const [formas, setFormas] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!payment) return;
    let ativo = true;
    setError("");
    setLoading(true);
    setFormas({ pagamento: payment.payment_method });
    setParcelas([]);
    ClinicaBelezaAPI.financeiro.payments.parcelas
      .list(payment.id)
      .then((data) => {
        if (!ativo) return;
        const lista = ((data as { parcelas?: ParcelaForma[] }).parcelas || []).filter(
          (p) => Number(p.valor) > 0.009,
        );
        setParcelas(lista);
        const distintas = new Set(lista.map((p) => p.payment_method));
        if (distintas.size > 1) {
          setFormas(Object.fromEntries(lista.map((p) => [String(p.id), p.payment_method])));
        }
      })
      .catch((err) => {
        if (ativo) setError(formatApiErrorBody(err) || "Não foi possível carregar o recebimento.");
      })
      .finally(() => {
        if (ativo) setLoading(false);
      });
    return () => {
      ativo = false;
    };
  }, [payment]);

  if (!payment) return null;

  const varias = new Set(parcelas.map((p) => p.payment_method)).size > 1;
  const formaAtual = CLINICA_FORMA_PAGAMENTO_LABEL[payment.payment_method] || payment.payment_method;
  const mudou = varias
    ? parcelas.some((p) => formas[String(p.id)] && formas[String(p.id)] !== p.payment_method)
    : (formas.pagamento || payment.payment_method) !== payment.payment_method;

  const salvar = async () => {
    setSaving(true);
    setError("");
    try {
      if (varias) {
        for (const parcela of parcelas) {
          const nova = formas[String(parcela.id)];
          if (!nova || nova === parcela.payment_method) continue;
          await ClinicaBelezaAPI.financeiro.payments.corrigirForma(payment.id, {
            payment_method: nova,
            parcela_id: parcela.id,
          });
        }
      } else {
        await ClinicaBelezaAPI.financeiro.payments.corrigirForma(payment.id, {
          payment_method: formas.pagamento,
        });
      }
      onSuccess();
      onClose();
    } catch (err) {
      setError(formatApiErrorBody(err) || "Não foi possível corrigir a forma de pagamento.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[70] flex items-center justify-center bg-black/50 p-3 sm:p-4">
      <div className="bg-white dark:bg-neutral-800 rounded-2xl shadow-xl w-full max-w-lg max-h-[92vh] flex flex-col overflow-hidden">
        <div className="flex items-center justify-between px-4 py-3 sm:px-5 border-b dark:border-neutral-700 shrink-0">
          <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">Corrigir forma de pagamento</h2>
          <button
            type="button"
            onClick={onClose}
            className="p-2 hover:bg-gray-100 dark:hover:bg-neutral-700 rounded-lg"
            aria-label="Fechar"
          >
            <X size={18} />
          </button>
        </div>
        <div className="overflow-y-auto flex-1 p-4 sm:p-5 space-y-4">
          {error && (
            <div className="p-2 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 text-sm">
              {error}
            </div>
          )}
          <div className="text-sm space-y-1">
            <p><strong>Cliente:</strong> {payment.paciente_nome || "—"}</p>
            <p><strong>Recebido:</strong> {formatCurrency(payment.amount)}</p>
            <p><strong>Forma lançada:</strong> {formaAtual}</p>
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-300">
            O valor recebido continua o mesmo. O recibo passa a mostrar a forma correta.
          </p>
          {loading ? (
            <p className="text-sm text-gray-500">Carregando...</p>
          ) : varias ? (
            <div className="space-y-3">
              <p className="text-sm text-gray-600 dark:text-gray-300">
                Este recebimento teve mais de uma forma. Corrija a que ficou errada.
              </p>
              {parcelas.map((parcela) => (
                <label key={parcela.id} className="block text-sm">
                  <span className="font-medium">
                    {formatCurrency(Number(parcela.valor))} · {formatDate(parcela.payment_date)}
                  </span>
                  <select
                    value={formas[String(parcela.id)] || parcela.payment_method}
                    onChange={(e) => setFormas((atual) => ({ ...atual, [String(parcela.id)]: e.target.value }))}
                    className="mt-1 w-full px-3 py-2 border rounded-lg dark:bg-neutral-700 dark:border-neutral-600"
                  >
                    {CLINICA_FORMA_PAGAMENTO_CORRIGIVEL.map((codigo) => (
                      <option key={codigo} value={codigo}>
                        {CLINICA_FORMA_PAGAMENTO_LABEL[codigo]}
                      </option>
                    ))}
                  </select>
                </label>
              ))}
            </div>
          ) : (
            <label className="block text-sm">
              <span className="font-medium">Forma correta</span>
              <select
                value={formas.pagamento || payment.payment_method}
                onChange={(e) => setFormas({ pagamento: e.target.value })}
                className="mt-1 w-full px-3 py-2 border rounded-lg dark:bg-neutral-700 dark:border-neutral-600"
              >
                {CLINICA_FORMA_PAGAMENTO_CORRIGIVEL.map((codigo) => (
                  <option key={codigo} value={codigo}>
                    {CLINICA_FORMA_PAGAMENTO_LABEL[codigo]}
                  </option>
                ))}
              </select>
            </label>
          )}
        </div>
        <div className="px-4 py-3 sm:px-5 border-t dark:border-neutral-700 flex gap-2 shrink-0">
          <button
            type="button"
            onClick={onClose}
            className="flex-1 py-2 px-4 rounded-lg border border-gray-300 dark:border-neutral-600"
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={() => { void salvar(); }}
            disabled={saving || loading || !mudou}
            className="flex-1 py-2 px-4 rounded-lg text-white disabled:opacity-50 font-medium"
            style={{ backgroundColor: "var(--cb-primary, #8B3D52)" }}
          >
            {saving ? "Salvando..." : "Salvar correção"}
          </button>
        </div>
      </div>
    </div>
  );
}
