import { Pencil, Trash2 } from "lucide-react";
import type { NomeAgendaItem } from "@/lib/clinica-beleza-api";

export function NomeAgendaListItem({
  item,
  isEditing,
  formBusy,
  onSetPadrao,
  onStartEdit,
  onDelete,
}: {
  item: NomeAgendaItem;
  isEditing: boolean;
  formBusy: boolean;
  onSetPadrao: (id: number) => void;
  onStartEdit: (item: NomeAgendaItem) => void;
  onDelete: (id: number) => void;
}) {
  return (
    <li
      className={`p-3 rounded-lg ${
        isEditing
          ? "border-2 border-purple-300 dark:border-purple-700 bg-purple-50/40"
          : "bg-gray-50 dark:bg-neutral-800"
      }`}
    >
      {isEditing ? (
        <p className="text-sm font-medium text-gray-900 dark:text-gray-100 break-words">{item.nome}</p>
      ) : (
        <div className="space-y-2">
          <div className="min-w-0">
            <span className="font-medium text-sm text-gray-900 dark:text-gray-100 break-words">{item.nome}</span>
            {item.is_padrao && (
              <span className="ml-1.5 text-xs font-normal px-2 py-0.5 rounded-full bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-200 whitespace-nowrap">
                Padrão
              </span>
            )}
          </div>
          <div className="flex flex-wrap items-center gap-1">
            {!item.is_padrao && (
              <button
                type="button"
                onClick={() => onSetPadrao(item.id)}
                disabled={formBusy}
                className="px-2 py-1 text-xs rounded border border-gray-300 dark:border-neutral-600 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-neutral-700 disabled:opacity-40"
                title="Definir como padrão"
              >
                Definir padrão
              </button>
            )}
            <button
              type="button"
              onClick={() => onStartEdit(item)}
              disabled={formBusy}
              className="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-neutral-700 disabled:opacity-40"
              title="Editar"
            >
              <Pencil size={14} className="text-gray-500" />
            </button>
            <button
              type="button"
              onClick={() => onDelete(item.id)}
              disabled={formBusy}
              className="p-1.5 rounded hover:bg-red-50 dark:hover:bg-red-900/20 disabled:opacity-40"
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
