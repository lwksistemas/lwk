"use client";

import { FolderOpen, Package, Settings2 } from "lucide-react";
import type { EstoqueCategoria } from "@/components/clinica-beleza/estoque/estoque-types";

interface Props {
  categorias: EstoqueCategoria[];
  loading?: boolean;
  onSelect: (categoria: EstoqueCategoria) => void;
  onVerTodos: () => void;
  onGerenciar: () => void;
  totalProdutos?: number;
}

export function EstoqueCategoriasGrid({
  categorias,
  loading,
  onSelect,
  onVerTodos,
  onGerenciar,
  totalProdutos,
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
          Selecione uma categoria para ver os produtos
          {typeof totalProdutos === "number" ? ` · ${totalProdutos} no total` : ""}
        </p>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={onVerTodos}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-lg border border-gray-300 dark:border-neutral-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-neutral-800"
          >
            <Package size={14} />
            Ver todos
          </button>
          <button
            type="button"
            onClick={onGerenciar}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-lg border border-gray-300 dark:border-neutral-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-neutral-800"
          >
            <Settings2 size={14} />
            Gerenciar
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
        {categorias.map((cat) => (
          <button
            key={cat.id}
            type="button"
            onClick={() => onSelect(cat)}
            className="text-left p-4 rounded-xl border border-gray-200 dark:border-neutral-700 bg-white dark:bg-neutral-900 hover:border-[var(--cb-primary,#8B3D52)] hover:shadow-sm transition-all group"
          >
            <div className="flex items-start gap-3">
              <span
                className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg"
                style={{ backgroundColor: `${cat.cor || "#8B3D52"}22`, color: cat.cor || "#8B3D52" }}
              >
                <FolderOpen size={18} />
              </span>
              <span className="min-w-0">
                <span className="block font-semibold text-gray-900 dark:text-gray-100 truncate group-hover:text-[var(--cb-primary,#8B3D52)]">
                  {cat.nome}
                </span>
                <span className="block text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                  {cat.produtos_count ?? 0} produto{(cat.produtos_count ?? 0) !== 1 ? "s" : ""}
                </span>
              </span>
            </div>
          </button>
        ))}
      </div>

      {categorias.length === 0 && (
        <p className="text-center text-sm text-gray-500 py-8">
          Nenhuma categoria cadastrada. Clique em Gerenciar para criar.
        </p>
      )}
    </div>
  );
}
