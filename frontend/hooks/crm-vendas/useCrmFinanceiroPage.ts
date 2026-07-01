'use client';

import { useCallback, useEffect, useState } from 'react';
import apiClient from '@/lib/api-client';
import { authService } from '@/lib/auth';
import { getCrmApiErrorDetail } from '@/lib/crm-utils';
import { useToast } from '@/components/ui/Toast';

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

async function fetchLancamentosPorTipo(
  tipo: TipoFinanceiro,
  vendedorFiltro: string,
  periodo: string,
  dataInicio: string,
  dataFim: string,
): Promise<LancamentoFinanceiro[]> {
  const params = new URLSearchParams({ tipo, page_size: '100', periodo });
  if (vendedorFiltro) params.set('vendedor_id', vendedorFiltro);
  if (periodo === 'personalizado' && dataInicio && dataFim) {
    params.set('data_inicio', dataInicio);
    params.set('data_fim', dataFim);
  }
  const { data } = await apiClient.get<{ results?: LancamentoFinanceiro[] } | LancamentoFinanceiro[]>(
    `crm-vendas/financeiro-lancamentos/?${params}`,
  );
  return Array.isArray(data) ? data : data.results ?? [];
}

export function useCrmFinanceiroPage() {
  const toast = useToast();
  const [resumo, setResumo] = useState<ResumoFinanceiro | null>(null);
  const [lancamentosDespesa, setLancamentosDespesa] = useState<LancamentoFinanceiro[]>([]);
  const [lancamentosReceita, setLancamentosReceita] = useState<LancamentoFinanceiro[]>([]);
  const [grupos, setGrupos] = useState<GrupoFinanceiro[]>([]);
  const [vendedores, setVendedores] = useState<VendedorOption[]>([]);
  const [vendedorFiltro, setVendedorFiltro] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [modalTipo, setModalTipo] = useState<TipoFinanceiro>('receita');
  const [editing, setEditing] = useState<LancamentoFinanceiro | null>(null);
  const [showGrupoModal, setShowGrupoModal] = useState(false);
  const [editingGrupo, setEditingGrupo] = useState<GrupoFinanceiro | null>(null);
  const [showGrupos, setShowGrupos] = useState(false);
  const [periodoRelatorio, setPeriodoRelatorio] = useState('mes_atual');
  const [dataInicioRel, setDataInicioRel] = useState('');
  const [dataFimRel, setDataFimRel] = useState('');
  const [grupoFiltroRelatorio, setGrupoFiltroRelatorio] = useState('');
  const [gerandoPdf, setGerandoPdf] = useState(false);
  const [sincronizando, setSincronizando] = useState(false);

  const isAdmin = !authService.isVendedor();

  const loadResumo = useCallback(async () => {
    const params = new URLSearchParams({ periodo: periodoRelatorio });
    if (vendedorFiltro) params.set('vendedor_id', vendedorFiltro);
    if (periodoRelatorio === 'personalizado' && dataInicioRel && dataFimRel) {
      params.set('data_inicio', dataInicioRel);
      params.set('data_fim', dataFimRel);
    }
    const { data } = await apiClient.get<ResumoFinanceiro>(
      `crm-vendas/financeiro/resumo/?${params}`,
    );
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

  const abrirNovo = async (tipo: TipoFinanceiro) => {
    setModalTipo(tipo);
    setEditing(null);
    try {
      await loadGrupos();
    } catch {
      /* mantém lista em cache */
    }
    setShowModal(true);
  };

  const editar = (item: LancamentoFinanceiro) => {
    setModalTipo(item.tipo);
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
    } catch (err) {
      toast.error(getCrmApiErrorDetail(err, 'Não foi possível salvar o lançamento.'));
      throw err;
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
      if (item.origem === 'recorrencia') {
        toast.warning('Lançamentos gerados por recorrência não podem ser excluídos.');
      } else {
        toast.warning('Lançamentos de comissão automática não podem ser excluídos.');
      }
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
      toast.error('Não foi possível excluir. O grupo pode estar em uso.');
    }
  };

  const gerarRelatorioPdf = async (grupoIdOverride?: number) => {
    if (periodoRelatorio === 'personalizado' && (!dataInicioRel || !dataFimRel)) {
      toast.warning('Informe data início e fim para o período personalizado.');
      return;
    }
    setGerandoPdf(true);
    try {
      const grupoId =
        grupoIdOverride ??
        (grupoFiltroRelatorio ? Number(grupoFiltroRelatorio) : null);
      const payload: Record<string, unknown> = {
        periodo: periodoRelatorio,
        vendedor_id: vendedorFiltro ? Number(vendedorFiltro) : null,
      };
      if (grupoId) payload.grupo_id = grupoId;
      if (periodoRelatorio === 'personalizado') {
        payload.data_inicio = dataInicioRel;
        payload.data_fim = dataFimRel;
      }
      const res = await apiClient.post('crm-vendas/financeiro/relatorio/', payload, {
        responseType: 'blob',
      });
      const grupoSlug = grupoId
        ? grupos.find((g) => g.id === grupoId)?.nome.replace(/\s+/g, '_').toLowerCase() ?? `grupo_${grupoId}`
        : 'geral';
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.download = `financeiro_crm_${periodoRelatorio}_${grupoSlug}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch {
      toast.error('Erro ao gerar relatório PDF.');
    } finally {
      setGerandoPdf(false);
    }
  };

  const sincronizarComissoes = async () => {
    if (!confirm('Importar comissões das oportunidades já ganhas para o financeiro?')) return;
    setSincronizando(true);
    try {
      const { data } = await apiClient.post<{
        criadas: number;
        atualizadas: number;
        ignoradas: number;
        oportunidades_analisadas: number;
      }>('crm-vendas/financeiro/sync-comissoes/', {});
      toast.success(
        `Sincronização concluída. Analisadas: ${data.oportunidades_analisadas}, ` +
          `criadas: ${data.criadas}, atualizadas: ${data.atualizadas}, ignoradas: ${data.ignoradas}`,
      );
      await loadAll();
    } catch {
      toast.error('Erro ao sincronizar comissões.');
    } finally {
      setSincronizando(false);
    }
  };

  return {
    resumo,
    lancamentosDespesa,
    lancamentosReceita,
    grupos,
    vendedores,
    vendedorFiltro,
    setVendedorFiltro,
    loading,
    saving,
    isAdmin,
    showModal,
    setShowModal,
    modalTipo,
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
    showGrupos,
    setShowGrupos,
    loadAll,
    loadGrupos,
    periodoRelatorio,
    setPeriodoRelatorio,
    dataInicioRel,
    setDataInicioRel,
    dataFimRel,
    setDataFimRel,
    grupoFiltroRelatorio,
    setGrupoFiltroRelatorio,
    gerandoPdf,
    gerarRelatorioPdf,
    sincronizando,
    sincronizarComissoes,
  };
}
