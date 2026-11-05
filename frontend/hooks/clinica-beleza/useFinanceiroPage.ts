"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import { useClinicaBelezaPaginatedList } from "@/hooks/clinica-beleza";
import { useToast } from "@/components/ui/Toast";
import type { DespesaItem } from "@/components/clinica-beleza/financeiro-page/DespesaFormModal";
import type {
  FinanceiroPayment,
  FinanceiroProfessional,
  FinanceiroResumo,
  FinanceiroTab,
} from "@/components/clinica-beleza/financeiro-page/types";

export function useFinanceiroPage() {
  const toast = useToast();
  const [tab, setTab] = useState<FinanceiroTab>("receitas");
  const [resumo, setResumo] = useState<FinanceiroResumo | null>(null);
  const [professionals, setProfessionals] = useState<FinanceiroProfessional[]>([]);
  const [loadingResumo, setLoadingResumo] = useState(true);
  const [statusFilter, setStatusFilter] = useState("");
  const [professionalFilter, setProfessionalFilter] = useState("");
  const [dateFilter, setDateFilter] = useState("");
  const [operadorFilter, setOperadorFilter] = useState("");
  const [formaFilter, setFormaFilter] = useState("");
  const [clienteFilter, setClienteFilter] = useState("");
  const [clienteConsulta, setClienteConsulta] = useState("");
  const [tipoFilter, setTipoFilter] = useState("");
  const [itemFilter, setItemFilter] = useState("");
  const [itemConsulta, setItemConsulta] = useState("");
  const [despesaStatusFilter, setDespesaStatusFilter] = useState("");
  const [despesaDateFilter, setDespesaDateFilter] = useState("");
  const [showDespesaModal, setShowDespesaModal] = useState(false);
  const [editingDespesa, setEditingDespesa] = useState<DespesaItem | null>(null);
  const [savingDespesa, setSavingDespesa] = useState(false);

  useEffect(() => {
    const espera = window.setTimeout(() => setClienteConsulta(clienteFilter.trim()), 350);
    return () => window.clearTimeout(espera);
  }, [clienteFilter]);

  useEffect(() => {
    const espera = window.setTimeout(() => setItemConsulta(itemFilter.trim()), 350);
    return () => window.clearTimeout(espera);
  }, [itemFilter]);

  const paymentQueryParams = useMemo(
    () => ({
      status: statusFilter || undefined,
      professional: professionalFilter || undefined,
      date: dateFilter || undefined,
      operador: operadorFilter || undefined,
      forma: formaFilter || undefined,
      cliente: clienteConsulta || undefined,
      tipo: tipoFilter || undefined,
      item: itemConsulta || undefined,
    }),
    [statusFilter, professionalFilter, dateFilter, operadorFilter, formaFilter, clienteConsulta, tipoFilter, itemConsulta],
  );

  const despesaQueryParams = useMemo(
    () => ({
      status: despesaStatusFilter || undefined,
      date: despesaDateFilter || undefined,
    }),
    [despesaStatusFilter, despesaDateFilter],
  );

  const paymentsList = useClinicaBelezaPaginatedList<FinanceiroPayment>({
    path: "/payments/",
    queryParams: paymentQueryParams,
    reloadDeps: [statusFilter, professionalFilter, dateFilter, operadorFilter, formaFilter, clienteConsulta, tipoFilter, itemConsulta],
  });

  const despesasList = useClinicaBelezaPaginatedList<DespesaItem>({
    path: "/despesas/",
    queryParams: despesaQueryParams,
    reloadDeps: [despesaStatusFilter, despesaDateFilter],
  });

  const loadResumo = useCallback(async () => {
    try {
      const data = await ClinicaBelezaAPI.financeiro.resumo();
      setResumo(data as FinanceiroResumo);
    } catch (e: unknown) {
      setResumo(null);
      toast.error(e instanceof Error ? e.message : "Erro ao carregar resumo financeiro.");
    }
  }, [toast]);

  const loadProfessionals = useCallback(async () => {
    try {
      const data = await ClinicaBelezaAPI.professionals.list({ all: 1 });
      const list = Array.isArray(data) ? (data as (FinanceiroProfessional & { is_profissional?: boolean })[]) : [];
      // Filtrar apenas profissionais reais (excluir administradores sem flag profissional)
      setProfessionals(list.filter((p) => p.is_profissional !== false));
    } catch (e: unknown) {
      setProfessionals([]);
      toast.error(e instanceof Error ? e.message : "Erro ao carregar profissionais.");
    }
  }, [toast]);

  const loadAll = useCallback(async () => {
    setLoadingResumo(true);
    await Promise.all([
      loadResumo(),
      loadProfessionals(),
      paymentsList.load(),
      despesasList.load(),
    ]);
    setLoadingResumo(false);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loadResumo, loadProfessionals, paymentsList.load, despesasList.load]);

  useEffect(() => {
    void loadAll();
  }, [loadAll]);

  const loading =
    loadingResumo || (tab === "receitas" ? paymentsList.loading : despesasList.loading);

  const totalListaReceitas = paymentsList.list.reduce(
    (s, p) => s + (p.status === "PAID" && p.payment_method !== "DESPESA" ? Number(p.amount) : 0),
    0,
  );

  const totalListaDespesas = despesasList.list.reduce(
    (s, d) => s + (d.status === "PAID" ? Number(d.valor) : 0),
    0,
  );

  const limparFiltrosReceita = () => {
    setStatusFilter("");
    setProfessionalFilter("");
    setDateFilter("");
    setOperadorFilter("");
    setFormaFilter("");
    setClienteFilter("");
    setClienteConsulta("");
    setTipoFilter("");
    setItemFilter("");
    setItemConsulta("");
  };

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
      toast.error("Não foi possível excluir a despesa.");
    }
  };

  const onDespesaSalva = async () => {
    setSavingDespesa(false);
    await loadAll();
  };

  return {
    tab,
    setTab,
    resumo,
    professionals,
    loadingResumo,
    loading,
    statusFilter,
    setStatusFilter,
    professionalFilter,
    setProfessionalFilter,
    dateFilter,
    setDateFilter,
    operadorFilter,
    setOperadorFilter,
    formaFilter,
    setFormaFilter,
    clienteFilter,
    setClienteFilter,
    tipoFilter,
    setTipoFilter,
    itemFilter,
    setItemFilter,
    limparFiltrosReceita,
    despesaStatusFilter,
    setDespesaStatusFilter,
    despesaDateFilter,
    setDespesaDateFilter,
    showDespesaModal,
    setShowDespesaModal,
    editingDespesa,
    savingDespesa,
    payments: paymentsList.list,
    loadingPayments: paymentsList.loading,
    paymentsPage: paymentsList.page,
    setPaymentsPage: paymentsList.setPage,
    paymentsTotalPages: paymentsList.totalPages,
    paymentsPageSize: paymentsList.pageSize,
    totalPayments: paymentsList.totalCount,
    despesas: despesasList.list,
    loadingDespesas: despesasList.loading,
    despesasPage: despesasList.page,
    setDespesasPage: despesasList.setPage,
    despesasTotalPages: despesasList.totalPages,
    despesasPageSize: despesasList.pageSize,
    totalDespesas: despesasList.totalCount,
    totalListaReceitas,
    totalListaDespesas,
    loadAll,
    abrirNovaDespesa,
    editarDespesa,
    removerDespesa,
    onDespesaSalva,
  };
}
