'use client';

import { useState, useEffect } from 'react';
import { FileText, Plus, Search, X, Check, AlertCircle } from 'lucide-react';
import apiClient from '@/lib/api-client';

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
}

export default function NFSePage() {
  const [nfses, setNfses] = useState<NFSe[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [filtroStatus, setFiltroStatus] = useState('');
  const [busca, setBusca] = useState('');

  useEffect(() => {
    carregarNFSes();
  }, [filtroStatus]);

  const carregarNFSes = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (filtroStatus) params.append('status', filtroStatus);
      
      const res = await apiClient.get(`/nfse/?${params.toString()}`);
      setNfses(res.data);
    } catch (error) {
      console.error('Erro ao carregar NFS-e:', error);
    } finally {
      setLoading(false);
    }
  };

  const nfsesFiltradas = nfses.filter(nf =>
    !busca ||
    nf.numero_nf.toLowerCase().includes(busca.toLowerCase()) ||
    nf.tomador_nome.toLowerCase().includes(busca.toLowerCase()) ||
    nf.tomador_cpf_cnpj.includes(busca)
  );

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'emitida':
        return 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400';
      case 'cancelada':
        return 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400';
      case 'erro':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <FileText size={28} />
            Notas Fiscais (NFS-e)
          </h1>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Gerencie as notas fiscais emitidas para seus clientes
          </p>
        </div>
        
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-[#0176d3] text-white rounded-lg hover:bg-[#0176d3]/90 transition-colors"
        >
          <Plus size={20} />
          Emitir NFS-e
        </button>
      </div>

      {/* Filtros */}
      <div className="bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Busca */}
          <div className="relative">
            <Search size={20} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              value={busca}
              onChange={(e) => setBusca(e.target.value)}
              placeholder="Buscar por número, cliente ou CPF/CNPJ..."
              className="w-full pl-10 pr-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white"
            />
          </div>

          {/* Filtro Status */}
          <select
            value={filtroStatus}
            onChange={(e) => setFiltroStatus(e.target.value)}
            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white"
          >
            <option value="">Todos os status</option>
            <option value="emitida">Emitida</option>
            <option value="cancelada">Cancelada</option>
            <option value="erro">Erro</option>
          </select>
        </div>
      </div>

      {/* Listagem */}
      {loading ? (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-[#0176d3]"></div>
          <p className="mt-2 text-gray-600 dark:text-gray-400">Carregando...</p>
        </div>
      ) : nfsesFiltradas.length === 0 ? (
        <div className="bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] p-12 text-center">
          <FileText size={48} className="mx-auto text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            Nenhuma nota fiscal encontrada
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            {busca || filtroStatus
              ? 'Tente ajustar os filtros de busca'
              : 'Comece emitindo sua primeira NFS-e'}
          </p>
          {!busca && !filtroStatus && (
            <button
              onClick={() => setShowModal(true)}
              className="inline-flex items-center gap-2 px-4 py-2 bg-[#0176d3] text-white rounded-lg hover:bg-[#0176d3]/90"
            >
              <Plus size={20} />
              Emitir NFS-e
            </button>
          )}
        </div>
      ) : (
        <div className="bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-[#0d1f3c]">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                    Número
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                    Data
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                    Cliente
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                    Serviço
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                    Valor
                  </th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {nfsesFiltradas.map((nf) => (
                  <tr
                    key={nf.id}
                    className="hover:bg-gray-50 dark:hover:bg-[#0d1f3c]/50 cursor-pointer"
                  >
                    <td className="px-4 py-3 text-sm">
                      <div className="font-medium text-gray-900 dark:text-white">
                        {nf.numero_nf}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">
                        RPS: {nf.numero_rps}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                      {new Date(nf.data_emissao).toLocaleDateString('pt-BR')}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <div className="font-medium text-gray-900 dark:text-white">
                        {nf.tomador_nome}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">
                        {nf.tomador_cpf_cnpj}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400 max-w-xs truncate">
                      {nf.servico_descricao}
                    </td>
                    <td className="px-4 py-3 text-sm text-right">
                      <div className="font-medium text-gray-900 dark:text-white">
                        R$ {parseFloat(nf.valor).toFixed(2)}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">
                        ISS: R$ {parseFloat(nf.valor_iss).toFixed(2)}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(nf.status)}`}>
                        {nf.status === 'emitida' && <Check size={14} />}
                        {nf.status === 'cancelada' && <X size={14} />}
                        {nf.status === 'erro' && <AlertCircle size={14} />}
                        {nf.status_display}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Modal de Emissão */}
      {showModal && (
        <ModalEmitirNFSe
          onClose={() => setShowModal(false)}
          onSuccess={() => {
            setShowModal(false);
            carregarNFSes();
          }}
        />
      )}
    </div>
  );
}

// Componente Modal será criado em arquivo separado
function ModalEmitirNFSe({ onClose, onSuccess }: { onClose: () => void; onSuccess: () => void }) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-[#16325c] rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
            Emitir NFS-e
          </h2>
          <p className="text-gray-600 dark:text-gray-400">
            Modal de emissão será implementado no próximo passo...
          </p>
          <div className="mt-6 flex justify-end gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-[#0d1f3c] rounded-lg"
            >
              Fechar
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
