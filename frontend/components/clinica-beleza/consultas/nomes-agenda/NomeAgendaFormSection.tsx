import { Loader2 } from "lucide-react";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";

export function NomeAgendaFormSection({
  formNome,
  editingId,
  saving,
  onNomeChange,
  onSave,
  onCancel,
}: {
  formNome: string;
  editingId: number | null;
  saving: boolean;
  onNomeChange: (v: string) => void;
  onSave: () => void;
  onCancel: () => void;
}) {
  return (
    <div className="mb-4 p-3 rounded-lg border-2 border-purple-200 dark:border-purple-800 bg-purple-50/50 dark:bg-purple-900/10 space-y-3">
      <label className="block text-xs font-medium text-gray-600 dark:text-gray-400">
        Nome da agenda *
      </label>
      <input
        type="text"
        value={formNome}
        onChange={(e) => onNomeChange(e.target.value)}
        placeholder="Ex: Estética, Dermatologia..."
        className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-neutral-600 bg-white dark:bg-neutral-800 text-sm"
        autoFocus
      />
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={onSave}
          disabled={saving}
          className="flex items-center gap-1.5 px-3 py-1.5 text-white rounded-lg text-sm font-medium disabled:opacity-50"
          style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
        >
          {saving ? <Loader2 size={14} className="animate-spin" /> : null}
          {editingId ? "Salvar" : "Adicionar"}
        </button>
        <button type="button" onClick={onCancel} className="px-3 py-1.5 text-sm text-gray-600 dark:text-gray-400">
          Cancelar
        </button>
      </div>
    </div>
  );
}
