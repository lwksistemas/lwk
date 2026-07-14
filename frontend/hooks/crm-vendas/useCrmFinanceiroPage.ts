'use client';

import { useState } from 'react';
import apiClient from '@/lib/api-client';
import { getCrmApiErrorDetail } from '@/lib/crm-utils';
import { useToast } from '@/components/ui/Toast';
import { useCrmFinanceiroData } from '@/hooks/crm-vendas/useCrmFinanceiroData';
import type {
  FinanceiroConfirmAction,
  GrupoFinanceiro,
  LancamentoFinanceiro,
  TipoFinanceiro,
} from '@/lib/crm-financeiro-types';

export type { TipoFinanceiro, GrupoFinanceiro, LancamentoFinanceiro, ResumoFinanceiro, VendedorOption } from '@/lib/crm-financeiro-types';

export function useCrmFinanceiroPage() {
  const toast = useToast();
  const data = useCrmFinanceiroData();

  const [saving, setSaving] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [modalTipo, setModalTipo] = useState<TipoFinanceiro>('receita');
  const [editing, setEditing] = useState<LancamentoFinanceiro | null>(null);
  const [showGrupoModal, setShowGrupoModal] = useState(false);
  const [editingGrupo, setEditingGrupo] = useState<GrupoFinanceiro | null>(null);
  const [showGrupos, setShowGrupos] = useState(false);
  const [gerandoPdf, setGerandoPdf] = useState(false);
  const [sincronizando, setSincronizando] = useState(false);
  const [confirmAction, setConfirmAction] = useState<FinanceiroConfirmAction>(null);
  const [confirmando, setConfirmando] = useState(false);

  const abrirNovo = async (tipo: TipoFinanceiro) => {
    setModalTipo(tipo);
    setEditing(null);
    try {
      await data.loadGrupos();
    } catch {
      /* cache */
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
      await data.loadAll();
    } catch (err) {
      toast.error(getCrmApiErrorDetail(err, 'Não foi possível salvar o lançamento.'));
      throw err;
    } finally {
      setSaving(false);
    }
  };

  const marcarPago = async (id: number) => {
    await apiClient.post(`crm-vendas/financeiro-lancamentos/${id}/marcar_pago/`, {});
    await data.loadAll();
  };

  const marcarPagoEmLote = async (ids: number[]) => {
    try {
      const { data: batch } = await apiClient.post<{
        atualizados: number;
        ignorados: number;
        solicitados: number;
      }>('crm-vendas/financeiro-lancamentos/acoes-lote/', {
        ids,
        acao: 'marcar_pago',
      });
      if (batch.atualizados === 0) {
        toast.warning('Nenhuma comissão foi marcada como recebida.');
      } else if (batch.ignorados > 0) {
        toast.warning(`${batch.atualizados} recebida(s), ${batch.ignorados} ignorada(s).`);
      } else {
        toast.success(`${batch.atualizados} comissão(ões) marcada(s) como recebida(s).`);
      }
      await data.loadAll();
    } catch (err) {
      toast.error(getCrmApiErrorDetail(err, 'Não foi possível marcar as comissões como recebidas.'));
      throw err;
    }
  };

  const cancelarComissaoEmLote = async (ids: number[]) => {
    try {
      const { data: batch } = await apiClient.post<{
        atualizados: number;
        ignorados: number;
      }>('crm-vendas/financeiro-lancamentos/acoes-lote/', {
        ids,
        acao: 'cancelar',
      });
      if (batch.atualizados === 0) {
        toast.warning('Nenhuma comissão foi cancelada.');
      } else if (batch.ignorados > 0) {
        toast.warning(`${batch.atualizados} cancelada(s), ${batch.ignorados} ignorada(s).`);
      } else {
        toast.success(`${batch.atualizados} comissão(ões) cancelada(s).`);
      }
      await data.loadAll();
    } catch (err) {
      toast.error(getCrmApiErrorDetail(err, 'Não foi possível cancelar as comissões.'));
      throw err;
    }
  };

  const requestReceberComissao = (item: LancamentoFinanceiro) => {
    const ids = item.ids_agregados ?? [];
    if (!ids.length) return;
    setConfirmAction({ type: 'receber_comissoes', item, ids });
  };

  const requestCancelarComissao = (item: LancamentoFinanceiro) => {
    const ids = item.ids_agregados ?? [];
    if (!ids.length) return;
    setConfirmAction({ type: 'cancelar_comissoes', item, ids });
  };

  const requestRemoverLancamento = (item: LancamentoFinanceiro) => {
    if (!item.editavel) {
      if (item.origem === 'recorrencia') {
        toast.warning('Lançamentos gerados por recorrência não podem ser excluídos.');
      } else {
        toast.warning('Lançamentos de comissão automática não podem ser excluídos.');
      }
      return;
    }
    setConfirmAction({ type: 'excluir_lancamento', item });
  };

  const executeRemoverLancamento = async (item: LancamentoFinanceiro) => {
    await apiClient.delete(`crm-vendas/financeiro-lancamentos/${item.id}/`);
    await data.loadAll();
  };

  const requestRemoverGrupo = (grupo: GrupoFinanceiro) => {
    setConfirmAction({ type: 'excluir_grupo', grupo });
  };

  const executeRemoverGrupo = async (grupo: GrupoFinanceiro) => {
    try {
      await apiClient.delete(`crm-vendas/financeiro-grupos/${grupo.id}/`);
      toast.success(`Grupo "${grupo.nome}" excluído.`);
      await data.loadAll();
    } catch (err: unknown) {
      toast.error(getCrmApiErrorDetail(err, 'Não foi possível excluir. O grupo pode estar em uso.'));
      throw new Error('excluir_grupo');
    }
  };

  const executeSincronizarComissoes = async () => {
    setSincronizando(true);
    try {
      const { data: syncData } = await apiClient.post<{
        criadas: number;
        atualizadas: number;
        ignoradas: number;
        oportunidades_analisadas: number;
      }>('crm-vendas/financeiro/sync-comissoes/', {});
      toast.success(
        `Sincronização concluída. Analisadas: ${syncData.oportunidades_analisadas}, ` +
          `criadas: ${syncData.criadas}, atualizadas: ${syncData.atualizadas}, ignoradas: ${syncData.ignoradas}`,
      );
      await data.loadAll();
    } catch (err: unknown) {
      toast.error(getCrmApiErrorDetail(err, 'Erro ao sincronizar comissões.'));
      throw new Error('sync_comissoes');
    } finally {
      setSincronizando(false);
    }
  };

  const closeConfirm = () => {
    if (confirmando || sincronizando) return;
    setConfirmAction(null);
  };

  const executeConfirm = async () => {
    if (!confirmAction) return;
    setConfirmando(true);
    try {
      if (confirmAction.type === 'excluir_lancamento') {
        await executeRemoverLancamento(confirmAction.item);
      } else if (confirmAction.type === 'excluir_grupo') {
        await executeRemoverGrupo(confirmAction.grupo);
      } else if (confirmAction.type === 'receber_comissoes') {
        await marcarPagoEmLote(confirmAction.ids);
      } else if (confirmAction.type === 'cancelar_comissoes') {
        await cancelarComissaoEmLote(confirmAction.ids);
      } else {
        await executeSincronizarComissoes();
      }
      setConfirmAction(null);
    } catch {
      /* toast já exibido */
    } finally {
      setConfirmando(false);
    }
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
      await data.loadAll();
    } finally {
      setSaving(false);
    }
  };

  const gerarRelatorioPdf = async (grupoIdOverride?: number) => {
    if (data.periodoRelatorio === 'personalizado' && (!data.dataInicioRel || !data.dataFimRel)) {
      toast.warning('Informe data início e fim para o período personalizado.');
      return;
    }
    setGerandoPdf(true);
    try {
      const grupoId =
        grupoIdOverride ?? (data.grupoFiltroRelatorio ? Number(data.grupoFiltroRelatorio) : null);
      const payload: Record<string, unknown> = {
        periodo: data.periodoRelatorio,
        vendedor_id: data.vendedorFiltro ? Number(data.vendedorFiltro) : null,
      };
      if (grupoId) payload.grupo_id = grupoId;
      if (data.periodoRelatorio === 'personalizado') {
        payload.data_inicio = data.dataInicioRel;
        payload.data_fim = data.dataFimRel;
      }
      const res = await apiClient.post('crm-vendas/financeiro/relatorio/', payload, {
        responseType: 'blob',
      });
      const grupoSlug = grupoId
        ? data.grupos.find((g) => g.id === grupoId)?.nome.replace(/\s+/g, '_').toLowerCase() ?? `grupo_${grupoId}`
        : 'geral';
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.download = `financeiro_crm_${data.periodoRelatorio}_${grupoSlug}.pdf`;
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

  return {
    ...data,
    saving,
    showModal,
    setShowModal,
    modalTipo,
    editing,
    abrirNovo,
    editar,
    salvarLancamento,
    marcarPago,
    receberComissao: requestReceberComissao,
    cancelarComissao: requestCancelarComissao,
    removerLancamento: requestRemoverLancamento,
    showGrupoModal,
    setShowGrupoModal,
    editingGrupo,
    setEditingGrupo,
    salvarGrupo,
    removerGrupo: requestRemoverGrupo,
    showGrupos,
    setShowGrupos,
    gerandoPdf,
    gerarRelatorioPdf,
    sincronizando,
    sincronizarComissoes: () => setConfirmAction({ type: 'sync_comissoes' }),
    confirmAction,
    confirmando,
    closeConfirm,
    executeConfirm,
  };
}
