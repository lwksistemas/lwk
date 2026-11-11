import { useState } from "react";
import { AlertCircle, CheckCircle2 } from "lucide-react";
import { formatCurrency } from "@/lib/financeiro-helpers";
import type { ImportResult } from "./estoque-importar-xml-types";
import { formatImportResultSummary, textoPagamentoNota } from "./estoque-importar-xml-utils";

interface EstoqueImportarXmlResultProps {
  resultado: ImportResult;
  respondendo?: boolean;
  onResponderPagamento?: (pago: boolean, vencimento: string) => void;
}

export function EstoqueImportarXmlResult({
  resultado,
  respondendo = false,
  onResponderPagamento,
}: EstoqueImportarXmlResultProps) {
  const [vencimento, setVencimento] = useState("");
  const financeiro = resultado.financeiro;
  const valor = financeiro?.valor ? formatCurrency(Number(financeiro.valor)) : "";
  return (
    <div className="p-4 rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800">
      <div className="flex items-center gap-2 mb-2">
        <CheckCircle2 size={20} className="text-green-600" />
        <span className="font-semibold text-green-800 dark:text-green-200">
          {formatImportResultSummary(resultado.criados, resultado.atualizados, resultado.ignorados || 0)}
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
      {financeiro?.lancado && (
        <p className="mt-2 text-xs text-green-800 dark:text-green-200">
          {financeiro.situacao === "pago"
            ? "Despesa lançada como paga."
            : textoPagamentoNota(financeiro)}
        </p>
      )}
      {financeiro?.precisa_resposta && (
        <div className="mt-3 p-3 rounded-lg bg-white/80 dark:bg-neutral-900/40 border border-green-200 dark:border-green-800 space-y-2">
          <p className="text-sm text-gray-800 dark:text-gray-100">
            A nota não informa se foi paga{valor ? ` (${valor})` : ""}. Como lançar a despesa?
          </p>
          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              disabled={respondendo}
              onClick={() => onResponderPagamento?.(true, "")}
              className="px-3 py-1.5 rounded-lg text-xs font-medium bg-[#8B3D52] text-white disabled:opacity-50"
            >
              Foi paga
            </button>
            <label className="flex items-center gap-1 text-xs text-gray-600 dark:text-gray-300">
              Vencimento
              <input
                type="date"
                value={vencimento}
                onChange={(e) => setVencimento(e.target.value)}
                className="px-2 py-1 border border-gray-300 dark:border-neutral-600 rounded bg-white dark:bg-neutral-800"
              />
            </label>
            <button
              type="button"
              disabled={respondendo || !vencimento}
              onClick={() => onResponderPagamento?.(false, vencimento)}
              className="px-3 py-1.5 rounded-lg text-xs font-medium border border-gray-300 dark:border-neutral-600 disabled:opacity-50"
            >
              Ainda não foi paga
            </button>
          </div>
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
