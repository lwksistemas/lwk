'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { normalizeListResponse } from '@/lib/crm-utils';
import { Plus, Eye, Edit2, Trash2, X, Package, Tag } from 'lucide-react';
import SkeletonTable from '@/components/crm-vendas/SkeletonTable';

interface Categoria {
  id: number;
  nome: string;
  cor: string;
  ordem: number;
}

interface ProdutoServico {
  id: number;
  tipo: 'produto' | 'servico';
  codigo: string;
  nome: string;
  descricao: string;
  categoria: number | null;
  categoria_nome?: string;
  categoria_cor?: string;
  preco: string;
  ativo: boolean;
  created_at: string;
}

type ModalType = 'create' | 'edit' | 'view' | 'delete' | null;

export default function CrmVendasProdutosServicosPage() {
  const params = useParams();
  const slug = (params?.slug as string) ?? '';
  const [itens, setItens] = useState<ProdutoServico[]>([]);
  const [categorias, setCategorias] = useState<Categoria[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalType, setModalType] = useState<ModalType>(null);
  const [selected, setSelected] = useState<ProdutoServico | null>(null);
  const [filtroTipo, setFiltroTipo] = useState<string>('');
  const [filtroCategoria, setFiltroCategoria] = useState<string>('');
  const [formData, setFormData] = useState({
    tipo: 'produto' as 'produto' | 'servico',
    codigo: '',
    nome: '',
    descricao: '',
    categoria: null as number | null,
    preco: '0',
    ativo: true,
  });
  const [submitting, setSubmitting] = useState(false);

  const loadCategorias = useCallback(async () => {
    try {
      const res = await apiClient.get<Categoria[] | { results: Categoria[] }>('/crm-vendas/categorias-produtos-servicos/?ativo=true');
      setCategorias(normalizeListResponse(res.data));
    } catch (err) {
      console.error('Erro ao carregar categorias:', err);
      setCategorias([]);
    }
  }, []);

  const loadItens = useCallback(async () => {
    try {
      setLoading(true);
      const params: Record<string, string> = {};
      if (filtroTipo) params.tipo = filtroTipo;
      if (filtroCategoria) params.categoria = filtroCategoria;
      const query = new URLSearchParams(params).toString();
      const url = query ? `/crm-vendas/produtos-servicos/?${query}` : '/crm-vendas/produtos-servicos/';
      const res = await apiClient.get<ProdutoServico[] | { results: ProdutoServico[] }>(url);
      setItens(normalizeListResponse(res.data));
      setError(null);
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      setError(e.response?.data?.detail || 'Erro ao carregar produtos e serviços.');
    } finally {
      setLoading(false);
    }
  }, [filtroTipo, filtroCategoria]);

  useEffect(() => {
    loadCategorias();
    loadItens();
  }, [loadCategorias, loadItens]);

  const openModal = (type: ModalType, item?: ProdutoServico) => {
    setModalType(type);
    setSelected(item || null);
    if (type === 'edit' && item) {
      setFormData({
        tipo: item.tipo,
        codigo: item.codigo || '',
        nome: item.nome || '',
        descricao: item.descricao || '',
        categoria: item.categoria || null,
        preco: item.preco || '0',
        ativo: item.ativo ?? true,
      });
    } else if (type === 'create') {
      setFormData({
        tipo: 'produto',
        codigo: '',
        nome: '',
        descricao: '',
        categoria: null,
        preco: '0',
        ativo: true,
      });
    }
  };

  const closeModal = () => {
    setModalType(null);
    setSelected(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.nome.trim()) {
      alert('Nome é obrigatório');
      return;
    }
    try {
      setSubmitting(true);
      const payload = {
        ...formData,
        preco: parseFloat(formData.preco) || 0,
      };
      if (modalType === 'create') {
        await apiClient.post('/crm-vendas/produtos-servicos/', payload);
      } else if (modalType === 'edit' && selected) {
        await apiClient.put(`/crm-vendas/produtos-servicos/${selected.id}/`, payload);
      }
      await loadItens();
      closeModal();
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      alert(e.response?.data?.detail || 'Erro ao salvar.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!selected) return;
    try {
      setSubmitting(true);
      await apiClient.delete(`/crm-vendas/produtos-servicos/${selected.id}/`);
      await loadItens();
      closeModal();
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      alert(e.response?.data?.detail || 'Erro ao excluir.');
    } finally {
      setSubmitting(false);
    }
  };

  const formatPreco = (v: string) => {
    const n = parseFloat(v);
    return isNaN(n) ? 'R$ 0,00' : n.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-48 animate-pulse" />
          <div className="h-10 bg-gray-200 dark:bg-gray-700 rounded w-40 animate-pulse" />
        </div>
        <SkeletonTable rows={5} columns={5} />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Cadastrar Serviço e Produto
          </h1>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Produtos e serviços disponíveis para incluir em novas oportunidades
          </p>
        </div>
        <div className="flex gap-2">
          <select
            value={filtroCategoria}
            onChange={(e) => setFiltroCategoria(e.target.value)}
            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
          >
            <option value="">Todas categorias</option>
            {categorias.map((cat) => (
              <option key={cat.id} value={cat.id}>
                {cat.nome}
              </option>
            ))}
          </select>
          <select
            value={filtroTipo}
            onChange={(e) => setFiltroTipo(e.target.value)}
            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
          >
            <option value="">Todos tipos</option>
            <option value="produto">Produtos</option>
            <option value="servico">Serviços</option>
          </select>
          <button
            type="button"
            onClick={() => openModal('create')}
            className="flex items-center gap-2 px-4 py-2 bg-[#0176d3] hover:bg-[#0159a8] text-white rounded text-sm font-medium transition-colors shadow-sm"
          >
            <Plus size={18} />
            <span>Novo</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 dark:bg-red-900/20 p-4 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-800">
          {error}
        </div>
      )}

      <div className="bg-white dark:bg-[#16325c] rounded-lg shadow border border-gray-200 dark:border-[#0d1f3c] overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[500px]">
            <thead>
              <tr className="border-b border-gray-200 dark:border-[#0d1f3c] bg-gray-50 dark:bg-[#0d1f3c]/50">
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                  Código
                </th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                  Categoria
                </th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                  Nome
                </th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                  Tipo
                </th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                  Preço
                </th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                  Status
                </th>
                <th className="text-right py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                  Ações
                </th>
              </tr>
            </thead>
            <tbody>
              {itens.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-gray-500 dark:text-gray-400">
                    <Package size={48} className="mx-auto mb-3 opacity-30" />
                    <p className="font-medium">Nenhum produto ou serviço cadastrado</p>
                    <p className="text-sm mt-1">Clique em &quot;Novo&quot; para cadastrar</p>
                  </td>
                </tr>
              ) : (
                itens.map((item) => (
                  <tr
                    key={item.id}
                    className="border-b border-gray-100 dark:border-[#0d1f3c] hover:bg-gray-50 dark:hover:bg-[#0d1f3c]/30 transition-colors"
                  >
                    <td className="py-3 px-4 text-gray-700 dark:text-gray-300 font-mono text-sm">
                      {item.codigo || '-'}
                    </td>
                    <td className="py-3 px-4">
                      {item.categoria_nome ? (
                        <span
                          className="inline-block px-2 py-0.5 rounded text-xs font-medium text-white"
                          style={{ backgroundColor: item.categoria_cor || '#6B7280' }}
                        >
                          {item.categoria_nome}
                        </span>
                      ) : (
                        <span className="text-gray-400 text-xs">Sem categoria</span>
                      )}
                    </td>
                    <td className="py-3 px-4 font-medium text-gray-900 dark:text-white">
                      {item.nome}
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${
                          item.tipo === 'produto'
                            ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200'
                            : 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200'
                        }`}
                      >
                        <Tag size={12} />
                        {item.tipo === 'produto' ? 'Produto' : 'Serviço'}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-gray-700 dark:text-gray-300">
                      {formatPreco(item.preco)}
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`inline-block px-2 py-0.5 rounded text-xs ${
                          item.ativo
                            ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
                            : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
                        }`}
                      >
                        {item.ativo ? 'Ativo' : 'Inativo'}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center justify-end gap-1">
                        <button
                          type="button"
                          onClick={() => openModal('view', item)}
                          className="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-600 dark:text-gray-300"
                          title="Visualizar"
                        >
                          <Eye size={16} />
                        </button>
                        <button
                          type="button"
                          onClick={() => openModal('edit', item)}
                          className="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-600 dark:text-gray-300"
                          title="Editar"
                        >
                          <Edit2 size={16} />
                        </button>
                        <button
                          type="button"
                          onClick={() => openModal('delete', item)}
                          className="p-1.5 rounded hover:bg-red-100 dark:hover:bg-red-900/30 text-red-600 dark:text-red-400"
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

      {/* Modal */}
      {modalType && (
        <>
          <div className="fixed inset-0 bg-black/50 z-[80]" onClick={closeModal} />
          <div className="fixed inset-0 z-[81] flex items-center justify-center p-4">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
              <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                  {modalType === 'create' && 'Novo Produto/Serviço'}
                  {modalType === 'edit' && 'Editar'}
                  {modalType === 'view' && 'Detalhes'}
                  {modalType === 'delete' && 'Excluir'}
                </h2>
                <button type="button" onClick={closeModal} className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700">
                  <X size={20} />
                </button>
              </div>
              <div className="p-6">
                {(modalType === 'create' || modalType === 'edit') && (
                  <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Tipo *</label>
                      <select
                        value={formData.tipo}
                        onChange={(e) => setFormData((f) => ({ ...f, tipo: e.target.value as 'produto' | 'servico' }))}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
                      >
                        <option value="produto">Produto</option>
                        <option value="servico">Serviço</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Código</label>
                      <input
                        type="text"
                        value={formData.codigo}
                        onChange={(e) => setFormData((f) => ({ ...f, codigo: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
                        placeholder="Ex: PROD-001 (opcional)"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Categoria</label>
                      <select
                        value={formData.categoria || ''}
                        onChange={(e) => setFormData((f) => ({ ...f, categoria: e.target.value ? parseInt(e.target.value) : null }))}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
                      >
                        <option value="">Sem categoria</option>
                        {categorias.map((cat) => (
                          <option key={cat.id} value={cat.id}>
                            {cat.nome}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nome *</label>
                      <input
                        type="text"
                        value={formData.nome}
                        onChange={(e) => setFormData((f) => ({ ...f, nome: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
                        placeholder="Ex: Consultoria"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Descrição</label>
                      <textarea
                        value={formData.descricao}
                        onChange={(e) => setFormData((f) => ({ ...f, descricao: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
                        rows={2}
                        placeholder="Descrição opcional"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Preço (R$)</label>
                      <input
                        type="number"
                        min="0"
                        step="0.01"
                        value={formData.preco}
                        onChange={(e) => setFormData((f) => ({ ...f, preco: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
                      />
                    </div>
                    {(modalType === 'edit') && (
                      <div className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          id="ativo"
                          checked={formData.ativo}
                          onChange={(e) => setFormData((f) => ({ ...f, ativo: e.target.checked }))}
                          className="rounded"
                        />
                        <label htmlFor="ativo" className="text-sm text-gray-700 dark:text-gray-300">Ativo</label>
                      </div>
                    )}
                    <div className="flex gap-2 pt-2">
                      <button type="button" onClick={closeModal} className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg">
                        Cancelar
                      </button>
                      <button type="submit" disabled={submitting} className="flex-1 px-4 py-2 bg-[#0176d3] hover:bg-[#0159a8] text-white rounded-lg disabled:opacity-50">
                        {submitting ? 'Salvando...' : 'Salvar'}
                      </button>
                    </div>
                  </form>
                )}
                {modalType === 'view' && selected && (
                  <div className="space-y-3">
                    <p><span className="font-medium">Tipo:</span> {selected.tipo === 'produto' ? 'Produto' : 'Serviço'}</p>
                    {selected.codigo && <p><span className="font-medium">Código:</span> {selected.codigo}</p>}
                    {selected.categoria_nome && (
                      <p>
                        <span className="font-medium">Categoria:</span>{' '}
                        <span
                          className="inline-block px-2 py-0.5 rounded text-xs font-medium text-white ml-1"
                          style={{ backgroundColor: selected.categoria_cor || '#6B7280' }}
                        >
                          {selected.categoria_nome}
                        </span>
                      </p>
                    )}
                    <p><span className="font-medium">Nome:</span> {selected.nome}</p>
                    <p><span className="font-medium">Preço:</span> {formatPreco(selected.preco)}</p>
                    <p><span className="font-medium">Status:</span> {selected.ativo ? 'Ativo' : 'Inativo'}</p>
                    {selected.descricao && <p><span className="font-medium">Descrição:</span> {selected.descricao}</p>}
                    <button type="button" onClick={closeModal} className="w-full mt-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg">
                      Fechar
                    </button>
                  </div>
                )}
                {modalType === 'delete' && selected && (
                  <div className="space-y-4">
                    <p className="text-gray-600 dark:text-gray-400">
                      Deseja excluir &quot;{selected.nome}&quot;? Esta ação não pode ser desfeita.
                    </p>
                    <div className="flex gap-2">
                      <button type="button" onClick={closeModal} className="flex-1 px-4 py-2 border rounded-lg">
                        Cancelar
                      </button>
                      <button type="button" onClick={handleDelete} disabled={submitting} className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg disabled:opacity-50">
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
