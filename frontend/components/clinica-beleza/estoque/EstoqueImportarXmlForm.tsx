import {
  ESTOQUE_IMPORT_CATEGORIAS,
  formatXmlFileSizeKb,
} from "./estoque-importar-xml-utils";
import type { EstoqueCategoria } from "./estoque-types";

interface EstoqueImportarXmlFormProps {
  arquivo: File | null;
  categoria: string;
  onCategoriaChange: (value: string) => void;
  onFileChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  categorias?: EstoqueCategoria[];
}

export function EstoqueImportarXmlForm({
  arquivo,
  categoria,
  onCategoriaChange,
  onFileChange,
  categorias,
}: EstoqueImportarXmlFormProps) {
  const options =
    categorias && categorias.length > 0
      ? categorias.map((c) => ({ value: c.slug, label: c.nome }))
      : ESTOQUE_IMPORT_CATEGORIAS.map((c) => ({ value: c.value, label: c.label }));

  return (
    <>
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Arquivo XML da NF-e *
        </label>
        <input
          type="file"
          accept=".xml"
          onChange={onFileChange}
          className="w-full text-sm text-gray-600 dark:text-gray-400 file:mr-3 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-[color-mix(in_srgb,var(--cb-primary,#8B3D52)_12%,transparent)] file:text-[var(--cb-primary,#8B3D52)]"
        />
        {arquivo && (
          <p className="mt-1 text-xs text-gray-500">
            {arquivo.name} ({formatXmlFileSizeKb(arquivo.size)})
          </p>
        )}
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Categoria padrão (fallback da inferência)
        </label>
        <select
          value={categoria}
          onChange={(e) => onCategoriaChange(e.target.value)}
          className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100"
        >
          {options.map((c) => (
            <option key={c.value} value={c.value}>
              {c.label}
            </option>
          ))}
        </select>
        <p className="mt-1 text-xs text-gray-500">
          Cada item será classificado por NCM/descrição; você pode ajustar no preview.
        </p>
      </div>
    </>
  );
}
