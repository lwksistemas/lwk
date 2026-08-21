"use client";

import { Pencil, Trash2 } from "lucide-react";
import { EntityListLoadMore } from "@/components/clinica-beleza/EntityListLoadMore";
import type { TermoConsentimentoTemplateItem } from "@/lib/clinica-beleza-api/types-entities";

interface Props {
  termos: TermoConsentimentoTemplateItem[];
  loading: boolean;
  page: number;
  totalPages: number;
  pageSize: number;
  totalCount: number;
  onPageChange: (page: number) => void;
  onEdit: (t: TermoConsentimentoTemplateItem) => void;
  onDelete: (t: TermoConsentimentoTemplateItem) => void;
}

export function TermosConsentimentoListView({
  termos,
  loading,
  page,
  totalPages,
  pageSize,
  totalCount,
  onPageChange,
  onEdit,
  onDelete,
}: Props) {
  return (
    <>
      {loading ? (
        <p className="text-sm text-gray-500 py-8 text-center">Carregando termos…</p>
      ) : termos.length === 0 ? (
        <p className="text-sm text-gray-500 py-8 text-center">
          Nenhum termo cadastrado. Crie um termo simples ou um TCLE Interativo.
        </p>
      ) : (
        <ul className="divide-y divide-gray-100 dark:divide-neutral-800 rounded-xl border border-gray-200 dark:border-neutral-700 bg-white dark:bg-neutral-900">
          {termos.map((t) => (
            <li key={t.id} className="flex items-center gap-3 px-4 py-3">
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">{t.nome}</p>
                <p className="text-xs text-gray-500">
                  {t.tipo === "interativo" ? "TCLE Interativo" : "Termo simples"}
                  {t.procedimentos && t.procedimentos.length > 0
                    ? ` · ${t.procedimentos.map((p) => p.nome).join(", ")}`
                    : " · sem procedimento vinculado"}
                </p>
              </div>
              <button type="button" onClick={() => onEdit(t)} className="p-2 text-gray-500 hover:text-gray-800" aria-label="Editar">
                <Pencil size={16} />
              </button>
              <button type="button" onClick={() => onDelete(t)} className="p-2 text-gray-500 hover:text-red-600" aria-label="Excluir">
                <Trash2 size={16} />
              </button>
            </li>
          ))}
        </ul>
      )}
      <EntityListLoadMore
        page={page}
        totalPages={totalPages}
        pageSize={pageSize}
        totalCount={totalCount}
        onPageChange={onPageChange}
      />
    </>
  );
}
