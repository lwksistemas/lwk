"use client";

import { FolderOpen, Stethoscope } from "lucide-react";

export type ProcedimentoCategoriaCard = {
  value: string;
  label: string;
  count: number;
};

interface Props {
  categorias: ProcedimentoCategoriaCard[];
  loading?: boolean;
  totalProcedimentos?: number;
  onSelect: (categoria: ProcedimentoCategoriaCard) => void;
  onVerTodos: () => void;
}

export function ProcedimentosCategoriasGrid({
  categorias,
  loading,
  totalProcedimentos,
  onSelect,
  onVerTodos,
}: Props) {
  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <div
          className="w-10 h-10 border-4 border-t-transparent rounded-full animate-spin"
          style={{ borderColor: "var(--cb-primary, #8B3D52)", borderTopColor: "transparent" }}
        />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Selecione uma categoria para ver os procedimentos
          {typeof totalProcedimentos === "number" ? ` · ${totalProcedimentos} no total` : ""}
        </p>
        <button
          type="button"
          onClick={onVerTodos}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-lg border border-gray-300 dark:border-neutral-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-neutral-800"
        >
          <Stethoscope size={14} />
          Ver todos
        </button>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
        {categorias.map((cat) => (
          <button
            key={cat.value}
            type="button"
            onClick={() => onSelect(cat)}
            className="text-left p-4 rounded-xl border border-gray-200 dark:border-neutral-700 bg-white dark:bg-neutral-900 hover:border-[var(--cb-primary,#8B3D52)] hover:shadow-sm transition-all group"
          >
            <div className="flex items-start gap-3">
              <span
                className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg"
                style={{
                  backgroundColor: "color-mix(in srgb, var(--cb-primary, #8B3D52) 12%, transparent)",
                  color: "var(--cb-primary, #8B3D52)",
                }}
              >
                <FolderOpen size={18} />
              </span>
              <span className="min-w-0">
                <span className="block font-semibold text-gray-900 dark:text-gray-100 truncate group-hover:text-[var(--cb-primary,#8B3D52)]">
                  {cat.label}
                </span>
                <span className="block text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                  {cat.count} procedimento{cat.count !== 1 ? "s" : ""}
                </span>
              </span>
            </div>
          </button>
        ))}
      </div>

      {categorias.length === 0 && (
        <p className="text-center text-sm text-gray-500 py-8">
          Nenhum procedimento cadastrado ainda. Clique em Novo Procedimento para começar.
        </p>
      )}
    </div>
  );
}
