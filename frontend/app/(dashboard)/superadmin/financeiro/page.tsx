'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { authService } from '@/lib/auth';

interface FinanceiroLoja {
  id: number;
  loja_nome: string;
  loja_id: number;
  data_proxima_cobranca: string;
  valor_mensalidade: string;
  dia_vencimento: number;
  status_pagamento: string;
  status_display: string;
  total_pago: string;
  total_pendente: string;
  forma_pagamento: string;
  ultimo_pagamento: string | null;
  created_at: string;
}

interface Estatisticas {
  total_lojas: number;
  lojas_ativas: number;
  lojas_pendentes: number;
  lojas_atrasadas: number;
  receita_mensal_total: number;
  receita_recebida: number;
  receita_pendente: number;
}

export default function FinanceiroPage() {
  const router = useRouter();
  const [financeiros, setFinanceiros] = useState<FinanceiroLoja[]>([]);
  const [estatisticas, setEstatisticas] = useState<Estatisticas | null>(null);
  const [loading, setLoading] = useState(true);
  const [filtroStatus, setFiltroStatus] = useState<string>('todos');

  useEffect(() => {
    if (typeof window !== 'undefined' && authService.getUserType() !== 'superadmin') {
      router.push('/superadmin/login');
      return;
    }
    loadFinanceiros();
    loadEstatisticas();
  }, [router]);

  const loadFinanceiros = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/superadmin/financeiro/');
      const data = response.data.results || response.data;
      setFinanceiros(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Erro ao carregar financeiros:', error);
      setFinanceiros([]);
    } finally {
      setLoading(false);
    }
  };

  const loadEstatisticas = async () => {
    try {
      const response = await apiClient.get('/superadmin/lojas/estatisticas/');
      setEstatisticas(response.data);
    } catch (error) {
      console.error('Erro ao carregar estatísticas:', error);
    }
  };

  const formatCurrency = (value: string | number) => {
    const num = typeof value === 'string' ? parseFloat(value) : value;
    return num.toLocaleString('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    });
  };

  const formatDate = (dateString: string) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('pt-BR');
  };

  const getStatusColor = (status: string) => {
    const colors: { [key: string]: string } = {
      'ativo': 'bg-green-100 text-green-800',
      'pendente': 'bg-yellow-100 text-yellow-800',
      'atrasado': 'bg-red-100 text-red-800',
      'suspenso': 'bg-gray-100 text-gray-800',
      'cancelado': 'bg-red-100 text-red-800',
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const financeirosFiltrados = filtroStatus === 'todos' 
    ? financeiros 
    : financeiros.filter(f => f.status_pagamento === filtroStatus);

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
              <h1 className="text-2xl font-bold">Financeiro</h1>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={loadFinanceiros}
                className="px-4 py-2 bg-purple-700 hover:bg-purple-800 rounded-md transition-colors"
              >
                🔄 Atualizar
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {/* Estatísticas */}
          {estatisticas && (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Receita Mensal</p>
                    <p className="text-2xl font-bold text-purple-600">
                      {formatCurrency(estatisticas.receita_mensal_total || 0)}
                    </p>
                  </div>
                  <div className="text-3xl">💰</div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Lojas Ativas</p>
                    <p className="text-2xl font-bold text-green-600">
                      {estatisticas.lojas_ativas}
                    </p>
                  </div>
                  <div className="text-3xl">✅</div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Pendentes</p>
                    <p className="text-2xl font-bold text-yellow-600">
                      {financeiros.filter(f => f.status_pagamento === 'pendente').length}
                    </p>
                  </div>
                  <div className="text-3xl">⏳</div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Atrasados</p>
                    <p className="text-2xl font-bold text-red-600">
                      {financeiros.filter(f => f.status_pagamento === 'atrasado').length}
                    </p>
                  </div>
                  <div className="text-3xl">🔴</div>
                </div>
              </div>
            </div>
          )}

          {/* Filtros */}
          <div className="bg-white rounded-lg shadow p-4 mb-6">
            <div className="flex items-center space-x-4">
              <span className="text-sm font-medium text-gray-700">Filtrar por status:</span>
              <div className="flex space-x-2">
                {['todos', 'ativo', 'pendente', 'atrasado', 'suspenso'].map((status) => (
                  <button
                    key={status}
                    onClick={() => setFiltroStatus(status)}
                    className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                      filtroStatus === status
                        ? 'bg-purple-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {status === 'todos' ? 'Todos' : status.charAt(0).toUpperCase() + status.slice(1)}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Tabela de Financeiros */}
          {loading ? (
            <div className="text-center py-12">Carregando...</div>
          ) : financeirosFiltrados.length === 0 ? (
            <div className="text-center py-12 bg-white rounded-lg shadow">
              <p className="text-gray-500">
                {filtroStatus === 'todos' 
                  ? 'Nenhum registro financeiro encontrado.' 
                  : `Nenhuma loja com status "${filtroStatus}".`
                }
              </p>
            </div>
          ) : (
            <div className="bg-white shadow rounded-lg overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Loja
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Mensalidade
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Vencimento
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Próxima Cobrança
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Total Pago
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Ações
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {financeirosFiltrados.map((financeiro) => (
                    <tr key={financeiro.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4">
                        <div>
                          <div className="font-medium text-gray-900">{financeiro.loja_nome}</div>
                          <div className="text-sm text-gray-500">
                            {financeiro.forma_pagamento || 'Não definido'}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(financeiro.status_pagamento)}`}>
                          {financeiro.status_display}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm font-medium text-gray-900">
                        {formatCurrency(financeiro.valor_mensalidade)}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        Dia {financeiro.dia_vencimento}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        {formatDate(financeiro.data_proxima_cobranca)}
                      </td>
                      <td className="px-6 py-4">
                        <div>
                          <div className="text-sm font-medium text-green-600">
                            {formatCurrency(financeiro.total_pago)}
                          </div>
                          {parseFloat(financeiro.total_pendente) > 0 && (
                            <div className="text-xs text-red-600">
                              Pendente: {formatCurrency(financeiro.total_pendente)}
                            </div>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm space-x-2">
                        <button 
                          className="text-blue-600 hover:text-blue-800"
                          onClick={() => router.push(`/superadmin/lojas`)}
                        >
                          Ver Loja
                        </button>
                        <button className="text-purple-600 hover:text-purple-800">
                          Histórico
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Resumo */}
          {financeirosFiltrados.length > 0 && (
            <div className="mt-6 bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Resumo Financeiro</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="border-l-4 border-purple-500 pl-4">
                  <p className="text-sm text-gray-600">Total de Lojas</p>
                  <p className="text-2xl font-bold text-gray-900">{financeirosFiltrados.length}</p>
                </div>
                <div className="border-l-4 border-green-500 pl-4">
                  <p className="text-sm text-gray-600">Receita Total Recebida</p>
                  <p className="text-2xl font-bold text-green-600">
                    {formatCurrency(
                      financeirosFiltrados.reduce((sum, f) => sum + parseFloat(f.total_pago), 0)
                    )}
                  </p>
                </div>
                <div className="border-l-4 border-red-500 pl-4">
                  <p className="text-sm text-gray-600">Total Pendente</p>
                  <p className="text-2xl font-bold text-red-600">
                    {formatCurrency(
                      financeirosFiltrados.reduce((sum, f) => sum + parseFloat(f.total_pendente), 0)
                    )}
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
