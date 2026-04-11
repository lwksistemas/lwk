'use client';

import { useState, useEffect } from 'react';
import { FileText, Plus, Search, X, Check, AlertCircle, RefreshCw, Trash2 } from 'lucide-react';
import apiClient from '@/lib/api-client';

/** Resposta DRF paginada ou lista direta */
function unwrapDrfList<T>(data: unknown): T[] {
  if (Array.isArray(data)) return data as T[];
  if (data && typeof data === 'object' && Array.isArray((data as { results?: unknown }).results)) {
    return (data as { results: T[] }).results;
  }
  return [];
}

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
    const num = (nf.numero_nf ?? '').toString().toLowerCase();
    const nome = (nf.tomador_nome ?? '').toString().toLowerCase();
    const doc = (nf.tomador_cpf_cnpj ?? '').toString();
    return num.includes(q) || nome.includes(q) || doc.includes(busca);
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
      setSyncMsg({
        type: 'err',
        text: ax.response?.data?.error || 'Não foi possível sincronizar com o Asaas.',
      });
    } finally {
      setSyncingId(null);
    }
  };

  const excluirNFSe = async (e: React.MouseEvent, nf: NFSe) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (!confirm(`Tem certeza que deseja excluir a NFS-e ${nf.numero_nf}?`)) {
      return;
    }

    setDeletingId(nf.id);
    try {
      await apiClient.delete(`/nfse/${nf.id}/`);
      setSyncMsg({ type: 'ok', text: 'NFS-e excluída com sucesso.' });
      await carregarNFSes();
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { error?: string } } };
      setSyncMsg({
        type: 'err',
        text: ax.response?.data?.error || 'Não foi possível excluir a NFS-e.',
      });
    } finally {
      setDeletingId(null);
    }
  };

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

      {syncMsg && (
        <div
          className={`rounded-lg border px-4 py-3 text-sm ${
            syncMsg.type === 'ok'
              ? 'bg-green-50 border-green-200 text-green-900 dark:bg-green-900/20 dark:border-green-800 dark:text-green-200'
              : 'bg-amber-50 border-amber-200 text-amber-900 dark:bg-amber-900/20 dark:border-amber-800 dark:text-amber-200'
          }`}
        >
          {syncMsg.text}
        </div>
      )}

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
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase w-[1%] whitespace-nowrap">
                    Ações
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {nfsesFiltradas.map((nf) => (
                  <tr
                    key={nf.id}
                    className="hover:bg-gray-50 dark:hover:bg-[#0d1f3c]/50"
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
                      {nf.data_emissao
                        ? new Date(nf.data_emissao).toLocaleDateString('pt-BR')
                        : '—'}
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
                        R$ {Number(nf.valor ?? 0).toFixed(2)}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">
                        ISS: R$ {Number(nf.valor_iss ?? 0).toFixed(2)}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <div className="flex flex-col items-center gap-1 max-w-[min(100%,280px)] mx-auto">
                        <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(nf.status)}`}>
                          {nf.status === 'emitida' && <Check size={14} />}
                          {nf.status === 'cancelada' && <X size={14} />}
                          {nf.status === 'erro' && <AlertCircle size={14} />}
                          {nf.status_display ?? nf.status}
                        </span>
                        {nf.status === 'erro' && nf.erro && (
                          <p
                            className="text-xs text-amber-800 dark:text-amber-200/90 text-left line-clamp-2 w-full"
                            title={nf.erro}
                          >
                            {nf.erro}
                          </p>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-2">
                        {nf.provedor === 'asaas' && (
                          <button
                            type="button"
                            title="Atualizar status com o painel Asaas (útil se a prefeitura rejeitou depois)"
                            onClick={(e) => sincronizarComAsaas(e, nf)}
                            disabled={syncingId === nf.id}
                            className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium text-[#0176d3] hover:bg-[#0176d3]/10 rounded-md disabled:opacity-50"
                          >
                            <RefreshCw size={14} className={syncingId === nf.id ? 'animate-spin' : ''} />
                            Sincronizar
                          </button>
                        )}
                        <button
                          type="button"
                          title="Excluir NFS-e"
                          onClick={(e) => excluirNFSe(e, nf)}
                          disabled={deletingId === nf.id}
                          className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-md disabled:opacity-50"
                        >
                          <Trash2 size={14} />
                          Excluir
                        </button>
                      </div>
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
          onRefreshList={() => carregarNFSes()}
        />
      )}
    </div>
  );
}

// Modal de Emissão de NFS-e
function ModalEmitirNFSe({
  onClose,
  onSuccess,
  onRefreshList,
}: {
  onClose: () => void;
  onSuccess: () => void;
  onRefreshList?: () => void;
}) {
  const [step, setStep] = useState<'escolha' | 'manual' | 'conta'>('escolha');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [contas, setContas] = useState<any[]>([]);
  const [loadingContas, setLoadingContas] = useState(false);
  
  const [formData, setFormData] = useState({
    conta_id: null as number | null,
    tomador_cpf_cnpj: '',
    tomador_nome: '',
    tomador_email: '',
    tomador_logradouro: '',
    tomador_numero: '',
    tomador_complemento: '',
    tomador_bairro: '',
    tomador_cidade: '',
    tomador_uf: '',
    tomador_cep: '',
    servico_descricao: '',
    valor_servicos: '',
    enviar_email: true,
  });

  useEffect(() => {
    if (step === 'conta') {
      carregarContas();
    }
  }, [step]);

  const carregarContas = async () => {
    try {
      setLoadingContas(true);
      const res = await apiClient.get('/crm-vendas/contas/');
      setContas(unwrapDrfList(res.data));
    } catch (error) {
      console.error('Erro ao carregar contas:', error);
    } finally {
      setLoadingContas(false);
    }
  };

  const handleContaChange = (contaId: number) => {
    const conta = contas.find(c => c.id === contaId);
    if (conta) {
      setFormData({
        ...formData,
        conta_id: contaId,
        tomador_cpf_cnpj: conta.cnpj || '',
        tomador_nome: conta.razao_social || conta.nome,
        tomador_email: conta.email || '',
        tomador_logradouro: conta.logradouro || '',
        tomador_numero: conta.numero || '',
        tomador_complemento: conta.complemento || '',
        tomador_bairro: conta.bairro || '',
        tomador_cidade: conta.cidade || '',
        tomador_uf: conta.uf || '',
        tomador_cep: conta.cep || '',
      });
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const payload = step === 'conta' 
        ? {
            conta_id: formData.conta_id,
            servico_descricao: formData.servico_descricao,
            valor_servicos: formData.valor_servicos,
            enviar_email: formData.enviar_email,
          }
        : {
            tomador_cpf_cnpj: formData.tomador_cpf_cnpj,
            tomador_nome: formData.tomador_nome,
            tomador_email: formData.tomador_email,
            tomador_logradouro: formData.tomador_logradouro,
            tomador_numero: formData.tomador_numero,
            tomador_complemento: formData.tomador_complemento,
            tomador_bairro: formData.tomador_bairro,
            tomador_cidade: formData.tomador_cidade,
            tomador_uf: formData.tomador_uf,
            tomador_cep: formData.tomador_cep,
            servico_descricao: formData.servico_descricao,
            valor_servicos: formData.valor_servicos,
            enviar_email: formData.enviar_email,
          };

      await apiClient.post('/nfse/emitir/', payload);
      onSuccess();
    } catch (err: any) {
      console.error('Erro ao emitir NFS-e:', err);
      setError(err.response?.data?.error || 'Erro ao emitir NFS-e');
      onRefreshList?.();
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-[#16325c] rounded-lg max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">
              Emitir NFS-e
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              <X size={24} />
            </button>
          </div>

          {error && (
            <div className="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-start gap-3">
              <AlertCircle size={20} className="text-red-600 dark:text-red-400 shrink-0 mt-0.5" />
              <span className="text-sm text-red-800 dark:text-red-200">{error}</span>
            </div>
          )}

          {/* Escolha do Método */}
          {step === 'escolha' && (
            <div className="space-y-4">
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                Como deseja preencher os dados do cliente?
              </p>

              <button
                onClick={() => setStep('conta')}
                className="w-full p-6 border-2 border-gray-200 dark:border-gray-600 rounded-lg hover:border-[#0176d3] hover:bg-[#e3f3ff] dark:hover:bg-[#0176d3]/10 transition-all text-left"
              >
                <div className="flex items-start gap-4">
                  <div className="p-3 bg-[#0176d3]/10 rounded-lg">
                    <FileText size={24} className="text-[#0176d3]" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900 dark:text-white mb-1">
                      Selecionar Empresa Cadastrada
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Escolha uma empresa já cadastrada no CRM. Os dados serão preenchidos automaticamente.
                    </p>
                  </div>
                </div>
              </button>

              <button
                onClick={() => setStep('manual')}
                className="w-full p-6 border-2 border-gray-200 dark:border-gray-600 rounded-lg hover:border-[#0176d3] hover:bg-[#e3f3ff] dark:hover:bg-[#0176d3]/10 transition-all text-left"
              >
                <div className="flex items-start gap-4">
                  <div className="p-3 bg-[#0176d3]/10 rounded-lg">
                    <Plus size={24} className="text-[#0176d3]" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900 dark:text-white mb-1">
                      Preencher Manualmente
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Digite os dados do cliente manualmente. Ideal para clientes não cadastrados.
                    </p>
                  </div>
                </div>
              </button>

              <div className="flex justify-end pt-4">
                <button
                  onClick={onClose}
                  className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-[#0d1f3c] rounded-lg"
                >
                  Cancelar
                </button>
              </div>
            </div>
          )}

          {/* Formulário com Conta Cadastrada */}
          {step === 'conta' && (
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Seleção de Conta */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Empresa / Cliente *
                </label>
                {loadingContas ? (
                  <div className="text-center py-4">
                    <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-[#0176d3]"></div>
                  </div>
                ) : (
                  <select
                    value={formData.conta_id || ''}
                    onChange={(e) => handleContaChange(Number(e.target.value))}
                    required
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white"
                  >
                    <option value="">Selecione uma empresa...</option>
                    {contas.map((conta) => (
                      <option key={conta.id} value={conta.id}>
                        {conta.nome} {conta.cnpj ? `- ${conta.cnpj}` : ''}
                      </option>
                    ))}
                  </select>
                )}
              </div>

              {/* Dados do Serviço */}
              <div className="border-t border-gray-200 dark:border-gray-700 pt-6">
                <h3 className="font-semibold text-gray-900 dark:text-white mb-4">
                  Dados do Serviço
                </h3>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Descrição do Serviço *
                    </label>
                    <textarea
                      value={formData.servico_descricao}
                      onChange={(e) => setFormData({ ...formData, servico_descricao: e.target.value })}
                      required
                      rows={3}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white"
                      placeholder="Ex: Desenvolvimento de sistema web personalizado"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Valor dos Serviços (R$) *
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      value={formData.valor_servicos}
                      onChange={(e) => setFormData({ ...formData, valor_servicos: e.target.value })}
                      required
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white"
                      placeholder="0.00"
                    />
                  </div>

                  <div>
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formData.enviar_email}
                        onChange={(e) => setFormData({ ...formData, enviar_email: e.target.checked })}
                        className="w-4 h-4"
                      />
                      <span className="text-sm text-gray-700 dark:text-gray-300">
                        Enviar NFS-e por email para o cliente
                      </span>
                    </label>
                  </div>
                </div>
              </div>

              {/* Botões */}
              <div className="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-700">
                <button
                  type="button"
                  onClick={() => setStep('escolha')}
                  className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-[#0d1f3c] rounded-lg"
                >
                  Voltar
                </button>
                <div className="flex gap-3">
                  <button
                    type="button"
                    onClick={onClose}
                    className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-[#0d1f3c] rounded-lg"
                  >
                    Cancelar
                  </button>
                  <button
                    type="submit"
                    disabled={loading}
                    className="px-6 py-2 bg-[#0176d3] text-white rounded-lg hover:bg-[#0176d3]/90 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {loading ? 'Emitindo...' : 'Emitir NFS-e'}
                  </button>
                </div>
              </div>
            </form>
          )}

          {/* Formulário Manual */}
          {step === 'manual' && (
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Dados do Cliente */}
              <div>
                <h3 className="font-semibold text-gray-900 dark:text-white mb-4">
                  Dados do Cliente
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      CPF/CNPJ *
                    </label>
                    <input
                      type="text"
                      value={formData.tomador_cpf_cnpj}
                      onChange={(e) => setFormData({ ...formData, tomador_cpf_cnpj: e.target.value })}
                      required
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white"
                      placeholder="000.000.000-00"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Nome/Razão Social *
                    </label>
                    <input
                      type="text"
                      value={formData.tomador_nome}
                      onChange={(e) => setFormData({ ...formData, tomador_nome: e.target.value })}
                      required
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white"
                    />
                  </div>

                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Email
                    </label>
                    <input
                      type="email"
                      value={formData.tomador_email}
                      onChange={(e) => setFormData({ ...formData, tomador_email: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white"
                    />
                  </div>
                </div>
              </div>

              {/* Endereço */}
              <div className="border-t border-gray-200 dark:border-gray-700 pt-6">
                <h3 className="font-semibold text-gray-900 dark:text-white mb-4">
                  Endereço
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      CEP
                    </label>
                    <input
                      type="text"
                      value={formData.tomador_cep}
                      onChange={(e) => setFormData({ ...formData, tomador_cep: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white"
                      placeholder="00000-000"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Logradouro
                    </label>
                    <input
                      type="text"
                      value={formData.tomador_logradouro}
                      onChange={(e) => setFormData({ ...formData, tomador_logradouro: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Número
                    </label>
                    <input
                      type="text"
                      value={formData.tomador_numero}
                      onChange={(e) => setFormData({ ...formData, tomador_numero: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Complemento
                    </label>
                    <input
                      type="text"
                      value={formData.tomador_complemento}
                      onChange={(e) => setFormData({ ...formData, tomador_complemento: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Bairro
                    </label>
                    <input
                      type="text"
                      value={formData.tomador_bairro}
                      onChange={(e) => setFormData({ ...formData, tomador_bairro: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Cidade *
                    </label>
                    <input
                      type="text"
                      value={formData.tomador_cidade}
                      onChange={(e) => setFormData({ ...formData, tomador_cidade: e.target.value })}
                      required
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      UF *
                    </label>
                    <input
                      type="text"
                      maxLength={2}
                      value={formData.tomador_uf}
                      onChange={(e) => setFormData({ ...formData, tomador_uf: e.target.value.toUpperCase() })}
                      required
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white"
                      placeholder="SP"
                    />
                  </div>
                </div>
              </div>

              {/* Dados do Serviço */}
              <div className="border-t border-gray-200 dark:border-gray-700 pt-6">
                <h3 className="font-semibold text-gray-900 dark:text-white mb-4">
                  Dados do Serviço
                </h3>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Descrição do Serviço *
                    </label>
                    <textarea
                      value={formData.servico_descricao}
                      onChange={(e) => setFormData({ ...formData, servico_descricao: e.target.value })}
                      required
                      rows={3}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white"
                      placeholder="Ex: Desenvolvimento de sistema web personalizado"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Valor dos Serviços (R$) *
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      value={formData.valor_servicos}
                      onChange={(e) => setFormData({ ...formData, valor_servicos: e.target.value })}
                      required
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white"
                      placeholder="0.00"
                    />
                  </div>

                  <div>
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formData.enviar_email}
                        onChange={(e) => setFormData({ ...formData, enviar_email: e.target.checked })}
                        className="w-4 h-4"
                      />
                      <span className="text-sm text-gray-700 dark:text-gray-300">
                        Enviar NFS-e por email para o cliente
                      </span>
                    </label>
                  </div>
                </div>
              </div>

              {/* Botões */}
              <div className="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-700">
                <button
                  type="button"
                  onClick={() => setStep('escolha')}
                  className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-[#0d1f3c] rounded-lg"
                >
                  Voltar
                </button>
                <div className="flex gap-3">
                  <button
                    type="button"
                    onClick={onClose}
                    className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-[#0d1f3c] rounded-lg"
                  >
                    Cancelar
                  </button>
                  <button
                    type="submit"
                    disabled={loading}
                    className="px-6 py-2 bg-[#0176d3] text-white rounded-lg hover:bg-[#0176d3]/90 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {loading ? 'Emitindo...' : 'Emitir NFS-e'}
                  </button>
                </div>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
