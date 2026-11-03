import { AlertCircle } from "lucide-react";
import { formatCurrency } from "@/lib/financeiro-helpers";
import type { PreviewResult, ProdutoPreview } from "./estoque-importar-xml-types";
import { formatProdutoPreviewLine } from "./estoque-importar-xml-utils";
import type { EstoqueCategoria } from "./estoque-types";
import { ESTOQUE_CATEGORIAS } from "./estoque-types";

function formatValorNota(valor: string | number | null | undefined): string {
  if (valor == null || valor === "") return "";
  const n = typeof valor === "number" ? valor : Number(String(valor).replace(",", "."));
  if (!Number.isFinite(n)) return "";
  return formatCurrency(n);
}

interface EstoqueImportarXmlPreviewProps {
  preview: PreviewResult;
  categorias?: EstoqueCategoria[];
  onProdutoCategoriaChange?: (index: number, slug: string, categoriaId?: number | null) => void;
}

export function EstoqueImportarXmlPreview({
  preview,
  categorias,
  onProdutoCategoriaChange,
}: EstoqueImportarXmlPreviewProps) {
  const options =
    categorias && categorias.length > 0
      ? categorias.map((c) => ({ value: c.slug, id: c.id, label: c.nome }))
      : ESTOQUE_CATEGORIAS.map((c) => ({ value: c.value, id: null as number | null, label: c.label }));

  const handleChange = (index: number, slug: string) => {
    const opt = options.find((o) => o.value === slug);
    onProdutoCategoriaChange?.(index, slug, opt?.id ?? null);
  };

  return (
    <div>
      {preview.aviso_destinatario && (
        <div className="p-3 rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 mb-3 flex items-start gap-2">
          <AlertCircle size={16} className="shrink-0 mt-0.5 text-amber-600" />
          <p className="text-sm text-amber-800 dark:text-amber-200">
            <strong>Atenção:</strong> {preview.aviso_destinatario}
          </p>
        </div>
      )}
      <div className="p-3 rounded-lg bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 mb-3">
        <p className="text-sm font-medium text-blue-800 dark:text-blue-200 flex flex-wrap items-baseline gap-x-2 gap-y-1">
          <span>
            NF nº {preview.nota.numero || "—"} — {preview.nota.fornecedor || "Fornecedor"}
          </span>
          {formatValorNota(preview.nota.valor_total) ? (
            <span className="font-semibold whitespace-nowrap">
              · Total {formatValorNota(preview.nota.valor_total)}
            </span>
          ) : null}
        </p>
        <p className="text-xs text-blue-600 dark:text-blue-400">
          {preview.total_produtos} produto{preview.total_produtos !== 1 ? "s" : ""} encontrado
          {preview.total_produtos !== 1 ? "s" : ""} · categorias inferidas (editáveis)
        </p>
      </div>

      <div className="border border-gray-200 dark:border-neutral-700 rounded-lg overflow-hidden">
        <div className="hidden sm:grid grid-cols-[minmax(0,1.6fr)_minmax(0,1fr)_minmax(12rem,0.7fr)] gap-3 px-3 py-2 text-[11px] uppercase tracking-wide text-gray-500 bg-gray-50 dark:bg-neutral-800/80 border-b border-gray-200 dark:border-neutral-700">
          <span>Produto</span>
          <span>Quantidade / valor</span>
          <span>Categoria</span>
        </div>
        <div className="max-h-[min(28rem,55vh)] overflow-y-auto divide-y divide-gray-100 dark:divide-neutral-700">
          {preview.produtos.map((p: ProdutoPreview, i) => (
            <div
              key={i}
              className="px-3 py-2.5 text-sm sm:grid sm:grid-cols-[minmax(0,1.6fr)_minmax(0,1fr)_minmax(12rem,0.7fr)] sm:gap-3 sm:items-center space-y-1.5 sm:space-y-0"
            >
              <div className="min-w-0">
                <p className="font-medium text-gray-900 dark:text-gray-100 break-words">{p.nome}</p>
                <p className="sm:hidden text-xs text-gray-500 dark:text-gray-400">
                  {formatProdutoPreviewLine(p)}
                </p>
              </div>
              <p className="hidden sm:block text-xs text-gray-600 dark:text-gray-300">
                {formatProdutoPreviewLine(p)}
              </p>
              {onProdutoCategoriaChange ? (
                <select
                  value={p.categoria || "outro"}
                  onChange={(e) => handleChange(i, e.target.value)}
                  className="w-full px-2 py-1.5 text-xs border border-gray-300 dark:border-neutral-600 rounded bg-white dark:bg-neutral-800"
                >
                  {options.map((c) => (
                    <option key={c.value} value={c.value}>
                      {c.label}
                    </option>
                  ))}
                </select>
              ) : (
                <span className="text-xs text-gray-500">{p.categoria || "—"}</span>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
