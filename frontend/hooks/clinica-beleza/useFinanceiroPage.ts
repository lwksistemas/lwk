"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import { useClinicaBelezaPaginatedList } from "@/hooks/clinica-beleza";
import type { DespesaItem } from "@/app/(dashboard)/loja/[slug]/clinica-beleza/financeiro/DespesaFormModal";
import type {
  FinanceiroPayment,
  FinanceiroProfessional,
  FinanceiroResumo,
  FinanceiroTab,
} from "@/app/(dashboard)/loja/[slug]/clinica-beleza/financeiro/types";

export function useFinanceiroPage() {
  const [tab, setTab] = useState<FinanceiroTab>("receitas");
  const [resumo, setResumo] = useState<FinanceiroResumo | null>(null);
  const [professionals, setProfessionals] = useState<FinanceiroProfessional[]>([]);
  const [loadingResumo, setLoadingResumo] = useState(true);
  const [statusFilter, setStatusFilter] = useState("");
  const [professionalFilter, setProfessionalFilter] = useState("");
  const [dateFilter, setDateFilter] = useState("");
  const [despesaStatusFilter, setDespesaStatusFilter] = useState("");
  const [despesaDateFilter, setDespesaDateFilter] = useState("");
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

  const paymentsList = useClinicaBelezaPaginatedList<FinanceiroPayment>({
    path: "/payments/",
    queryParams: paymentQueryParams,
    reloadDeps: [statusFilter, professionalFilter, dateFilter],
  });

  const despesasList = useClinicaBelezaPaginatedList<DespesaItem>({
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
      setProfessionals(Array.isArray(data) ? (data as FinanceiroProfessional[]) : []);
    } catch {
      setProfessionals([]);
    }
  }, []);

  const loadAll = useCallback(async () => {
    setLoadingResumo(true);
    await Promise.all([
      loadResumo(),
      loadProfessionals(),
      paymentsList.load(),
      despesasList.load(),
    ]);
    setLoadingResumo(false);
  }, [loadResumo, loadProfessionals, paymentsList.load, despesasList.load]);

  useEffect(() => {
    void loadAll();
  }, [loadAll]);

  const loading =
    loadingResumo || (tab === "receitas" ? paymentsList.loading : despesasList.loading);

  const totalListaReceitas = paymentsList.list.reduce(
    (s, p) => s + (p.status === "PAID" ? Number(p.amount) : 0),
    0,
  );

  const totalListaDespesas = despesasList.list.reduce(
    (s, d) => s + (d.status === "PAID" ? Number(d.valor) : 0),
    0,
  );

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
