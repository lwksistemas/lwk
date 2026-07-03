"use client";

import { X } from "lucide-react";
import { DIAS_SEMANA } from "./horarios-trabalho-modal-utils";
import { useHorariosTrabalhoModal } from "./useHorariosTrabalhoModal";

export interface ModalHorariosTrabalhoProps {
  professionalId: number;
  professionalName: string;
  onClose: () => void;
  onSaved?: () => void;
}

export function ModalHorariosTrabalho({
  professionalId,
  professionalName,
  onClose,
  onSaved,
}: ModalHorariosTrabalhoProps) {
  const { loading, saving, error, rows, updateRow, handleSave } = useHorariosTrabalhoModal(
    professionalId,
    onClose,
    onSaved,
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
      <div className="bg-white dark:bg-neutral-800 rounded-2xl shadow-xl w-full max-w-2xl max-h-[90vh] flex flex-col border dark:border-neutral-700">
        <div className="flex justify-between items-center p-4 border-b dark:border-neutral-700 shrink-0">
          <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">
            Horários de trabalho — {professionalName}
          </h2>
          <button onClick={onClose} className="p-2 hover:bg-gray-100 dark:hover:bg-neutral-700 rounded" aria-label="Fechar">
            <X size={20} />
          </button>
        </div>

        <div className="p-4 overflow-y-auto flex-1 min-h-0">
          {error && (
            <div className="mb-4 p-2 rounded bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 text-sm">{error}</div>
          )}
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="w-8 h-8 border-2 border-purple-600 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : (
            <>
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
                Marque os dias em que o profissional trabalha e defina entrada, saída e intervalo (ex.: almoço).
              </p>
              <div className="space-y-3">
                {DIAS_SEMANA.map((d) => (
                  <div key={d.value} className="flex flex-wrap items-center gap-2 p-3 rounded-lg bg-gray-50 dark:bg-neutral-700/50">
                    <label className="flex items-center gap-2 w-full sm:w-40 shrink-0">
                      <input
                        type="checkbox"
                        checked={rows[d.value].ativo}
                        onChange={(e) => updateRow(d.value, "ativo", e.target.checked)}
                        className="rounded border-gray-300 dark:border-neutral-600 text-purple-600"
                      />
                      <span className="text-sm font-medium text-gray-800 dark:text-gray-200">{d.label}</span>
                    </label>
                    <div className="flex flex-wrap items-center gap-2 flex-1">
                      <div className="flex items-center gap-1">
                        <span className="text-xs text-gray-500 dark:text-gray-400">Entrada</span>
                        <input
                          type="time"
                          value={rows[d.value].hora_entrada}
                          onChange={(e) => updateRow(d.value, "hora_entrada", e.target.value)}
                          disabled={!rows[d.value].ativo}
                          className="px-2 py-1.5 border dark:border-neutral-600 rounded bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100 text-sm disabled:opacity-50"
                        />
                      </div>
                      <div className="flex items-center gap-1">
                        <span className="text-xs text-gray-500 dark:text-gray-400">Saída</span>
                        <input
                          type="time"
                          value={rows[d.value].hora_saida}
                          onChange={(e) => updateRow(d.value, "hora_saida", e.target.value)}
                          disabled={!rows[d.value].ativo}
                          className="px-2 py-1.5 border dark:border-neutral-600 rounded bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100 text-sm disabled:opacity-50"
                        />
                      </div>
                      <div className="flex items-center gap-1">
                        <span className="text-xs text-gray-500 dark:text-gray-400">Intervalo</span>
                        <input
                          type="time"
                          value={rows[d.value].intervalo_inicio ?? ""}
                          onChange={(e) => updateRow(d.value, "intervalo_inicio", e.target.value || null)}
                          disabled={!rows[d.value].ativo}
                          className="w-20 px-2 py-1.5 border dark:border-neutral-600 rounded bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100 text-sm disabled:opacity-50"
                        />
                        <span className="text-gray-400">–</span>
                        <input
                          type="time"
                          value={rows[d.value].intervalo_fim ?? ""}
                          onChange={(e) => updateRow(d.value, "intervalo_fim", e.target.value || null)}
                          disabled={!rows[d.value].ativo}
                          className="w-20 px-2 py-1.5 border dark:border-neutral-600 rounded bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100 text-sm disabled:opacity-50"
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>

        <div className="flex gap-2 p-4 border-t dark:border-neutral-700 shrink-0">
          <button
            onClick={onClose}
            className="flex-1 py-2 rounded-lg border border-gray-300 dark:border-neutral-600 hover:bg-gray-50 dark:hover:bg-neutral-700 text-gray-700 dark:text-gray-300"
          >
            Cancelar
          </button>
          <button
            onClick={() => void handleSave()}
            disabled={saving || loading}
            className="flex-1 py-2 rounded-lg bg-purple-600 text-white hover:bg-purple-700 disabled:opacity-50"
          >
            {saving ? "Salvando..." : "Salvar horários"}
          </button>
        </div>
      </div>
    </div>
  );
}

export type { HorarioTrabalhoItem } from "./horarios-trabalho-modal-utils";
