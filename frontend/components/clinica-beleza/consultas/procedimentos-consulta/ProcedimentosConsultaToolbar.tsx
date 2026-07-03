import { ChevronDown, ChevronUp, Plus } from "lucide-react";

export function ProcedimentosConsultaToolbar({
  itensCount,
  showManageList,
  podeAdicionar,
  saving,
  onToggleManageList,
  onAbrirAddForm,
}: {
  itensCount: number;
  showManageList: boolean;
  podeAdicionar: boolean;
  saving: boolean;
  onToggleManageList: () => void;
  onAbrirAddForm: () => void;
}) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      {itensCount > 0 && (
        <button
          type="button"
          onClick={onToggleManageList}
          className="inline-flex items-center gap-1 text-xs text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200"
        >
          {showManageList ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          Gerenciar ({itensCount})
        </button>
      )}
      {podeAdicionar && (
        <button
          type="button"
          onClick={onAbrirAddForm}
          disabled={saving}
          className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium border border-gray-300 dark:border-neutral-600 text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-neutral-700 disabled:opacity-50"
        >
          <Plus size={14} />
          Procedimento
        </button>
      )}
    </div>
  );
}
