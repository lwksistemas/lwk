'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { authService } from '@/lib/auth';
import { ModalNovoPlano } from '@/components/superadmin/planos';

interface TipoLoja {
  id: number;
  nome: string;
  cor_primaria: string;
}

interface Plano {
  id: number;
  nome: string;
  slug: string;
  descricao: string;
  preco_mensal: string;
  preco_anual: string;
  max_produtos: number;
  max_usuarios: number;
  max_pedidos_mes: number;
  espaco_storage_gb: number;
  tem_relatorios_avancados: boolean;
  tem_api_acesso: boolean;
  tem_suporte_prioritario: boolean;
  tem_dominio_customizado: boolean;
  tem_whatsapp_integration: boolean;
  is_active: boolean;
  ordem: number;
  total_lojas: number;
  tipos_loja_nomes: string[];
  created_at: string;
}

export default function PlanosPage() {
  const router = useRouter();
  const [planos, setPlanos] = useState<Plano[]>([]);
  const [tipos, setTipos] = useState<TipoLoja[]>([]);
  const [tipoSelecionado, setTipoSelecionado] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [viewMode, setViewMode] = useState<'tipos' | 'planos'>('tipos');
  const [editingPlano, setEditingPlano] = useState<Plano | null>(null);

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
      console.error('Erro ao carregar tipos:', error);
      setTipos([]);
    } finally {
      setLoading(false);
    }
  };

  const loadPlanosPorTipo = async (tipoId: number) => {
    try {
      setLoading(true);
      const response = await apiClient.get(`/superadmin/planos/por_tipo/?tipo_id=${tipoId}`);
      setPlanos(response.data);
      setTipoSelecionado(tipoId);
      setViewMode('planos');
    } catch (error) {
      console.error('Erro ao carregar planos:', error);
      setPlanos([]);
    } finally {
      setLoading(false);
    }
  };

  const voltarParaTipos = () => {
    setViewMode('tipos');
    setTipoSelecionado(null);
    setPlanos([]);
  };

  const handleEdit = (plano: Plano) => {
    setEditingPlano(plano);
    setShowModal(true);
  };

  const handleDelete = async (plano: Plano) => {
    if (plano.total_lojas > 0) {
      alert('Não é possível excluir um plano que possui lojas associadas.');
      return;
    }

    if (!confirm(`Tem certeza que deseja excluir o plano "${plano.nome}"?`)) {
      return;
    }

    try {
      await apiClient.delete(`/superadmin/planos/${plano.id}/`);
      alert('Plano excluído com sucesso!');
      if (tipoSelecionado) {
        loadPlanosPorTipo(tipoSelecionado);
      }
    } catch (error: any) {
      console.error('Erro ao excluir plano:', error);
      alert(`Erro ao excluir: ${error.response?.data?.error || 'Erro desconhecido'}`);
    }
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setEditingPlano(null);
  };

  const formatPrice = (price: string) => {
    return parseFloat(price).toLocaleString('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    });
  };

  const getPlanoColor = (ordem: number) => {
    const colors = [
      'border-green-200 bg-green-50',
      'border-blue-200 bg-blue-50',
      'border-purple-200 bg-purple-50',
    ];
    return colors[ordem - 1] || colors[0];
  };

  const getPlanoBadgeColor = (ordem: number) => {
    const colors = [
      'bg-green-100 text-green-800',
      'bg-blue-100 text-blue-800',
      'bg-purple-100 text-purple-800',
    ];
    return colors[ordem - 1] || colors[0];
  };

  const getIconForType = (nome: string) => {
    switch (nome.toLowerCase()) {
      case 'e-commerce': return '🛒';
      case 'serviços': return '🔧';
      case 'restaurante': return '🍕';
      case 'clínica de estética': return '💅';
      case 'crm vendas': return '📊';
      default: return '🏪';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <nav className="bg-purple-900 text-white shadow-lg">
        <div className="w-full max-w-full px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center space-x-4">
              <a href="/superadmin/dashboard" className="text-purple-200 hover:text-white">
                ← Voltar
              </a>
              <h1 className="text-2xl font-bold">Planos de Assinatura</h1>
            </div>
            {viewMode === 'planos' && (
              <button
                onClick={() => setShowModal(true)}
                className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-md transition-colors"
              >
                + Novo Plano
              </button>
            )}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="w-full max-w-full py-6 px-4 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {loading ? (
            <div className="text-center py-12">Carregando...</div>
          ) : viewMode === 'tipos' ? (
            /* Visualização de Tipos de Loja */
            <div className="space-y-6">
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-2xl font-bold text-gray-900 mb-2">
                  Selecione um Tipo de Loja
                </h2>
                <p className="text-gray-600">
                  Escolha um tipo de loja para visualizar e gerenciar seus planos de assinatura
                </p>
              </div>

              {tipos.length === 0 ? (
                <div className="text-center py-12 bg-white rounded-lg shadow">
                  <p className="text-gray-500 mb-4">Nenhum tipo de loja cadastrado ainda.</p>
                  <a
                    href="/superadmin/tipos-loja"
                    className="inline-block px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700"
                  >
                    Criar Tipos de Loja
                  </a>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {tipos.map((tipo) => (
                    <button
                      key={tipo.id}
                      onClick={() => loadPlanosPorTipo(tipo.id)}
                      className="bg-white rounded-lg shadow-md hover:shadow-xl transition-all p-8 text-left border-2 border-transparent hover:border-purple-300"
                    >
                      <div className="flex items-center space-x-4 mb-4">
                        <div
                          className="w-16 h-16 rounded-full flex items-center justify-center text-3xl"
                          style={{ backgroundColor: tipo.cor_primaria + '20' }}
                        >
                          {getIconForType(tipo.nome)}
                        </div>
                        <div className="flex-1">
                          <h3 className="text-xl font-bold text-gray-900">{tipo.nome}</h3>
                          <div
                            className="w-12 h-1 rounded-full mt-2"
                            style={{ backgroundColor: tipo.cor_primaria }}
                          />
                        </div>
                      </div>
                      <div className="flex items-center justify-between text-sm text-gray-600">
                        <span>Ver planos disponíveis</span>
                        <span className="text-2xl">→</span>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          ) : (
            /* Visualização de Planos */
            <div className="space-y-6">
              {/* Header com breadcrumb */}
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <button
                      onClick={voltarParaTipos}
                      className="text-purple-600 hover:text-purple-800 mb-2 flex items-center space-x-2"
                    >
                      <span>←</span>
                      <span>Voltar para Tipos de Loja</span>
                    </button>
                    <h2 className="text-2xl font-bold text-gray-900 flex items-center space-x-3">
                      <span>{getIconForType(tipos.find(t => t.id === tipoSelecionado)?.nome || '')}</span>
                      <span>{tipos.find(t => t.id === tipoSelecionado)?.nome}</span>
                    </h2>
                    <p className="text-gray-600 mt-1">
                      {planos.length} plano(s) disponível(is)
                    </p>
                  </div>
                </div>
              </div>

              {/* Lista de Planos */}
              {planos.length === 0 ? (
                <div className="text-center py-12 bg-white rounded-lg shadow">
                  <p className="text-gray-500 mb-4">
                    Nenhum plano disponível para este tipo de loja.
                  </p>
                  <button
                    onClick={() => setShowModal(true)}
                    className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700"
                  >
                    Criar Primeiro Plano
                  </button>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {planos.map((plano) => (
                    <div
                      key={plano.id}
                      className={`bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow border-2 ${getPlanoColor(plano.ordem)}`}
                    >
                      {/* Header do Card */}
                      <div className="p-6 text-center">
                        <div className="flex justify-between items-start mb-2">
                          <span className={`px-2 py-1 text-xs rounded-full ${getPlanoBadgeColor(plano.ordem)}`}>
                            {plano.ordem === 1 ? 'Básico' : plano.ordem === 2 ? 'Intermediário' : 'Avançado'}
                          </span>
                          {!plano.is_active && (
                            <span className="px-2 py-1 text-xs rounded-full bg-red-100 text-red-800">
                              Inativo
                            </span>
                          )}
                        </div>
                        
                        <h3 className="text-xl font-bold text-gray-900 mb-2">{plano.nome}</h3>
                        <p className="text-gray-600 text-sm mb-4">{plano.descricao}</p>
                        
                        {/* Preços */}
                        <div className="mb-4">
                          <div className="text-3xl font-bold text-purple-600">
                            {formatPrice(plano.preco_mensal)}
                          </div>
                          <div className="text-sm text-gray-500">por mês</div>
                          {plano.preco_anual && parseFloat(plano.preco_anual) > 0 && (
                            <div className="text-sm text-green-600 mt-1">
                              ou {formatPrice(plano.preco_anual)}/ano
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Limites */}
                      <div className="px-6 pb-4">
                        <h4 className="text-sm font-medium text-gray-700 mb-3">Limites:</h4>
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-gray-600">Produtos:</span>
                            <span className="font-medium">
                              {plano.max_produtos === 999999 ? 'Ilimitado' : plano.max_produtos}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Usuários:</span>
                            <span className="font-medium">{plano.max_usuarios}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Pedidos/mês:</span>
                            <span className="font-medium">
                              {plano.max_pedidos_mes === 999999 ? 'Ilimitado' : plano.max_pedidos_mes}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Storage:</span>
                            <span className="font-medium">{plano.espaco_storage_gb}GB</span>
                          </div>
                        </div>
                      </div>

                      {/* Funcionalidades */}
                      <div className="px-6 pb-4">
                        <h4 className="text-sm font-medium text-gray-700 mb-3">Funcionalidades:</h4>
                        <div className="flex flex-wrap gap-1">
                          {plano.tem_relatorios_avancados && (
                            <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                              📊 Relatórios
                            </span>
                          )}
                          {plano.tem_api_acesso && (
                            <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded">
                              🔌 API
                            </span>
                          )}
                          {plano.tem_suporte_prioritario && (
                            <span className="px-2 py-1 bg-purple-100 text-purple-800 text-xs rounded">
                              ⭐ Suporte VIP
                            </span>
                          )}
                          {plano.tem_dominio_customizado && (
                            <span className="px-2 py-1 bg-orange-100 text-orange-800 text-xs rounded">
                              🌐 Domínio
                            </span>
                          )}
                          {plano.tem_whatsapp_integration && (
                            <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded">
                              💬 WhatsApp
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Estatísticas e Ações */}
                      <div className="px-6 pb-6">
                        <div className="flex justify-between items-center pt-4 border-t">
                          <div className="text-sm">
                            <div className="font-medium text-purple-600">{plano.total_lojas} lojas</div>
                            <div className="text-xs text-gray-500">
                              {new Date(plano.created_at).toLocaleDateString('pt-BR')}
                            </div>
                          </div>
                          <div className="space-x-2">
                            <button 
                              onClick={() => handleEdit(plano)}
                              className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                            >
                              Editar
                            </button>
                            {plano.total_lojas === 0 && (
                              <button 
                                onClick={() => handleDelete(plano)}
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
          )}
        </div>
      </main>

      {/* Modal Novo Plano */}
      {showModal && (
        <ModalNovoPlano 
          onClose={handleCloseModal} 
          onSuccess={() => loadPlanosPorTipo(tipoSelecionado!)}
          editingPlano={editingPlano}
        />
      )}
    </div>
  );
}
function NovoPlanoModal({ 
  onClose, 
  onSuccess,
  editingPlano 
}: { 
  onClose: () => void; 
  onSuccess: () => void;
  editingPlano?: Plano | null;
}) {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    nome: editingPlano?.nome || '',
    slug: editingPlano?.slug || '',
    descricao: editingPlano?.descricao || '',
    preco_mensal: editingPlano?.preco_mensal || '',
    preco_anual: editingPlano?.preco_anual || '',
    max_produtos: editingPlano?.max_produtos || 100,
    max_usuarios: editingPlano?.max_usuarios || 3,
    max_pedidos_mes: editingPlano?.max_pedidos_mes || 100,
    espaco_storage_gb: editingPlano?.espaco_storage_gb || 5,
    tem_relatorios_avancados: editingPlano?.tem_relatorios_avancados || false,
    tem_api_acesso: editingPlano?.tem_api_acesso || false,
    tem_suporte_prioritario: editingPlano?.tem_suporte_prioritario || false,
    tem_dominio_customizado: editingPlano?.tem_dominio_customizado || false,
    tem_whatsapp_integration: editingPlano?.tem_whatsapp_integration || false,
    is_active: editingPlano?.is_active ?? true,
    ordem: editingPlano?.ordem || 1,
  });

  const isEditing = !!editingPlano;

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    
    if (type === 'checkbox') {
      const checked = (e.target as HTMLInputElement).checked;
      setFormData(prev => ({ ...prev, [name]: checked }));
    } else if (type === 'number') {
      setFormData(prev => ({ ...prev, [name]: parseInt(value) || 0 }));
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
      if (isEditing && editingPlano) {
        // Atualizar plano existente
        await apiClient.put(`/superadmin/planos/${editingPlano.id}/`, formData);
        alert('Plano atualizado com sucesso!');
      } else {
        // Criar novo plano
        await apiClient.post('/superadmin/planos/', formData);
        alert('Plano criado com sucesso!');
      }
      onSuccess();
      onClose();
    } catch (error: any) {
      console.error('Erro ao salvar plano:', error);
      alert(`Erro: ${error.response?.data?.error || JSON.stringify(error.response?.data) || 'Erro ao salvar plano'}`);
    } finally {
      setLoading(false);
    }
  };

  const planosPreDefinidos = [
    {
      nome: 'Básico',
      ordem: 1,
      preco_mensal: '49.90',
      max_produtos: 100,
      max_usuarios: 3,
      max_pedidos_mes: 100,
      espaco_storage_gb: 5,
    },
    {
      nome: 'Profissional',
      ordem: 2,
      preco_mensal: '99.90',
      max_produtos: 500,
      max_usuarios: 10,
      max_pedidos_mes: 500,
      espaco_storage_gb: 20,
      tem_relatorios_avancados: true,
      tem_whatsapp_integration: true,
    },
    {
      nome: 'Enterprise',
      ordem: 3,
      preco_mensal: '199.90',
      max_produtos: 999999,
      max_usuarios: 50,
      max_pedidos_mes: 999999,
      espaco_storage_gb: 100,
      tem_relatorios_avancados: true,
      tem_api_acesso: true,
      tem_suporte_prioritario: true,
      tem_dominio_customizado: true,
      tem_whatsapp_integration: true,
    },
  ];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 overflow-y-auto">
      <div className="bg-white rounded-lg p-8 max-w-4xl w-full my-8">
        <h2 className="text-2xl font-bold mb-6 text-purple-900">
          {isEditing ? 'Editar Plano de Assinatura' : 'Novo Plano de Assinatura'}
        </h2>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Templates Pré-definidos */}
          <div>
            <h3 className="text-lg font-semibold mb-3 text-gray-700">Templates Rápidos</h3>
            <div className="grid grid-cols-3 gap-3">
              {planosPreDefinidos.map((template) => (
                <button
                  key={template.nome}
                  type="button"
                  onClick={() => setFormData(prev => ({
                    ...prev,
                    ...template,
                    nome: template.nome,
                    slug: template.nome.toLowerCase(),
                    descricao: `Plano ${template.nome}`,
                  }))}
                  className="p-4 border-2 border-gray-200 rounded-lg hover:border-purple-400 transition-all text-left"
                >
                  <div className="font-semibold text-gray-900">{template.nome}</div>
                  <div className="text-sm text-purple-600 mt-1">R$ {template.preco_mensal}/mês</div>
                  <div className="text-xs text-gray-500 mt-1">{template.max_usuarios} usuários</div>
                </button>
              ))}
            </div>
          </div>

          {/* Informações Básicas */}
          <div>
            <h3 className="text-lg font-semibold mb-4 text-gray-700">Informações Básicas</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nome do Plano *
                </label>
                <input
                  type="text"
                  name="nome"
                  value={formData.nome}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500"
                  placeholder="Ex: Básico"
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
                  placeholder="basico"
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
                  rows={2}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500"
                  placeholder="Descrição do plano..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Preço Mensal (R$) *
                </label>
                <input
                  type="text"
                  name="preco_mensal"
                  value={formData.preco_mensal}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500"
                  placeholder="49.90"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Preço Anual (R$)
                </label>
                <input
                  type="text"
                  name="preco_anual"
                  value={formData.preco_anual}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500"
                  placeholder="499.00"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Ordem de Exibição *
                </label>
                <select
                  name="ordem"
                  value={formData.ordem}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500"
                >
                  <option value={1}>1 - Básico</option>
                  <option value={2}>2 - Intermediário</option>
                  <option value={3}>3 - Avançado</option>
                </select>
              </div>
            </div>
          </div>

          {/* Limites */}
          <div>
            <h3 className="text-lg font-semibold mb-4 text-gray-700">Limites</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Produtos
                </label>
                <input
                  type="number"
                  name="max_produtos"
                  value={formData.max_produtos}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500"
                />
                <p className="text-xs text-gray-500 mt-1">999999 = Ilimitado</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Usuários
                </label>
                <input
                  type="number"
                  name="max_usuarios"
                  value={formData.max_usuarios}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Pedidos/mês
                </label>
                <input
                  type="number"
                  name="max_pedidos_mes"
                  value={formData.max_pedidos_mes}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500"
                />
                <p className="text-xs text-gray-500 mt-1">999999 = Ilimitado</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Storage (GB)
                </label>
                <input
                  type="number"
                  name="espaco_storage_gb"
                  value={formData.espaco_storage_gb}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500"
                />
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
                  name="tem_relatorios_avancados"
                  checked={formData.tem_relatorios_avancados}
                  onChange={handleChange}
                  className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                />
                <span className="text-sm">📊 Relatórios Avançados</span>
              </label>

              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  name="tem_api_acesso"
                  checked={formData.tem_api_acesso}
                  onChange={handleChange}
                  className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                />
                <span className="text-sm">🔌 Acesso à API</span>
              </label>

              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  name="tem_suporte_prioritario"
                  checked={formData.tem_suporte_prioritario}
                  onChange={handleChange}
                  className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                />
                <span className="text-sm">⭐ Suporte Prioritário</span>
              </label>

              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  name="tem_dominio_customizado"
                  checked={formData.tem_dominio_customizado}
                  onChange={handleChange}
                  className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                />
                <span className="text-sm">🌐 Domínio Customizado</span>
              </label>

              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  name="tem_whatsapp_integration"
                  checked={formData.tem_whatsapp_integration}
                  onChange={handleChange}
                  className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                />
                <span className="text-sm">💬 Integração WhatsApp</span>
              </label>

              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  name="is_active"
                  checked={formData.is_active}
                  onChange={handleChange}
                  className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                />
                <span className="text-sm">✅ Plano Ativo</span>
              </label>
            </div>
          </div>

          {/* Preview */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="text-lg font-semibold mb-3 text-gray-700">Preview</h3>
            <div className="bg-white rounded-lg border-2 border-purple-200 p-6 text-center">
              <h4 className="text-xl font-bold text-gray-900 mb-2">{formData.nome || 'Nome do Plano'}</h4>
              <p className="text-gray-600 text-sm mb-4">{formData.descricao || 'Descrição...'}</p>
              <div className="text-3xl font-bold text-purple-600 mb-1">
                R$ {formData.preco_mensal || '0,00'}
              </div>
              <div className="text-sm text-gray-500">por mês</div>
              <div className="mt-4 text-sm text-gray-600">
                {formData.max_usuarios} usuários • {formData.max_produtos === 999999 ? 'Produtos ilimitados' : `${formData.max_produtos} produtos`}
              </div>
            </div>
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
              {loading ? (isEditing ? 'Salvando...' : 'Criando...') : (isEditing ? 'Salvar Alterações' : 'Criar Plano')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
