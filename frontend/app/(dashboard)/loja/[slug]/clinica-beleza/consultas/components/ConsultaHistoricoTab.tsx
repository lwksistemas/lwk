import { ChevronRight, Pill } from "lucide-react";
import type { Consulta } from "./consultas-types";
import type { PrescricaoMemedItem } from "@/lib/clinica-beleza-api";

export function ConsultaHistoricoTab({
  historico,
  selectedId,
  prescricoes = [],
  formatData,
  onSelect,
}: {
  historico: Consulta[];
  selectedId: number;
  prescricoes?: PrescricaoMemedItem[];
  formatData: (d?: string | null) => string;
  onSelect: (c: Consulta) => void;
}) {
  return (
    <div className="space-y-6">
      {prescricoes.length > 0 && (
        <div className="rounded-xl border border-gray-200 dark:border-neutral-700 bg-white dark:bg-neutral-800/80 p-4 md:p-6 space-y-3">
          <h3 className="flex items-center gap-2 font-semibold text-gray-900 dark:text-gray-100 mb-2">
            <Pill size={16} className="text-[#8B3D52]" />
            Receituários e exames (Memed)
          </h3>
          {prescricoes.map((p) => (
            <div
              key={p.id}
              className="p-4 rounded-lg border border-gray-200 dark:border-neutral-600"
            >
              <p className="text-xs text-gray-500">
                {formatData(p.created_at)}
                {p.professional_name ? ` · ${p.professional_name}` : ""}
              </p>
              {p.itens && p.itens.length > 0 ? (
                <ul className="mt-1.5 space-y-1">
                  {p.itens.map((it, idx) => (
                    <li key={idx} className="text-sm text-gray-800 dark:text-gray-200">
                      <span className="font-medium">{it.nome}</span>
                      {it.posologia ? <span className="text-gray-500"> — {it.posologia}</span> : null}
                    </li>
                  ))}
                </ul>
              ) : (
                p.resumo && <p className="mt-1.5 text-sm text-gray-700 dark:text-gray-300 whitespace-pre-line">{p.resumo}</p>
              )}
            </div>
          ))}
        </div>
      )}

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
    </div>
  );
}
