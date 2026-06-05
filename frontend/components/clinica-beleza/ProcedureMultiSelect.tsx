"use client";

import { useMemo } from "react";
import { Trash2 } from "lucide-react";
import { precoProcedimento } from "@/lib/convenio-precos";
import { entityName, procedureDuration, procedurePrice } from "@/lib/clinica-beleza-entities";

export interface ProcedureOption {
  id: number;
  name?: string;
  nome?: string;
  duration?: number;
  duracao_minutos?: number;
  price?: string;
  preco?: string | number;
}

interface Props {
  procedures: ProcedureOption[];
  selectedIds: number[];
  onAdd: (id: number) => void;
  onRemove: (id: number) => void;
  convenioId?: number | "";
  precosMap?: Record<number, number>;
  showSummary?: boolean;
}

export function ProcedureMultiSelect({
  procedures,
  selectedIds,
  onAdd,
  onRemove,
  convenioId = "",
  precosMap = {},
  showSummary = true,
}: Props) {
  const disponiveis = useMemo(
    () => procedures.filter((p) => !selectedIds.includes(p.id)),
    [procedures, selectedIds],
  );

  const resumo = useMemo(() => {
    let duracao = 0;
    let valor = 0;
    for (const id of selectedIds) {
      const proc = procedures.find((p) => p.id === id);
      if (proc) {
        duracao += procedureDuration(proc);
        const particular = Number(procedurePrice(proc)) || 0;
        valor += precoProcedimento(id, particular, convenioId, precosMap);
      }
    }
    return { duracao, valor };
  }, [selectedIds, procedures, convenioId, precosMap]);

  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
        Procedimentos * <span className="font-normal text-gray-400">(pode adicionar vários)</span>
      </label>
      <select
        className="w-full px-3 py-2.5 text-sm border border-gray-300 dark:border-neutral-600 rounded-lg dark:bg-neutral-700 focus:ring-2 focus:ring-pink-200 dark:focus:ring-pink-800 focus:border-pink-400 outline-none transition-colors"
        defaultValue=""
        onChange={(e) => {
          const id = Number(e.target.value);
          if (id) onAdd(id);
          e.target.value = "";
        }}
      >
        <option value="">Adicionar procedimento...</option>
        {disponiveis.map((p) => (
          <option key={p.id} value={p.id}>{entityName(p)}</option>
        ))}
      </select>

      {selectedIds.length > 0 && (
        <div className="mt-3 space-y-2">
          {selectedIds.map((id) => {
            const proc = procedures.find((p) => p.id === id);
            if (!proc) return null;
            const particular = Number(procedurePrice(proc)) || 0;
            const valorProc = precoProcedimento(id, particular, convenioId, precosMap);
            return (
              <div key={id} className="flex items-center justify-between px-4 py-3 bg-gray-50 dark:bg-neutral-700/50 rounded-lg">
                <div className="text-sm">
                  <span className="font-medium text-gray-800 dark:text-gray-200">{entityName(proc)}</span>
                  <span className="text-gray-500 dark:text-gray-400 ml-2 text-xs">
                    {procedureDuration(proc)}min
                    {valorProc > 0 ? ` · R$ ${valorProc.toFixed(2)}` : ""}
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => onRemove(id)}
                  className="p-1.5 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            );
          })}
          {showSummary && (
            <div className="flex items-center justify-between px-4 py-2 text-sm text-gray-600 dark:text-gray-400 border-t dark:border-neutral-600 mt-2 pt-3">
              <span>Duração total: <strong>{resumo.duracao} min</strong></span>
              {resumo.valor > 0 && <span>Valor: <strong>R$ {resumo.valor.toFixed(2)}</strong></span>}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
