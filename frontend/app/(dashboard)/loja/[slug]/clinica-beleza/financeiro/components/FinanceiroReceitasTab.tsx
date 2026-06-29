"use client";

import { EntityListLoadMore } from "@/components/clinica-beleza/EntityListLoadMore";
import {
  CLINICA_FORMA_PAGAMENTO_LABEL,
  CLINICA_PAGAMENTO_STATUS_LABEL,
} from "@/lib/clinica-beleza-constants";
import { formatClinicaDateTime } from "@/lib/clinica-beleza-datetime";
import { entityName } from "@/lib/clinica-beleza-entities";
import { formatCurrency } from "@/lib/financeiro-helpers";
import type { FinanceiroPayment, FinanceiroProfessional } from "../types";

interface FinanceiroReceitasTabProps {
  payments: FinanceiroPayment[];
  professionals: FinanceiroProfessional[];
  loading: boolean;
  page: number;
  totalPages: number;
  totalCount: number;
  pageSize: number;
  totalLista: number;
  statusFilter: string;
  professionalFilter: string;
  dateFilter: string;
  onStatusFilterChange: (value: string) => void;
  onProfessionalFilterChange: (value: string) => void;
  onDateFilterChange: (value: string) => void;
  onPageChange: (page: number) => void;
}

export function FinanceiroReceitasTab({
  payments,
  professionals,
  loading,
  page,
  totalPages,
  totalCount,
  pageSize,
  totalLista,
  statusFilter,
  professionalFilter,
  dateFilter,
  onStatusFilterChange,
  onProfessionalFilterChange,
  onDateFilterChange,
  onPageChange,
}: FinanceiroReceitasTabProps) {
  return (
    <>
      <div className="flex flex-wrap gap-3 mb-4">
        <input
          type="date"
          value={dateFilter}
          onChange={(e) => onDateFilterChange(e.target.value)}
          className="px-3 py-2 border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100 text-sm"
        />
        <select
          value={statusFilter}
          onChange={(e) => onStatusFilterChange(e.target.value)}
          className="px-3 py-2 border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100 text-sm"
        >
          <option value="">Todos os status</option>
          <option value="PAID">Pago</option>
          <option value="PENDING">Pendente</option>
          <option value="CANCELLED">Cancelado</option>
        </select>
        <select
          value={professionalFilter}
          onChange={(e) => onProfessionalFilterChange(e.target.value)}
          className="px-3 py-2 border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100 text-sm"
        >
          <option value="">Todos os profissionais</option>
          {professionals.map((p) => (
            <option key={p.id} value={p.id}>
              {entityName(p)}
            </option>
          ))}
        </select>
      </div>
      <section className="bg-white dark:bg-neutral-800 rounded-xl shadow-md overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 dark:bg-neutral-700 border-b border-gray-200 dark:border-neutral-600">
              <tr>
                <th className="text-left py-3 px-4 font-semibold">Data</th>
                <th className="text-left py-3 px-4 font-semibold">Cliente</th>
                <th className="text-left py-3 px-4 font-semibold">Profissional</th>
                <th className="text-left py-3 px-4 font-semibold">Procedimentos</th>
                <th className="text-right py-3 px-4 font-semibold">Valor</th>
                <th className="text-left py-3 px-4 font-semibold">Pagamento</th>
                <th className="text-left py-3 px-4 font-semibold">Status</th>
                <th className="text-right py-3 px-4 font-semibold">Comissão</th>
              </tr>
            </thead>
            <tbody>
              {payments.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-gray-500">
                    Nenhum lançamento. Receitas são criadas ao finalizar consultas.
                  </td>
                </tr>
              ) : (
                payments.map((p) => (
                  <tr key={p.id} className="border-b border-gray-100 dark:border-neutral-700">
                    <td className="py-3 px-4 whitespace-nowrap text-gray-600">
                      {p.data_atendimento
                        ? formatClinicaDateTime(new Date(p.data_atendimento))
                        : "—"}
                    </td>
                    <td className="py-3 px-4">{p.paciente_nome || "—"}</td>
                    <td className="py-3 px-4">{p.profissional_nome || "—"}</td>
                    <td className="py-3 px-4 max-w-[220px] text-sm leading-snug">
                      {p.procedimento_nome || "—"}
                    </td>
                    <td className="py-3 px-4 text-right font-medium">
                      {formatCurrency(p.amount)}
                    </td>
                    <td className="py-3 px-4">
                      {CLINICA_FORMA_PAGAMENTO_LABEL[p.payment_method] || p.payment_method}
                    </td>
                    <td className="py-3 px-4">
                      <span className="inline-block px-2 py-1 rounded-full text-xs font-medium bg-gray-100 dark:bg-neutral-600">
                        {CLINICA_PAGAMENTO_STATUS_LABEL[p.status] || p.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right whitespace-nowrap">
                      {formatCurrency(p.comissao_valor || 0)}
                      {p.comissao_percentual ? (
                        <span className="block text-xs text-gray-500 font-normal">
                          ref. {p.comissao_percentual}% do total
                        </span>
                      ) : null}
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
          itemLabel="pagamentos"
        />
      </section>
      {payments.length > 0 && (
        <p className="mt-3 text-sm text-gray-500">
          Total na lista (pagos): {formatCurrency(totalLista)}
        </p>
      )}
    </>
  );
}
