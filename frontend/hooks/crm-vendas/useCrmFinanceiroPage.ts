'use client';

import { useCallback, useEffect, useState } from 'react';
import apiClient from '@/lib/api-client';
import { authService } from '@/lib/auth';

export type TipoFinanceiro = 'receita' | 'despesa';

export interface GrupoFinanceiro {
  id: number;
  nome: string;
  tipo: TipoFinanceiro;
  is_active: boolean;
  ordem: number;
}

export interface LancamentoFinanceiro {
  id: number;
  vendedor: number;
  vendedor_nome: string;
  grupo: number | null;
  grupo_nome: string;
  tipo: TipoFinanceiro;
  tipo_display: string;
  origem: string;
  origem_display: string;
  descricao: string;
  valor: number;
  status: string;
  status_display: string;
  data_vencimento: string;
  data_pagamento: string | null;
  oportunidade: number | null;
  oportunidade_titulo: string;
  observacoes: string;
  editavel: boolean;
}

export interface ResumoFinanceiro {
  receitas_pagas: number;
  receitas_pendentes: number;
  despesas_pagas: number;
  despesas_pendentes: number;
  saldo_realizado: number;
  saldo_previsto: number;
  comissao_vendas_total: number;
}

export interface VendedorOption {
  id: number;
  nome: string;
}

export function useCrmFinanceiroPage() {
  const [tab, setTab] = useState<TipoFinanceiro | 'grupos'>('receita');
  const [resumo, setResumo] = useState<ResumoFinanceiro | null>(null);
  const [lancamentos, setLancamentos] = useState<LancamentoFinanceiro[]>([]);
  const [grupos, setGrupos] = useState<GrupoFinanceiro[]>([]);
  const [vendedores, setVendedores] = useState<VendedorOption[]>([]);
  const [vendedorFiltro, setVendedorFiltro] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState<LancamentoFinanceiro | null>(null);
  const [showGrupoModal, setShowGrupoModal] = useState(false);
  const [editingGrupo, setEditingGrupo] = useState<GrupoFinanceiro | null>(null);

  const isAdmin = !authService.isVendedor();

  const loadResumo = useCallback(async () => {
    const params = vendedorFiltro ? `?vendedor_id=${vendedorFiltro}` : '';
    const { data } = await apiClient.get<ResumoFinanceiro>(`crm-vendas/financeiro/resumo/${params}`);
    setResumo(data);
  }, [vendedorFiltro]);

  const loadLancamentos = useCallback(async () => {
    if (tab === 'grupos') return;
    const params = new URLSearchParams({ tipo: tab, page_size: '100' });
    if (vendedorFiltro) params.set('vendedor_id', vendedorFiltro);
    const { data } = await apiClient.get<{ results?: LancamentoFinanceiro[] } | LancamentoFinanceiro[]>(
      `crm-vendas/financeiro-lancamentos/?${params}`,
    );
    setLancamentos(Array.isArray(data) ? data : data.results ?? []);
  }, [tab, vendedorFiltro]);

  const loadGrupos = useCallback(async () => {
    const { data } = await apiClient.get<{ results?: GrupoFinanceiro[] } | GrupoFinanceiro[]>(
      'crm-vendas/financeiro-grupos/?page_size=200',
    );
    setGrupos(Array.isArray(data) ? data : data.results ?? []);
  }, []);

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
      await Promise.all([loadResumo(), loadLancamentos(), loadGrupos(), loadVendedores()]);
    } finally {
      setLoading(false);
    }
  }, [loadResumo, loadLancamentos, loadGrupos, loadVendedores]);

  useEffect(() => {
    loadAll();
  }, [loadAll]);

  useEffect(() => {
    if (!loading) loadLancamentos();
  }, [tab, vendedorFiltro, loadLancamentos, loading]);

  const abrirNovo = (tipo: TipoFinanceiro) => {
    setEditing(null);
    setTab(tipo);
    setShowModal(true);
  };

  const editar = (item: LancamentoFinanceiro) => {
    setEditing(item);
    setShowModal(true);
  };

  const salvarLancamento = async (payload: Record<string, unknown>) => {
    setSaving(true);
    try {
      if (editing) {
        await apiClient.patch(`crm-vendas/financeiro-lancamentos/${editing.id}/`, payload);
      } else {
        await apiClient.post('crm-vendas/financeiro-lancamentos/', payload);
      }
      setShowModal(false);
      await loadAll();
    } finally {
      setSaving(false);
    }
  };

  const marcarPago = async (id: number) => {
    await apiClient.post(`crm-vendas/financeiro-lancamentos/${id}/marcar_pago/`, {});
    await loadAll();
  };

  const removerLancamento = async (item: LancamentoFinanceiro) => {
    if (!item.editavel) {
      alert('Lançamentos de comissão automática não podem ser excluídos.');
      return;
    }
    if (!confirm('Excluir este lançamento?')) return;
    await apiClient.delete(`crm-vendas/financeiro-lancamentos/${item.id}/`);
    await loadAll();
  };

  const salvarGrupo = async (payload: Record<string, unknown>) => {
    setSaving(true);
    try {
      if (editingGrupo) {
        await apiClient.patch(`crm-vendas/financeiro-grupos/${editingGrupo.id}/`, payload);
      } else {
        await apiClient.post('crm-vendas/financeiro-grupos/', payload);
      }
      setShowGrupoModal(false);
      setEditingGrupo(null);
      await loadAll();
    } finally {
      setSaving(false);
    }
  };

  const removerGrupo = async (grupo: GrupoFinanceiro) => {
    if (!confirm(`Excluir grupo "${grupo.nome}"?`)) return;
    try {
      await apiClient.delete(`crm-vendas/financeiro-grupos/${grupo.id}/`);
      await loadAll();
    } catch {
      alert('Não foi possível excluir. O grupo pode estar em uso.');
    }
  };

  return {
    tab,
    setTab,
    resumo,
    lancamentos,
    grupos,
    vendedores,
    vendedorFiltro,
    setVendedorFiltro,
    loading,
    saving,
    isAdmin,
    showModal,
    setShowModal,
    editing,
    abrirNovo,
    editar,
    salvarLancamento,
    marcarPago,
    removerLancamento,
    showGrupoModal,
    setShowGrupoModal,
    editingGrupo,
    setEditingGrupo,
    salvarGrupo,
    removerGrupo,
    loadAll,
  };
}
