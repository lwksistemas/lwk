import { Search } from "lucide-react";
import {
  ESTOQUE_CATEGORIAS,
  estoqueCategoriaLabel,
  type EstoqueCategoria,
} from "@/components/clinica-beleza/estoque/estoque-types";

interface Props {
  categoriaFilter: string;
  searchTerm: string;
  onSearchChange: (value: string) => void;
  onCategoriaChange: (value: string) => void;
  categorias?: EstoqueCategoria[];
}

export function EstoqueFilters({
  categoriaFilter,
  searchTerm,
  onSearchChange,
  onCategoriaChange,
  categorias,
}: Props) {
  const options =
    categorias && categorias.length > 0
      ? categorias.map((c) => ({ value: c.slug, label: c.nome }))
      : ESTOQUE_CATEGORIAS.map((c) => ({ value: c.value, label: c.label }));

  return (
    <div className="flex flex-wrap items-center gap-3 mb-4">
      {categoriaFilter && (
        <span
          className="px-2 py-1 rounded-full text-sm"
          style={{
            backgroundColor: "color-mix(in srgb, var(--cb-primary, #8B3D52) 15%, transparent)",
            color: "var(--cb-primary, #8B3D52)",
          }}
        >
          Filtro: {estoqueCategoriaLabel(categoriaFilter, categorias)}
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
        {options.map((c) => (
          <option key={c.value} value={c.value}>
            {c.label}
          </option>
        ))}
      </select>
    </div>
  );
}
