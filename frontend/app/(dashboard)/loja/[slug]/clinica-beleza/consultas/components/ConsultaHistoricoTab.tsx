import { ChevronRight } from "lucide-react";
import type { Consulta } from "./consultas-types";

export function ConsultaHistoricoTab({
  historico,
  selectedId,
  formatData,
  onSelect,
}: {
  historico: Consulta[];
  selectedId: number;
  formatData: (d?: string | null) => string;
  onSelect: (c: Consulta) => void;
}) {
  return (
    <div className="rounded-xl border border-gray-200 dark:border-neutral-700 bg-white dark:bg-neutral-800/80 p-4 md:p-6 space-y-3">
      <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">Consultas anteriores do cliente</h3>
      {historico.length === 0 ? (
        <p className="text-gray-500 text-sm">Nenhuma consulta anterior.</p>
      ) : (
        historico.map((h) => (
          <button
            key={h.id}
            type="button"
            onClick={() => h.id !== selectedId && onSelect(h)}
            disabled={h.id === selectedId}
            className={`w-full text-left p-4 rounded-lg border transition-colors ${
              h.id === selectedId
                ? "border-[#8B3D52] bg-[#F5E6EA]/40 dark:bg-neutral-700 cursor-default"
                : "border-gray-200 dark:border-neutral-600 hover:bg-gray-50 dark:hover:bg-neutral-700/50"
            }`}
          >
            <div className="flex justify-between items-center gap-2">
              <div>
                <p className="font-medium text-gray-900 dark:text-gray-100">{h.procedure_name}</p>
                <p className="text-xs text-gray-500 mt-0.5">
                  {formatData(h.data_inicio)}
                  {h.professional_name ? ` · ${h.professional_name}` : ""}
                </p>
              </div>
              {h.id !== selectedId && <ChevronRight size={18} className="text-gray-400 shrink-0" />}
            </div>
            {h.total_evolucoes > 0 && (
              <p className="text-xs text-gray-500 mt-1">{h.total_evolucoes} evolução(ões)</p>
            )}
          </button>
        ))
      )}
    </div>
  );
}
