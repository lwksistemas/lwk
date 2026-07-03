import { Pencil, Trash2 } from "lucide-react";
import type { LocalAtendimentoItem } from "@/lib/clinica-beleza-api";
import { formatCurrencyBR } from "./locais-atendimento-utils";
import { LocalAtendimentoFormFields } from "./LocalAtendimentoFormFields";

export function LocalAtendimentoListItem({
  local,
  isEditing,
  formBusy,
  formNome,
  formValor,
  saving,
  onNomeChange,
  onValorChange,
  onSave,
  onCancel,
  onSetPadrao,
  onStartEdit,
  onDelete,
}: {
  local: LocalAtendimentoItem;
  isEditing: boolean;
  formBusy: boolean;
  formNome: string;
  formValor: string;
  saving: boolean;
  onNomeChange: (v: string) => void;
  onValorChange: (v: string) => void;
  onSave: () => void;
  onCancel: () => void;
  onSetPadrao: (id: number) => void;
  onStartEdit: (local: LocalAtendimentoItem) => void;
  onDelete: (id: number) => void;
}) {
  return (
    <li
      className={`p-3 rounded-lg ${
        isEditing
          ? "border-2 border-purple-300 dark:border-purple-700 bg-purple-50/40 dark:bg-purple-900/10"
          : "bg-gray-50 dark:bg-neutral-800"
      }`}
    >
      {isEditing ? (
        <div>
          <p className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-3 break-words">
            Editando: {local.nome}
          </p>
          <LocalAtendimentoFormFields
            formNome={formNome}
            formValor={formValor}
            onNomeChange={onNomeChange}
            onValorChange={onValorChange}
            onSave={onSave}
            onCancel={onCancel}
            saving={saving}
            saveLabel="Salvar"
          />
        </div>
      ) : (
        <div className="space-y-2">
          <div className="min-w-0">
            <p className="font-medium text-gray-900 dark:text-gray-100 text-sm break-words">{local.nome}</p>
            <div className="flex flex-wrap items-center gap-x-2 gap-y-1 mt-1">
              {local.is_padrao && (
                <span className="text-xs font-normal px-2 py-0.5 rounded-full bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-200">
                  Padrão
                </span>
              )}
              <span className="text-gray-500 dark:text-gray-400 text-sm">
                {formatCurrencyBR(local.valor_consulta)}
              </span>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-1">
            {!local.is_padrao && (
              <button
                type="button"
                onClick={() => onSetPadrao(local.id)}
                disabled={formBusy}
                className="px-2 py-1 text-xs rounded border border-gray-300 dark:border-neutral-600 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-neutral-700 disabled:opacity-40"
                title="Definir como padrão"
              >
                Definir padrão
              </button>
            )}
            <button
              type="button"
              onClick={() => onStartEdit(local)}
              disabled={formBusy}
              className="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-neutral-700 disabled:opacity-40"
              aria-label={`Editar ${local.nome}`}
              title="Editar"
            >
              <Pencil size={14} className="text-gray-500" />
            </button>
            <button
              type="button"
              onClick={() => onDelete(local.id)}
              disabled={formBusy}
              className="p-1.5 rounded hover:bg-red-50 dark:hover:bg-red-900/20 disabled:opacity-40"
              aria-label={`Excluir ${local.nome}`}
              title="Excluir"
            >
              <Trash2 size={14} className="text-red-500" />
            </button>
          </div>
        </div>
      )}
    </li>
  );
}
