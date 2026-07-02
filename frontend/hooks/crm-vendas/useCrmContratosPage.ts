'use client';

import { useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { getCrmApiErrorDetail } from '@/lib/crm-utils';
import { useToast } from '@/components/ui/Toast';
import { usePaginatedList } from '@/hooks/usePaginatedList';
import { useWhatsappEnvioFlags } from '@/hooks/useWhatsappEnvioFlags';
import { useCrmDocumentoActions } from '@/hooks/useCrmDocumentoActions';
import { CRM_CONTRATO_STATUS_LABEL as STATUS_LABEL } from '@/lib/crm-constants';

export interface CrmContrato {
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
  data_assinatura: string | null;
  created_at: string;
}

export type CrmContratoModalType = 'view' | 'delete' | 'cancelar' | null;

export function useCrmContratosPage(slug: string) {
  const toast = useToast();
  const router = useRouter();
  const [filtroStatus, setFiltroStatus] = useState('');

  const {
    items: contratos,
    page,
    setPage,
    totalCount,
    totalPages,
    pageSize,
    loading,
    error,
    reload: loadContratos,
  } = usePaginatedList<CrmContrato>('/crm-vendas/contratos/', {
    params: { status: filtroStatus || undefined },
    errorFallback: 'Erro ao carregar contratos.',
  });

  const contratosFiltrados = useMemo(
    () => contratos.filter((c) => !filtroStatus || c.status === filtroStatus),
    [contratos, filtroStatus],
  );

  const [modalType, setModalType] = useState<CrmContratoModalType>(null);
  const [selected, setSelected] = useState<CrmContrato | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [alterandoStatus, setAlterandoStatus] = useState<number | null>(null);
  const [menuAberto, setMenuAberto] = useState<number | null>(null);
  const [confirmAction, setConfirmAction] = useState<{
    type: 'marcar_assinado';
    id: number;
    titulo: string;
  } | null>(null);
  const [confirmando, setConfirmando] = useState(false);

  const { enviandoId, handleEnviarCliente, handleDownloadPdf, handleDownloadDocx } =
    useCrmDocumentoActions('contratos', loadContratos);

  const { contrato: contratoWhatsappHabilitado } = useWhatsappEnvioFlags();

  const filtroOpcoes = useMemo(
    () =>
      ['', 'rascunho', 'enviado', 'assinado', 'cancelado'].map((s) => ({
        value: s,
        label:
          s === ''
            ? `Todos (${contratos.length})`
            : `${STATUS_LABEL[s] || s} (${contratos.filter((c) => c.status === s).length})`,
      })),
    [contratos],
  );

  const openModal = (type: CrmContratoModalType, item?: CrmContrato) => {
    setModalType(type);
    setSelected(item || null);
  };

  const closeModal = () => {
    setModalType(null);
    setSelected(null);
  };

  const requestMarcarComoAssinado = (contrato: CrmContrato) => {
    setConfirmAction({
      type: 'marcar_assinado',
      id: contrato.id,
      titulo: contrato.titulo || contrato.numero || 'este contrato',
    });
  };

  const closeConfirm = () => {
    if (confirmando) return;
    setConfirmAction(null);
  };

  const executeConfirm = async () => {
    if (!confirmAction) return;
    setConfirmando(true);
    const { id } = confirmAction;
    try {
      setAlterandoStatus(id);
      await apiClient.patch(`/crm-vendas/contratos/${id}/`, {
        status_assinatura: 'concluido',
        status: 'assinado',
      });
      await loadContratos(true);
      toast.success('Contrato marcado como assinado com sucesso!');
      setConfirmAction(null);
    } catch (err: unknown) {
      toast.error(getCrmApiErrorDetail(err, 'Erro ao atualizar status.'));
    } finally {
      setAlterandoStatus(null);
      setConfirmando(false);
    }
  };

  const handleMarcarComoAssinado = (contratoId: number) => {
    const contrato = contratos.find((c) => c.id === contratoId);
    if (contrato) requestMarcarComoAssinado(contrato);
  };

  const handleCancelarContrato = async (motivo: string) => {
    if (!selected) return;
    try {
      setAlterandoStatus(selected.id);
      await apiClient.post(`/crm-vendas/contratos/${selected.id}/cancelar/`, { motivo });
      await loadContratos(true);
      closeModal();
      toast.success('Contrato cancelado.');
    } catch (err: unknown) {
      throw new Error(getCrmApiErrorDetail(err, 'Erro ao cancelar contrato.'));
    } finally {
      setAlterandoStatus(null);
    }
  };

  const handleDelete = async () => {
    if (!selected) return;
    try {
      setSubmitting(true);
      await apiClient.delete(`/crm-vendas/contratos/${selected.id}/`);
      await loadContratos(true);
      closeModal();
      toast.success('Contrato excluído.');
    } catch (err: unknown) {
      toast.error(getCrmApiErrorDetail(err, 'Erro ao excluir.'));
    } finally {
      setSubmitting(false);
    }
  };

  const irParaNovoContrato = () => {
    router.push(`/loja/${slug}/crm-vendas/contratos/nova`);
  };

  const irParaEditarContrato = (id: number) => {
    router.push(`/loja/${slug}/crm-vendas/contratos/${id}/editar`);
  };

  return {
    slug,
    contratos,
    contratosFiltrados,
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
    modalType,
    selected,
    submitting,
    alterandoStatus,
    menuAberto,
    setMenuAberto,
    enviandoId,
    contratoWhatsappHabilitado,
    handleEnviarCliente,
    handleDownloadPdf,
    handleDownloadDocx,
    openModal,
    closeModal,
    handleMarcarComoAssinado,
    handleCancelarContrato,
    handleDelete,
    confirmAction,
    confirmando,
    closeConfirm,
    executeConfirm,
    irParaNovoContrato,
    irParaEditarContrato,
  };
}
