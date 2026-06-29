import { Search } from "lucide-react";
import {
  ESTOQUE_CATEGORIAS,
  estoqueCategoriaLabel,
} from "@/components/clinica-beleza/estoque/estoque-types";

interface Props {
  categoriaFilter: string;
  searchTerm: string;
  onSearchChange: (value: string) => void;
  onCategoriaChange: (value: string) => void;
}

export function EstoqueFilters({
  categoriaFilter,
  searchTerm,
  onSearchChange,
  onCategoriaChange,
}: Props) {
  return (
    <div className="flex flex-wrap items-center gap-3 mb-4">
      {categoriaFilter && (
        <span className="px-2 py-1 rounded-full bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-200 text-sm">
          Filtro: {estoqueCategoriaLabel(categoriaFilter)}
        </span>
      )}
      <div className="relative flex-1 min-w-[200px] max-w-sm">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
        <input
          type="text"
          placeholder="Buscar por nome..."
          value={searchTerm}
          onChange={(e) => onSearchChange(e.target.value)}
          className="w-full pl-9 pr-3 py-2 border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100 text-sm"
        />
      </div>
      <select
        value={categoriaFilter}
        onChange={(e) => onCategoriaChange(e.target.value)}
        className="px-3 py-2 border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100 text-sm"
      >
        <option value="">Todas as categorias</option>
        {ESTOQUE_CATEGORIAS.map((c) => (
          <option key={c.value} value={c.value}>
            {c.label}
          </option>
        ))}
      </select>
    </div>
  );
}
