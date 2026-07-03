import { Loader2 } from "lucide-react";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { toUpperCase } from "@/lib/format-br";
import type { ProcedureOption } from "./procedimentos-consulta-types";
import { PROCEDIMENTOS_SELECT_CLASS } from "./procedimentos-consulta-types";

export function ProcedimentoAdicionarForm({
  opcoesDisponiveis,
  procedureId,
  saving,
  onProcedureChange,
  onAdicionar,
  onCancel,
}: {
  opcoesDisponiveis: ProcedureOption[];
  procedureId: number | "";
  saving: boolean;
  onProcedureChange: (id: number | "") => void;
  onAdicionar: () => void;
  onCancel: () => void;
}) {
  return (
    <div className="p-3 rounded-lg border border-purple-200 dark:border-purple-800 bg-purple-50/40 dark:bg-purple-900/10 space-y-2">
      <label className="block text-xs font-medium text-gray-700 dark:text-gray-300">Incluir procedimento</label>
      <select
        value={procedureId}
        onChange={(e) => onProcedureChange(e.target.value ? Number(e.target.value) : "")}
        className={PROCEDIMENTOS_SELECT_CLASS}
        autoFocus
      >
        <option value="">Selecione...</option>
        {opcoesDisponiveis.map((p) => (
          <option key={p.id} value={p.id}>
            {toUpperCase(p.nome)}
          </option>
        ))}
      </select>
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={onAdicionar}
          disabled={saving || !procedureId}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-white disabled:opacity-50"
          style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
        >
          {saving ? <Loader2 size={14} className="animate-spin" /> : null}
          Incluir
        </button>
        <button
          type="button"
          onClick={onCancel}
          disabled={saving}
          className="px-3 py-1.5 text-xs text-gray-600 dark:text-gray-400"
        >
          Cancelar
        </button>
      </div>
    </div>
  );
}
