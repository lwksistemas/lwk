'use client';

import { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { getCrmApiErrorDetail } from '@/lib/crm-utils';
import { useToast } from '@/components/ui/Toast';
import { usePaginatedList } from '@/hooks/usePaginatedList';
import { useWhatsappEnvioFlags } from '@/hooks/useWhatsappEnvioFlags';
import { useCrmDocumentoActions } from '@/hooks/useCrmDocumentoActions';
import { CRM_PROPOSTA_STATUS_LABEL as STATUS_LABEL } from '@/lib/crm-constants';
import { propostaOcultaColunaAssinatura } from '@/lib/crm-propostas-helpers';

export type { PropostasConfirmAction } from '@/lib/crm-propostas-helpers';
export { propostaOcultaColunaAssinatura } from '@/lib/crm-propostas-helpers';

export interface CrmProposta {
  id: number;
  oportunidade: number;
  oportunidade_titulo: string;
  lead_nome: string;
  lead_email?: string;
  lead_telefone?: string;
  vendedor_nome?: string;
  vendedor_email?: string;
  vendedor_telefone?: string;
  numero: string;
  titulo: string;
  conteudo: string;
  valor_total: string | null;
  desconto_tipo: 'percentual' | 'valor';
  desconto_valor: string;
  valor_com_desconto: string | null;
  status: string;
  status_assinatura?: string;
  motivo_cancelamento?: string;
  data_envio: string | null;
  data_resposta: string | null;
  created_at: string;
}

export type CrmPropostaModalType = 'view' | 'delete' | 'cancelar' | null;

export function useCrmPropostasPage(slug: string) {
  const toast = useToast();
  const router = useRouter();
  const [filtroStatus, setFiltroStatus] = useState('');
  const statusParam = filtroStatus || undefined;

  const {
    items: propostas,
    page,
    setPage,
    totalCount,
    totalPages,
    pageSize,
    loading,
    error,
    reload: loadPropostas,
  } = usePaginatedList<CrmProposta>('/crm-vendas/propostas/', {
    params: { status: statusParam },
    errorFallback: 'Erro ao carregar propostas.',
  });

  const exibirColunaAssinatura = propostas.some((p) => !propostaOcultaColunaAssinatura(p));

  const [modalType, setModalType] = useState<CrmPropostaModalType>(null);
  const [selected, setSelected] = useState<CrmProposta | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [alterandoStatus, setAlterandoStatus] = useState<number | null>(null);
  const [menuAberto, setMenuAberto] = useState<number | null>(null);
  const [confirmAction, setConfirmAction] = useState<
    | { type: 'marcar_assinado'; id: number; titulo: string }
    | { type: 'confirmar_pedido'; id: number; titulo: string }
    | null
  >(null);
  const [confirmando, setConfirmando] = useState(false);

  const { enviandoId, handleEnviarCliente, handleDownloadPdf, handleDownloadDocx } =
    useCrmDocumentoActions('propostas', loadPropostas);

  const { proposta: propostaWhatsappHabilitada } = useWhatsappEnvioFlags();

  const requestMarcarComoAssinado = (proposta: CrmProposta) => {
    setConfirmAction({
      type: 'marcar_assinado',
      id: proposta.id,
      titulo: proposta.titulo || proposta.numero || 'esta proposta',
    });
  };

  const requestConfirmarPedido = (proposta: CrmProposta) => {
    setConfirmAction({
      type: 'confirmar_pedido',
      id: proposta.id,
      titulo: proposta.titulo || proposta.numero || 'esta proposta',
    });
  };

  const closeConfirm = () => {
    if (confirmando) return;
    setConfirmAction(null);
  };

  const executeConfirm = async () => {
    if (!confirmAction) return;
    setConfirmando(true);
    const { type, id } = confirmAction;
    try {
      if (type === 'marcar_assinado') {
        setAlterandoStatus(id);
        await apiClient.patch(`/crm-vendas/propostas/${id}/`, {
          status_assinatura: 'concluido',
          status: 'aceita',
        });
        await loadPropostas(true);
        toast.success('Proposta marcada como assinada com sucesso!');
      } else {
        setAlterandoStatus(id);
        await apiClient.post(`/crm-vendas/propostas/${id}/confirmar_pedido/`);
        await loadPropostas(true);
        toast.success('Proposta confirmada como pedido.');
      }
      setConfirmAction(null);
    } catch (err: unknown) {
      const fallback =
        type === 'marcar_assinado' ? 'Erro ao atualizar status.' : 'Erro ao confirmar pedido.';
      toast.error(getCrmApiErrorDetail(err, fallback));
    } finally {
      setAlterandoStatus(null);
      setConfirmando(false);
    }
  };

  const handleMarcarComoAssinado = (propostaId: number) => {
    const proposta = propostas.find((p) => p.id === propostaId);
    if (proposta) requestMarcarComoAssinado(proposta);
  };

  const handleConfirmarPedido = (propostaId: number) => {
    const proposta = propostas.find((p) => p.id === propostaId);
    if (proposta) requestConfirmarPedido(proposta);
  };

  const handleCancelarProposta = async (motivo: string) => {
    if (!selected) return;
    try {
      setAlterandoStatus(selected.id);
      await apiClient.post(`/crm-vendas/propostas/${selected.id}/cancelar/`, { motivo });
      await loadPropostas(true);
      closeModal();
      toast.success('Proposta cancelada.');
    } catch (err: unknown) {
      throw new Error(getCrmApiErrorDetail(err, 'Erro ao cancelar proposta.'));
    } finally {
      setAlterandoStatus(null);
    }
  };

  const openModal = (type: CrmPropostaModalType, item?: CrmProposta) => {
    setModalType(type);
    setSelected(item || null);
  };

  const closeModal = () => {
    setModalType(null);
    setSelected(null);
  };

  const irParaEditarProposta = useCallback(
    (propostaId: number) => {
      router.push(`/loja/${slug}/crm-vendas/propostas/${propostaId}/editar`);
    },
    [router, slug],
  );

  const handleDelete = async () => {
    if (!selected) return;
    try {
      setSubmitting(true);
      await apiClient.delete(`/crm-vendas/propostas/${selected.id}/`);
      await loadPropostas(true);
      closeModal();
      toast.success('Proposta excluída.');
    } catch (err: unknown) {
      toast.error(getCrmApiErrorDetail(err, 'Erro ao excluir.'));
    } finally {
      setSubmitting(false);
    }
  };

  const filtroOpcoes = ['', 'rascunho', 'enviada', 'pedido', 'cancelada'].map((s) => ({
    value: s,
    label:
      s === ''
        ? `Todos (${filtroStatus === '' ? totalCount : propostas.length})`
        : `${STATUS_LABEL[s] || s} (${
            filtroStatus === s
              ? totalCount
              : propostas.filter(
                  (p) =>
                    p.status === s ||
                    (s === 'pedido' && (p.status === 'aceita' || p.status === 'pedido')),
                ).length
          })`,
  }));

  return {
    slug,
    propostas,
    page,
    setPage,
    totalCount,
    totalPages,
    pageSize,
    loading,
    error,
    filtroStatus,
    setFiltroStatus,
    filtroOpcoes,
    exibirColunaAssinatura,
    propostaWhatsappHabilitada,
    enviandoId,
    handleEnviarCliente,
    handleDownloadPdf,
    handleDownloadDocx,
    modalType,
    selected,
    submitting,
    alterandoStatus,
    menuAberto,
    setMenuAberto,
    openModal,
    closeModal,
    irParaEditarProposta,
    handleDelete,
    handleMarcarComoAssinado,
    handleConfirmarPedido,
    handleCancelarProposta,
    confirmAction,
    confirmando,
    closeConfirm,
    executeConfirm,
  };
}
