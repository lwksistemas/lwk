"use client";

import { Ban, Check, FileText, X } from "lucide-react";
import { formatCurrency } from "@/lib/financeiro-helpers";
import { formatarObservacoesOrcamento, STATUS_LABEL } from "./orcamento-tab-utils";
import type { Orcamento } from "./types";

interface OrcamentoViewerModalProps {
  visualizando: Orcamento;
  abrindoPdf: number | null;
  decidindoStatus: number | null;
  onClose: () => void;
  onPdf: (id: number) => void;
  onAceitar: (id: number) => void;
  onRecusar: (id: number) => void;
}

export function OrcamentoViewerModal({
  visualizando,
  abrindoPdf,
  decidindoStatus,
  onClose,
  onPdf,
  onAceitar,
  onRecusar,
}: OrcamentoViewerModalProps) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-3 sm:p-4"
      onClick={onClose}
    >
      <div
        className="bg-white dark:bg-neutral-800 rounded-2xl shadow-2xl w-full min-w-0 max-w-3xl max-h-[min(90vh,100%)] flex flex-col overflow-hidden"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="orcamento-visualizar-titulo"
        data-resizable-columns="off"
      >
        <div className="shrink-0 flex items-start justify-between gap-3 px-5 sm:px-6 py-3.5 border-b border-gray-200 dark:border-neutral-700">
          <div className="min-w-0">
            <h3 id="orcamento-visualizar-titulo" className="text-lg font-semibold text-gray-900 dark:text-white">
              Orçamento
            </h3>
            <p className="text-sm text-gray-500 mt-0.5 truncate">
              {visualizando.patient_name}
              {visualizando.professional_name ? ` · ${visualizando.professional_name}` : ""}
              {" · "}
              {new Date(visualizando.created_at).toLocaleDateString("pt-BR")}
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-neutral-700 text-gray-500 shrink-0"
            aria-label="Fechar"
          >
            <X size={18} />
          </button>
        </div>

        <div className="flex-1 min-h-0 min-w-0 overflow-y-auto overflow-x-hidden p-5 sm:p-6 space-y-4">
          <div className="grid w-full min-w-0 grid-cols-[minmax(0,1fr)_2.75rem_max-content] gap-x-3 text-sm">
            <div className="pb-2 font-medium text-gray-500 border-b border-gray-200 dark:border-gray-700">
              Procedimento
            </div>
            <div className="pb-2 font-medium text-center text-gray-500 border-b border-gray-200 dark:border-gray-700">
              Qtd
            </div>
            <div className="pb-2 font-medium text-right text-gray-500 border-b border-gray-200 dark:border-gray-700">
              Valor
            </div>
            {visualizando.itens.map((it) => (
              <div key={it.id} className="contents">
                <div className="min-w-0 py-2 break-words text-gray-900 dark:text-gray-100 border-b border-gray-100 dark:border-gray-700">
                  {it.nome_procedimento}
                </div>
                <div className="py-2 text-center text-gray-600 border-b border-gray-100 dark:border-gray-700">
                  {it.quantidade}
                </div>
                <div className="py-2 pl-3 text-right font-medium tabular-nums whitespace-nowrap border-b border-gray-100 dark:border-gray-700">
                  {formatCurrency(it.subtotal)}
                </div>
              </div>
            ))}
            <div className="col-span-2 pt-3 text-right font-semibold">Total</div>
            <div className="pt-3 pl-3 text-right font-bold tabular-nums whitespace-nowrap">
              {formatCurrency(visualizando.valor_total)}
            </div>
          </div>

          {visualizando.observacoes ? (
            <div className="pt-3 border-t border-gray-100 dark:border-neutral-700">
              <p className="text-xs font-medium text-gray-500 mb-1">Observações</p>
              <p className="text-sm text-gray-800 dark:text-gray-200 whitespace-pre-wrap break-words leading-relaxed">
                {formatarObservacoesOrcamento(visualizando.observacoes)}
              </p>
            </div>
          ) : null}

          <p className="text-xs text-gray-500">
            Válido por {visualizando.validade_dias} dias · {STATUS_LABEL[visualizando.status] || visualizando.status}
          </p>
        </div>

        <div className="shrink-0 flex flex-wrap gap-2 px-5 sm:px-6 py-3 border-t border-gray-200 dark:border-neutral-700 bg-white/90 dark:bg-neutral-800/90">
          <button
            type="button"
            onClick={() => onPdf(visualizando.id)}
            disabled={abrindoPdf === visualizando.id}
            className="flex items-center gap-1 px-4 py-2 text-sm text-white rounded-lg disabled:opacity-50"
            style={{ backgroundColor: "var(--cb-primary, #8B3D52)" }}
          >
            <FileText size={16} /> {abrindoPdf === visualizando.id ? "Abrindo..." : "Abrir PDF"}
          </button>
          {visualizando.status !== "ACEITO" && (
            <button
              type="button"
              onClick={() => onAceitar(visualizando.id)}
              disabled={decidindoStatus === visualizando.id}
              className="flex items-center gap-1 px-4 py-2 text-sm border border-emerald-300 text-emerald-800 rounded-lg disabled:opacity-50"
            >
              <Check size={16} /> Aceitar
            </button>
          )}
          {visualizando.status !== "RECUSADO" && (
            <button
              type="button"
              onClick={() => onRecusar(visualizando.id)}
              disabled={decidindoStatus === visualizando.id}
              className="flex items-center gap-1 px-4 py-2 text-sm border border-red-300 text-red-700 rounded-lg disabled:opacity-50"
            >
              <Ban size={16} /> Recusar
            </button>
          )}
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-sm border rounded-lg"
          >
            Fechar
          </button>
        </div>
      </div>
    </div>
  );
}
