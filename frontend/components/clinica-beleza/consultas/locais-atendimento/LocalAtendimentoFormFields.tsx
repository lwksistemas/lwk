import { Loader2 } from "lucide-react";

export function LocalAtendimentoFormFields({
  formNome,
  formValor,
  onNomeChange,
  onValorChange,
  onSave,
  onCancel,
  saving,
  saveLabel,
}: {
  formNome: string;
  formValor: string;
  onNomeChange: (v: string) => void;
  onValorChange: (v: string) => void;
  onSave: () => void;
  onCancel: () => void;
  saving: boolean;
  saveLabel: string;
}) {
  return (
    <div className="space-y-3">
      <div>
        <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
          Nome do local
        </label>
        <input
          type="text"
          value={formNome}
          onChange={(e) => onNomeChange(e.target.value)}
          placeholder="Ex: Consultório, Home Care..."
          className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-neutral-600 bg-white dark:bg-neutral-800 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-purple-500/40"
          autoFocus
        />
      </div>
      <div>
        <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
          Valor da consulta (R$)
        </label>
        <input
          type="number"
          step="0.01"
          min="0"
          value={formValor}
          onChange={(e) => onValorChange(e.target.value)}
          placeholder="0,00"
          className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-neutral-600 bg-white dark:bg-neutral-800 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-purple-500/40"
        />
      </div>
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={onSave}
          disabled={saving}
          className="flex items-center gap-1.5 px-3 py-1.5 text-white rounded-lg text-sm font-medium disabled:opacity-50"
          style={{ backgroundColor: 'var(--cb-primary, #8B3D52)' }}
        >
          {saving ? <Loader2 size={14} className="animate-spin" /> : null}
          {saveLabel}
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="px-3 py-1.5 rounded-lg text-sm font-medium text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-neutral-800"
        >
          Cancelar
        </button>
      </div>
    </div>
  );
}
