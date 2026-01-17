'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { authService } from '@/lib/auth';

interface TipoLoja {
  id: number;
  nome: string;
  slug: string;
  descricao: string;
  dashboard_template: string;
  cor_primaria: string;
  cor_secundaria: string;
  tem_produtos: boolean;
  tem_servicos: boolean;
  tem_agendamento: boolean;
  tem_delivery: boolean;
  tem_estoque: boolean;
  total_lojas: number;
  created_at: string;
}

export default function TiposLojaPage() {
  const router = useRouter();
  const [tipos, setTipos] = useState<TipoLoja[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingTipo, setEditingTipo] = useState<TipoLoja | null>(null);

  useEffect(() => {
    if (typeof window !== 'undefined' && authService.getUserType() !== 'superadmin') {
      router.push('/superadmin/login');
      return;
    }
    loadTipos();
  }, [router]);

  const loadTipos = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/superadmin/tipos-loja/');
      const data = response.data.results || response.data;
      setTipos(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Erro ao carregar tipos de loja:', error);
      setTipos([]);
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (tipo: TipoLoja) => {
    setEditingTipo(tipo);
    setShowModal(true);
  };

  const handleDelete = async (tipo: TipoLoja) => {
    if (tipo.total_lojas > 0) {
      alert('Não é possível excluir um tipo de loja que possui lojas associadas.');
      return;
    }

    if (!confirm(`Tem certeza que deseja excluir o tipo "${tipo.nome}"?`)) {
      return;
    }

    try {
      await apiClient.delete(`/superadmin/tipos-loja/${tipo.id}/`);
      alert('Tipo de loja excluído com sucesso!');
      loadTipos();
    } catch (error: any) {
      console.error('Erro ao excluir tipo de loja:', error);
      alert(`Erro ao excluir: ${error.response?.data?.error || 'Erro desconhecido'}`);
    }
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setEditingTipo(null);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <nav className="bg-purple-900 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center space-x-4">
              <a href="/superadmin/dashboard" className="text-purple-200 hover:text-white">
                ← Voltar
              </a>
              <h1 className="text-2xl font-bold">Tipos de Loja</h1>
            </div>
            <button
              onClick={() => setShowModal(true)}
              className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-md transition-colors"
            >
              + Novo Tipo
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {loading ? (
            <div className="text-center py-12">Carregando...</div>
          ) : tipos.length === 0 ? (
            <div className="text-center py-12 bg-white rounded-lg shadow">
              <p className="text-gray-500 mb-4">Nenhum tipo de loja cadastrado ainda.</p>
              <button
                onClick={() => setShowModal(true)}
                className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700"
              >
                Criar Primeiro Tipo
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {Array.isArray(tipos) && tipos.map((tipo) => (
                <div
                  key={tipo.id}
                  className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow"
                >
                  {/* Header do Card */}
                  <div 
                    className="h-20 flex items-center justify-center"
                    style={{ backgroundColor: tipo.cor_primaria }}
                  >
                    <h3 className="text-xl font-bold text-white">{tipo.nome}</h3>
                  </div>

                  {/* Conteúdo do Card */}
                  <div className="p-6">
                    <p className="text-gray-600 mb-4">{tipo.descricao}</p>
                    
                    {/* Estatísticas */}
                    <div className="mb-4">
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-sm text-gray-500">Lojas usando:</span>
                        <span className="font-semibold text-purple-600">{tipo.total_lojas}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-500">Template:</span>
                        <span className="text-sm font-medium">{tipo.dashboard_template}</span>
                      </div>
                    </div>

                    {/* Funcionalidades */}
                    <div className="mb-4">
                      <h4 className="text-sm font-medium text-gray-700 mb-2">Funcionalidades:</h4>
                      <div className="flex flex-wrap gap-1">
                        {tipo.tem_produtos && (
                          <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded">
                            Produtos
                          </span>
                        )}
                        {tipo.tem_servicos && (
                          <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                            Serviços
                          </span>
                        )}
                        {tipo.tem_agendamento && (
                          <span className="px-2 py-1 bg-purple-100 text-purple-800 text-xs rounded">
                            Agendamento
                          </span>
                        )}
                        {tipo.tem_delivery && (
                          <span className="px-2 py-1 bg-orange-100 text-orange-800 text-xs rounded">
                            Delivery
                          </span>
                        )}
                        {tipo.tem_estoque && (
                          <span className="px-2 py-1 bg-gray-100 text-gray-800 text-xs rounded">
                            Estoque
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Cores */}
                    <div className="mb-4">
                      <h4 className="text-sm font-medium text-gray-700 mb-2">Cores:</h4>
                      <div className="flex space-x-2">
                        <div className="flex items-center space-x-1">
                          <div
                            className="w-4 h-4 rounded-full border"
                            style={{ backgroundColor: tipo.cor_primaria }}
                          />
                          <span className="text-xs text-gray-500">Primária</span>
                        </div>
                        <div className="flex items-center space-x-1">
                          <div
                            className="w-4 h-4 rounded-full border"
                            style={{ backgroundColor: tipo.cor_secundaria }}
                          />
                          <span className="text-xs text-gray-500">Secundária</span>
                        </div>
                      </div>
                    </div>

                    {/* Ações */}
                    <div className="flex justify-between items-center pt-4 border-t">
                      <span className="text-xs text-gray-400">
                        {new Date(tipo.created_at).toLocaleDateString('pt-BR')}
                      </span>
                      <div className="space-x-2">
                        <button 
                          onClick={() => handleEdit(tipo)}
                          className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                        >
                          Editar
                        </button>
                        {tipo.total_lojas === 0 && (
                          <button 
                            onClick={() => handleDelete(tipo)}
                            className="text-red-600 hover:text-red-800 text-sm font-medium"
                          >
                            Excluir
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>

      {/* Modal Novo Tipo */}
      {showModal && (
        <NovoTipoModal 
          onClose={handleCloseModal} 
          onSuccess={loadTipos}
          editingTipo={editingTipo}
        />
      )}
    </div>
  );
}

// Componente do Modal
function NovoTipoModal({ 
  onClose, 
  onSuccess,
  editingTipo 
}: { 
  onClose: () => void; 
  onSuccess: () => void;
  editingTipo?: TipoLoja | null;
}) {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    nome: editingTipo?.nome || '',
    slug: editingTipo?.slug || '',
    descricao: editingTipo?.descricao || '',
    dashboard_template: editingTipo?.dashboard_template || 'default',
    cor_primaria: editingTipo?.cor_primaria || '#10B981',
    cor_secundaria: editingTipo?.cor_secundaria || '#059669',
    tem_produtos: editingTipo?.tem_produtos ?? true,
    tem_servicos: editingTipo?.tem_servicos ?? false,
    tem_agendamento: editingTipo?.tem_agendamento ?? false,
    tem_delivery: editingTipo?.tem_delivery ?? false,
    tem_estoque: editingTipo?.tem_estoque ?? true,
  });

  const isEditing = !!editingTipo;

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    
    if (type === 'checkbox') {
      const checked = (e.target as HTMLInputElement).checked;
      setFormData(prev => ({ ...prev, [name]: checked }));
    } else {
      setFormData(prev => ({ ...prev, [name]: value }));
    }
    
    // Auto-gerar slug a partir do nome
    if (name === 'nome') {
      const slug = value.toLowerCase()
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/(^-|-$)/g, '');
      setFormData(prev => ({ ...prev, slug }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      if (isEditing && editingTipo) {
        // Atualizar tipo existente
        await apiClient.put(`/superadmin/tipos-loja/${editingTipo.id}/`, formData);
        alert('Tipo de loja atualizado com sucesso!');
      } else {
        // Criar novo tipo
        await apiClient.post('/superadmin/tipos-loja/', formData);
        alert('Tipo de loja criado com sucesso!');
      }
      onSuccess();
      onClose();
    } catch (error: any) {
      console.error('Erro ao salvar tipo de loja:', error);
      alert(`Erro: ${error.response?.data?.error || JSON.stringify(error.response?.data) || 'Erro ao salvar tipo'}`);
    } finally {
      setLoading(false);
    }
  };

  const coresPreDefinidas = [
    { nome: 'Verde', primaria: '#10B981', secundaria: '#059669' },
    { nome: 'Azul', primaria: '#3B82F6', secundaria: '#2563EB' },
    { nome: 'Vermelho', primaria: '#EF4444', secundaria: '#DC2626' },
    { nome: 'Roxo', primaria: '#8B5CF6', secundaria: '#7C3AED' },
    { nome: 'Laranja', primaria: '#F97316', secundaria: '#EA580C' },
    { nome: 'Rosa', primaria: '#EC4899', secundaria: '#DB2777' },
  ];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg p-8 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <h2 className="text-2xl font-bold mb-6 text-purple-900">
          {isEditing ? 'Editar Tipo de Loja' : 'Novo Tipo de Loja'}
        </h2>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Informações Básicas */}
          <div>
            <h3 className="text-lg font-semibold mb-4 text-gray-700">Informações Básicas</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nome do Tipo *
                </label>
                <input
                  type="text"
                  name="nome"
                  value={formData.nome}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500"
                  placeholder="Ex: E-commerce"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Slug *
                </label>
                <input
                  type="text"
                  name="slug"
                  value={formData.slug}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500"
                  placeholder="e-commerce"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Descrição *
                </label>
                <textarea
                  name="descricao"
                  value={formData.descricao}
                  onChange={handleChange}
                  required
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500"
                  placeholder="Descrição do tipo de loja..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Template do Dashboard
                </label>
                <select
                  name="dashboard_template"
                  value={formData.dashboard_template}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500"
                >
                  <option value="default">Padrão</option>
                  <option value="ecommerce">E-commerce</option>
                  <option value="servicos">Serviços</option>
                  <option value="restaurante">Restaurante</option>
                </select>
              </div>
            </div>
          </div>

          {/* Cores */}
          <div>
            <h3 className="text-lg font-semibold mb-4 text-gray-700">Cores do Tema</h3>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Cores Pré-definidas
              </label>
              <div className="grid grid-cols-3 gap-2">
                {coresPreDefinidas.map((cor) => (
                  <button
                    key={cor.nome}
                    type="button"
                    onClick={() => setFormData(prev => ({
                      ...prev,
                      cor_primaria: cor.primaria,
                      cor_secundaria: cor.secundaria
                    }))}
                    className={`p-3 rounded-lg border-2 transition-all ${
                      formData.cor_primaria === cor.primaria
                        ? 'border-purple-600 bg-purple-50'
                        : 'border-gray-200 hover:border-purple-300'
                    }`}
                  >
                    <div className="flex items-center space-x-2">
                      <div
                        className="w-6 h-6 rounded-full"
                        style={{ backgroundColor: cor.primaria }}
                      />
                      <span className="text-sm font-medium">{cor.nome}</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Cor Primária
                </label>
                <div className="flex space-x-2">
                  <input
                    type="color"
                    name="cor_primaria"
                    value={formData.cor_primaria}
                    onChange={handleChange}
                    className="w-12 h-10 border border-gray-300 rounded"
                  />
                  <input
                    type="text"
                    value={formData.cor_primaria}
                    onChange={(e) => setFormData(prev => ({ ...prev, cor_primaria: e.target.value }))}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500"
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Cor Secundária
                </label>
                <div className="flex space-x-2">
                  <input
                    type="color"
                    name="cor_secundaria"
                    value={formData.cor_secundaria}
                    onChange={handleChange}
                    className="w-12 h-10 border border-gray-300 rounded"
                  />
                  <input
                    type="text"
                    value={formData.cor_secundaria}
                    onChange={(e) => setFormData(prev => ({ ...prev, cor_secundaria: e.target.value }))}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Funcionalidades */}
          <div>
            <h3 className="text-lg font-semibold mb-4 text-gray-700">Funcionalidades</h3>
            <div className="grid grid-cols-2 gap-4">
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  name="tem_produtos"
                  checked={formData.tem_produtos}
                  onChange={handleChange}
                  className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                />
                <span className="text-sm">Produtos</span>
              </label>

              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  name="tem_servicos"
                  checked={formData.tem_servicos}
                  onChange={handleChange}
                  className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                />
                <span className="text-sm">Serviços</span>
              </label>

              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  name="tem_agendamento"
                  checked={formData.tem_agendamento}
                  onChange={handleChange}
                  className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                />
                <span className="text-sm">Agendamento</span>
              </label>

              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  name="tem_delivery"
                  checked={formData.tem_delivery}
                  onChange={handleChange}
                  className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                />
                <span className="text-sm">Delivery</span>
              </label>

              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  name="tem_estoque"
                  checked={formData.tem_estoque}
                  onChange={handleChange}
                  className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                />
                <span className="text-sm">Controle de Estoque</span>
              </label>
            </div>
          </div>

          {/* Preview */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="text-lg font-semibold mb-3 text-gray-700">Preview</h3>
            <div 
              className="h-16 rounded-lg flex items-center justify-center mb-2"
              style={{ backgroundColor: formData.cor_primaria }}
            >
              <span className="text-white font-bold">{formData.nome || 'Nome do Tipo'}</span>
            </div>
            <p className="text-sm text-gray-600">{formData.descricao || 'Descrição do tipo...'}</p>
          </div>

          {/* Botões */}
          <div className="flex justify-end space-x-4 pt-4">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="px-6 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 disabled:opacity-50"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (isEditing ? 'Salvando...' : 'Criando...') : (isEditing ? 'Salvar Alterações' : 'Criar Tipo')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}