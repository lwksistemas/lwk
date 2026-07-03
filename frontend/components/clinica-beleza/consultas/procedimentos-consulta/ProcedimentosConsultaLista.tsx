import { Trash2 } from "lucide-react";
import { formatCurrency } from "@/lib/financeiro-helpers";
import { toUpperCase } from "@/lib/format-br";
import type { AppointmentProcedureItem } from "./procedimentos-consulta-types";

export function ProcedimentosConsultaLista({
  itens,
  saving,
  onRemover,
}: {
  itens: AppointmentProcedureItem[];
  saving: boolean;
  onRemover: (item: AppointmentProcedureItem) => void;
}) {
  return (
    <ul className="rounded-lg border border-gray-200 dark:border-neutral-700 divide-y divide-gray-100 dark:divide-neutral-700 bg-gray-50/50 dark:bg-neutral-800/50">
      {itens.map((item) => (
        <li key={item.id} className="flex items-center justify-between gap-2 px-3 py-2 text-sm">
          <span className="font-medium text-gray-800 dark:text-gray-200 truncate">
            {toUpperCase(item.procedure_name)}
          </span>
          <div className="flex items-center gap-2 shrink-0">
            <span className="text-xs tabular-nums text-gray-500">{formatCurrency(item.valor_efetivo)}</span>
            <button
              type="button"
              onClick={() => onRemover(item)}
              disabled={saving}
              className="p-1 rounded hover:bg-red-50 dark:hover:bg-red-900/20 disabled:opacity-40"
              title="Remover"
            >
              <Trash2 size={13} className="text-red-500" />
            </button>
          </div>
        </li>
      ))}
    </ul>
  );
}
