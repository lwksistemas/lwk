'use client';

import { useState, useEffect } from 'react';
import { FileText, Plus, Search, X, Check, AlertCircle, RefreshCw, Trash2, Download, Mail } from 'lucide-react';
import apiClient from '@/lib/api-client';
import { logger } from '@/lib/logger';
import { ModalEmitirNFSe } from './components/ModalEmitirNFSe';
import { useCRMConfig } from '@/contexts/CRMConfigContext';

function nfUsaIssnet(nf: NFSe, lojaProvedor?: string): boolean {
  const p = (nf.provedor || '').toLowerCase();
  const d = (nf.provedor_display || '').toLowerCase();
  const loja = (lojaProvedor || '').toLowerCase();
  if (p === 'issnet' || d.includes('issnet')) return true;
  if (loja === 'issnet') return true;
  return false;
}

function syncEndpoint(nf: NFSe, lojaProvedor?: string): 'sincronizar-issnet' | 'sincronizar-asaas' | null {
  if (nfUsaIssnet(nf, lojaProvedor)) return 'sincronizar-issnet';
  if ((nf.provedor || '').toLowerCase() === 'asaas' || (lojaProvedor || '').toLowerCase() === 'asaas') {
    return 'sincronizar-asaas';
  }
  return null;
}

interface NFSe {
  id: number;
  numero_nf: string;
  numero_rps: number;
  codigo_verificacao: string;
  data_emissao: string;
  valor: string;
  valor_iss: string;
  aliquota_iss: string;
  valor_liquido: number;
  tomador_nome: string;
  tomador_cpf_cnpj: string;
  tomador_email?: string;
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
  const { config } = useCRMConfig();
  const lojaProvedor = config?.provedor_nf;
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
      logger.warn('Erro ao carregar NFS-e:', error);
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

  const sincronizarStatus = async (e: React.MouseEvent, nf: NFSe) => {
    e.preventDefault();
    e.stopPropagation();
    const endpoint = syncEndpoint(nf, lojaProvedor);
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

  const baixarPdfNFSe = async (e: React.MouseEvent, nf: NFSe) => {
    e.preventDefault();
    e.stopPropagation();
    try {
      // Primeiro: tentar sem blob para detectar JSON com URL
      const res = await apiClient.get(`/nfse/${nf.id}/download_pdf/`);
      
      // Se retornou JSON com URL (DANFE real do ISSNet)
      if (res.data && res.data.url) {
        window.open(res.data.url, '_blank');
        // Se o PDF já mostra "cancelada" e o CRM ainda não, sincronizar em 2º plano.
        if (nfUsaIssnet(nf, lojaProvedor)) {
          try {
            await apiClient.post(`/nfse/${nf.id}/sincronizar-issnet/`);
            await carregarNFSes();
          } catch {
            // silencioso: download do PDF não deve falhar por causa da sincronização
          }
        }
        return;
      }
      
      // Se não tem URL, baixar como blob (PDF interno)
      const resBlob = await apiClient.get(`/nfse/${nf.id}/download_pdf/`, { responseType: 'blob' });
      const blob = resBlob.data instanceof Blob ? resBlob.data : new Blob([resBlob.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      window.open(url, '_blank');
      setTimeout(() => window.URL.revokeObjectURL(url), 10000);
    } catch {
      alert('PDF não disponível.');
    }
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
          lojaProvedor={lojaProvedor}
          syncingId={syncingId}
          deletingId={deletingId}
          onSync={sincronizarStatus}
          onDelete={excluirNFSe}
          onDownloadPdf={baixarPdfNFSe}
          onReenviarEmail={reenviarEmailNFSe}
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

function NfseTable({ nfses, lojaProvedor, syncingId, deletingId, onSync, onDelete, onDownloadPdf, onReenviarEmail }: {
  nfses: NFSe[];
  lojaProvedor?: string;
  syncingId: number | null;
  deletingId: number | null;
  onSync: (e: React.MouseEvent, nf: NFSe) => void;
  onDelete: (e: React.MouseEvent, nf: NFSe) => void;
  onDownloadPdf: (e: React.MouseEvent, nf: NFSe) => void;
  onReenviarEmail: (e: React.MouseEvent, nf: NFSe) => void;
}) {
  return (
    <div className="bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
          <FileText size={20} /> Notas Fiscais
        </h2>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 dark:bg-[#0d1f3c]">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">NF</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Data</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Tomador</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Valor</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">ISS</th>
              <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Status</th>
              <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Ações</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {nfses.map((nf) => (
              <NfseRow key={nf.id} nf={nf} lojaProvedor={lojaProvedor} syncingId={syncingId} deletingId={deletingId} onSync={onSync} onDelete={onDelete} onDownloadPdf={onDownloadPdf} onReenviarEmail={onReenviarEmail} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function NfseRow({ nf, lojaProvedor, syncingId, deletingId, onSync, onDelete, onDownloadPdf, onReenviarEmail }: {
  nf: NFSe; lojaProvedor?: string; syncingId: number | null; deletingId: number | null;
  onSync: (e: React.MouseEvent, nf: NFSe) => void;
  onDelete: (e: React.MouseEvent, nf: NFSe) => void;
  onDownloadPdf: (e: React.MouseEvent, nf: NFSe) => void;
  onReenviarEmail: (e: React.MouseEvent, nf: NFSe) => void;
}) {
  const statusColor = STATUS_COLORS[nf.status] || 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400';
  const aliquota = Number(nf.aliquota_iss ?? 0).toFixed(2);
  const podeBaixar = nf.status === 'emitida' || nf.status === 'cancelada';
  const podeSincronizar = nf.status === 'emitida' || nf.status === 'erro';
  return (
    <tr className="hover:bg-gray-50 dark:hover:bg-[#0d1f3c]/50">
      <td className="px-4 py-3 text-sm">
        <div className="font-bold text-gray-900 dark:text-white">{nf.numero_nf || '—'}</div>
        <div className="text-xs text-gray-500 dark:text-gray-400">RPS {nf.numero_rps}</div>
      </td>
      <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400 whitespace-nowrap">
        {nf.data_emissao ? new Date(nf.data_emissao).toLocaleDateString('pt-BR') + ', ' + new Date(nf.data_emissao).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }) : '—'}
      </td>
      <td className="px-4 py-3 text-sm">
        <div className="font-medium text-gray-900 dark:text-white">{nf.tomador_nome}</div>
        <div className="text-xs text-gray-500 dark:text-gray-400">{nf.tomador_cpf_cnpj}</div>
      </td>
      <td className="px-4 py-3 text-sm text-right font-medium text-gray-900 dark:text-white">
        R$ {Number(nf.valor ?? 0).toFixed(2)}
      </td>
      <td className="px-4 py-3 text-sm text-right">
        <div className="text-gray-700 dark:text-gray-300">R$ {Number(nf.valor_iss ?? 0).toFixed(2)}</div>
        <div className="text-xs text-gray-500 dark:text-gray-400">{aliquota}%</div>
      </td>
      <td className="px-4 py-3 text-center">
        <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${statusColor}`}>
          {nf.status_display ?? nf.status}
        </span>
        {nf.status === 'erro' && nf.erro && (
          <p className="text-xs text-amber-700 dark:text-amber-300 mt-1 max-w-[200px] truncate" title={nf.erro}>{nf.erro}</p>
        )}
      </td>
      <td className="px-4 py-3">
        <div className="flex items-center justify-center gap-1">
          {podeBaixar && (
            <>
              <button type="button" title="Baixar PDF" onClick={(e) => onDownloadPdf(e, nf)} className="p-1.5 text-gray-600 hover:text-purple-600 hover:bg-purple-50 dark:hover:bg-purple-900/20 rounded">
                <FileText size={16} />
              </button>
              <button type="button" title="Baixar XML" onClick={(e) => {
                e.preventDefault(); e.stopPropagation();
                apiClient.get(`/nfse/${nf.id}/download_xml/`, { responseType: 'blob' }).then(res => {
                  const blob = res.data instanceof Blob ? res.data : new Blob([res.data]);
                  const url = window.URL.createObjectURL(blob);
                  const a = document.createElement('a'); a.href = url; a.download = `nfse_${nf.numero_nf || nf.id}.xml`;
                  document.body.appendChild(a); a.click(); window.URL.revokeObjectURL(url); document.body.removeChild(a);
                }).catch(() => alert('XML não disponível'));
              }} className="p-1.5 text-gray-600 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded">
                <Download size={16} />
              </button>
              <button type="button" title="Reenviar por email" onClick={(e) => onReenviarEmail(e, nf)} className="p-1.5 text-gray-600 hover:text-green-600 hover:bg-green-50 dark:hover:bg-green-900/20 rounded">
                <Mail size={16} />
              </button>
            </>
          )}
          {nf.status === 'emitida' && (
            <>
              <button type="button" title="Cancelar NFS-e" onClick={(e) => {
                e.preventDefault(); e.stopPropagation();
                const motivos: Record<string, string> = {
                  '1': 'Erro na emissão',
                  '2': 'Serviço não prestado',
                  '4': 'Duplicidade da nota',
                };
                const opcao = prompt(
                  `CANCELAR NFS-e ${nf.numero_nf || `RPS ${nf.numero_rps}`}?\n\nEscolha o motivo:\n1 - Erro na emissão\n2 - Serviço não prestado\n4 - Duplicidade da nota\n\nDigite o número (1, 2 ou 4):`
                );
                if (!opcao || !motivos[opcao]) return;

                if ((nf.provedor || '').toLowerCase() === 'issnet' && opcao === '1') {
                  const ok = confirm(
                    'A prefeitura/ISSNet costuma recusar cancelamento por "Erro na emissão" (E206) e exigir substituição.\n\nRecomendado: usar "2 - Serviço não prestado" ou "4 - Duplicidade".\n\nDeseja continuar mesmo assim?'
                  );
                  if (!ok) return;
                }

                const motivoTexto = prompt('Descreva o motivo (opcional):') || motivos[opcao];
                apiClient.post(`/nfse/${nf.id}/cancelar/`, { motivo: motivoTexto, codigo_cancelamento: opcao }).then(() => {
                  alert('Cancelamento enviado. Se aprovado pela prefeitura, o status será atualizado.');
                  window.location.reload();
                }).catch((err: any) => {
                  alert(err.response?.data?.error || 'Erro ao cancelar NFS-e');
                });
              }} className="p-1.5 text-gray-600 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded">
                <X size={16} />
              </button>
            </>
          )}
          {podeSincronizar && syncEndpoint(nf, lojaProvedor) && (
            <button
              type="button"
              title={
                nfUsaIssnet(nf, lojaProvedor)
                  ? 'Sincronizar status com ISSNet (portal da prefeitura)'
                  : 'Sincronizar com Asaas'
              }
              onClick={(e) => onSync(e, nf)}
              disabled={syncingId === nf.id}
              className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium text-[#0176d3] hover:bg-[#0176d3]/10 border border-[#0176d3]/30 rounded disabled:opacity-50 whitespace-nowrap"
            >
              <RefreshCw size={14} className={syncingId === nf.id ? 'animate-spin shrink-0' : 'shrink-0'} />
              Sincronizar
            </button>
          )}
          {nf.status !== 'emitida' && nf.status !== 'cancelada' && (
            <button type="button" title="Excluir" onClick={(e) => onDelete(e, nf)} disabled={deletingId === nf.id} className="p-1.5 text-gray-600 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded disabled:opacity-50">
              <Trash2 size={16} />
            </button>
          )}
        </div>
      </td>
    </tr>
  );
}
