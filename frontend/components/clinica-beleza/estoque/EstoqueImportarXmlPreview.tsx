import { AlertCircle } from "lucide-react";
import type { PreviewResult } from "./estoque-importar-xml-types";
import { formatProdutoPreviewLine } from "./estoque-importar-xml-utils";

interface EstoqueImportarXmlPreviewProps {
  preview: PreviewResult;
}

export function EstoqueImportarXmlPreview({ preview }: EstoqueImportarXmlPreviewProps) {
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
        <p className="text-sm font-medium text-blue-800 dark:text-blue-200">
          NF nº {preview.nota.numero || "—"} — {preview.nota.fornecedor || "Fornecedor"}
        </p>
        <p className="text-xs text-blue-600 dark:text-blue-400">
          {preview.total_produtos} produto{preview.total_produtos !== 1 ? "s" : ""} encontrado
          {preview.total_produtos !== 1 ? "s" : ""}
        </p>
      </div>
      <div className="max-h-48 overflow-y-auto border border-gray-200 dark:border-neutral-700 rounded-lg divide-y divide-gray-100 dark:divide-neutral-700">
        {preview.produtos.map((p, i) => (
          <div key={i} className="px-3 py-2 text-sm">
            <p className="font-medium text-gray-900 dark:text-gray-100 truncate">{p.nome}</p>
            <p className="text-xs text-gray-500 dark:text-gray-400">{formatProdutoPreviewLine(p)}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
