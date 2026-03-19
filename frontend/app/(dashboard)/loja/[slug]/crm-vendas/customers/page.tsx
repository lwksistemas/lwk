'use client';

import { useEffect, useState } from 'react';
import { useSearchParams, useRouter, useParams } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { normalizeListResponse } from '@/lib/crm-utils';
import { Plus, Eye, Edit2, Trash2, X, Building2, Mail, Phone, MapPin, Tag } from 'lucide-react';
import SkeletonTable from '@/components/crm-vendas/SkeletonTable';

interface Conta {
  id: number;
  nome: string;
  razao_social?: string;
  cnpj?: string;
  inscricao_estadual?: string;
  segmento: string;
  telefone?: string;
  email?: string;
  site?: string;
  cep?: string;
  logradouro?: string;
  numero?: string;
  complemento?: string;
  bairro?: string;
  cidade?: string;
  uf?: string;
  endereco?: string;
  observacoes?: string;
  created_at: string;
}

type ModalType = 'create' | 'edit' | 'view' | 'delete' | null;

export default function CrmVendasCustomersPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();
  const slug = (params?.slug as string) ?? '';
  const [contas, setContas] = useState<Conta[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalType, setModalType] = useState<ModalType>(null);
  const [selectedConta, setSelectedConta] = useState<Conta | null>(null);
  const [formData, setFormData] = useState({
    nome: '',
    razao_social: '',
    cnpj: '',
    inscricao_estadual: '',
    segmento: '',
    telefone: '',
    email: '',
    site: '',
    cep: '',
    logradouro: '',
    numero: '',
    complemento: '',
    bairro: '',
    cidade: '',
    uf: '',
    observacoes: '',
  });
  const [submitting, setSubmitting] = useState(false);
  const [consultingCNPJ, setConsultingCNPJ] = useState(false);
  const [creatingOpportunity, setCreatingOpportunity] = useState(false);

  const loadContas = async () => {
    try {
      setLoading(true);
      const res = await apiClient.get<Conta[] | { results: Conta[] }>('/crm-vendas/contas/');
      setContas(normalizeListResponse(res.data));
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

  // Abrir modal de visualização quando ?ver=ID (ex.: vindo da busca global)
  useEffect(() => {
    const verId = searchParams.get('ver');
    if (!verId) return;
    const id = parseInt(verId, 10);
    if (isNaN(id)) return;
    const found = contas.find((c) => c.id === id);
    if (found) {
      openModal('view', found);
      router.replace(`/loja/${slug}/crm-vendas/customers`, { scroll: false });
    } else if (!loading) {
      apiClient
        .get<Conta>(`/crm-vendas/contas/${id}/`)
        .then((res) => {
          openModal('view', res.data);
          router.replace(`/loja/${slug}/crm-vendas/customers`, { scroll: false });
        })
        .catch(() => {});
    }
  }, [searchParams.get('ver'), contas, loading, slug, router]);

  const openModal = (type: ModalType, conta?: Conta) => {
    setModalType(type);
    setSelectedConta(conta || null);
    if (type === 'edit' && conta) {
      setFormData({
        nome: conta.nome || '',
        razao_social: conta.razao_social || '',
        cnpj: conta.cnpj || '',
        inscricao_estadual: conta.inscricao_estadual || '',
        segmento: conta.segmento || '',
        telefone: conta.telefone || '',
        email: conta.email || '',
        site: conta.site || '',
        cep: conta.cep || '',
        logradouro: conta.logradouro || '',
        numero: conta.numero || '',
        complemento: conta.complemento || '',
        bairro: conta.bairro || '',
        cidade: conta.cidade || '',
        uf: conta.uf || '',
        observacoes: conta.observacoes || '',
      });
    } else if (type === 'create') {
      setFormData({
        nome: '',
        razao_social: '',
        cnpj: '',
        inscricao_estadual: '',
        segmento: '',
        telefone: '',
        email: '',
        site: '',
        cep: '',
        logradouro: '',
        numero: '',
        complemento: '',
        bairro: '',
        cidade: '',
        uf: '',
        observacoes: '',
      });
    }
  };

  const closeModal = () => {
    setModalType(null);
    setSelectedConta(null);
    setFormData({
      nome: '',
      razao_social: '',
      cnpj: '',
      inscricao_estadual: '',
      segmento: '',
      telefone: '',
      email: '',
      site: '',
      cep: '',
      logradouro: '',
      numero: '',
      complemento: '',
      bairro: '',
      cidade: '',
      uf: '',
      observacoes: '',
    });
  };

  // Consultar CNPJ na API da Receita Federal
  const consultarCNPJ = async () => {
    const cnpjLimpo = formData.cnpj.replace(/\D/g, '');
    
    if (cnpjLimpo.length !== 14) {
      alert('CNPJ inválido. Digite 14 dígitos.');
      return;
    }

    try {
      setConsultingCNPJ(true);
      const response = await fetch(`https://brasilapi.com.br/api/cnpj/v1/${cnpjLimpo}`);
      
      if (!response.ok) {
        throw new Error('CNPJ não encontrado');
      }

      const data = await response.json();
      
      setFormData({
        ...formData,
        razao_social: data.razao_social || '',
        nome: data.nome_fantasia || data.razao_social || formData.nome,
        telefone: data.ddd_telefone_1 ? `(${data.ddd_telefone_1.substring(0, 2)}) ${data.ddd_telefone_1.substring(2)}` : formData.telefone,
        email: data.email || formData.email,
        cep: data.cep || '',
        logradouro: data.logradouro || '',
        numero: data.numero || '',
        complemento: data.complemento || '',
        bairro: data.bairro || '',
        cidade: data.municipio || '',
        uf: data.uf || '',
      });
      
      alert('Dados da empresa carregados com sucesso!');
    } catch (error) {
      alert('Erro ao consultar CNPJ. Verifique o número e tente novamente.');
    } finally {
      setConsultingCNPJ(false);
    }
  };

  // Consultar CEP na API ViaCEP
  const consultarCEP = async () => {
    const cepLimpo = formData.cep.replace(/\D/g, '');
    
    if (cepLimpo.length !== 8) {
      alert('CEP inválido. Digite 8 dígitos.');
      return;
    }

    try {
      const response = await fetch(`https://viacep.com.br/ws/${cepLimpo}/json/`);
      const data = await response.json();
      
      if (data.erro) {
        throw new Error('CEP não encontrado');
      }

      setFormData({
        ...formData,
        logradouro: data.logradouro || formData.logradouro,
        bairro: data.bairro || formData.bairro,
        cidade: data.localidade || formData.cidade,
        uf: data.uf || formData.uf,
      });
    } catch (error) {
      alert('Erro ao consultar CEP. Verifique o número e tente novamente.');
    }
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

  const handleCriarOportunidade = async () => {
    if (!selectedConta) return;
    
    try {
      setCreatingOpportunity(true);
      
      // Criar Lead vinculado à Conta
      const leadResponse = await apiClient.post('/crm-vendas/leads/', {
        nome: selectedConta.nome,
        empresa: selectedConta.nome,
        email: selectedConta.email || '',
        telefone: selectedConta.telefone || '',
        origem: 'site',
        status: 'qualificado',
        conta_id: selectedConta.id,
        cpf_cnpj: selectedConta.cnpj || '',
        cep: selectedConta.cep || '',
        logradouro: selectedConta.logradouro || '',
        numero: selectedConta.numero || '',
        complemento: selectedConta.complemento || '',
        bairro: selectedConta.bairro || '',
        cidade: selectedConta.cidade || '',
        uf: selectedConta.uf || '',
      });
      
      // Redirecionar para pipeline com modal de criar oportunidade
      router.push(`/loja/${slug}/crm-vendas/pipeline?novo=1&lead_id=${leadResponse.data.id}`);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Erro ao criar oportunidade.');
      setCreatingOpportunity(false);
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
                    {/* CNPJ e Consulta */}
                    <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg border border-blue-200 dark:border-blue-800">
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="md:col-span-2">
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                            CNPJ
                          </label>
                          <input
                            type="text"
                            value={formData.cnpj}
                            onChange={(e) => setFormData({ ...formData, cnpj: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-[#0176d3] focus:border-transparent"
                            placeholder="00.000.000/0000-00"
                            maxLength={18}
                          />
                        </div>
                        <div className="flex items-end">
                          <button
                            type="button"
                            onClick={consultarCNPJ}
                            disabled={consultingCNPJ || !formData.cnpj}
                            className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                          >
                            {consultingCNPJ ? 'Consultando...' : 'Consultar CNPJ'}
                          </button>
                        </div>
                      </div>
                      <p className="text-xs text-blue-700 dark:text-blue-300 mt-2">
                        💡 Digite o CNPJ e clique em "Consultar CNPJ" para preencher automaticamente os dados da empresa
                      </p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* Dados da Empresa */}
                      <div className="md:col-span-2">
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Razão Social
                        </label>
                        <input
                          type="text"
                          value={formData.razao_social}
                          onChange={(e) => setFormData({ ...formData, razao_social: e.target.value })}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-[#0176d3] focus:border-transparent"
                        />
                      </div>

                      <div className="md:col-span-2">
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Nome Fantasia <span className="text-red-500">*</span>
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
                          Inscrição Estadual
                        </label>
                        <input
                          type="text"
                          value={formData.inscricao_estadual}
                          onChange={(e) => setFormData({ ...formData, inscricao_estadual: e.target.value })}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-[#0176d3] focus:border-transparent"
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
                          placeholder="Ex: Tecnologia, Varejo, Serviços"
                        />
                      </div>

                      {/* Contato */}
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Telefone
                        </label>
                        <input
                          type="tel"
                          value={formData.telefone}
                          onChange={(e) => setFormData({ ...formData, telefone: e.target.value })}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-[#0176d3] focus:border-transparent"
                          placeholder="(00) 00000-0000"
                        />
                      </div>

                      <div>
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
                          Site
                        </label>
                        <input
                          type="url"
                          value={formData.site}
                          onChange={(e) => setFormData({ ...formData, site: e.target.value })}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-[#0176d3] focus:border-transparent"
                          placeholder="https://exemplo.com.br"
                        />
                      </div>

                      {/* Endereço */}
                      <div className="md:col-span-2">
                        <hr className="border-gray-200 dark:border-gray-700 my-2" />
                        <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">Endereço</h3>
                      </div>

                      <div className="md:col-span-1">
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          CEP
                        </label>
                        <div className="flex gap-2">
                          <input
                            type="text"
                            value={formData.cep}
                            onChange={(e) => setFormData({ ...formData, cep: e.target.value })}
                            onBlur={consultarCEP}
                            className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-[#0176d3] focus:border-transparent"
                            placeholder="00000-000"
                            maxLength={9}
                          />
                        </div>
                      </div>

                      <div className="md:col-span-1">
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          UF
                        </label>
                        <input
                          type="text"
                          value={formData.uf}
                          onChange={(e) => setFormData({ ...formData, uf: e.target.value.toUpperCase() })}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-[#0176d3] focus:border-transparent"
                          placeholder="SP"
                          maxLength={2}
                        />
                      </div>

                      <div className="md:col-span-2">
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Logradouro
                        </label>
                        <input
                          type="text"
                          value={formData.logradouro}
                          onChange={(e) => setFormData({ ...formData, logradouro: e.target.value })}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-[#0176d3] focus:border-transparent"
                          placeholder="Rua, Avenida, etc."
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Número
                        </label>
                        <input
                          type="text"
                          value={formData.numero}
                          onChange={(e) => setFormData({ ...formData, numero: e.target.value })}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-[#0176d3] focus:border-transparent"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Complemento
                        </label>
                        <input
                          type="text"
                          value={formData.complemento}
                          onChange={(e) => setFormData({ ...formData, complemento: e.target.value })}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-[#0176d3] focus:border-transparent"
                          placeholder="Apto, Sala, etc."
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Bairro
                        </label>
                        <input
                          type="text"
                          value={formData.bairro}
                          onChange={(e) => setFormData({ ...formData, bairro: e.target.value })}
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

                      {/* Observações */}
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

                      {(selectedConta.cidade || selectedConta.uf) && (
                        <div className="flex items-start gap-2">
                          <MapPin size={18} className="text-gray-400 mt-0.5" />
                          <div>
                            <p className="text-xs text-gray-500 dark:text-gray-400">Localização</p>
                            <p className="text-sm text-gray-900 dark:text-white">
                              {[selectedConta.cidade, selectedConta.uf].filter(Boolean).join(' - ')}
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
                        onClick={handleCriarOportunidade}
                        className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded transition-colors disabled:opacity-50 flex items-center gap-2"
                        disabled={creatingOpportunity}
                      >
                        <Plus size={16} />
                        {creatingOpportunity ? 'Criando...' : 'Criar Oportunidade'}
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
