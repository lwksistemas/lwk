"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { EntityListLoadMore } from "@/components/clinica-beleza/EntityListLoadMore";
import { useParams } from "next/navigation";
import { DollarSign, Calendar, TrendingUp, Wallet, RefreshCw, Plus, Pencil, Trash2 } from "lucide-react";
import { ClinicaBelezaPageContent } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import {
  CLINICA_FORMA_PAGAMENTO_LABEL,
  CLINICA_PAGAMENTO_STATUS_LABEL,
} from "@/lib/clinica-beleza-constants";
import { formatCurrency } from "@/lib/financeiro-helpers";
import { formatClinicaDateTime } from "@/lib/clinica-beleza-datetime";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import { entityName } from "@/lib/clinica-beleza-entities";
import { useClinicaBelezaPaginatedList } from "@/hooks/clinica-beleza/useClinicaBelezaPaginatedList";
import { DespesaFormModal, type DespesaItem } from "./DespesaFormModal";

interface Resumo {
  caixa_diario: number;
  total_mes: number;
  contas_a_receber: number;
  comissao_mes: number;
  despesas_operacionais?: number;
  despesas_pendentes?: number;
  despesas: number;
  lucro: number;
}

interface Payment {
  id: number;
  appointment: number;
  amount: string;
  payment_method: string;
  status: string;
  payment_date: string | null;
  comissao_percentual: number;
  comissao_valor: string;
  paciente_nome: string;
  profissional_nome: string;
  procedimento_nome: string;
  data_atendimento: string;
  created_at: string;
}

interface Professional {
  id: number;
  name?: string;
  nome?: string;
}

type FinanceiroTab = "receitas" | "despesas";

export default function FinanceiroClinicaPage() {
  const params = useParams();
  const slug = params.slug as string;
  const [tab, setTab] = useState<FinanceiroTab>("receitas");
  const [resumo, setResumo] = useState<Resumo | null>(null);
  const [professionals, setProfessionals] = useState<Professional[]>([]);
  const [loadingResumo, setLoadingResumo] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [professionalFilter, setProfessionalFilter] = useState<string>("");
  const [dateFilter, setDateFilter] = useState<string>("");
  const [despesaStatusFilter, setDespesaStatusFilter] = useState<string>("");
  const [despesaDateFilter, setDespesaDateFilter] = useState<string>("");
  const [showDespesaModal, setShowDespesaModal] = useState(false);
  const [editingDespesa, setEditingDespesa] = useState<DespesaItem | null>(null);
  const [savingDespesa, setSavingDespesa] = useState(false);

  const paymentQueryParams = useMemo(
    () => ({
      status: statusFilter || undefined,
      professional: professionalFilter || undefined,
      date: dateFilter || undefined,
    }),
    [statusFilter, professionalFilter, dateFilter],
  );

  const despesaQueryParams = useMemo(
    () => ({
      status: despesaStatusFilter || undefined,
      date: despesaDateFilter || undefined,
    }),
    [despesaStatusFilter, despesaDateFilter],
  );

  const {
    list: payments,
    loading: loadingPayments,
    load: loadPayments,
    page: paymentsPage,
    setPage: setPaymentsPage,
    totalPages: paymentsTotalPages,
    pageSize: paymentsPageSize,
    totalCount: totalPayments,
  } = useClinicaBelezaPaginatedList<Payment>({
    path: "/payments/",
    queryParams: paymentQueryParams,
    reloadDeps: [statusFilter, professionalFilter, dateFilter],
  });

  const {
    list: despesas,
    loading: loadingDespesas,
    load: loadDespesas,
    page: despesasPage,
    setPage: setDespesasPage,
    totalPages: despesasTotalPages,
    pageSize: despesasPageSize,
    totalCount: totalDespesas,
  } = useClinicaBelezaPaginatedList<DespesaItem>({
    path: "/despesas/",
    queryParams: despesaQueryParams,
    reloadDeps: [despesaStatusFilter, despesaDateFilter],
  });

  const loadResumo = useCallback(async () => {
    try {
      const data = await ClinicaBelezaAPI.financeiro.resumo();
      setResumo(data);
    } catch {
      setResumo(null);
    }
  }, []);

  const loadProfessionals = useCallback(async () => {
    try {
      const data = await ClinicaBelezaAPI.professionals.list();
      setProfessionals(Array.isArray(data) ? data : []);
    } catch {
      setProfessionals([]);
    }
  }, []);

  const loadAll = useCallback(async () => {
    setLoadingResumo(true);
    await Promise.all([loadResumo(), loadProfessionals(), loadPayments(), loadDespesas()]);
    setLoadingResumo(false);
  }, [loadResumo, loadProfessionals, loadPayments, loadDespesas]);

  useEffect(() => {
    loadAll();
  }, [loadAll]);

  const loading = loadingResumo || (tab === "receitas" ? loadingPayments : loadingDespesas);
  const totalListaReceitas = payments.reduce((s, p) => s + (p.status === "PAID" ? Number(p.amount) : 0), 0);
  const totalListaDespesas = despesas.reduce((s, d) => s + (d.status === "PAID" ? Number(d.valor) : 0), 0);

  const abrirNovaDespesa = () => {
    setEditingDespesa(null);
    setShowDespesaModal(true);
  };

  const editarDespesa = (d: DespesaItem) => {
    setEditingDespesa(d);
    setShowDespesaModal(true);
  };

  const removerDespesa = async (d: DespesaItem) => {
    if (!confirm(`Excluir despesa "${d.descricao}"?`)) return;
    try {
      await ClinicaBelezaAPI.financeiro.despesas.delete(d.id);
      await loadAll();
    } catch {
      alert("Não foi possível excluir a despesa.");
    }
  };

  const onDespesaSalva = async () => {
    setSavingDespesa(false);
    await loadAll();
  };

  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title="Financeiro da Clínica"
        subtitle="Receitas, despesas e comissões"
        extraActions={
          <button
            type="button"
            onClick={() => loadAll()}
            disabled={loading}
            className="flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 text-white rounded-lg hover:opacity-90 disabled:opacity-50 text-xs sm:text-sm font-medium"
            style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
          >
            <RefreshCw size={16} className={loading ? "animate-spin" : ""} />
            <span className="hidden sm:inline">Atualizar</span>
          </button>
        }
      />
      <ClinicaBelezaPageContent>
        {loadingResumo && !resumo ? (
          <div className="flex justify-center py-12">
            <div className="w-10 h-10 border-4 border-purple-600 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : (
          <>
            <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              <div className="bg-white dark:bg-neutral-800 rounded-xl shadow-md p-4 border border-green-100 dark:border-green-900/50">
                <div className="flex items-center gap-2 text-green-700 dark:text-green-400 mb-1">
                  <Wallet size={20} />
                  <span className="text-sm font-medium">Caixa hoje</span>
                </div>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {formatCurrency(resumo?.caixa_diario ?? 0)}
                </p>
              </div>
              <div className="bg-white dark:bg-neutral-800 rounded-xl shadow-md p-4 border border-purple-100 dark:border-purple-900/50">
                <div className="flex items-center gap-2 text-purple-700 dark:text-purple-400 mb-1">
                  <DollarSign size={20} />
                  <span className="text-sm font-medium">Receita mês</span>
                </div>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {formatCurrency(resumo?.total_mes ?? 0)}
                </p>
              </div>
              <div className="bg-white dark:bg-neutral-800 rounded-xl shadow-md p-4 border border-amber-100 dark:border-amber-900/50">
                <div className="flex items-center gap-2 text-amber-700 dark:text-amber-400 mb-1">
                  <Calendar size={20} />
                  <span className="text-sm font-medium">A receber</span>
                </div>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {formatCurrency(resumo?.contas_a_receber ?? 0)}
                </p>
                {(resumo?.despesas_pendentes ?? 0) > 0 && (
                  <p className="text-xs text-amber-600 dark:text-amber-400 mt-1">
                    A pagar: {formatCurrency(resumo?.despesas_pendentes ?? 0)}
                  </p>
                )}
              </div>
              <div className="bg-white dark:bg-neutral-800 rounded-xl shadow-md p-4 border border-blue-100 dark:border-blue-900/50">
                <div className="flex items-center gap-2 text-blue-700 dark:text-blue-400 mb-1">
                  <TrendingUp size={20} />
                  <span className="text-sm font-medium">Despesas mês</span>
                </div>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {formatCurrency(resumo?.despesas ?? 0)}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Comissões {formatCurrency(resumo?.comissao_mes ?? 0)}
                  {(resumo?.despesas_operacionais ?? 0) > 0 && (
                    <> · Operacionais {formatCurrency(resumo?.despesas_operacionais ?? 0)}</>
                  )}
                </p>
                <p className="text-xs font-medium text-emerald-600 dark:text-emerald-400 mt-1">
                  Lucro: {formatCurrency(resumo?.lucro ?? 0)}
                </p>
              </div>
            </section>

            <div className="flex flex-wrap items-center gap-2 mb-4">
              <button
                type="button"
                onClick={() => setTab("receitas")}
                className={`px-4 py-2 rounded-lg text-sm font-medium ${
                  tab === "receitas"
                    ? "text-white"
                    : "bg-white dark:bg-neutral-800 text-gray-700 dark:text-gray-300 border border-gray-200 dark:border-neutral-700"
                }`}
                style={tab === "receitas" ? { backgroundColor: CLINICA_BELEZA_PRIMARY } : undefined}
              >
                Receitas (atendimentos)
              </button>
              <button
                type="button"
                onClick={() => setTab("despesas")}
                className={`px-4 py-2 rounded-lg text-sm font-medium ${
                  tab === "despesas"
                    ? "text-white"
                    : "bg-white dark:bg-neutral-800 text-gray-700 dark:text-gray-300 border border-gray-200 dark:border-neutral-700"
                }`}
                style={tab === "despesas" ? { backgroundColor: CLINICA_BELEZA_PRIMARY } : undefined}
              >
                Despesas
              </button>
              {tab === "despesas" && (
                <button
                  type="button"
                  onClick={abrirNovaDespesa}
                  className="ml-auto inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-white text-sm font-medium"
                  style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
                >
                  <Plus size={16} />
                  Nova despesa
                </button>
              )}
            </div>

            {tab === "receitas" ? (
              <>
                <div className="flex flex-wrap gap-3 mb-4">
                  <input
                    type="date"
                    value={dateFilter}
                    onChange={(e) => setDateFilter(e.target.value)}
                    className="px-3 py-2 border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100 text-sm"
                  />
                  <select
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                    className="px-3 py-2 border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100 text-sm"
                  >
                    <option value="">Todos os status</option>
                    <option value="PAID">Pago</option>
                    <option value="PENDING">Pendente</option>
                    <option value="CANCELLED">Cancelado</option>
                  </select>
                  <select
                    value={professionalFilter}
                    onChange={(e) => setProfessionalFilter(e.target.value)}
                    className="px-3 py-2 border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100 text-sm"
                  >
                    <option value="">Todos os profissionais</option>
                    {professionals.map((p) => (
                      <option key={p.id} value={p.id}>{entityName(p)}</option>
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
                                {p.data_atendimento ? formatClinicaDateTime(new Date(p.data_atendimento)) : "—"}
                              </td>
                              <td className="py-3 px-4">{p.paciente_nome || "—"}</td>
                              <td className="py-3 px-4">{p.profissional_nome || "—"}</td>
                              <td className="py-3 px-4 max-w-[220px] text-sm leading-snug">
                                {p.procedimento_nome || "—"}
                              </td>
                              <td className="py-3 px-4 text-right font-medium">{formatCurrency(p.amount)}</td>
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
                    page={paymentsPage}
                    totalPages={paymentsTotalPages}
                    totalCount={totalPayments ?? 0}
                    pageSize={paymentsPageSize}
                    loading={loadingPayments}
                    onPageChange={setPaymentsPage}
                    itemLabel="pagamentos"
                  />
                </section>
                {payments.length > 0 && (
                  <p className="mt-3 text-sm text-gray-500">
                    Total na lista (pagos): {formatCurrency(totalListaReceitas)}
                  </p>
                )}
              </>
            ) : (
              <>
                <div className="flex flex-wrap gap-3 mb-4">
                  <input
                    type="date"
                    value={despesaDateFilter}
                    onChange={(e) => setDespesaDateFilter(e.target.value)}
                    className="px-3 py-2 border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-sm"
                    title="Filtrar por vencimento"
                  />
                  <select
                    value={despesaStatusFilter}
                    onChange={(e) => setDespesaStatusFilter(e.target.value)}
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
                          <th className="text-left py-3 px-4 font-semibold hidden sm:table-cell">Pagamento</th>
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
                                {d.data_vencimento ? String(d.data_vencimento).slice(0, 10).split("-").reverse().join("/") : "—"}
                              </td>
                              <td className="py-3 px-4 font-medium">{d.descricao}</td>
                              <td className="py-3 px-4 text-gray-600">{d.categoria_nome || "—"}</td>
                              <td className="py-3 px-4 text-right font-medium">{formatCurrency(d.valor)}</td>
                              <td className="py-3 px-4">
                                {CLINICA_PAGAMENTO_STATUS_LABEL[d.status] || d.status}
                              </td>
                              <td className="py-3 px-4 hidden sm:table-cell text-gray-600">
                                {d.status === "PAID"
                                  ? CLINICA_FORMA_PAGAMENTO_LABEL[d.forma_pagamento] || d.forma_pagamento || "—"
                                  : "—"}
                              </td>
                              <td className="py-3 px-4">
                                <div className="flex gap-1 justify-end">
                                  <button
                                    type="button"
                                    onClick={() => editarDespesa(d)}
                                    className="p-1.5 text-gray-600 hover:bg-gray-100 dark:hover:bg-neutral-700 rounded"
                                    title="Editar"
                                  >
                                    <Pencil size={15} />
                                  </button>
                                  <button
                                    type="button"
                                    onClick={() => removerDespesa(d)}
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
                    page={despesasPage}
                    totalPages={despesasTotalPages}
                    totalCount={totalDespesas ?? 0}
                    pageSize={despesasPageSize}
                    loading={loadingDespesas}
                    onPageChange={setDespesasPage}
                    itemLabel="despesas"
                  />
                </section>
                {despesas.length > 0 && (
                  <p className="mt-3 text-sm text-gray-500">
                    Total na lista (pagas): {formatCurrency(totalListaDespesas)}
                  </p>
                )}
              </>
            )}
          </>
        )}
      </ClinicaBelezaPageContent>

      <DespesaFormModal
        open={showDespesaModal}
        editing={editingDespesa}
        saving={savingDespesa}
        onClose={() => setShowDespesaModal(false)}
        onSaved={onDespesaSalva}
      />
    </>
  );
}
