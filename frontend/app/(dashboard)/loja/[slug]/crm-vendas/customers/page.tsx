'use client';

import { useEffect, useState } from 'react';
import apiClient from '@/lib/api-client';
import { Plus, Eye, Edit2, Trash2, X, Building2, Mail, Phone, MapPin, Tag } from 'lucide-react';

interface Conta {
  id: number;
  nome: string;
  segmento: string;
  telefone?: string;
  email?: string;
  cidade?: string;
  estado?: string;
  endereco?: string;
  site?: string;
  created_at: string;
}

type ModalType = 'create' | 'edit' | 'view' | 'delete' | null;

export default function CrmVendasCustomersPage() {
  const [contas, setContas] = useState<Conta[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalType, setModalType] = useState<ModalType>(null);
  const [selectedConta, setSelectedConta] = useState<Conta | null>(null);
  const [formData, setFormData] = useState({
    nome: '',
    segmento: '',
    telefone: '',
    email: '',
    cidade: '',
    estado: '',
    endereco: '',
    site: '',
  });
  const [submitting, setSubmitting] = useState(false);

  const loadContas = async () => {
    try {
      setLoading(true);
      const res = await apiClient.get<Conta[] | { results: Conta[] }>('/crm-vendas/contas/');
      const data = res.data;
      setContas(Array.isArray(data) ? data : (data as { results: Conta[] }).results ?? []);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao carregar clientes.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadContas();
  }, []);

  const openModal = (type: ModalType, conta?: Conta) => {
    setModalType(type);
    setSelectedConta(conta || null);
    if (type === 'edit' && conta) {
      setFormData({
        nome: conta.nome || '',
        segmento: conta.segmento || '',
        telefone: conta.telefone || '',
        email: conta.email || '',
        cidade: conta.cidade || '',
        estado: conta.estado || '',
        endereco: conta.endereco || '',
        site: conta.site || '',
      });
    } else if (type === 'create') {
      setFormData({
        nome: '',
        segmento: '',
        telefone: '',
        email: '',
        cidade: '',
        estado: '',
        endereco: '',
        site: '',
      });
    }
  };

  const closeModal = () => {
    setModalType(null);
    setSelectedConta(null);
    setFormData({
      nome: '',
      segmento: '',
      telefone: '',
      email: '',
      cidade: '',
      estado: '',
      endereco: '',
      site: '',
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.nome.trim()) {
      alert('Nome é obrigatório');
      return;
    }

    try {
      setSubmitting(true);
      
      if (modalType === 'create') {
        await apiClient.post('/crm-vendas/contas/', formData);
      } else if (modalType === 'edit' && selectedConta) {
        await apiClient.put(`/crm-vendas/contas/${selectedConta.id}/`, formData);
      }
      
      await loadContas();
      closeModal();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Erro ao salvar cliente.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!selectedConta) return;
    
    try {
      setSubmitting(true);
      await apiClient.delete(`/crm-vendas/contas/${selectedConta.id}/`);
      await loadContas();
      closeModal();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Erro ao excluir cliente.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[300px]">
        <div className="text-gray-500 dark:text-gray-400">
          Carregando clientes...
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Contas
        </h1>
        <button
          type="button"
          onClick={() => openModal('create')}
          className="flex items-center gap-2 px-4 py-2 bg-[#0176d3] hover:bg-[#0159a8] text-white rounded text-sm font-medium transition-colors shadow-sm"
        >
          <Plus size={18} />
          <span>Nova Conta</span>
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="rounded-lg bg-red-50 dark:bg-red-900/20 p-4 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-800">
          {error}
        </div>
      )}

      {/* Table */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[600px]">
            <thead>
              <tr className="border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/50">
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                  Nome da Conta
                </th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                  Segmento
                </th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                  Email
                </th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                  Cidade
                </th>
                <th className="text-right py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                  Ações
                </th>
              </tr>
            </thead>
            <tbody>
              {contas.length === 0 ? (
                <tr>
                  <td
                    colSpan={5}
                    className="py-12 text-center text-gray-500 dark:text-gray-400"
                  >
                    <Building2 size={48} className="mx-auto mb-3 opacity-30" />
                    <p className="font-medium">Nenhuma conta cadastrada</p>
                    <p className="text-sm mt-1">Clique em "Nova Conta" para começar</p>
                  </td>
                </tr>
              ) : (
                contas.map((conta) => (
                  <tr
                    key={conta.id}
                    className="border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors"
                  >
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded bg-gradient-to-br from-[#0176d3] to-[#0d9dda] flex items-center justify-center text-white font-semibold text-xs shrink-0">
                          {conta.nome.charAt(0).toUpperCase()}
                        </div>
                        <span className="font-medium text-gray-900 dark:text-white">
                          {conta.nome}
                        </span>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-gray-700 dark:text-gray-300">
                      {conta.segmento || '–'}
                    </td>
                    <td className="py-3 px-4 text-gray-700 dark:text-gray-300">
                      {conta.email || '–'}
                    </td>
                    <td className="py-3 px-4 text-gray-700 dark:text-gray-300">
                      {conta.cidade || '–'}
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center justify-end gap-1">
                        <button
                          type="button"
                          onClick={() => openModal('view', conta)}
                          className="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-600 dark:text-gray-300 transition-colors"
                          title="Visualizar"
                        >
                          <Eye size={16} />
                        </button>
                        <button
                          type="button"
                          onClick={() => openModal('edit', conta)}
                          className="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-600 dark:text-gray-300 transition-colors"
                          title="Editar"
                        >
                          <Edit2 size={16} />
                        </button>
                        <button
                          type="button"
                          onClick={() => openModal('delete', conta)}
                          className="p-1.5 rounded hover:bg-red-100 dark:hover:bg-red-900/30 text-red-600 dark:text-red-400 transition-colors"
                          title="Excluir"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modals */}
      {modalType && (
        <>
          <div
            className="fixed inset-0 bg-black/50 z-40"
            onClick={closeModal}
          />
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              {/* Modal Header */}
              <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                  {modalType === 'create' && 'Nova Conta'}
                  {modalType === 'edit' && 'Editar Conta'}
                  {modalType === 'view' && 'Detalhes da Conta'}
                  {modalType === 'delete' && 'Excluir Conta'}
                </h2>
                <button
                  type="button"
                  onClick={closeModal}
                  className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500 dark:text-gray-400"
                >
                  <X size={20} />
                </button>
              </div>

              {/* Modal Content */}
              <div className="p-6">
                {(modalType === 'create' || modalType === 'edit') && (
                  <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="md:col-span-2">
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Nome da Conta <span className="text-red-500">*</span>
                        </label>
                        <input
                          type="text"
                          value={formData.nome}
                          onChange={(e) => setFormData({ ...formData, nome: e.target.value })}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-[#0176d3] focus:border-transparent"
                          required
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Segmento
                        </label>
                        <input
                          type="text"
                          value={formData.segmento}
                          onChange={(e) => setFormData({ ...formData, segmento: e.target.value })}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-[#0176d3] focus:border-transparent"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Telefone
                        </label>
                        <input
                          type="tel"
                          value={formData.telefone}
                          onChange={(e) => setFormData({ ...formData, telefone: e.target.value })}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-[#0176d3] focus:border-transparent"
                        />
                      </div>

                      <div className="md:col-span-2">
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Email
                        </label>
                        <input
                          type="email"
                          value={formData.email}
                          onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-[#0176d3] focus:border-transparent"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Cidade
                        </label>
                        <input
                          type="text"
                          value={formData.cidade}
                          onChange={(e) => setFormData({ ...formData, cidade: e.target.value })}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-[#0176d3] focus:border-transparent"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Estado
                        </label>
                        <input
                          type="text"
                          value={formData.estado}
                          onChange={(e) => setFormData({ ...formData, estado: e.target.value })}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-[#0176d3] focus:border-transparent"
                        />
                      </div>

                      <div className="md:col-span-2">
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Endereço
                        </label>
                        <input
                          type="text"
                          value={formData.endereco}
                          onChange={(e) => setFormData({ ...formData, endereco: e.target.value })}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-[#0176d3] focus:border-transparent"
                        />
                      </div>

                      <div className="md:col-span-2">
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Site
                        </label>
                        <input
                          type="url"
                          value={formData.site}
                          onChange={(e) => setFormData({ ...formData, site: e.target.value })}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-[#0176d3] focus:border-transparent"
                          placeholder="https://"
                        />
                      </div>
                    </div>

                    <div className="flex justify-end gap-3 pt-4">
                      <button
                        type="button"
                        onClick={closeModal}
                        className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                        disabled={submitting}
                      >
                        Cancelar
                      </button>
                      <button
                        type="submit"
                        className="px-4 py-2 bg-[#0176d3] hover:bg-[#0159a8] text-white rounded transition-colors disabled:opacity-50"
                        disabled={submitting}
                      >
                        {submitting ? 'Salvando...' : 'Salvar'}
                      </button>
                    </div>
                  </form>
                )}

                {modalType === 'view' && selectedConta && (
                  <div className="space-y-4">
                    <div className="flex items-center gap-3 pb-4 border-b border-gray-200 dark:border-gray-700">
                      <div className="w-12 h-12 rounded bg-gradient-to-br from-[#0176d3] to-[#0d9dda] flex items-center justify-center text-white font-bold text-lg">
                        {selectedConta.nome.charAt(0).toUpperCase()}
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                          {selectedConta.nome}
                        </h3>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          {selectedConta.segmento || 'Sem segmento'}
                        </p>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {selectedConta.email && (
                        <div className="flex items-start gap-2">
                          <Mail size={18} className="text-gray-400 mt-0.5" />
                          <div>
                            <p className="text-xs text-gray-500 dark:text-gray-400">Email</p>
                            <p className="text-sm text-gray-900 dark:text-white">{selectedConta.email}</p>
                          </div>
                        </div>
                      )}

                      {selectedConta.telefone && (
                        <div className="flex items-start gap-2">
                          <Phone size={18} className="text-gray-400 mt-0.5" />
                          <div>
                            <p className="text-xs text-gray-500 dark:text-gray-400">Telefone</p>
                            <p className="text-sm text-gray-900 dark:text-white">{selectedConta.telefone}</p>
                          </div>
                        </div>
                      )}

                      {(selectedConta.cidade || selectedConta.estado) && (
                        <div className="flex items-start gap-2">
                          <MapPin size={18} className="text-gray-400 mt-0.5" />
                          <div>
                            <p className="text-xs text-gray-500 dark:text-gray-400">Localização</p>
                            <p className="text-sm text-gray-900 dark:text-white">
                              {[selectedConta.cidade, selectedConta.estado].filter(Boolean).join(', ')}
                            </p>
                          </div>
                        </div>
                      )}

                      {selectedConta.segmento && (
                        <div className="flex items-start gap-2">
                          <Tag size={18} className="text-gray-400 mt-0.5" />
                          <div>
                            <p className="text-xs text-gray-500 dark:text-gray-400">Segmento</p>
                            <p className="text-sm text-gray-900 dark:text-white">{selectedConta.segmento}</p>
                          </div>
                        </div>
                      )}
                    </div>

                    <div className="flex justify-end gap-3 pt-4">
                      <button
                        type="button"
                        onClick={closeModal}
                        className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                      >
                        Fechar
                      </button>
                      <button
                        type="button"
                        onClick={() => openModal('edit', selectedConta)}
                        className="px-4 py-2 bg-[#0176d3] hover:bg-[#0159a8] text-white rounded transition-colors"
                      >
                        Editar
                      </button>
                    </div>
                  </div>
                )}

                {modalType === 'delete' && selectedConta && (
                  <div className="space-y-4">
                    <div className="flex items-center gap-3 p-4 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800">
                      <div className="w-10 h-10 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center text-red-600 dark:text-red-400">
                        <Trash2 size={20} />
                      </div>
                      <div>
                        <p className="font-medium text-red-900 dark:text-red-200">
                          Tem certeza que deseja excluir esta conta?
                        </p>
                        <p className="text-sm text-red-700 dark:text-red-300 mt-1">
                          Esta ação não pode ser desfeita.
                        </p>
                      </div>
                    </div>

                    <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                      <p className="text-sm font-medium text-gray-900 dark:text-white">
                        {selectedConta.nome}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        {selectedConta.segmento || 'Sem segmento'}
                      </p>
                    </div>

                    <div className="flex justify-end gap-3 pt-4">
                      <button
                        type="button"
                        onClick={closeModal}
                        className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                        disabled={submitting}
                      >
                        Cancelar
                      </button>
                      <button
                        type="button"
                        onClick={handleDelete}
                        className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded transition-colors disabled:opacity-50"
                        disabled={submitting}
                      >
                        {submitting ? 'Excluindo...' : 'Excluir'}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
