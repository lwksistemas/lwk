'use client';

import { useCallback, useEffect, useState, type MouseEvent } from 'react';
import apiClient from '@/lib/api-client';
import { getCrmApiErrorDetail } from '@/lib/crm-utils';
import { usePaginatedList } from '@/hooks/usePaginatedList';
import { useNfseQueuedPolling } from '@/hooks/useNfseQueuedPolling';
import { useWhatsappEnvioFlags } from '@/hooks/useWhatsappEnvioFlags';
import { useToast } from '@/components/ui/Toast';
import { telefoneInternacionalBr } from '@/lib/format-br';
import {
  blobFromApiData,
  downloadBlobFile,
  mensagemEmissaoNota,
  nfseIdentificador,
  nfseSyncEndpoint,
  nfUsaIssnet,
  openPdfFromJsonUrl,
  type NfseCancelamentoEscolha,
  type NfseEmissaoResult,
} from '@/lib/nfse-helpers';
import type { NFSe } from '@/lib/nfse-loja-types';

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
    message: (nf) =>
      `Reenviar NFS-e ${nf.numero_nf || nf.numero_rps}${nf.tomador_nome ? ` ${nf.tomador_nome}` : ''} por email para ${nf.tomador_email}?`,
    confirmLabel: 'Reenviar',
    variant: 'primary',
  },
};

/** Listagem + ações de NFS-e da loja (CRM e Clínica da Beleza). */
export function useNfseLojaPage(lojaProvedor: string | undefined | null) {
  const toast = useToast();
  const _lojaProvedor = lojaProvedor ?? undefined;
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
  const [emissaoPolling, setEmissaoPolling] = useState<{
    active: boolean;
    idsAntes: number[];
    capturarBase: boolean;
  }>({
    active: false,
    idsAntes: [],
    capturarBase: false,
  });
  const [confirmAction, setConfirmAction] = useState<NfseConfirmAction | null>(null);
  const [confirmando, setConfirmando] = useState(false);
  const [nfCancelamento, setNfCancelamento] = useState<NFSe | null>(null);
  const [erroCancelamento, setErroCancelamento] = useState<string | null>(null);
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
    aplicarPagina,
  } = usePaginatedList<NFSe>('/nfse/', {
    params: {
      status: filtroStatus || undefined,
      busca: buscaDebounced || undefined,
    },
  });

  const pararEmissao = useCallback(() => {
    setEmissaoPolling({ active: false, idsAntes: [], capturarBase: false });
  }, []);

  const aoAtualizarLista = useCallback((data: { results: NFSe[]; count: number; totalPages: number }) => {
    aplicarPagina(data);
  }, [aplicarPagina]);

  const aoResolverEmissao = useCallback((nota: NFSe) => {
    pararEmissao();
    const aviso = mensagemEmissaoNota(nota);
    setSyncMsg(aviso);
  }, [pararEmissao]);

  const handlePollingTimeout = useCallback(() => {
    pararEmissao();
    setSyncMsg({
      type: 'info',
      text: 'A emissão ainda está em andamento. A lista já foi atualizada.',
    });
  }, [pararEmissao]);

  useNfseQueuedPolling<NFSe>({
    active: emissaoPolling.active,
    idsAntes: emissaoPolling.idsAntes,
    capturarBase: emissaoPolling.capturarBase,
    queryParams: {},
    onPage: aoAtualizarLista,
    onResolved: aoResolverEmissao,
    onTimeout: handlePollingTimeout,
  });

  const sincronizarStatus = async (e: MouseEvent, nf: NFSe) => {
    e.preventDefault();
    e.stopPropagation();
    const endpoint = nfseSyncEndpoint(nf, _lojaProvedor);
    if (!endpoint) {
      setSyncMsg({ type: 'err', text: 'Sincronização não disponível para este provedor.' });
      return;
    }
    setSyncMsg(null);
    setSyncingId(nf.id);
    try {
      const res = await apiClient.post(`/nfse/${nf.id}/${endpoint}/`);
      const data = res.data as { message?: string; aviso?: boolean };
      const msg =
        data?.message ||
        (endpoint === 'sincronizar-issnet'
          ? 'Status atualizado conforme o ISSNet.'
          : 'Status atualizado conforme o Asaas.');
      if (data?.aviso) {
        setSyncMsg({ type: 'info', text: msg });
        return;
      }
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
      const res = await apiClient.get(`/nfse/${nf.id}/download_pdf/`, { responseType: 'blob' });
      const contentType = String(res.headers?.['content-type'] || '');
      if (contentType.includes('application/json')) {
        const texto = await (res.data as Blob).text();
        const json = JSON.parse(texto) as { url?: string; error?: string; precisa_colar_link?: boolean };
        if (json.url && openPdfFromJsonUrl(json)) {
          if (nfUsaIssnet(nf, _lojaProvedor)) {
            try {
              await apiClient.post(`/nfse/${nf.id}/sincronizar-issnet/`);
              await carregarNFSes(true);
            } catch {
              // silencioso: download do PDF não deve falhar por causa da sincronização
            }
          }
          return;
        }
        if (json.precisa_colar_link) {
          toast.error(
            json.error ||
              'Cole o link do e-mail do ISSNet (Nota_Digital_Nacional.aspx) no ícone de colar desta nota.',
          );
          return;
        }
        toast.error(json.error || 'PDF não disponível.');
        return;
      }
      const numero = nf.numero_nf || String(nf.numero_rps || nf.id);
      const empresa = (nf.tomador_nome || 'tomador').replace(/[\\/:*?"<>|]/g, '').trim().slice(0, 40);
      const prefixo = (nf.provedor || '').toLowerCase() === 'nacional' ? 'DANFSe' : 'NFSe';
      downloadBlobFile(blobFromApiData(res.data, 'application/pdf'), `${prefixo}-${numero}-${empresa}.pdf`);
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { error?: string; precisa_colar_link?: boolean } | Blob } };
      const data = ax.response?.data;
      if (data instanceof Blob) {
        try {
          const json = JSON.parse(await data.text()) as { error?: string; precisa_colar_link?: boolean };
          if (json.precisa_colar_link) {
            toast.error(
              json.error ||
                'Cole o link do e-mail do ISSNet (Nota_Digital_Nacional.aspx) no ícone de colar desta nota.',
            );
            return;
          }
          toast.error(json.error || 'PDF não disponível.');
          return;
        } catch {
          toast.error('PDF não disponível.');
          return;
        }
      }
      const msg = data && 'error' in data ? data.error : undefined;
      if (data && 'precisa_colar_link' in data && data.precisa_colar_link) {
        toast.error(
          msg ||
            'Cole o link do e-mail do ISSNet (Nota_Digital_Nacional.aspx) no ícone de colar desta nota.',
        );
        return;
      }
      toast.error(msg || 'PDF não disponível.');
    }
  };

  const requestCancelarNFSe = (nf: NFSe) => {
    setErroCancelamento(null);
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
      toast.success('NFS-e cancelada com sucesso.');
      setErroCancelamento(null);
      setNfCancelamento(null);
      await carregarNFSes(true);
    } catch (err: unknown) {
      const ax = err as { response?: { status?: number; data?: { error?: string; cancelamento_manual_necessario?: boolean } } };
      if (ax.response?.status === 403) {
        const semPermissao = getCrmApiErrorDetail(err, 'Sem permissão para cancelar esta nota.');
        setErroCancelamento(semPermissao);
        toast.error(semPermissao);
        return;
      }
      const manualNecessario = ax.response?.data?.cancelamento_manual_necessario;
      const errorMsg = ax.response?.data?.error || getCrmApiErrorDetail(err, 'Erro ao cancelar NFS-e');

      if (manualNecessario) {
        // ISSNet Nacional Ribeirão Preto: cancelamento via API não disponível
        toast.warning(
          'Cancelamento automático indisponível no padrão Nacional. ' +
          'Abra o portal da prefeitura para solicitar o cancelamento, ' +
          'depois use "Sincronizar" para atualizar o status.'
        );
        // Abrir portal em nova aba
        window.open(
          'https://ribeiraopreto.solarbpm.softplan.com.br/atendimento/',
          '_blank'
        );
      } else {
        setErroCancelamento(errorMsg);
        toast.error('A prefeitura não cancelou a nota. O motivo está nesta janela.');
      }
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
    const listaConfiavel = !filtroStatus && !busca && page === 1;
    setFiltroStatus('');
    setBusca('');
    setBuscaDebounced('');
    setPage(1);
    if (result.queued) {
      setEmissaoPolling({
        active: true,
        idsAntes: listaConfiavel ? nfses.map((nota) => nota.id) : [],
        capturarBase: !listaConfiavel,
      });
      setSyncMsg({ type: 'info', text: result.message });
    } else {
      setEmissaoPolling({ active: false, idsAntes: [], capturarBase: false });
      setSyncMsg({ type: 'ok', text: result.message });
    }
    void carregarNFSes(false, { page: 1, params: {} });
  };

  const handleRecuperarSuccess = (message: string) => {
    setShowRecuperarModal(false);
    setSyncMsg({ type: 'ok', text: message });
    setFiltroStatus('');
    setBusca('');
    setBuscaDebounced('');
    setPage(1);
    void carregarNFSes(false, { page: 1, params: {} });
  };

  const confirmCopy = confirmAction ? CONFIRM_COPY[confirmAction.type] : null;

  return {
    lojaProvedor: _lojaProvedor,
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
    erroCancelamento,
    confirmarCancelamentoNFSe,
    cancelandoNFSe,
    abrirModalWhatsapp,
    enviarWhatsappNFSe,
    requestReenviarEmail,
    handleEmitirSuccess,
    handleRecuperarSuccess,
    carregarNFSes,
  };
}
