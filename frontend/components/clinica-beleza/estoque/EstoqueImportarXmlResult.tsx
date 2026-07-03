import { AlertCircle, CheckCircle2 } from "lucide-react";
import type { ImportResult } from "./estoque-importar-xml-types";
import { formatImportResultSummary } from "./estoque-importar-xml-utils";

interface EstoqueImportarXmlResultProps {
  resultado: ImportResult;
}

export function EstoqueImportarXmlResult({ resultado }: EstoqueImportarXmlResultProps) {
  return (
    <div className="p-4 rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800">
      <div className="flex items-center gap-2 mb-2">
        <CheckCircle2 size={20} className="text-green-600" />
        <span className="font-semibold text-green-800 dark:text-green-200">
          {formatImportResultSummary(resultado.criados, resultado.atualizados)}
        </span>
      </div>
      {resultado.nota.numero && (
        <p className="text-xs text-green-700 dark:text-green-300">
          NF nº {resultado.nota.numero} — {resultado.nota.fornecedor}
        </p>
      )}
      {resultado.aviso_destinatario && (
        <div className="mt-2 p-2 rounded bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 flex items-start gap-2">
          <AlertCircle size={14} className="shrink-0 mt-0.5 text-amber-600" />
          <p className="text-xs text-amber-800 dark:text-amber-200">{resultado.aviso_destinatario}</p>
        </div>
      )}
      {resultado.erros.length > 0 && (
        <div className="mt-2 text-xs text-red-600">
          {resultado.erros.length} erro{resultado.erros.length !== 1 ? "s" : ""}:
          {resultado.erros.slice(0, 3).map((e, i) => (
            <p key={i}>
              • {e.nome}: {JSON.stringify(e.erros)}
            </p>
          ))}
        </div>
      )}
    </div>
  );
}
