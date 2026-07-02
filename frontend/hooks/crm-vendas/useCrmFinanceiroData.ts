'use client';

import { useCallback, useEffect, useState } from 'react';
import apiClient from '@/lib/api-client';
import { authService } from '@/lib/auth';
import {
  fetchLancamentosPorTipo,
  type GrupoFinanceiro,
  type LancamentoFinanceiro,
  type ResumoFinanceiro,
  type VendedorOption,
} from '@/lib/crm-financeiro-types';

export function useCrmFinanceiroData() {
  const [resumo, setResumo] = useState<ResumoFinanceiro | null>(null);
  const [lancamentosDespesa, setLancamentosDespesa] = useState<LancamentoFinanceiro[]>([]);
  const [lancamentosReceita, setLancamentosReceita] = useState<LancamentoFinanceiro[]>([]);
  const [grupos, setGrupos] = useState<GrupoFinanceiro[]>([]);
  const [vendedores, setVendedores] = useState<VendedorOption[]>([]);
  const [vendedorFiltro, setVendedorFiltro] = useState('');
  const [loading, setLoading] = useState(true);
  const [periodoRelatorio, setPeriodoRelatorio] = useState('mes_atual');
  const [dataInicioRel, setDataInicioRel] = useState('');
  const [dataFimRel, setDataFimRel] = useState('');
  const [grupoFiltroRelatorio, setGrupoFiltroRelatorio] = useState('');

  const isAdmin = !authService.isVendedor();

  const loadResumo = useCallback(async () => {
    const params = new URLSearchParams({ periodo: periodoRelatorio });
    if (vendedorFiltro) params.set('vendedor_id', vendedorFiltro);
    if (periodoRelatorio === 'personalizado' && dataInicioRel && dataFimRel) {
      params.set('data_inicio', dataInicioRel);
      params.set('data_fim', dataFimRel);
    }
    const { data } = await apiClient.get<ResumoFinanceiro>(`crm-vendas/financeiro/resumo/?${params}`);
    setResumo(data);
  }, [vendedorFiltro, periodoRelatorio, dataInicioRel, dataFimRel]);

  const loadLancamentos = useCallback(async () => {
    const [despesas, receitas] = await Promise.all([
      fetchLancamentosPorTipo('despesa', vendedorFiltro, periodoRelatorio, dataInicioRel, dataFimRel),
      fetchLancamentosPorTipo('receita', vendedorFiltro, periodoRelatorio, dataInicioRel, dataFimRel),
    ]);
    setLancamentosDespesa(despesas);
    setLancamentosReceita(receitas);
  }, [vendedorFiltro, periodoRelatorio, dataInicioRel, dataFimRel]);

  const loadGrupos = useCallback(async () => {
    const params = isAdmin ? '?incluir_inativos=true' : '';
    const { data } = await apiClient.get<{ results?: GrupoFinanceiro[] } | GrupoFinanceiro[]>(
      `crm-vendas/financeiro-grupos/${params}`,
    );
    setGrupos(Array.isArray(data) ? data : data.results ?? []);
  }, [isAdmin]);

  const loadVendedores = useCallback(async () => {
    if (!isAdmin) return;
    const { data } = await apiClient.get<{ results?: VendedorOption[] } | VendedorOption[]>(
      'crm-vendas/vendedores/?page_size=200',
    );
    setVendedores(Array.isArray(data) ? data : data.results ?? []);
  }, [isAdmin]);

  const loadAll = useCallback(async () => {
    setLoading(true);
    try {
      await Promise.allSettled([loadResumo(), loadLancamentos(), loadGrupos(), loadVendedores()]);
    } finally {
      setLoading(false);
    }
  }, [loadResumo, loadLancamentos, loadGrupos, loadVendedores]);

  useEffect(() => {
    loadAll();
  }, [loadAll]);

  return {
    resumo,
    lancamentosDespesa,
    lancamentosReceita,
    grupos,
    vendedores,
    vendedorFiltro,
    setVendedorFiltro,
    loading,
    isAdmin,
    periodoRelatorio,
    setPeriodoRelatorio,
    dataInicioRel,
    setDataInicioRel,
    dataFimRel,
    setDataFimRel,
    grupoFiltroRelatorio,
    setGrupoFiltroRelatorio,
    loadAll,
    loadGrupos,
  };
}
