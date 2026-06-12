'use client';

import { useEffect, useState } from 'react';
import apiClient from '@/lib/api-client';
import CrmPaginationBar from '@/components/crm-vendas/CrmPaginationBar';
import { usePaginatedList } from '@/hooks/usePaginatedList';
import {
  nfseIdentificador,
  nfseSyncEndpoint,
  nfUsaIssnet,
  openBlobInNewTab,
  openPdfFromJsonUrl,
  solicitarCancelamentoNFSe,
} from '@/lib/nfse-helpers';
import { useWhatsappEnvioFlags } from '@/hooks/useWhatsappEnvioFlags';
import { telefoneInternacionalBr } from '@/lib/format-br';
import { ModalEmitirNFSe } from './components/ModalEmitirNFSe';
import ModalNfseEnviarWhatsapp from './components/ModalNfseEnviarWhatsapp';
import { NfseLojaEmptyState } from './components/NfseLojaEmptyState';
import { NfseLojaFilters } from './components/NfseLojaFilters';
import { NfseLojaHeader } from './components/NfseLojaHeader';
import { NfseLojaLoading } from './components/NfseLojaLoading';
import { NfseLojaSyncMessage } from './components/NfseLojaSyncMessage';
import { NfseLojaTable } from './components/NfseLojaTable';
import type { NFSe } from './types';
import { useCRMConfig } from '@/contexts/CRMConfigContext';

export default function NFSePage() {
  const { config } = useCRMConfig();
  const lojaProvedor = config?.provedor_nf;
  const [showModal, setShowModal] = useState(false);
  const [filtroStatus, setFiltroStatus] = useState('');
  const [busca, setBusca] = useState('');
  const [buscaDebounced, setBuscaDebounced] = useState('');
  const [syncingId, setSyncingId] = useState<number | null>(null);
  const [syncMsg, setSyncMsg] = useState<{ type: 'ok' | 'err'; text: string } | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [nfWhatsapp, setNfWhatsapp] = useState<NFSe | null>(null);
  const { whatsappAtivo } = useWhatsappEnvioFlags();

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

  const sincronizarStatus = async (e: React.MouseEvent, nf: NFSe) => {
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
      const ax = err as { response?: { data?: { error?: string } } };
      setSyncMsg({ type: 'err', text: ax.response?.data?.error || 'Não foi possível sincronizar.' });
    } finally {
      setSyncingId(null);
    }
  };

  const excluirNFSe = async (e: React.MouseEvent, nf: NFSe) => {
    e.preventDefault();
    e.stopPropagation();
    if (!confirm(`Tem certeza que deseja excluir a NFS-e ${nf.numero_nf}?`)) return;
    setDeletingId(nf.id);
    try {
      await apiClient.delete(`/nfse/${nf.id}/`);
      setSyncMsg({ type: 'ok', text: 'NFS-e excluída com sucesso.' });
      await carregarNFSes(true);
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { error?: string } } };
      setSyncMsg({ type: 'err', text: ax.response?.data?.error || 'Não foi possível excluir.' });
    } finally {
      setDeletingId(null);
    }
  };

  const baixarPdfNFSe = async (e: React.MouseEvent, nf: NFSe) => {
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
      alert('PDF não disponível.');
    }
  };

  const cancelarNFSe = async (nf: NFSe) => {
    const escolha = solicitarCancelamentoNFSe(nfseIdentificador(nf), { provedor: nf.provedor });
    if (!escolha) return;
    try {
      await apiClient.post(`/nfse/${nf.id}/cancelar/`, {
        motivo: escolha.motivo,
        codigo_cancelamento: escolha.codigo,
      });
      alert('Cancelamento enviado. Se aprovado pela prefeitura, o status será atualizado.');
      await carregarNFSes(true);
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { error?: string } } };
      alert(ax.response?.data?.error || 'Erro ao cancelar NFS-e');
    }
  };

  const abrirModalWhatsapp = (e: React.MouseEvent, nf: NFSe) => {
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

  const reenviarEmailNFSe = async (e: React.MouseEvent, nf: NFSe) => {
    e.preventDefault();
    e.stopPropagation();
    if (!nf.tomador_email) {
      alert('Esta NFS-e não possui email do tomador cadastrado.');
      return;
    }
    if (!confirm(`Reenviar nota fiscal por email para ${nf.tomador_email}?`)) return;
    try {
      await apiClient.post(`/nfse/${nf.id}/reenviar_email/`);
      setSyncMsg({ type: 'ok', text: `Email reenviado para ${nf.tomador_email}` });
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { error?: string } } };
      setSyncMsg({ type: 'err', text: ax.response?.data?.error || 'Erro ao reenviar email.' });
    }
  };

  return (
    <div className="space-y-6">
      <NfseLojaHeader onEmitir={() => setShowModal(true)} />

      {syncMsg && <NfseLojaSyncMessage type={syncMsg.type} text={syncMsg.text} />}

      <NfseLojaFilters
        busca={busca}
        setBusca={setBusca}
        filtroStatus={filtroStatus}
        setFiltroStatus={setFiltroStatus}
      />

      {loading ? (
        <NfseLojaLoading />
      ) : nfses.length === 0 ? (
        <NfseLojaEmptyState hasFiltros={!!busca || !!filtroStatus} onEmitir={() => setShowModal(true)} />
      ) : (
        <>
          <NfseLojaTable
            nfses={nfses}
            lojaProvedor={lojaProvedor}
            syncingId={syncingId}
            deletingId={deletingId}
            onSync={sincronizarStatus}
            onDelete={excluirNFSe}
            onDownloadPdf={baixarPdfNFSe}
            onReenviarEmail={reenviarEmailNFSe}
            onEnviarWhatsapp={abrirModalWhatsapp}
            onCancelar={cancelarNFSe}
            whatsappHabilitado={whatsappAtivo}
          />
          <CrmPaginationBar
            page={page}
            totalPages={totalPages}
            totalCount={totalCount}
            pageSize={pageSize}
            loading={loading}
            itemLabel="notas"
            onPageChange={setPage}
          />
        </>
      )}

      {nfWhatsapp && (
        <ModalNfseEnviarWhatsapp
          nf={nfWhatsapp}
          onClose={() => setNfWhatsapp(null)}
          onEnviar={enviarWhatsappNFSe}
        />
      )}

      {showModal && (
        <ModalEmitirNFSe
          onClose={() => setShowModal(false)}
          onSuccess={() => {
            setShowModal(false);
            carregarNFSes(true);
          }}
        />
      )}
    </div>
  );
}
