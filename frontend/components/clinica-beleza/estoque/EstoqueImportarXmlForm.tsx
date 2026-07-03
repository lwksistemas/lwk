import {
  ESTOQUE_IMPORT_CATEGORIAS,
  formatXmlFileSizeKb,
} from "./estoque-importar-xml-utils";

interface EstoqueImportarXmlFormProps {
  arquivo: File | null;
  categoria: string;
  onCategoriaChange: (value: string) => void;
  onFileChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
}

export function EstoqueImportarXmlForm({
  arquivo,
  categoria,
  onCategoriaChange,
  onFileChange,
}: EstoqueImportarXmlFormProps) {
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
          className="w-full text-sm text-gray-600 dark:text-gray-400 file:mr-3 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-purple-50 file:text-purple-700 dark:file:bg-purple-900/20 dark:file:text-purple-300 hover:file:bg-purple-100"
        />
        {arquivo && (
          <p className="mt-1 text-xs text-gray-500">
            {arquivo.name} ({formatXmlFileSizeKb(arquivo.size)})
          </p>
        )}
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Categoria padrão dos produtos
        </label>
        <select
          value={categoria}
          onChange={(e) => onCategoriaChange(e.target.value)}
          className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100"
        >
          {ESTOQUE_IMPORT_CATEGORIAS.map((c) => (
            <option key={c.value} value={c.value}>
              {c.label}
            </option>
          ))}
        </select>
      </div>
    </>
  );
}
