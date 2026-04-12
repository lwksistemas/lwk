'use client';

import { useEffect, useState } from 'react';
import { useSearchParams, useRouter, useParams } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { normalizeListResponse } from '@/lib/crm-utils';
import { Plus, Eye, Edit2, Trash2, User } from 'lucide-react';
import SkeletonTable from '@/components/crm-vendas/SkeletonTable';
import { ContatoFormModal } from './components/ContatoFormModal';
import { ContatoViewModal } from './components/ContatoViewModal';
import { ContatoDeleteModal } from './components/ContatoDeleteModal';

interface Conta { id: number; nome: string; }
interface Contato {
  id: number; nome: string; email?: string; telefone?: string;
  cargo?: string; conta: number; conta_nome?: string; observacoes?: string; created_at: string;
}

type ModalType = 'create' | 'edit' | 'view' | 'delete' | null;

const EMPTY_FORM = { nome: '', email: '', telefone: '', cargo: '', conta: '', observacoes: '' };

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
  const [formData, setFormData] = useState(EMPTY_FORM);
  const [submitting, setSubmitting] = useState(false);
  const [contaFiltro, setContaFiltro] = useState<number | null>(null);

  const loadContatos = async (contaId?: number | null, silent = false) => {
    try {
      if (!silent) setLoading(true);
      const url = contaId ? `/crm-vendas/contatos/?conta_id=${contaId}` : '/crm-vendas/contatos/';
      const res = await apiClient.get<Contato[] | { results: Contato[] }>(url);
      setContatos(normalizeListResponse(res.data));
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao carregar contatos.');
    } finally {
      if (!silent) setLoading(false);
    }
  };

  const loadContas = async () => {
    try {
      const res = await apiClient.get<Conta[] | { results: Conta[] }>('/crm-vendas/contas/');
      setContas(normalizeListResponse(res.data));
    } catch (err) {
      console.error('Erro ao carregar contas:', err);
    }
  };

  const contaIdNaUrl = searchParams.get('conta_id');
  const verParam = searchParams.get('ver');

  useEffect(() => {
    if (contaIdNaUrl) {
      const id = parseInt(contaIdNaUrl, 10);
      if (!isNaN(id)) { setContaFiltro(id); loadContatos(id); loadContas(); return; }
    }
    setContaFiltro(null); loadContatos(null); loadContas();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [contaIdNaUrl]);

  useEffect(() => {
    if (searchParams.get('criar') === '1' && contas.length > 0) {
      const cid = searchParams.get('conta_id');
      if (cid) setFormData((f) => ({ ...f, conta: cid }));
      openModal('create');
      router.replace(`/loja/${slug}/crm-vendas/contatos`, { scroll: false });
    }
  }, [searchParams, contas, router, slug]);

  useEffect(() => {
    if (!verParam) return;
    const id = parseInt(verParam, 10);
    if (isNaN(id)) return;
    const found = contatos.find((c) => c.id === id);
    if (found) { openModal('view', found); router.replace(`/loja/${slug}/crm-vendas/contatos`, { scroll: false }); }
    else if (!loading) {
      apiClient.get<Contato>(`/crm-vendas/contatos/${id}/`).then((res) => {
        openModal('view', res.data); router.replace(`/loja/${slug}/crm-vendas/contatos`, { scroll: false });
      }).catch(() => {});
    }
  }, [verParam, contatos, loading, slug, router]);

  const openModal = (type: ModalType, contato?: Contato) => {
    setModalType(type);
    setSelectedContato(contato || null);
    if (type === 'edit' && contato) {
      setFormData({ nome: contato.nome || '', email: contato.email || '', telefone: contato.telefone || '', cargo: contato.cargo || '', conta: String(contato.conta) || '', observacoes: contato.observacoes || '' });
    } else if (type === 'create') {
      setFormData(EMPTY_FORM);
    }
  };

  const closeModal = () => { setModalType(null); setSelectedContato(null); setFormData(EMPTY_FORM); };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.nome.trim()) { alert('Nome é obrigatório'); return; }
    if (!formData.conta) { alert('Conta é obrigatória'); return; }
    try {
      setSubmitting(true);
      const payload = { ...formData, conta: parseInt(formData.conta, 10) };
      if (modalType === 'create') {
        const res = await apiClient.post('/crm-vendas/contatos/', payload);
        const novoContato = res.data;
        try {
          const contaRes = await apiClient.get(`/crm-vendas/contas/${payload.conta}/`);
          const conta = contaRes.data;
          const leadPayload = {
            nome: novoContato.nome, empresa: conta.nome, email: novoContato.email || conta.email || '',
            telefone: novoContato.telefone || conta.telefone || '', origem: 'site', status: 'novo',
            conta: conta.id, contato: novoContato.id, cpf_cnpj: conta.cnpj || '',
            cep: conta.cep || '', logradouro: conta.logradouro || '', numero: conta.numero || '',
            complemento: conta.complemento || '', bairro: conta.bairro || '', cidade: conta.cidade || '', uf: conta.uf || '',
          };
          await apiClient.post('/crm-vendas/leads/', leadPayload);
          alert(`✅ Contato e Lead criados com sucesso!`);
        } catch (leadErr: any) {
          alert(`✅ Contato criado!\n\n⚠️ Lead automático falhou: ${leadErr.response?.data?.detail || leadErr.message}`);
        }
      } else if (modalType === 'edit' && selectedContato) {
        await apiClient.put(`/crm-vendas/contatos/${selectedContato.id}/`, payload);
      }
      await loadContatos(contaFiltro, true);
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
      await loadContatos(contaFiltro, true);
      closeModal();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Erro ao excluir contato.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading && contatos.length === 0) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-32 animate-pulse" />
          <div className="h-10 bg-gray-200 dark:bg-gray-700 rounded w-32 animate-pulse" />
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
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Contatos</h1>
          {contaFiltro ? (
            <div className="flex items-center gap-2 mt-1">
              <p className="text-sm text-gray-600 dark:text-gray-400">Filtrando por conta:</p>
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400">
                {contas.find((c) => c.id === contaFiltro)?.nome || `ID ${contaFiltro}`}
              </span>
              <button type="button" onClick={() => { setContaFiltro(null); loadContatos(null); router.replace(`/loja/${slug}/crm-vendas/contatos`, { scroll: false }); }} className="text-xs text-blue-600 dark:text-blue-400 hover:underline">
                Limpar filtro
              </button>
            </div>
          ) : (
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">Pessoas vinculadas às contas</p>
          )}
        </div>
        <button type="button" onClick={() => openModal('create')} className="flex items-center gap-2 px-4 py-2 bg-[#0176d3] hover:bg-[#0159a8] text-white rounded text-sm font-medium transition-colors shadow-sm">
          <Plus size={18} /> <span>Novo Contato</span>
        </button>
      </div>

      {error && <div className="rounded-lg bg-red-50 dark:bg-red-900/20 p-4 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-800">{error}</div>}

      {/* Table */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[600px]">
            <thead>
              <tr className="border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/50">
                {['Nome', 'Conta', 'Cargo', 'Email', 'Ações'].map((h, i) => (
                  <th key={h} className={`py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider ${i === 4 ? 'text-right' : 'text-left'}`}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {contatos.length === 0 ? (
                <tr><td colSpan={5} className="py-12 text-center text-gray-500 dark:text-gray-400">
                  <User size={48} className="mx-auto mb-3 opacity-30" />
                  <p className="font-medium">Nenhum contato cadastrado</p>
                  <p className="text-sm mt-1">Clique em &quot;Novo Contato&quot; para começar</p>
                </td></tr>
              ) : contatos.map((c) => (
                <tr key={c.id} className="border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2">
                      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#06a59a] to-[#0d9dda] flex items-center justify-center text-white font-semibold text-xs shrink-0">{c.nome.charAt(0).toUpperCase()}</div>
                      <span className="font-medium text-gray-900 dark:text-white">{c.nome}</span>
                    </div>
                  </td>
                  <td className="py-3 px-4 text-gray-700 dark:text-gray-300">{c.conta_nome || '–'}</td>
                  <td className="py-3 px-4 text-gray-700 dark:text-gray-300">{c.cargo || '–'}</td>
                  <td className="py-3 px-4 text-gray-700 dark:text-gray-300">{c.email || '–'}</td>
                  <td className="py-3 px-4">
                    <div className="flex items-center justify-end gap-1">
                      <button type="button" onClick={() => openModal('view', c)} className="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-600 dark:text-gray-300" title="Visualizar"><Eye size={16} /></button>
                      <button type="button" onClick={() => openModal('edit', c)} className="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-600 dark:text-gray-300" title="Editar"><Edit2 size={16} /></button>
                      <button type="button" onClick={() => openModal('delete', c)} className="p-1.5 rounded hover:bg-red-100 dark:hover:bg-red-900/30 text-red-600 dark:text-red-400" title="Excluir"><Trash2 size={16} /></button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modals */}
      {(modalType === 'create' || modalType === 'edit') && (
        <ContatoFormModal title={modalType === 'create' ? 'Novo Contato' : 'Editar Contato'} formData={formData} contas={contas} submitting={submitting} onChange={setFormData} onSubmit={handleSubmit} onClose={closeModal} />
      )}
      {modalType === 'view' && selectedContato && (
        <ContatoViewModal contato={selectedContato} onClose={closeModal} onEdit={() => openModal('edit', selectedContato)} />
      )}
      {modalType === 'delete' && selectedContato && (
        <ContatoDeleteModal contato={selectedContato} submitting={submitting} onClose={closeModal} onConfirm={handleDelete} />
      )}
    </div>
  );
}
