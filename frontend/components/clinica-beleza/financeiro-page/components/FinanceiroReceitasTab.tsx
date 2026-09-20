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
import { statusPagamentoReceita } from "../payment-status";

function formatVencimento(iso: string | null): string {
  if (!iso) return "—";
  return String(iso).slice(0, 10).split("-").reverse().join("/");
}

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
  cobrandoId: number | null;
  onStatusFilterChange: (value: string) => void;
  onProfessionalFilterChange: (value: string) => void;
  onDateFilterChange: (value: string) => void;
  onPageChange: (page: number) => void;
  onBaixa: (payment: FinanceiroPayment) => void;
  onCobrar: (payment: FinanceiroPayment, canal: "whatsapp" | "email") => void;
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
  cobrandoId,
  onStatusFilterChange,
  onProfessionalFilterChange,
  onDateFilterChange,
  onPageChange,
  onBaixa,
  onCobrar,
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
          <option value="PARTIAL">Parcial</option>
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
          <table className="text-sm">
            <thead className="bg-gray-50 dark:bg-neutral-700 border-b border-gray-200 dark:border-neutral-600">
              <tr>
                <th className="text-left py-3 px-4 font-semibold">Data</th>
                <th className="text-left py-3 px-4 font-semibold">Cliente</th>
                <th className="text-left py-3 px-4 font-semibold">Profissional</th>
                <th className="text-left py-3 px-4 font-semibold">Procedimentos</th>
                <th className="text-right py-3 px-4 font-semibold">Valor</th>
                <th className="text-left py-3 px-4 font-semibold">Pagamento</th>
                <th className="text-left py-3 px-4 font-semibold whitespace-nowrap">Vencimento</th>
                <th className="text-left py-3 px-4 font-semibold">Status</th>
                <th className="text-right py-3 px-4 font-semibold whitespace-nowrap min-w-[8.5rem]">
                  Comissão
                </th>
                <th className="py-3 px-3 min-w-[9rem]"></th>
              </tr>
            </thead>
            <tbody>
              {payments.length === 0 ? (
                <tr>
                  <td colSpan={10} className="py-8 text-center text-gray-500">
                    Nenhum lançamento. Receitas são criadas ao finalizar consultas.
                  </td>
                </tr>
              ) : (
                payments.map((p) => {
                  const status = statusPagamentoReceita(p);
                  return (
                  <tr key={p.id} className="border-b border-gray-100 dark:border-neutral-700">
                    <td className="py-3 px-4 whitespace-nowrap text-gray-600">
                      {p.data_atendimento
                        ? formatClinicaDateTime(new Date(p.data_atendimento))
                        : "—"}
                    </td>
                    <td className="py-3 px-4">{p.paciente_nome || "—"}</td>
                    <td className="py-3 px-4">{p.profissional_nome || "—"}</td>
                    <td className="py-3 px-4 max-w-[220px] text-sm leading-snug col-allow-wrap">
                      {p.procedimento_nome || "Consulta"}
                    </td>
                    <td className="py-3 px-4 text-right font-medium">
                      {formatCurrency(p.valor_total_efetivo ?? p.amount)}
                    </td>
                    <td className="py-3 px-4">
                      {p.retorno_gratuito
                        ? "Retorno"
                        : CLINICA_FORMA_PAGAMENTO_LABEL[p.payment_method] || p.payment_method}
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      {!p.retorno_gratuito && p.data_vencimento ? (
                        <>
                          <span className={p.vencido ? "text-red-600 dark:text-red-400 font-medium" : "text-gray-600 dark:text-gray-400"}>
                            {formatVencimento(p.data_vencimento)}
                          </span>
                          {p.vencido && (
                            <span className="block text-xs text-red-600 dark:text-red-400">
                              {p.dias_atraso} dia(s) em atraso
                            </span>
                          )}
                        </>
                      ) : (
                        <span className="text-gray-400">—</span>
                      )}
                    </td>
                    <td className="py-3 px-4 col-allow-wrap">
                      {p.retorno_gratuito ? (
                        <span className="inline-block px-2 py-1 rounded-full text-xs font-medium bg-sky-100 text-sky-800 dark:bg-sky-900/30 dark:text-sky-300">
                          Isento
                        </span>
                      ) : (
                        <>
                          <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${
                            status === "PAID"
                              ? "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300"
                              : status === "PENDING"
                              ? "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300"
                              : status === "PARTIAL"
                              ? "bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300"
                              : "bg-gray-100 dark:bg-neutral-600"
                          }`}>
                            {CLINICA_PAGAMENTO_STATUS_LABEL[status] || status}
                          </span>
                          {status === "PARTIAL" && p.saldo_devedor > 0 && (
                            <span className="block text-xs text-orange-600 dark:text-orange-400 mt-0.5">
                              Falta {formatCurrency(p.saldo_devedor)}
                            </span>
                          )}
                        </>
                      )}
                    </td>
                    <td className="py-3 px-4 text-right col-allow-wrap">
                      {formatCurrency(p.comissao_valor || 0)}
                      {p.comissao_percentual ? (
                        <span className="block text-xs text-gray-500 font-normal">
                          ref. {p.comissao_percentual}% do total
                        </span>
                      ) : null}
                    </td>
                    <td className="py-3 px-3 text-center">
                      <div className="flex flex-col items-stretch gap-1">
                        {!p.retorno_gratuito && (status === "PENDING" || status === "PARTIAL") && (
                          <button
                            type="button"
                            onClick={() => onBaixa(p)}
                            className="text-xs px-2 py-1 rounded-lg bg-purple-600 hover:bg-purple-700 text-white font-medium whitespace-nowrap"
                          >
                            {status === "PARTIAL" ? "Complementar" : "Dar Baixa"}
                          </button>
                        )}
                        {p.vencido && (
                          <div className="flex items-center justify-center gap-1">
                            <button
                              type="button"
                              onClick={() => onCobrar(p, "whatsapp")}
                              disabled={cobrandoId === p.id}
                              title="Cobrar por WhatsApp"
                              className="text-xs px-2 py-1 rounded-lg bg-green-600 hover:bg-green-700 text-white font-medium disabled:opacity-50"
                            >
                              Zap
                            </button>
                            <button
                              type="button"
                              onClick={() => onCobrar(p, "email")}
                              disabled={cobrandoId === p.id}
                              title="Cobrar por e-mail"
                              className="text-xs px-2 py-1 rounded-lg border border-gray-300 dark:border-neutral-600 text-gray-700 dark:text-gray-200 font-medium disabled:opacity-50"
                            >
                              E-mail
                            </button>
                          </div>
                        )}
                      </div>
                    </td>
                  </tr>
                  );
                })
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
