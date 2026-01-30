'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { authService } from '@/lib/auth';

interface Estatisticas {
  total_lojas: number;
  lojas_ativas: number;
  lojas_trial: number;
  lojas_inativas: number;
  receita_mensal_estimada: number;
}

interface Loja {
  id: number;
  nome: string;
  tipo_loja_nome: string;
  plano_nome: string;
  is_active: boolean;
  is_trial: boolean;
  created_at: string;
}

interface FinanceiroLoja {
  id: number;
  loja_nome: string;
  valor_mensalidade: string;
  status_pagamento: string;
  status_display: string;
  total_pago: string;
  total_pendente: string;
}

interface Usuario {
  id: number;
  tipo: string;
  is_active: boolean;
}

export default function RelatoriosPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [estatisticas, setEstatisticas] = useState<Estatisticas | null>(null);
  const [lojas, setLojas] = useState<Loja[]>([]);
  const [financeiros, setFinanceiros] = useState<FinanceiroLoja[]>([]);
  const [usuarios, setUsuarios] = useState<Usuario[]>([]);
  const [periodoSelecionado, setPeriodoSelecionado] = useState<string>('mes');

  useEffect(() => {
    if (typeof window !== 'undefined' && authService.getUserType() !== 'superadmin') {
      router.push('/superadmin/login');
      return;
    }
    loadDados();
  }, [router]);

  const loadDados = async () => {
    try {
      setLoading(true);
      
      // Carregar estatísticas
      const statsRes = await apiClient.get('/superadmin/lojas/estatisticas/');
      setEstatisticas(statsRes.data);
      
      // Carregar lojas
      const lojasRes = await apiClient.get('/superadmin/lojas/');
      const lojasData = lojasRes.data.results || lojasRes.data;
      setLojas(Array.isArray(lojasData) ? lojasData : []);
      
      // Carregar financeiros
      const finRes = await apiClient.get('/superadmin/financeiro/');
      const finData = finRes.data.results || finRes.data;
      setFinanceiros(Array.isArray(finData) ? finData : []);
      
      // Carregar usuários
      const usersRes = await apiClient.get('/superadmin/usuarios/');
      const usersData = usersRes.data.results || usersRes.data;
      setUsuarios(Array.isArray(usersData) ? usersData : []);
      
    } catch (error) {
      console.error('Erro ao carregar dados:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value: number | string) => {
    const num = typeof value === 'string' ? parseFloat(value) : value;
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(num || 0);
  };

  // Cálculos de relatórios
  const receitaTotal = financeiros.reduce((acc, f) => acc + parseFloat(f.total_pago || '0'), 0);
  const receitaPendente = financeiros.reduce((acc, f) => acc + parseFloat(f.total_pendente || '0'), 0);
  const receitaMensal = financeiros.reduce((acc, f) => acc + parseFloat(f.valor_mensalidade || '0'), 0);
  
  const lojasAtivas = lojas.filter(l => l.is_active).length;
  const lojasTrial = lojas.filter(l => l.is_trial).length;
  const lojasInativas = lojas.filter(l => !l.is_active).length;
  
  const usuariosAtivos = usuarios.filter(u => u.is_active).length;
  const superAdmins = usuarios.filter(u => u.tipo === 'superadmin').length;
  const suporte = usuarios.filter(u => u.tipo === 'suporte').length;
  
  // Lojas por tipo
  const lojasPorTipo: { [key: string]: number } = {};
  lojas.forEach(loja => {
    lojasPorTipo[loja.tipo_loja_nome] = (lojasPorTipo[loja.tipo_loja_nome] || 0) + 1;
  });
  
  // Lojas por plano
  const lojasPorPlano: { [key: string]: number } = {};
  lojas.forEach(loja => {
    lojasPorPlano[loja.plano_nome] = (lojasPorPlano[loja.plano_nome] || 0) + 1;
  });
  
  // Status de pagamento
  const statusPagamento: { [key: string]: number } = {};
  financeiros.forEach(f => {
    statusPagamento[f.status_display] = (statusPagamento[f.status_display] || 0) + 1;
  });

  // Lojas criadas nos últimos 30 dias
  const dataLimite = new Date();
  dataLimite.setDate(dataLimite.getDate() - 30);
  const lojasRecentes = lojas.filter(l => new Date(l.created_at) >= dataLimite).length;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <nav className="bg-pink-900 text-white shadow-lg">
        <div className="w-full max-w-full px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center space-x-4">
              <a href="/superadmin/dashboard" className="text-pink-200 hover:text-white">
                ← Voltar
              </a>
              <h1 className="text-2xl font-bold">Relatórios e Análises</h1>
            </div>
            <div className="flex space-x-2">
              <button
                onClick={() => setPeriodoSelecionado('mes')}
                className={`px-4 py-2 rounded-md text-sm ${
                  periodoSelecionado === 'mes'
                    ? 'bg-pink-700'
                    : 'bg-pink-800 hover:bg-pink-700'
                }`}
              >
                Este Mês
              </button>
              <button
                onClick={() => setPeriodoSelecionado('trimestre')}
                className={`px-4 py-2 rounded-md text-sm ${
                  periodoSelecionado === 'trimestre'
                    ? 'bg-pink-700'
                    : 'bg-pink-800 hover:bg-pink-700'
                }`}
              >
                Trimestre
              </button>
              <button
                onClick={() => setPeriodoSelecionado('ano')}
                className={`px-4 py-2 rounded-md text-sm ${
                  periodoSelecionado === 'ano'
                    ? 'bg-pink-700'
                    : 'bg-pink-800 hover:bg-pink-700'
                }`}
              >
                Este Ano
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="w-full max-w-full py-6 px-4 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {loading ? (
            <div className="text-center py-12">Carregando relatórios...</div>
          ) : (
            <>
              {/* Resumo Executivo */}
              <div className="mb-8">
                <h2 className="text-2xl font-bold text-gray-900 mb-4">📊 Resumo Executivo</h2>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                  <div className="bg-gradient-to-br from-purple-500 to-purple-600 text-white p-6 rounded-lg shadow-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-purple-100 text-sm">Receita Total</p>
                        <p className="text-3xl font-bold mt-2">{formatCurrency(receitaTotal)}</p>
                      </div>
                      <div className="text-4xl">💰</div>
                    </div>
                  </div>

                  <div className="bg-gradient-to-br from-green-500 to-green-600 text-white p-6 rounded-lg shadow-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-green-100 text-sm">Receita Mensal</p>
                        <p className="text-3xl font-bold mt-2">{formatCurrency(receitaMensal)}</p>
                      </div>
                      <div className="text-4xl">📈</div>
                    </div>
                  </div>

                  <div className="bg-gradient-to-br from-blue-500 to-blue-600 text-white p-6 rounded-lg shadow-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-blue-100 text-sm">Lojas Ativas</p>
                        <p className="text-3xl font-bold mt-2">{lojasAtivas}</p>
                      </div>
                      <div className="text-4xl">🏪</div>
                    </div>
                  </div>

                  <div className="bg-gradient-to-br from-yellow-500 to-yellow-600 text-white p-6 rounded-lg shadow-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-yellow-100 text-sm">Novas (30 dias)</p>
                        <p className="text-3xl font-bold mt-2">{lojasRecentes}</p>
                      </div>
                      <div className="text-4xl">🆕</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Análise Financeira */}
              <div className="mb-8">
                <h2 className="text-2xl font-bold text-gray-900 mb-4">💵 Análise Financeira</h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="bg-white p-6 rounded-lg shadow">
                    <h3 className="text-lg font-semibold text-gray-700 mb-4">Receitas</h3>
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="text-gray-600">Total Recebido:</span>
                        <span className="font-bold text-green-600">{formatCurrency(receitaTotal)}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-gray-600">Pendente:</span>
                        <span className="font-bold text-yellow-600">{formatCurrency(receitaPendente)}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-gray-600">Mensal Estimada:</span>
                        <span className="font-bold text-blue-600">{formatCurrency(receitaMensal)}</span>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white p-6 rounded-lg shadow">
                    <h3 className="text-lg font-semibold text-gray-700 mb-4">Status de Pagamento</h3>
                    <div className="space-y-2">
                      {Object.entries(statusPagamento).map(([status, count]) => (
                        <div key={status} className="flex justify-between items-center">
                          <span className="text-gray-600">{status}:</span>
                          <span className="font-bold">{count}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="bg-white p-6 rounded-lg shadow">
                    <h3 className="text-lg font-semibold text-gray-700 mb-4">Métricas</h3>
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="text-gray-600">Ticket Médio:</span>
                        <span className="font-bold text-purple-600">
                          {formatCurrency(lojasAtivas > 0 ? receitaMensal / lojasAtivas : 0)}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-gray-600">Taxa de Conversão:</span>
                        <span className="font-bold text-green-600">
                          {lojas.length > 0 ? ((lojasAtivas / lojas.length) * 100).toFixed(1) : 0}%
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-gray-600">Lojas em Trial:</span>
                        <span className="font-bold text-yellow-600">{lojasTrial}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Análise de Lojas */}
              <div className="mb-8">
                <h2 className="text-2xl font-bold text-gray-900 mb-4">🏪 Análise de Lojas</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="bg-white p-6 rounded-lg shadow">
                    <h3 className="text-lg font-semibold text-gray-700 mb-4">Lojas por Tipo</h3>
                    <div className="space-y-3">
                      {Object.entries(lojasPorTipo).map(([tipo, count]) => (
                        <div key={tipo} className="flex items-center justify-between">
                          <span className="text-gray-600">{tipo}</span>
                          <div className="flex items-center space-x-3">
                            <div className="w-32 bg-gray-200 rounded-full h-2">
                              <div
                                className="bg-purple-600 h-2 rounded-full"
                                style={{ width: `${(count / lojas.length) * 100}%` }}
                              ></div>
                            </div>
                            <span className="font-bold text-gray-900 w-8 text-right">{count}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="bg-white p-6 rounded-lg shadow">
                    <h3 className="text-lg font-semibold text-gray-700 mb-4">Lojas por Plano</h3>
                    <div className="space-y-3">
                      {Object.entries(lojasPorPlano).map(([plano, count]) => (
                        <div key={plano} className="flex items-center justify-between">
                          <span className="text-gray-600">{plano}</span>
                          <div className="flex items-center space-x-3">
                            <div className="w-32 bg-gray-200 rounded-full h-2">
                              <div
                                className="bg-blue-600 h-2 rounded-full"
                                style={{ width: `${(count / lojas.length) * 100}%` }}
                              ></div>
                            </div>
                            <span className="font-bold text-gray-900 w-8 text-right">{count}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* Análise de Usuários */}
              <div className="mb-8">
                <h2 className="text-2xl font-bold text-gray-900 mb-4">👥 Análise de Usuários</h2>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                  <div className="bg-white p-6 rounded-lg shadow">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-gray-600">Total de Usuários</p>
                        <p className="text-2xl font-bold text-purple-600 mt-2">{usuarios.length}</p>
                      </div>
                      <div className="text-3xl">👥</div>
                    </div>
                  </div>

                  <div className="bg-white p-6 rounded-lg shadow">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-gray-600">Super Admins</p>
                        <p className="text-2xl font-bold text-purple-600 mt-2">{superAdmins}</p>
                      </div>
                      <div className="text-3xl">👑</div>
                    </div>
                  </div>

                  <div className="bg-white p-6 rounded-lg shadow">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-gray-600">Suporte</p>
                        <p className="text-2xl font-bold text-blue-600 mt-2">{suporte}</p>
                      </div>
                      <div className="text-3xl">🛠️</div>
                    </div>
                  </div>

                  <div className="bg-white p-6 rounded-lg shadow">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-gray-600">Ativos</p>
                        <p className="text-2xl font-bold text-green-600 mt-2">{usuariosAtivos}</p>
                      </div>
                      <div className="text-3xl">✅</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Status Geral do Sistema */}
              <div className="mb-8">
                <h2 className="text-2xl font-bold text-gray-900 mb-4">⚡ Status Geral do Sistema</h2>
                <div className="bg-white p-6 rounded-lg shadow">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div>
                      <h3 className="text-sm font-medium text-gray-500 mb-3">Lojas</h3>
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <span className="text-gray-600">Ativas:</span>
                          <span className="font-semibold text-green-600">{lojasAtivas}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Trial:</span>
                          <span className="font-semibold text-yellow-600">{lojasTrial}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Inativas:</span>
                          <span className="font-semibold text-red-600">{lojasInativas}</span>
                        </div>
                      </div>
                    </div>

                    <div>
                      <h3 className="text-sm font-medium text-gray-500 mb-3">Financeiro</h3>
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <span className="text-gray-600">Ativos:</span>
                          <span className="font-semibold text-green-600">
                            {financeiros.filter(f => f.status_pagamento === 'ativo').length}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Pendentes:</span>
                          <span className="font-semibold text-yellow-600">
                            {financeiros.filter(f => f.status_pagamento === 'pendente').length}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Atrasados:</span>
                          <span className="font-semibold text-red-600">
                            {financeiros.filter(f => f.status_pagamento === 'atrasado').length}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div>
                      <h3 className="text-sm font-medium text-gray-500 mb-3">Crescimento</h3>
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <span className="text-gray-600">Novas (30d):</span>
                          <span className="font-semibold text-blue-600">{lojasRecentes}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Taxa Ativas:</span>
                          <span className="font-semibold text-green-600">
                            {lojas.length > 0 ? ((lojasAtivas / lojas.length) * 100).toFixed(0) : 0}%
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Conversão Trial:</span>
                          <span className="font-semibold text-purple-600">
                            {lojas.length > 0 ? (((lojas.length - lojasTrial) / lojas.length) * 100).toFixed(0) : 0}%
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Ações Rápidas */}
              <div className="bg-gradient-to-r from-pink-50 to-purple-50 p-6 rounded-lg border-2 border-pink-200">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">🚀 Ações Rápidas</h3>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <a
                    href="/superadmin/lojas"
                    className="px-4 py-3 bg-white hover:bg-gray-50 rounded-lg shadow text-center transition-colors"
                  >
                    <div className="text-2xl mb-1">🏪</div>
                    <div className="text-sm font-medium text-gray-700">Ver Lojas</div>
                  </a>
                  <a
                    href="/superadmin/financeiro"
                    className="px-4 py-3 bg-white hover:bg-gray-50 rounded-lg shadow text-center transition-colors"
                  >
                    <div className="text-2xl mb-1">💰</div>
                    <div className="text-sm font-medium text-gray-700">Financeiro</div>
                  </a>
                  <a
                    href="/superadmin/usuarios"
                    className="px-4 py-3 bg-white hover:bg-gray-50 rounded-lg shadow text-center transition-colors"
                  >
                    <div className="text-2xl mb-1">👥</div>
                    <div className="text-sm font-medium text-gray-700">Usuários</div>
                  </a>
                  <a
                    href="/superadmin/planos"
                    className="px-4 py-3 bg-white hover:bg-gray-50 rounded-lg shadow text-center transition-colors"
                  >
                    <div className="text-2xl mb-1">💎</div>
                    <div className="text-sm font-medium text-gray-700">Planos</div>
                  </a>
                </div>
              </div>
            </>
          )}
        </div>
      </main>
    </div>
  );
}
