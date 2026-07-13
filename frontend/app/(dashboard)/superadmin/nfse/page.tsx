'use client';

import { useState, useEffect, useCallback } from 'react';
import apiClient from '@/lib/api-client';
import { logger } from '@/lib/logger';
import {
  downloadBlobFile,
  nfseIdentificador,
  openPdfFromApiBlobResponse,
  type NfseCancelamentoEscolha,
} from '@/lib/nfse-helpers';
import { NfseCancelamentoModal } from '@/components/nfse/NfseCancelamentoModal';
import { ModalEmitirNFSeManual } from './components/ModalEmitirNFSeManual';
import { NfseSuperadminFilters } from './components/NfseSuperadminFilters';
import { NfseSuperadminHeader } from './components/NfseSuperadminHeader';
import { NfseSuperadminMessage } from './components/NfseSuperadminMessage';
import { NfseSuperadminTable } from './components/NfseSuperadminTable';
import type { NFSeEmitida } from './types';

export default function NFSeEmitidasPage() {
  const [notas, setNotas] = useState<NFSeEmitida[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [filtroStatus, setFiltroStatus] = useState('');
  const [showModalEmitir, setShowModalEmitir] = useState(false);
  const [nfCancelamento, setNfCancelamento] = useState<NFSeEmitida | null>(null);
  const [cancelandoNFSe, setCancelandoNFSe] = useState(false);

  const loadNotas = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filtroStatus) params.append('status', filtroStatus);
      const { data } = await apiClient.get(`/superadmin/nfse-emitidas/?${params.toString()}`);
      setNotas(data.notas || []);
      setTotal(data.total || 0);
    } catch (error) {
      logger.warn('Erro ao carregar NFS-e:', error);
    } finally {
      setLoading(false);
    }
  }, [filtroStatus]);

  useEffect(() => {
    void loadNotas();
  }, [loadNotas]);

  const handleBaixarXml = async (nf: NFSeEmitida) => {
    try {
      const { data } = await apiClient.get(`/superadmin/nfse-emitidas/${nf.id}/xml/`);
      if (data.success && data.xml) {
        const blob = new Blob([data.xml], { type: 'application/xml' });
        downloadBlobFile(blob, `nfse_${nf.numero_nf || nf.id}.xml`);
      } else {
        setMessage({ type: 'error', text: data.error || 'XML não disponível' });
      }
    } catch {
      setMessage({ type: 'error', text: 'Erro ao baixar XML' });
    }
  };

  const handleBaixarPdf = async (nf: NFSeEmitida) => {
    try {
      const res = await apiClient.get(`/superadmin/nfse-emitidas/${nf.id}/pdf/`, { responseType: 'blob' });
      await openPdfFromApiBlobResponse(res);
    } catch {
      setMessage({ type: 'error', text: 'PDF não disponível.' });
    }
  };

  const handleReenviar = async (nf: NFSeEmitida) => {
    if (!confirm(`Reenviar NFS-e ${nf.numero_nf} por email para ${nf.tomador_email}?`)) return;
    try {
      const { data } = await apiClient.post(`/superadmin/nfse-emitidas/${nf.id}/reenviar/`);
      if (data.success) {
        setMessage({ type: 'success', text: data.message });
      } else {
        setMessage({ type: 'error', text: data.error });
      }
    } catch {
      setMessage({ type: 'error', text: 'Erro ao reenviar' });
    }
  };

  const handleCancelar = (nf: NFSeEmitida) => {
    setNfCancelamento(nf);
  };

  const confirmarCancelamento = async (escolha: NfseCancelamentoEscolha) => {
    if (!nfCancelamento) return;
    setCancelandoNFSe(true);
    try {
      const { data } = await apiClient.post(`/superadmin/nfse-emitidas/${nfCancelamento.id}/cancelar/`, {
        codigo_cancelamento: escolha.codigo,
        motivo: escolha.motivo,
      });
      if (data.success) {
        setMessage({ type: 'success', text: data.message });
        setNfCancelamento(null);
        loadNotas();
      } else {
        setMessage({ type: 'error', text: data.error });
      }
    } catch {
      setMessage({ type: 'error', text: 'Erro ao cancelar' });
    } finally {
      setCancelandoNFSe(false);
    }
  };

  const handleExcluir = async (nf: NFSeEmitida) => {
    if (!confirm(`EXCLUIR registro da NFS-e ${nf.numero_nf || `RPS ${nf.numero_rps}`}? O registro será removido do sistema.`))
      return;
    try {
      const { data } = await apiClient.delete(`/superadmin/nfse-emitidas/${nf.id}/excluir/`);
      if (data.success) {
        setMessage({ type: 'success', text: data.message });
        loadNotas();
      } else {
        setMessage({ type: 'error', text: data.error });
      }
    } catch {
      setMessage({ type: 'error', text: 'Erro ao excluir' });
    }
  };

  return (
    <div className="w-full max-w-full px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      <NfseSuperadminHeader
        total={total}
        loading={loading}
        onEmitir={() => setShowModalEmitir(true)}
        onAtualizar={loadNotas}
      />

      {message && <NfseSuperadminMessage type={message.type} text={message.text} />}

      <NfseSuperadminFilters filtroStatus={filtroStatus} onFiltroChange={setFiltroStatus} />

      <NfseSuperadminTable
        notas={notas}
        loading={loading}
        onBaixarPdf={handleBaixarPdf}
        onBaixarXml={handleBaixarXml}
        onReenviar={handleReenviar}
        onCancelar={handleCancelar}
        onExcluir={handleExcluir}
      />

      {showModalEmitir && (
        <ModalEmitirNFSeManual
          onClose={() => setShowModalEmitir(false)}
          onSuccess={() => {
            setShowModalEmitir(false);
            setMessage({ type: 'success', text: 'NFS-e emitida com sucesso!' });
            loadNotas();
          }}
        />
      )}

      {nfCancelamento && (
        <NfseCancelamentoModal
          identificador={nfseIdentificador(nfCancelamento)}
          provedor={nfCancelamento.provedor}
          loading={cancelandoNFSe}
          onClose={() => !cancelandoNFSe && setNfCancelamento(null)}
          onConfirm={confirmarCancelamento}
        />
      )}
    </div>
  );
}
