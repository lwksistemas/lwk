"use client";

import { Plus, Trash2 } from "lucide-react";
import { CLINICA_FORMA_PAGAMENTO_LABEL } from "@/lib/clinica-beleza-constants";
import { formatCurrency } from "@/lib/financeiro-helpers";
import {
  parseMoneyInput,
  type EntradaPagamentoLinha,
} from "../modal-receber-consulta-utils";

const fieldClass =
  "w-full px-3 py-2 border rounded-lg dark:bg-neutral-700 dark:border-neutral-600";

interface ReceberFormasPagamentoProps {
  entradas: EntradaPagamentoLinha[];
  distribuido: number;
  totalLiquido: number;
  somaOk: boolean;
  onAdd: () => void;
  onRemove: (id: string) => void;
  onUpdate: (id: string, patch: Partial<EntradaPagamentoLinha>) => void;
}

export function ReceberFormasPagamento({
  entradas,
  distribuido,
  totalLiquido,
  somaOk,
  onAdd,
  onRemove,
  onUpdate,
}: ReceberFormasPagamentoProps) {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-gray-500 dark:text-gray-400 text-xs uppercase font-semibold">
          Formas de pagamento
        </p>
        <button
          type="button"
          onClick={onAdd}
          className="inline-flex items-center gap-1 text-sm font-medium text-[#8B4557] hover:underline"
        >
          <Plus size={16} /> Adicionar forma
        </button>
      </div>

      <div className="space-y-3">
        {entradas.map((linha, idx) => (
          <div
            key={linha.id}
            className="rounded-lg border border-gray-200 dark:border-neutral-600 p-3 space-y-2"
          >
            <div className="flex items-center justify-between gap-2">
              <span className="text-xs text-gray-500">Forma {idx + 1}</span>
              {entradas.length > 1 && (
                <button
                  type="button"
                  onClick={() => onRemove(linha.id)}
                  className="p-1 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded"
                  aria-label="Remover forma"
                >
                  <Trash2 size={16} />
                </button>
              )}
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              <div>
                <label className="block text-xs font-medium mb-1">Forma</label>
                <select
                  value={linha.payment_method}
                  onChange={(e) => onUpdate(linha.id, { payment_method: e.target.value })}
                  className={fieldClass}
                >
                  {Object.entries(CLINICA_FORMA_PAGAMENTO_LABEL).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium mb-1">Valor (R$)</label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={linha.valor}
                  onChange={(e) => onUpdate(linha.id, { valor: e.target.value })}
                  className={fieldClass}
                />
              </div>
            </div>
            {linha.payment_method === "CREDIT_CARD" && (
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-xs font-medium mb-1">Parcelas</label>
                  <select
                    value={linha.parcelas || "1"}
                    onChange={(e) => onUpdate(linha.id, { parcelas: e.target.value })}
                    className={fieldClass}
                  >
                    {Array.from({ length: 12 }, (_, i) => i + 1).map((n) => (
                      <option key={n} value={String(n)}>
                        {n}x
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium mb-1">Valor parcela (R$)</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={linha.valorParcela || ""}
                    onChange={(e) => onUpdate(linha.id, { valorParcela: e.target.value })}
                    placeholder={(
                      parseMoneyInput(linha.valor) / (Number(linha.parcelas) || 1)
                    ).toFixed(2)}
                    className={fieldClass}
                  />
                  <p className="text-xs text-gray-500 mt-0.5">Com taxa do cartão</p>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      <p
        className={`text-sm font-medium ${
          somaOk ? "text-green-700 dark:text-green-400" : "text-amber-700 dark:text-amber-400"
        }`}
      >
        Distribuído: {formatCurrency(distribuido)} / {formatCurrency(totalLiquido)}
        {somaOk ? " ✓" : ""}
      </p>
    </div>
  );
}
