"use client";

import { Pencil, Trash2 } from "lucide-react";
import { EntityListLoadMore } from "@/components/clinica-beleza/EntityListLoadMore";
import {
  CLINICA_FORMA_PAGAMENTO_LABEL,
  CLINICA_PAGAMENTO_STATUS_LABEL,
} from "@/lib/clinica-beleza-constants";
import { formatCurrency } from "@/lib/financeiro-helpers";
import type { DespesaItem } from "../DespesaFormModal";

interface FinanceiroDespesasTabProps {
  despesas: DespesaItem[];
  loading: boolean;
  page: number;
  totalPages: number;
  totalCount: number;
  pageSize: number;
  totalLista: number;
  statusFilter: string;
  dateFilter: string;
  onStatusFilterChange: (value: string) => void;
  onDateFilterChange: (value: string) => void;
  onPageChange: (page: number) => void;
  onEdit: (d: DespesaItem) => void;
  onRemove: (d: DespesaItem) => void;
}

export function FinanceiroDespesasTab({
  despesas,
  loading,
  page,
  totalPages,
  totalCount,
  pageSize,
  totalLista,
  statusFilter,
  dateFilter,
  onStatusFilterChange,
  onDateFilterChange,
  onPageChange,
  onEdit,
  onRemove,
}: FinanceiroDespesasTabProps) {
  return (
    <>
      <div className="flex flex-wrap gap-3 mb-4">
        <input
          type="date"
          value={dateFilter}
          onChange={(e) => onDateFilterChange(e.target.value)}
          className="px-3 py-2 border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-sm"
          title="Filtrar por vencimento"
        />
        <select
          value={statusFilter}
          onChange={(e) => onStatusFilterChange(e.target.value)}
          className="px-3 py-2 border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-sm"
        >
          <option value="">Todos os status</option>
          <option value="PAID">Pago</option>
          <option value="PENDING">Pendente</option>
          <option value="CANCELLED">Cancelado</option>
        </select>
      </div>
      <section className="bg-white dark:bg-neutral-800 rounded-xl shadow-md overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 dark:bg-neutral-700 border-b">
              <tr>
                <th className="text-left py-3 px-4 font-semibold">Vencimento</th>
                <th className="text-left py-3 px-4 font-semibold">Descrição</th>
                <th className="text-left py-3 px-4 font-semibold">Categoria</th>
                <th className="text-right py-3 px-4 font-semibold">Valor</th>
                <th className="text-left py-3 px-4 font-semibold">Status</th>
                <th className="text-left py-3 px-4 font-semibold hidden sm:table-cell">
                  Pagamento
                </th>
                <th className="w-20 p-3" />
              </tr>
            </thead>
            <tbody>
              {despesas.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-gray-500">
                    Nenhuma despesa lançada. Clique em <strong>Nova despesa</strong>.
                  </td>
                </tr>
              ) : (
                despesas.map((d) => (
                  <tr key={d.id} className="border-b border-gray-100 dark:border-neutral-700">
                    <td className="py-3 px-4 whitespace-nowrap">
                      {d.data_vencimento
                        ? String(d.data_vencimento).slice(0, 10).split("-").reverse().join("/")
                        : "—"}
                    </td>
                    <td className="py-3 px-4 font-medium">{d.descricao}</td>
                    <td className="py-3 px-4 text-gray-600">{d.categoria_nome || "—"}</td>
                    <td className="py-3 px-4 text-right font-medium">
                      {formatCurrency(d.valor)}
                    </td>
                    <td className="py-3 px-4">
                      {CLINICA_PAGAMENTO_STATUS_LABEL[d.status] || d.status}
                    </td>
                    <td className="py-3 px-4 hidden sm:table-cell text-gray-600">
                      {d.status === "PAID"
                        ? CLINICA_FORMA_PAGAMENTO_LABEL[d.forma_pagamento] ||
                          d.forma_pagamento ||
                          "—"
                        : "—"}
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex gap-1 justify-end">
                        <button
                          type="button"
                          onClick={() => onEdit(d)}
                          className="p-1.5 text-gray-600 hover:bg-gray-100 dark:hover:bg-neutral-700 rounded"
                          title="Editar"
                        >
                          <Pencil size={15} />
                        </button>
                        <button
                          type="button"
                          onClick={() => onRemove(d)}
                          className="p-1.5 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded"
                          title="Excluir"
                        >
                          <Trash2 size={15} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        <EntityListLoadMore
          page={page}
          totalPages={totalPages}
          totalCount={totalCount}
          pageSize={pageSize}
          loading={loading}
          onPageChange={onPageChange}
          itemLabel="despesas"
        />
      </section>
      {despesas.length > 0 && (
        <p className="mt-3 text-sm text-gray-500">
          Total na lista (pagas): {formatCurrency(totalLista)}
        </p>
      )}
    </>
  );
}
