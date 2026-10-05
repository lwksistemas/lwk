"use client";

import { formatCurrency } from "@/lib/financeiro-helpers";
import { STATUS_LABEL, statusBadgeClass } from "../tab-panels/orcamento-tab/orcamento-tab-utils";
import type { Orcamento } from "../tab-panels/orcamento-tab/types";

export function HistoricoOrcamentosSection({
  orcamentos,
  loading,
}: {
  orcamentos: Orcamento[];
  loading: boolean;
}) {
  if (loading) return <p className="text-sm text-gray-500">Carregando orçamentos...</p>;
  if (orcamentos.length === 0) {
    return <p className="text-sm text-gray-500">Nenhum orçamento deste cliente.</p>;
  }

  return (
    <ul className="space-y-3">
      {orcamentos.map((orc) => (
        <li key={orc.id} className="border border-gray-200 dark:border-neutral-700 rounded-lg p-3">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-semibold text-gray-900 dark:text-white">
              {formatCurrency(orc.valor_total)}
            </span>
            <span className={`text-xs px-2 py-0.5 rounded-full ${statusBadgeClass(orc.status)}`}>
              {STATUS_LABEL[orc.status] || orc.status}
            </span>
            {!orc.consulta_id && (
              <span className="text-xs text-amber-700 dark:text-amber-300">Sem atendimento</span>
            )}
            <span className="text-xs text-gray-500 ml-auto">
              {new Date(orc.created_at).toLocaleDateString("pt-BR")}
              {orc.professional_name ? ` · ${orc.professional_name}` : ""}
            </span>
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">
            {orc.itens.map((item) => item.nome_procedimento).join(", ")}
          </p>
        </li>
      ))}
    </ul>
  );
}
