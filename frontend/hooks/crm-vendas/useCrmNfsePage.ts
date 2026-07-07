'use client';

import { useCallback, useEffect, useState, type MouseEvent } from 'react';
import apiClient from '@/lib/api-client';
import { fetchCrmPaginatedPage, getCrmApiErrorDetail } from '@/lib/crm-utils';
import { usePaginatedList, DEFAULT_PAGE_SIZE } from '@/hooks/usePaginatedList';
import { useNfseQueuedPolling } from '@/hooks/useNfseQueuedPolling';
import { useWhatsappEnvioFlags } from '@/hooks/useWhatsappEnvioFlags';
import { useCRMConfig } from '@/contexts/CRMConfigContext';
import { useToast } from '@/components/ui/Toast';
import { telefoneInternacionalBr } from '@/lib/format-br';
import {
  nfseIdentificador,
  nfseSyncEndpoint,
  nfUsaIssnet,
  openBlobInNewTab,
  openPdfFromJsonUrl,
  type NfseCancelamentoEscolha,
  type NfseEmissaoResult,
} from '@/lib/nfse-helpers';
import type { NFSe } from '@/app/(dashboard)/loja/[slug]/crm-vendas/nfse/types';

export type NfseSyncMessage = { type: 'ok' | 'err' | 'info'; text: string } | null;

export type NfseConfirmAction =
  | { type: 'excluir'; nf: NFSe }
  | { type: 'reenviar_email'; nf: NFSe };

const CONFIRM_COPY: Record<
  NfseConfirmAction['type'],
  {
    title: string;
    message: (nf: NFSe) => string;
    confirmLabel: string;
    variant: 'danger' | 'primary';
  }
> = {
  excluir: {
    title: 'Excluir NFS-e',
    message: (nf) => `Tem certeza que deseja excluir a NFS-e ${nfseIdentificador(nf)}?`,
    confirmLabel: 'Excluir',
    variant: 'danger',
  },
  reenviar_email: {
    title: 'Reenviar email',
    message: (nf) => `Reenviar nota fiscal por email para ${nf.tomador_email}?`,
    confirmLabel: 'Reenviar',
    variant: 'primary',
  },
};

export function useCrmNfsePage() {
  const toast = useToast();
  const { config } = useCRMConfig();
  const lojaProvedor = config?.provedor_nf;
  const { whatsappAtivo } = useWhatsappEnvioFlags();

  const [showModal, setShowModal] = useState(false);
  const [showRecuperarModal, setShowRecuperarModal] = useState(false);
  const [filtroStatus, setFiltroStatus] = useState('');
  const [busca, setBusca] = useState('');
  const [buscaDebounced, setBuscaDebounced] = useState('');
  const [syncingId, setSyncingId] = useState<number | null>(null);
  const [syncMsg, setSyncMsg] = useState<NfseSyncMessage>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [nfWhatsapp, setNfWhatsapp] = useState<NFSe | null>(null);
  const [emissaoPolling, setEmissaoPolling] = useState<{ active: boolean; countBefore: number }>({
    active: false,
    countBefore: 0,
  });
  const [confirmAction, setConfirmAction] = useState<NfseConfirmAction | null>(null);
  const [confirmando, setConfirmando] = useState(false);
  const [nfCancelamento, setNfCancelamento] = useState<NFSe | null>(null);
  const [cancelandoNFSe, setCancelandoNFSe] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setBuscaDebounced(busca.trim()), 400);
    return () => clearTimeout(timer);
  }, [busca]);

  const {
    items: nfses,
    page,
    setPage,
    totalCount,
    totalPages,
    pageSize,
    loading,
    reload: carregarNFSes,
  } = usePaginatedList<NFSe>('/nfse/', {
    params: {
      status: filtroStatus || undefined,
      busca: buscaDebounced || undefined,
    },
  });

  const handlePollingTick = useCallback(() => {
    void carregarNFSes(true);
  }, [carregarNFSes]);

  const handlePollingFound = useCallback(async () => {
    setEmissaoPolling({ active: false, countBefore: 0 });
    await carregarNFSes(true);
    try {
      const data = await fetchCrmPaginatedPage<NFSe>('/nfse/', 1, DEFAULT_PAGE_SIZE, {});
      const newest = data.results[0];
      if (newest?.status === 'erro' && newest.erro) {
        setSyncMsg({ type: 'err', text: `Falha na emissão: ${newest.erro}` });
        return;
      }
      if (newest?.status === 'emitida' && newest.numero_nf) {
        setSyncMsg({ type: 'ok', text: `NFS-e ${newest.numero_nf} emitida com sucesso.` });
        return;
      }
    } catch {
      // mantém mensagem genérica abaixo
    }
    setSyncMsg({ type: 'ok', text: 'Emissão processada. Verifique o status da nota na lista.' });
  }, [carregarNFSes]);

  const handlePollingTimeout = useCallback(() => {
    setEmissaoPolling({ active: false, countBefore: 0 });
    setSyncMsg({
      type: 'ok',
      text: 'Lista atualizada. Se a nota não apareceu, aguarde mais um momento ou atualize a página.',
    });
  }, []);

  useNfseQueuedPolling({
    active: emissaoPolling.active,
    countBefore: emissaoPolling.countBefore,
    queryParams: {},
    onTick: handlePollingTick,
    onFound: () => {
      void handlePollingFound();
    },
    onTimeout: handlePollingTimeout,
  });

  const sincronizarStatus = async (e: MouseEvent, nf: NFSe) => {
    e.preventDefault();
    e.stopPropagation();
    const endpoint = nfseSyncEndpoint(nf, lojaProvedor);
    if (!endpoint) {
      setSyncMsg({ type: 'err', text: 'Sincronização não disponível para este provedor.' });
      return;
    }
    setSyncMsg(null);
    setSyncingId(nf.id);
    try {
      const res = await apiClient.post(`/nfse/${nf.id}/${endpoint}/`);
      const msg =
        (res.data as { message?: string })?.message ||
        (endpoint === 'sincronizar-issnet'
          ? 'Status atualizado conforme o ISSNet.'
          : 'Status atualizado conforme o Asaas.');
      setSyncMsg({ type: 'ok', text: msg });
      await carregarNFSes(true);
    } catch (err: unknown) {
      setSyncMsg({
        type: 'err',
        text: getCrmApiErrorDetail(err, 'Não foi possível sincronizar.'),
      });
    } finally {
      setSyncingId(null);
    }
  };

  const requestExcluirNFSe = (e: MouseEvent, nf: NFSe) => {
    e.preventDefault();
    e.stopPropagation();
    setConfirmAction({ type: 'excluir', nf });
  };

  const requestReenviarEmail = (e: MouseEvent, nf: NFSe) => {
    e.preventDefault();
    e.stopPropagation();
    if (!nf.tomador_email) {
      toast.warning('Esta NFS-e não possui email do tomador cadastrado.');
      return;
    }
    setConfirmAction({ type: 'reenviar_email', nf });
  };

  const executeConfirm = async () => {
    if (!confirmAction) return;
    setConfirmando(true);
    const { type, nf } = confirmAction;
    try {
      if (type === 'excluir') {
        setDeletingId(nf.id);
        await apiClient.delete(`/nfse/${nf.id}/`);
        setSyncMsg({ type: 'ok', text: 'NFS-e excluída com sucesso.' });
        await carregarNFSes(true);
      } else {
        await apiClient.post(`/nfse/${nf.id}/reenviar_email/`);
        setSyncMsg({ type: 'ok', text: `Email reenviado para ${nf.tomador_email}` });
      }
      setConfirmAction(null);
    } catch (err: unknown) {
      const fallback = type === 'excluir' ? 'Não foi possível excluir.' : 'Erro ao reenviar email.';
      setSyncMsg({ type: 'err', text: getCrmApiErrorDetail(err, fallback) });
    } finally {
      setConfirmando(false);
      setDeletingId(null);
    }
  };

  const baixarPdfNFSe = async (e: MouseEvent, nf: NFSe) => {
    e.preventDefault();
    e.stopPropagation();
    try {
      const res = await apiClient.get(`/nfse/${nf.id}/download_pdf/`);

      if (openPdfFromJsonUrl(res.data)) {
        if (nfUsaIssnet(nf, lojaProvedor)) {
          try {
            await apiClient.post(`/nfse/${nf.id}/sincronizar-issnet/`);
            await carregarNFSes(true);
          } catch {
            // silencioso: download do PDF não deve falhar por causa da sincronização
          }
        }
        return;
      }

      const resBlob = await apiClient.get(`/nfse/${nf.id}/download_pdf/`, { responseType: 'blob' });
      const blob =
        resBlob.data instanceof Blob ? resBlob.data : new Blob([resBlob.data], { type: 'application/pdf' });
      openBlobInNewTab(blob);
    } catch {
      toast.error('PDF não disponível.');
    }
  };

  const requestCancelarNFSe = (nf: NFSe) => {
    setNfCancelamento(nf);
  };

  const confirmarCancelamentoNFSe = async (escolha: NfseCancelamentoEscolha) => {
    if (!nfCancelamento) return;
    setCancelandoNFSe(true);
    try {
      await apiClient.post(`/nfse/${nfCancelamento.id}/cancelar/`, {
        motivo: escolha.motivo,
        codigo_cancelamento: escolha.codigo,
      });
      toast.success('NFS-e cancelada no ISSNet com sucesso.');
      setNfCancelamento(null);
      await carregarNFSes(true);
    } catch (err: unknown) {
      toast.error(getCrmApiErrorDetail(err, 'Erro ao cancelar NFS-e'));
    } finally {
      setCancelandoNFSe(false);
    }
  };

  const abrirModalWhatsapp = (e: MouseEvent, nf: NFSe) => {
    e.preventDefault();
    e.stopPropagation();
    setNfWhatsapp(nf);
  };

  const enviarWhatsappNFSe = async (telefone: string) => {
    if (!nfWhatsapp) return;
    const res = await apiClient.post<{ message?: string }>(`/nfse/${nfWhatsapp.id}/enviar_whatsapp/`, {
      telefone: telefoneInternacionalBr(telefone),
    });
    setSyncMsg({ type: 'ok', text: res.data.message || 'NFS-e enviada por WhatsApp.' });
    setNfWhatsapp(null);
  };

  const handleEmitirSuccess = (result: NfseEmissaoResult) => {
    setShowModal(false);
    const countBefore = totalCount;
    void carregarNFSes(true);
    if (result.queued) {
      setEmissaoPolling({ active: true, countBefore });
      setSyncMsg({ type: 'info', text: result.message });
    } else {
      setSyncMsg({ type: 'ok', text: result.message });
    }
  };

  const handleRecuperarSuccess = (message: string) => {
    setShowRecuperarModal(false);
    setSyncMsg({ type: 'ok', text: message });
    void carregarNFSes(true);
  };

  const confirmCopy = confirmAction ? CONFIRM_COPY[confirmAction.type] : null;

  return {
    lojaProvedor,
    whatsappAtivo,
    showModal,
    setShowModal,
    showRecuperarModal,
    setShowRecuperarModal,
    filtroStatus,
    setFiltroStatus,
    busca,
    setBusca,
    syncMsg,
    syncingId,
    deletingId,
    nfWhatsapp,
    setNfWhatsapp,
    nfses,
    page,
    setPage,
    totalCount,
    totalPages,
    pageSize,
    loading,
    confirmAction,
    setConfirmAction,
    confirmando,
    confirmCopy,
    executeConfirm,
    sincronizarStatus,
    requestExcluirNFSe,
    baixarPdfNFSe,
    requestCancelarNFSe,
    nfCancelamento,
    setNfCancelamento,
    confirmarCancelamentoNFSe,
    cancelandoNFSe,
    abrirModalWhatsapp,
    enviarWhatsappNFSe,
    requestReenviarEmail,
    handleEmitirSuccess,
    handleRecuperarSuccess,
  };
}
