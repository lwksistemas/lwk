'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { authService } from '@/lib/auth';

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

  useEffect(() => {
    if (typeof window !== 'undefined' && authService.getUserType() !== 'superadmin') {
      router.push('/superadmin/login');
      return;
    }
    loadTiposEPlanos();
  }, [router]);

  const loadTiposEPlanos = async () => {
    try {
      setLoading(true);
      // Carregar tipos de loja
      const tiposResponse = await apiClient.get('/superadmin/tipos-loja/');
      const tiposData = tiposResponse.data.results || tiposResponse.data;
      setTipos(Array.isArray(tiposData) ? tiposData : []);
      
      // Carregar todos os planos inicialmente
      const planosResponse = await apiClient.get('/superadmin/planos/');
      const planosData = planosResponse.data.results || planosResponse.data;
      setPlanos(Array.isArray(planosData) ? planosData : []);
    } catch (error) {
      console.error('Erro ao carregar dados:', error);
      setTipos([]);
      setPlanos([]);
    } finally {
      setLoading(false);
    }
  };

  const loadPlanosPorTipo = async (tipoId: number) => {
    try {
      const response = await apiClient.get(`/superadmin/planos/por_tipo/?tipo_id=${tipoId}`);
      setPlanos(response.data);
      setTipoSelecionado(tipoId);
    } catch (error) {
      console.error('Erro ao carregar planos por tipo:', error);
      setPlanos([]);
    }
  };

  const mostrarTodosPlanos = async () => {
    try {
      const response = await apiClient.get('/superadmin/planos/');
      const data = response.data.results || response.data;
      setPlanos(Array.isArray(data) ? data : []);
      setTipoSelecionado(null);
    } catch (error) {
      console.error('Erro ao carregar todos os planos:', error);
    }
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
      'border-orange-200 bg-orange-50',
    ];
    return colors[ordem - 1] || colors[0];
  };

  const getPlanoBadgeColor = (ordem: number) => {
    const colors = [
      'bg-green-100 text-green-800',
      'bg-blue-100 text-blue-800',
      'bg-purple-100 text-purple-800',
      'bg-orange-100 text-orange-800',
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
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center space-x-4">
              <a href="/superadmin/dashboard" className="text-purple-200 hover:text-white">
                ← Voltar
              </a>
              <h1 className="text-2xl font-bold">Planos de Assinatura</h1>
            </div>
            <button
              onClick={() => setShowModal(true)}
              className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-md transition-colors"
            >
              + Novo Plano
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {loading ? (
            <div className="text-center py-12">Carregando...</div>
          ) : (
            <div className="space-y-8">
              {/* Filtro por Tipos de Loja */}
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">
                  Filtrar Planos por Tipo de Loja
                </h2>
                <div className="flex flex-wrap gap-3">
                  <button
                    onClick={mostrarTodosPlanos}
                    className={`px-4 py-2 rounded-lg border-2 transition-all ${
                      tipoSelecionado === null
                        ? 'border-purple-600 bg-purple-50 text-purple-700'
                        : 'border-gray-200 hover:border-purple-300 text-gray-700'
                    }`}
                  >
                    <div className="flex items-center space-x-2">
                      <span className="text-lg">�</span>
                      <span className="font-medium">Todos os Planos</span>
                    </div>
                  </button>
                  
                  {tipos.map((tipo) => (
                    <button
                      key={tipo.id}
                      onClick={() => loadPlanosPorTipo(tipo.id)}
                      className={`px-4 py-2 rounded-lg border-2 transition-all ${
                        tipoSelecionado === tipo.id
                          ? 'border-purple-600 bg-purple-50 text-purple-700'
                          : 'border-gray-200 hover:border-purple-300 text-gray-700'
                      }`}
                    >
                      <div className="flex items-center space-x-2">
                        <span className="text-lg">{getIconForType(tipo.nome)}</span>
                        <div
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: tipo.cor_primaria }}
                        />
                        <span className="font-medium">{tipo.nome}</span>
                      </div>
                    </button>
                  ))}
                </div>
                
                {/* Indicador do filtro ativo */}
                <div className="mt-4 text-sm text-gray-600">
                  {tipoSelecionado === null ? (
                    <span>Mostrando todos os {planos.length} planos disponíveis</span>
                  ) : (
                    <span>
                      Mostrando {planos.length} plano(s) para{' '}
                      <strong>{tipos.find(t => t.id === tipoSelecionado)?.nome}</strong>
                    </span>
                  )}
                </div>
              </div>

              {/* Lista de Planos */}
              {planos.length === 0 ? (
                <div className="text-center py-12 bg-white rounded-lg shadow">
                  <p className="text-gray-500 mb-4">
                    {tipoSelecionado === null 
                      ? 'Nenhum plano cadastrado ainda.' 
                      : 'Nenhum plano disponível para este tipo de loja.'
                    }
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
                          <div className="flex items-center space-x-1">
                            {!plano.is_active && (
                              <span className="px-2 py-1 text-xs rounded-full bg-red-100 text-red-800">
                                Inativo
                              </span>
                            )}
                            {tipoSelecionado === null && plano.tipos_loja_nomes.length > 0 && (
                              <span className="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800">
                                Específico
                              </span>
                            )}
                          </div>
                        </div>
                        
                        <h3 className="text-xl font-bold text-gray-900 mb-2">{plano.nome}</h3>
                        <p className="text-gray-600 text-sm mb-4">{plano.descricao}</p>
                        
                        {/* Preços */}
                        <div className="mb-4">
                          <div className="text-3xl font-bold text-purple-600">
                            {formatPrice(plano.preco_mensal)}
                          </div>
                          <div className="text-sm text-gray-500">por mês</div>
                          {plano.preco_anual && (
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
                              Relatórios
                            </span>
                          )}
                          {plano.tem_api_acesso && (
                            <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded">
                              API
                            </span>
                          )}
                          {plano.tem_suporte_prioritario && (
                            <span className="px-2 py-1 bg-purple-100 text-purple-800 text-xs rounded">
                              Suporte VIP
                            </span>
                          )}
                          {plano.tem_dominio_customizado && (
                            <span className="px-2 py-1 bg-orange-100 text-orange-800 text-xs rounded">
                              Domínio
                            </span>
                          )}
                          {plano.tem_whatsapp_integration && (
                            <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded">
                              WhatsApp
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Tipos de Loja */}
                      <div className="px-6 pb-4">
                        <h4 className="text-sm font-medium text-gray-700 mb-2">Disponível para:</h4>
                        <div className="flex flex-wrap gap-1">
                          {plano.tipos_loja_nomes.length > 0 ? (
                            plano.tipos_loja_nomes.map((tipo, index) => (
                              <span key={index} className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                                {tipo}
                              </span>
                            ))
                          ) : (
                            <span className="text-xs text-gray-500">Todos os tipos</span>
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
                            <button className="text-blue-600 hover:text-blue-800 text-sm">
                              Editar
                            </button>
                            {plano.total_lojas === 0 && (
                              <button className="text-red-600 hover:text-red-800 text-sm">
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
      {showModal && <NovoPlanoModal onClose={() => setShowModal(false)} onSuccess={loadTiposEPlanos} />}
    </div>
  );
}

// Componente do Modal (versão simplificada para não quebrar)
function NovoPlanoModal({ onClose, onSuccess }: { onClose: () => void; onSuccess: () => void }) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg p-8 max-w-md w-full">
        <h2 className="text-2xl font-bold mb-4 text-purple-900">Novo Plano</h2>
        <p className="text-gray-600 mb-4">
          Funcionalidade em desenvolvimento. Use a API ou Django Admin para criar planos.
        </p>
        <div className="flex justify-end space-x-4">
          <button
            onClick={onClose}
            className="px-6 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
          >
            Fechar
          </button>
        </div>
      </div>
    </div>
  );
}