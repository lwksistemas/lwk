'use client';

import { useEffect, useState } from 'react';
import { useSearchParams, useRouter, useParams } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { normalizeListResponse } from '@/lib/crm-utils';
import { Plus, Eye, Edit2, Trash2, X, User, Mail, Phone, Building2, Briefcase } from 'lucide-react';
import SkeletonTable from '@/components/crm-vendas/SkeletonTable';

interface Conta {
  id: number;
  nome: string;
}

interface Contato {
  id: number;
  nome: string;
  email?: string;
  telefone?: string;
  cargo?: string;
  conta: number;
  conta_nome?: string;
  observacoes?: string;
  created_at: string;
}

type ModalType = 'create' | 'edit' | 'view' | 'delete' | null;

export default function CrmVendasContatosPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();
  const slug = (params?.slug as string) ?? '';
  const [contatos, setContatos] = useState<Contato[]>([]);
  const [contas, setContas] = useState<Conta[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalType, setModalType] = useState<ModalType>(null);
  const [selectedContato, setSelectedContato] = useState<Contato | null>(null);
  const [formData, setFormData] = useState({
    nome: '',
    email: '',
    telefone: '',
    cargo: '',
    conta: '',
    observacoes: '',
  });
  const [submitting, setSubmitting] = useState(false);
  const [contaFiltro, setContaFiltro] = useState<number | null>(null);

  const loadContatos = async (contaId?: number | null) => {
    try {
      setLoading(true);
      console.log('Carregando contatos...');
      const url = contaId 
        ? `/crm-vendas/contatos/?conta_id=${contaId}`
        : '/crm-vendas/contatos/';
      const res = await apiClient.get<Contato[] | { results: Contato[] }>(url);
      console.log('Resposta da API:', res.data);
      const contatosNormalizados = normalizeListResponse(res.data);
      console.log('Contatos normalizados:', contatosNormalizados);
      setContatos(contatosNormalizados);
      setError(null);
    } catch (err: any) {
      console.error('Erro ao carregar contatos:', err);
      setError(err.response?.data?.detail || 'Erro ao carregar contatos.');
    } finally {
      setLoading(false);
    }
  };

  const loadContas = async () => {
    try {
      const res = await apiClient.get<Conta[] | { results: Conta[] }>('/crm-vendas/contas/');
      setContas(normalizeListResponse(res.data));
    } catch (err: any) {
      console.error('Erro ao carregar contas:', err);
    }
  };

  useEffect(() => {
    // Detectar filtro por conta_id na URL
    const contaIdParam = searchParams.get('conta_id');
    if (contaIdParam) {
      const contaId = parseInt(contaIdParam, 10);
      if (!isNaN(contaId)) {
        setContaFiltro(contaId);
        loadContatos(contaId);
        loadContas();
        return;
      }
    }
    
    // Carregar todos os contatos se não houver filtro
    loadContatos();
    loadContas();
  }, [searchParams]);

  // Abrir modal de criação quando ?criar=1
  useEffect(() => {
    if (searchParams.get('criar') === '1' && contas.length > 0) {
      const contaIdParam = searchParams.get('conta_id');
      if (contaIdParam) {
        const contaId = parseInt(contaIdParam, 10);
        if (!isNaN(contaId)) {
          // Pré-selecionar a conta no formulário
          setFormData((f) => ({ ...f, conta: String(contaId) }));
        }
      }
      openModal('create');
      router.replace(`/loja/${slug}/crm-vendas/contatos`, { scroll: false });
    }
  }, [searchParams, contas, router, slug]);

  // Abrir modal de visualização quando ?ver=ID
  useEffect(() => {
    const verId = searchParams.get('ver');
    if (!verId) return;
    const id = parseInt(verId, 10);
    if (isNaN(id)) return;
    const found = contatos.find((c) => c.id === id);
    if (found) {
      openModal('view', found);
      router.replace(`/loja/${slug}/crm-vendas/contatos`, { scroll: false });
    } else if (!loading) {
      apiClient
        .get<Contato>(`/crm-vendas/contatos/${id}/`)
        .then((res) => {
          openModal('view', res.data);
          router.replace(`/loja/${slug}/crm-vendas/contatos`, { scroll: false });
        })
        .catch(() => {});
    }
  }, [searchParams.get('ver'), contatos, loading, slug, router]);

  const openModal = (type: ModalType, contato?: Contato) => {
    setModalType(type);
    setSelectedContato(contato || null);
    if (type === 'edit' && contato) {
      setFormData({
        nome: contato.nome || '',
        email: contato.email || '',
        telefone: contato.telefone || '',
        cargo: contato.cargo || '',
        conta: String(contato.conta) || '',
        observacoes: contato.observacoes || '',
      });
    } else if (type === 'create') {
      setFormData({
        nome: '',
        email: '',
        telefone: '',
        cargo: '',
        conta: '',
        observacoes: '',
      });
    }
  };

  const closeModal = () => {
    setModalType(null);
    setSelectedContato(null);
    setFormData({
      nome: '',
      email: '',
      telefone: '',
      cargo: '',
      conta: '',
      observacoes: '',
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.nome.trim()) {
      alert('Nome é obrigatório');
      return;
    }

    if (!formData.conta) {
      alert('Conta é obrigatória');
      return;
    }

    try {
      setSubmitting(true);
      
      const payload = {
        ...formData,
        conta: parseInt(formData.conta, 10),
      };
      
      if (modalType === 'create') {
        await apiClient.post('/crm-vendas/contatos/', payload);
      } else if (modalType === 'edit' && selectedContato) {
        await apiClient.put(`/crm-vendas/contatos/${selectedContato.id}/`, payload);
      }
      
      await loadContatos();
      closeModal();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Erro ao salvar contato.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!selectedContato) return;
    
    try {
      setSubmitting(true);
      await apiClient.delete(`/crm-vendas/contatos/${selectedContato.id}/`);
      await loadContatos();
      closeModal();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Erro ao excluir contato.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-32 animate-pulse"></div>
          <div className="h-10 bg-gray-200 dark:bg-gray-700 rounded w-32 animate-pulse"></div>
        </div>
        <SkeletonTable rows={5} columns={5} />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Contatos
          </h1>
          {contaFiltro ? (
            <div className="flex items-center gap-2 mt-1">
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Filtrando por conta:
              </p>
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400">
                {contas.find(c => c.id === contaFiltro)?.nome || `ID ${contaFiltro}`}
              </span>
              <button
                type="button"
                onClick={() => {
                  setContaFiltro(null);
                  loadContatos(null);
                  router.replace(`/loja/${slug}/crm-vendas/contatos`, { scroll: false });
                }}
                className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
              >
                Limpar filtro
              </button>
            </div>
          ) : (
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              Pessoas vinculadas às contas
            </p>
          )}
        </div>
        <button
          type="button"
          onClick={() => openModal('create')}
          className="flex items-center gap-2 px-4 py-2 bg-[#0176d3] hover:bg-[#0159a8] text-white rounded text-sm font-medium transition-colors shadow-sm"
        >
          <Plus size={18} />
          <span>Novo Contato</span>
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
                  Nome
                </th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                  Conta
                </th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                  Cargo
                </th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                  Email
                </th>
                <th className="text-right py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                  Ações
                </th>
              </tr>
            </thead>
            <tbody>
              {contatos.length === 0 ? (
                <tr>
                  <td
                    colSpan={5}
                    className="py-12 text-center text-gray-500 dark:text-gray-400"
                  >
                    <User size={48} className="mx-auto mb-3 opacity-30" />
                    <p className="font-medium">Nenhum contato cadastrado</p>
                    <p className="text-sm mt-1">Clique em "Novo Contato" para começar</p>
                  </td>
                </tr>
              ) : (
                contatos.map((contato) => (
                  <tr
                    key={contato.id}
                    className="border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors"
                  >
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#06a59a] to-[#0d9dda] flex items-center justify-center text-white font-semibold text-xs shrink-0">
                          {contato.nome.charAt(0).toUpperCase()}
                        </div>
                        <span className="font-medium text-gray-900 dark:text-white">
                          {contato.nome}
                        </span>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-gray-700 dark:text-gray-300">
                      {contato.conta_nome || '–'}
                    </td>
                    <td className="py-3 px-4 text-gray-700 dark:text-gray-300">
                      {contato.cargo || '–'}
                    </td>
                    <td className="py-3 px-4 text-gray-700 dark:text-gray-300">
                      {contato.email || '–'}
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center justify-end gap-1">
                        <button
                          type="button"
                          onClick={() => openModal('view', contato)}
                          className="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-600 dark:text-gray-300 transition-colors"
                          title="Visualizar"
                        >
                          <Eye size={16} />
                        </button>
                        <button
                          type="button"
                          onClick={() => openModal('edit', contato)}
                          className="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-600 dark:text-gray-300 transition-colors"
                          title="Editar"
                        >
                          <Edit2 size={16} />
                        </button>
                        <button
                          type="button"
                          onClick={() => openModal('delete', contato)}
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
                  {modalType === 'create' && 'Novo Contato'}
                  {modalType === 'edit' && 'Editar Contato'}
                  {modalType === 'view' && 'Detalhes do Contato'}
                  {modalType === 'delete' && 'Excluir Contato'}
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
                          Nome <span className="text-red-500">*</span>
                        </label>
                        <input
                          type="text"
                          value={formData.nome}
                          onChange={(e) => setFormData({ ...formData, nome: e.target.value })}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-[#0176d3] focus:border-transparent"
                          required
                        />
                      </div>

                      <div className="md:col-span-2">
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Conta <span className="text-red-500">*</span>
                        </label>
                        <select
                          value={formData.conta}
                          onChange={(e) => setFormData({ ...formData, conta: e.target.value })}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-[#0176d3] focus:border-transparent"
                          required
                        >
                          <option value="">Selecione uma conta</option>
                          {contas.map((conta) => (
                            <option key={conta.id} value={conta.id}>
                              {conta.nome}
                            </option>
                          ))}
                        </select>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Cargo
                        </label>
                        <input
                          type="text"
                          value={formData.cargo}
                          onChange={(e) => setFormData({ ...formData, cargo: e.target.value })}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-[#0176d3] focus:border-transparent"
                          placeholder="Ex: Gerente de Compras"
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

                      <div className="md:col-span-2">
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Observações
                        </label>
                        <textarea
                          value={formData.observacoes}
                          onChange={(e) => setFormData({ ...formData, observacoes: e.target.value })}
                          rows={3}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-[#0176d3] focus:border-transparent"
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

                {modalType === 'view' && selectedContato && (
                  <div className="space-y-4">
                    <div className="flex items-center gap-3 pb-4 border-b border-gray-200 dark:border-gray-700">
                      <div className="w-12 h-12 rounded-full bg-gradient-to-br from-[#06a59a] to-[#0d9dda] flex items-center justify-center text-white font-bold text-lg">
                        {selectedContato.nome.charAt(0).toUpperCase()}
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                          {selectedContato.nome}
                        </h3>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          {selectedContato.cargo || 'Sem cargo definido'}
                        </p>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="flex items-start gap-2">
                        <Building2 size={18} className="text-gray-400 mt-0.5" />
                        <div>
                          <p className="text-xs text-gray-500 dark:text-gray-400">Conta</p>
                          <p className="text-sm text-gray-900 dark:text-white">{selectedContato.conta_nome}</p>
                        </div>
                      </div>

                      {selectedContato.cargo && (
                        <div className="flex items-start gap-2">
                          <Briefcase size={18} className="text-gray-400 mt-0.5" />
                          <div>
                            <p className="text-xs text-gray-500 dark:text-gray-400">Cargo</p>
                            <p className="text-sm text-gray-900 dark:text-white">{selectedContato.cargo}</p>
                          </div>
                        </div>
                      )}

                      {selectedContato.email && (
                        <div className="flex items-start gap-2">
                          <Mail size={18} className="text-gray-400 mt-0.5" />
                          <div>
                            <p className="text-xs text-gray-500 dark:text-gray-400">Email</p>
                            <p className="text-sm text-gray-900 dark:text-white">{selectedContato.email}</p>
                          </div>
                        </div>
                      )}

                      {selectedContato.telefone && (
                        <div className="flex items-start gap-2">
                          <Phone size={18} className="text-gray-400 mt-0.5" />
                          <div>
                            <p className="text-xs text-gray-500 dark:text-gray-400">Telefone</p>
                            <p className="text-sm text-gray-900 dark:text-white">{selectedContato.telefone}</p>
                          </div>
                        </div>
                      )}
                    </div>

                    {selectedContato.observacoes && (
                      <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                        <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Observações</p>
                        <p className="text-sm text-gray-900 dark:text-white whitespace-pre-wrap">
                          {selectedContato.observacoes}
                        </p>
                      </div>
                    )}

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
                        onClick={() => openModal('edit', selectedContato)}
                        className="px-4 py-2 bg-[#0176d3] hover:bg-[#0159a8] text-white rounded transition-colors"
                      >
                        Editar
                      </button>
                    </div>
                  </div>
                )}

                {modalType === 'delete' && selectedContato && (
                  <div className="space-y-4">
                    <div className="flex items-center gap-3 p-4 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800">
                      <div className="w-10 h-10 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center text-red-600 dark:text-red-400">
                        <Trash2 size={20} />
                      </div>
                      <div>
                        <p className="font-medium text-red-900 dark:text-red-200">
                          Tem certeza que deseja excluir este contato?
                        </p>
                        <p className="text-sm text-red-700 dark:text-red-300 mt-1">
                          Esta ação não pode ser desfeita.
                        </p>
                      </div>
                    </div>

                    <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                      <p className="text-sm font-medium text-gray-900 dark:text-white">
                        {selectedContato.nome}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        {selectedContato.conta_nome}
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
