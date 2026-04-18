'use client';

import { useEffect, useState } from 'react';
import { useSearchParams, useRouter, useParams } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { normalizeListResponse } from '@/lib/crm-utils';
import { Plus, Eye, Edit2, Trash2, Building2 } from 'lucide-react';
import SkeletonTable from '@/components/crm-vendas/SkeletonTable';
import { ContaFormModal, type ContaFormData } from './components/ContaFormModal';
import { ContaViewModal } from './components/ContaViewModal';
import { ContaDeleteModal } from './components/ContaDeleteModal';

interface Conta {
  id: number; nome: string; razao_social?: string; cnpj?: string; inscricao_estadual?: string;
  tipo: string; segmento: string; telefone?: string; email?: string; site?: string;
  cep?: string; logradouro?: string; numero?: string; complemento?: string;
  bairro?: string; cidade?: string; uf?: string; observacoes?: string; created_at: string;
}

type ModalType = 'create' | 'edit' | 'view' | 'delete' | null;

const EMPTY_FORM: ContaFormData = {
  nome: '', razao_social: '', cnpj: '', inscricao_estadual: '', tipo: 'cliente', segmento: '',
  telefone: '', email: '', site: '', cep: '', logradouro: '', numero: '',
  complemento: '', bairro: '', cidade: '', uf: '', observacoes: '',
};

export default function CrmVendasCustomersPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();
  const slug = (params?.slug as string) ?? '';
  const verParam = searchParams.get('ver');

  const [contas, setContas] = useState<Conta[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalType, setModalType] = useState<ModalType>(null);
  const [selectedConta, setSelectedConta] = useState<Conta | null>(null);
  const [formData, setFormData] = useState<ContaFormData>(EMPTY_FORM);
  const [submitting, setSubmitting] = useState(false);
  const [consultingCNPJ, setConsultingCNPJ] = useState(false);

  const loadContas = async (silent = false) => {
    try {
      if (!silent) setLoading(true);
      const res = await apiClient.get<Conta[] | { results: Conta[] }>('/crm-vendas/contas/');
      setContas(normalizeListResponse(res.data));
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao carregar clientes.');
    } finally {
      if (!silent) setLoading(false);
    }
  };

  useEffect(() => { loadContas(); }, []);

  useEffect(() => {
    if (!verParam) return;
    const id = parseInt(verParam, 10);
    if (isNaN(id)) return;
    const found = contas.find((c) => c.id === id);
    if (found) { openModal('view', found); router.replace(`/loja/${slug}/crm-vendas/customers`, { scroll: false }); }
    else if (!loading) {
      apiClient.get<Conta>(`/crm-vendas/contas/${id}/`).then((res) => {
        openModal('view', res.data); router.replace(`/loja/${slug}/crm-vendas/customers`, { scroll: false });
      }).catch(() => {});
    }
  }, [verParam, contas, loading, slug, router]);

  const openModal = (type: ModalType, conta?: Conta) => {
    setModalType(type);
    setSelectedConta(conta || null);
    if (type === 'edit' && conta) {
      setFormData({
        nome: conta.nome || '', razao_social: conta.razao_social || '', cnpj: conta.cnpj || '',
        inscricao_estadual: conta.inscricao_estadual || '', tipo: conta.tipo || 'cliente', segmento: conta.segmento || '',
        telefone: conta.telefone || '', email: conta.email || '', site: conta.site || '',
        cep: conta.cep || '', logradouro: conta.logradouro || '', numero: conta.numero || '',
        complemento: conta.complemento || '', bairro: conta.bairro || '',
        cidade: conta.cidade || '', uf: conta.uf || '', observacoes: conta.observacoes || '',
      });
    } else if (type === 'create') {
      setFormData(EMPTY_FORM);
    }
  };

  const closeModal = () => { setModalType(null); setSelectedConta(null); setFormData(EMPTY_FORM); };

  const consultarCNPJ = async () => {
    const cnpj = formData.cnpj.replace(/\D/g, '');
    if (cnpj.length !== 14) { alert('CNPJ inválido.'); return; }
    try {
      setConsultingCNPJ(true);
      const res = await fetch(`https://brasilapi.com.br/api/cnpj/v1/${cnpj}`);
      if (!res.ok) throw new Error('CNPJ não encontrado');
      const d = await res.json();
      setFormData((f) => ({
        ...f, razao_social: d.razao_social || '', nome: d.nome_fantasia || d.razao_social || f.nome,
        telefone: d.ddd_telefone_1 ? `(${d.ddd_telefone_1.substring(0, 2)}) ${d.ddd_telefone_1.substring(2)}` : f.telefone,
        email: d.email || f.email, cep: d.cep || '', logradouro: d.logradouro || '',
        numero: d.numero || '', complemento: d.complemento || '', bairro: d.bairro || '',
        cidade: d.municipio || '', uf: d.uf || '',
      }));
      alert('Dados carregados!');
    } catch { alert('Erro ao consultar CNPJ.'); } finally { setConsultingCNPJ(false); }
  };

  const consultarCEP = async () => {
    const cep = formData.cep.replace(/\D/g, '');
    if (cep.length !== 8) return;
    try {
      const res = await fetch(`https://viacep.com.br/ws/${cep}/json/`);
      const d = await res.json();
      if (d.erro) return;
      setFormData((f) => ({ ...f, logradouro: d.logradouro || f.logradouro, bairro: d.bairro || f.bairro, cidade: d.localidade || f.cidade, uf: d.uf || f.uf }));
    } catch { /* silently fail */ }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.nome.trim()) { alert('Nome é obrigatório'); return; }
    try {
      setSubmitting(true);
      if (modalType === 'create') await apiClient.post('/crm-vendas/contas/', formData);
      else if (modalType === 'edit' && selectedConta) await apiClient.put(`/crm-vendas/contas/${selectedConta.id}/`, formData);
      await loadContas(true); closeModal();
    } catch (err: any) { alert(err.response?.data?.detail || 'Erro ao salvar.'); } finally { setSubmitting(false); }
  };

  const handleDelete = async () => {
    if (!selectedConta) return;
    try {
      setSubmitting(true);
      await apiClient.delete(`/crm-vendas/contas/${selectedConta.id}/`);
      await loadContas(true); closeModal();
    } catch (err: any) { alert(err.response?.data?.detail || 'Erro ao excluir.'); } finally { setSubmitting(false); }
  };

  if (loading && contas.length === 0) {
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
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Contas</h1>
        <button type="button" onClick={() => openModal('create')} className="flex items-center gap-2 px-4 py-2 bg-[#0176d3] hover:bg-[#0159a8] text-white rounded text-sm font-medium shadow-sm">
          <Plus size={18} /> <span>Nova Conta</span>
        </button>
      </div>

      {error && <div className="rounded-lg bg-red-50 dark:bg-red-900/20 p-4 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-800">{error}</div>}

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[600px]">
            <thead>
              <tr className="border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/50">
                {['Nome da Conta', 'Tipo', 'Segmento', 'Email', 'Cidade'].map((h) => (
                  <th key={h} className="text-left py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">{h}</th>
                ))}
                <th className="text-right py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">Ações</th>
              </tr>
            </thead>
            <tbody>
              {contas.length === 0 ? (
                <tr><td colSpan={6} className="py-12 text-center text-gray-500 dark:text-gray-400">
                  <Building2 size={48} className="mx-auto mb-3 opacity-30" />
                  <p className="font-medium">Nenhuma conta cadastrada</p>
                  <p className="text-sm mt-1">Clique em &quot;Nova Conta&quot; para começar</p>
                </td></tr>
              ) : contas.map((c) => (
                <tr key={c.id} className="border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2">
                      <div className="w-8 h-8 rounded bg-gradient-to-br from-[#0176d3] to-[#0d9dda] flex items-center justify-center text-white font-semibold text-xs shrink-0">{c.nome.charAt(0).toUpperCase()}</div>
                      <span className="font-medium text-gray-900 dark:text-white">{c.nome}</span>
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                      c.tipo === 'prestadora' ? 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300' :
                      c.tipo === 'ambos' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300' :
                      'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
                    }`}>
                      {c.tipo === 'prestadora' ? 'Prestadora' : c.tipo === 'ambos' ? 'Cliente + Prestadora' : 'Cliente'}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-gray-700 dark:text-gray-300">{c.segmento || '–'}</td>
                  <td className="py-3 px-4 text-gray-700 dark:text-gray-300">{c.email || '–'}</td>
                  <td className="py-3 px-4 text-gray-700 dark:text-gray-300">{c.cidade || '–'}</td>
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

      {(modalType === 'create' || modalType === 'edit') && (
        <ContaFormModal title={modalType === 'create' ? 'Nova Conta' : 'Editar Conta'} formData={formData} submitting={submitting} consultingCNPJ={consultingCNPJ} onChange={setFormData} onSubmit={handleSubmit} onClose={closeModal} onConsultarCNPJ={consultarCNPJ} onConsultarCEP={consultarCEP} />
      )}
      {modalType === 'view' && selectedConta && (
        <ContaViewModal conta={selectedConta} onClose={closeModal} onEdit={() => openModal('edit', selectedConta)} />
      )}
      {modalType === 'delete' && selectedConta && (
        <ContaDeleteModal nome={selectedConta.nome} segmento={selectedConta.segmento} submitting={submitting} onClose={closeModal} onConfirm={handleDelete} />
      )}
    </div>
  );
}
