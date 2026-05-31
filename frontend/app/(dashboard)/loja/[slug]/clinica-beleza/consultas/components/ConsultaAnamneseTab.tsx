import { Pencil, Save, X } from "lucide-react";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import type { Anamnese } from "./consultas-types";
import { ANAMNESE_FIELDS } from "./consultas-types";
import { PreviewBlock } from "./PreviewBlock";

export function ConsultaAnamneseTab({
  anamnese,
  anamneseDraft,
  editAnamnese,
  saving,
  onStartEdit,
  onCancelEdit,
  onChangeDraft,
  onSave,
}: {
  anamnese: Anamnese;
  anamneseDraft: Anamnese;
  editAnamnese: boolean;
  saving: boolean;
  onStartEdit: () => void;
  onCancelEdit: () => void;
  onChangeDraft: React.Dispatch<React.SetStateAction<Anamnese>>;
  onSave: () => void;
}) {
  return (
    <div className="rounded-xl border border-gray-200 dark:border-neutral-700 bg-white dark:bg-neutral-800/80 p-4 md:p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-gray-900 dark:text-gray-100">Anamnese do cliente</h3>
        {!editAnamnese ? (
          <button
            type="button"
            onClick={onStartEdit}
            className="inline-flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-lg border border-gray-300 dark:border-neutral-600 hover:bg-gray-50 dark:hover:bg-neutral-700"
          >
            <Pencil size={14} />
            Editar
          </button>
        ) : (
          <button type="button" onClick={onCancelEdit} className="inline-flex items-center gap-1.5 text-sm text-gray-500">
            <X size={14} />
            Cancelar
          </button>
        )}
      </div>
      {!editAnamnese ? (
        <>
          {ANAMNESE_FIELDS.map(([field, label]) => (
            <PreviewBlock key={field} label={label} value={String(anamnese[field] ?? "")} />
          ))}
          <div className="grid grid-cols-2 gap-4">
            <PreviewBlock label="Peso (kg)" value={anamnese.peso != null && anamnese.peso !== "" ? String(anamnese.peso) : ""} />
            <PreviewBlock label="Altura (m)" value={anamnese.altura != null && anamnese.altura !== "" ? String(anamnese.altura) : ""} />
          </div>
        </>
      ) : (
        <>
          {ANAMNESE_FIELDS.map(([field, label]) => (
            <div key={field}>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{label}</label>
              <textarea
                rows={field === "queixa_principal" ? 3 : 2}
                value={String(anamneseDraft[field] ?? "")}
                onChange={(e) => onChangeDraft((prev) => ({ ...prev, [field]: e.target.value }))}
                className="w-full px-3 py-2 border rounded-lg dark:bg-neutral-700 dark:border-neutral-600 text-sm"
              />
            </div>
          ))}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium mb-1">Peso (kg)</label>
              <input
                type="number"
                step="0.01"
                value={anamneseDraft.peso ?? ""}
                onChange={(e) => onChangeDraft((prev) => ({ ...prev, peso: e.target.value }))}
                className="w-full px-3 py-2 border rounded-lg dark:bg-neutral-700 dark:border-neutral-600"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Altura (m)</label>
              <input
                type="number"
                step="0.01"
                value={anamneseDraft.altura ?? ""}
                onChange={(e) => onChangeDraft((prev) => ({ ...prev, altura: e.target.value }))}
                className="w-full px-3 py-2 border rounded-lg dark:bg-neutral-700 dark:border-neutral-600"
              />
            </div>
          </div>
          <button
            type="button"
            onClick={onSave}
            disabled={saving}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-white disabled:opacity-50"
            style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
          >
            <Save size={18} />
            Salvar anamnese
          </button>
        </>
      )}
    </div>
  );
}
