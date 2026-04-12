'use client';

import { useState, useEffect } from 'react';
import { FileText, Plus, Search, X, Check, AlertCircle, RefreshCw, Trash2 } from 'lucide-react';
import apiClient from '@/lib/api-client';
import { ModalEmitirNFSe } from './components/ModalEmitirNFSe';

interface NFSe {
  id: number;
  numero_nf: string;
  numero_rps: number;
  codigo_verificacao: string;
  data_emissao: string;
  valor: string;
  valor_iss: string;
  valor_liquido: number;
  tomador_nome: string;
  tomador_cpf_cnpj: string;
  servico_descricao: string;
  status: string;
  status_display: string;
  provedor_display: string;
  provedor?: string;
  asaas_invoice_id?: string;
  erro?: string;
}

function unwrapDrfList<T>(data: unknown): T[] {
  if (Array.isArray(data)) return data as T[];
  if (data && typeof data === 'object' && Array.isArray((data as { results?: unknown }).results)) {
    return (data as { results: T[] }).results;
  }
  return [];
}

const STATUS_COLORS: Record<string, string> = {
  emitida: 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400',
  cancelada: 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400',
  erro: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400',
};

export default function NFSePage() {
  const [nfses, setNfses] = useState<NFSe[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [filtroStatus, setFiltroStatus] = useState('');
  const [busca, setBusca] = useState('');
  const [syncingId, setSyncingId] = useState<number | null>(null);
  const [syncMsg, setSyncMsg] = useState<{ type: 'ok' | 'err'; text: string } | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  useEffect(() => {
    carregarNFSes();
  }, [filtroStatus]);

  const carregarNFSes = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (filtroStatus) params.append('status', filtroStatus);
      const res = await apiClient.get(`/nfse/?${params.toString()}`);
      setNfses(unwrapDrfList<NFSe>(res.data));
    } catch (error) {
      console.error('Erro ao carregar NFS-e:', error);
    } finally {
      setLoading(false);
    }
  };

  const nfsesFiltradas = nfses.filter((nf) => {
    if (!busca) return true;
    const q = busca.toLowerCase();
    return (
      (nf.numero_nf ?? '').toLowerCase().includes(q) ||
      (nf.tomador_nome ?? '').toLowerCase().includes(q) ||
      (nf.tomador_cpf_cnpj ?? '').includes(busca)
    );
  });

  const sincronizarComAsaas = async (e: React.MouseEvent, nf: NFSe) => {
    e.preventDefault();
    e.stopPropagation();
    setSyncMsg(null);
    setSyncingId(nf.id);
    try {
      await apiClient.post(`/nfse/${nf.id}/sincronizar-asaas/`);
      setSyncMsg({ type: 'ok', text: 'Status atualizado conforme o Asaas.' });
      await carregarNFSes();
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
      await carregarNFSes();
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { error?: string } } };
      setSyncMsg({ type: 'err', text: ax.response?.data?.error || 'Não foi possível excluir.' });
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="space-y-6">
      <NfseHeader onEmitir={() => setShowModal(true)} />

      {syncMsg && <SyncMessage type={syncMsg.type} text={syncMsg.text} />}

      <NfseFilters busca={busca} setBusca={setBusca} filtroStatus={filtroStatus} setFiltroStatus={setFiltroStatus} />

      {loading ? (
        <LoadingSpinner />
      ) : nfsesFiltradas.length === 0 ? (
        <EmptyState hasFiltros={!!busca || !!filtroStatus} onEmitir={() => setShowModal(true)} />
      ) : (
        <NfseTable
          nfses={nfsesFiltradas}
          syncingId={syncingId}
          deletingId={deletingId}
          onSync={sincronizarComAsaas}
          onDelete={excluirNFSe}
        />
      )}

      {showModal && (
        <ModalEmitirNFSe
          onClose={() => setShowModal(false)}
          onSuccess={() => { setShowModal(false); carregarNFSes(); }}
          onRefreshList={carregarNFSes}
        />
      )}
    </div>
  );
}


/* ── Sub-components (page-level, not worth separate files) ── */

function NfseHeader({ onEmitir }: { onEmitir: () => void }) {
  return (
    <div className="flex items-center justify-between">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <FileText size={28} /> Notas Fiscais (NFS-e)
        </h1>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
          Gerencie as notas fiscais emitidas para seus clientes
        </p>
      </div>
      <button onClick={onEmitir} className="flex items-center gap-2 px-4 py-2 bg-[#0176d3] text-white rounded-lg hover:bg-[#0176d3]/90 transition-colors">
        <Plus size={20} /> Emitir NFS-e
      </button>
    </div>
  );
}

function SyncMessage({ type, text }: { type: 'ok' | 'err'; text: string }) {
  const cls = type === 'ok'
    ? 'bg-green-50 border-green-200 text-green-900 dark:bg-green-900/20 dark:border-green-800 dark:text-green-200'
    : 'bg-amber-50 border-amber-200 text-amber-900 dark:bg-amber-900/20 dark:border-amber-800 dark:text-amber-200';
  return <div className={`rounded-lg border px-4 py-3 text-sm ${cls}`}>{text}</div>;
}

function NfseFilters({ busca, setBusca, filtroStatus, setFiltroStatus }: {
  busca: string; setBusca: (v: string) => void;
  filtroStatus: string; setFiltroStatus: (v: string) => void;
}) {
  return (
    <div className="bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] p-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="relative">
          <Search size={20} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input type="text" value={busca} onChange={(e) => setBusca(e.target.value)} placeholder="Buscar por número, cliente ou CPF/CNPJ..." className="w-full pl-10 pr-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white" />
        </div>
        <select value={filtroStatus} onChange={(e) => setFiltroStatus(e.target.value)} className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white">
          <option value="">Todos os status</option>
          <option value="emitida">Emitida</option>
          <option value="cancelada">Cancelada</option>
          <option value="erro">Erro</option>
        </select>
      </div>
    </div>
  );
}

function LoadingSpinner() {
  return (
    <div className="text-center py-12">
      <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-[#0176d3]" />
      <p className="mt-2 text-gray-600 dark:text-gray-400">Carregando...</p>
    </div>
  );
}

function EmptyState({ hasFiltros, onEmitir }: { hasFiltros: boolean; onEmitir: () => void }) {
  return (
    <div className="bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] p-12 text-center">
      <FileText size={48} className="mx-auto text-gray-400 mb-4" />
      <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">Nenhuma nota fiscal encontrada</h3>
      <p className="text-gray-600 dark:text-gray-400 mb-4">
        {hasFiltros ? 'Tente ajustar os filtros de busca' : 'Comece emitindo sua primeira NFS-e'}
      </p>
      {!hasFiltros && (
        <button onClick={onEmitir} className="inline-flex items-center gap-2 px-4 py-2 bg-[#0176d3] text-white rounded-lg hover:bg-[#0176d3]/90">
          <Plus size={20} /> Emitir NFS-e
        </button>
      )}
    </div>
  );
}

function NfseTable({ nfses, syncingId, deletingId, onSync, onDelete }: {
  nfses: NFSe[];
  syncingId: number | null;
  deletingId: number | null;
  onSync: (e: React.MouseEvent, nf: NFSe) => void;
  onDelete: (e: React.MouseEvent, nf: NFSe) => void;
}) {
  return (
    <div className="bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 dark:bg-[#0d1f3c]">
            <tr>
              {['Número', 'Data', 'Cliente', 'Serviço'].map((h) => (
                <th key={h} className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">{h}</th>
              ))}
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Valor</th>
              <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Status</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase w-[1%] whitespace-nowrap">Ações</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {nfses.map((nf) => (
              <NfseRow key={nf.id} nf={nf} syncingId={syncingId} deletingId={deletingId} onSync={onSync} onDelete={onDelete} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function NfseRow({ nf, syncingId, deletingId, onSync, onDelete }: {
  nf: NFSe; syncingId: number | null; deletingId: number | null;
  onSync: (e: React.MouseEvent, nf: NFSe) => void;
  onDelete: (e: React.MouseEvent, nf: NFSe) => void;
}) {
  const statusColor = STATUS_COLORS[nf.status] || 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400';
  return (
    <tr className="hover:bg-gray-50 dark:hover:bg-[#0d1f3c]/50">
      <td className="px-4 py-3 text-sm">
        <div className="font-medium text-gray-900 dark:text-white">{nf.numero_nf}</div>
        <div className="text-xs text-gray-500 dark:text-gray-400">RPS: {nf.numero_rps}</div>
      </td>
      <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
        {nf.data_emissao ? new Date(nf.data_emissao).toLocaleDateString('pt-BR') : '—'}
      </td>
      <td className="px-4 py-3 text-sm">
        <div className="font-medium text-gray-900 dark:text-white">{nf.tomador_nome}</div>
        <div className="text-xs text-gray-500 dark:text-gray-400">{nf.tomador_cpf_cnpj}</div>
      </td>
      <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400 max-w-xs truncate">{nf.servico_descricao}</td>
      <td className="px-4 py-3 text-sm text-right">
        <div className="font-medium text-gray-900 dark:text-white">R$ {Number(nf.valor ?? 0).toFixed(2)}</div>
        <div className="text-xs text-gray-500 dark:text-gray-400">ISS: R$ {Number(nf.valor_iss ?? 0).toFixed(2)}</div>
      </td>
      <td className="px-4 py-3 text-center">
        <div className="flex flex-col items-center gap-1 max-w-[min(100%,280px)] mx-auto">
          <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${statusColor}`}>
            {nf.status === 'emitida' && <Check size={14} />}
            {nf.status === 'cancelada' && <X size={14} />}
            {nf.status === 'erro' && <AlertCircle size={14} />}
            {nf.status_display ?? nf.status}
          </span>
          {nf.status === 'erro' && nf.erro && (
            <p className="text-xs text-amber-800 dark:text-amber-200/90 text-left line-clamp-2 w-full" title={nf.erro}>{nf.erro}</p>
          )}
        </div>
      </td>
      <td className="px-4 py-3 text-right">
        <div className="flex items-center justify-end gap-2">
          {nf.provedor === 'asaas' && (
            <button type="button" title="Sincronizar com Asaas" onClick={(e) => onSync(e, nf)} disabled={syncingId === nf.id} className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium text-[#0176d3] hover:bg-[#0176d3]/10 rounded-md disabled:opacity-50">
              <RefreshCw size={14} className={syncingId === nf.id ? 'animate-spin' : ''} /> Sincronizar
            </button>
          )}
          <button type="button" title="Excluir NFS-e" onClick={(e) => onDelete(e, nf)} disabled={deletingId === nf.id} className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-md disabled:opacity-50">
            <Trash2 size={14} /> Excluir
          </button>
        </div>
      </td>
    </tr>
  );
}
