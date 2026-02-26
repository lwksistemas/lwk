'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { authService } from '@/lib/auth';

interface LojaStorage {
  id: number;
  nome: string;
  slug: string;
  storage_usado_mb: number;
  storage_limite_mb: number;
  storage_livre_mb: number;
  storage_percentual: number;
  storage_status: 'ok' | 'warning' | 'critical';
  storage_status_texto: string;
  storage_alerta_enviado: boolean;
  storage_ultima_verificacao: string | null;
  storage_horas_desde_verificacao: number | null;
  plano_nome: string;
  is_active: boolean;
}

export default function MonitoramentoStoragePage() {
  const router = useRouter();
  const [lojas, setLojas] = useState<LojaStorage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [ordenacao, setOrdenacao] = useState<'percentual' | 'uso' | 'nome'>('percentual');
  const [filtroStatus, setFiltroStatus] = useState<'todos' | 'ok' | 'warning' | 'critical'>('todos');
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    // Verificar autenticação
    if (!authService.isAuthenticated()) {
      router.push('/login');
      return;
    }

    const userType = authService.getUserType();
    if (userType !== 'superadmin') {
      router.push('/login');
      return;
    }

    carregarLojas();

    // Auto-refresh a cada 30 segundos
    let interval: NodeJS.Timeout;
    if (autoRefresh) {
      interval = setInterval(() => {
        carregarLojas(true); // true = silent refresh
      }, 30000);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [router, autoRefresh]);

  const carregarLojas = async (silent = false) => {
    try {
      if (!silent) setLoading(true);
      
      const response = await apiClient.get('/api/superadmin/storage/');
      
      if (response.data) {
        setLojas(response.data.lojas || []);
        setError('');
      }
    } catch (err: any) {
      console.error('Erro ao carregar storage:', err);
      if (!silent) {
        setError(err.response?.data?.error || 'Erro ao carregar dados de storage');
      }
    } finally {
      if (!silent) setLoading(false);
    }
  };

  const verificarLoja = async (lojaId: number) => {
    try {
      await apiClient.post(`/api/superadmin/lojas/${lojaId}/verificar-storage/`);
      carregarLojas(true);
    } catch (err: any) {
      console.error('Erro ao verificar storage:', err);
      alert(err.response?.data?.error || 'Erro ao verificar storage');
    }
  };

  const lojasOrdenadas = [...lojas].sort((a, b) => {
    if (ordenacao === 'percentual') {
      return b.storage_percentual - a.storage_percentual;
    } else if (ordenacao === 'uso') {
      return b.storage_usado_mb - a.storage_usado_mb;
    } else {
      return a.nome.localeCompare(b.nome);
    }
  });

  const lojasFiltradas = lojasOrdenadas.filter(loja => {
    if (filtroStatus === 'todos') return true;
    return loja.storage_status === filtroStatus;
  });

  const estatisticas = {
    total: lojas.length,
    ok: lojas.filter(l => l.storage_status === 'ok').length,
    warning: lojas.filter(l => l.storage_status === 'warning').length,
    critical: lojas.filter(l => l.storage_status === 'critical').length,
    uso_total_gb: lojas.reduce((acc, l) => acc + (l.storage_usado_mb / 1024), 0),
    limite_total_gb: lojas.reduce((acc, l) => acc + (l.storage_limite_mb / 1024), 0),
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Carregando dados de storage...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">💾 Monitoramento de Storage</h1>
              <p className="text-gray-600 mt-1">Acompanhe o crescimento do banco de todas as lojas em tempo real</p>
            </div>
            <button
              onClick={() => router.push('/superadmin/dashboard')}
              className="px-4 py-2 text-gray-600 hover:text-gray-900"
            >
              ← Voltar
            </button>
          </div>
        </div>

        {/* Estatísticas */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-sm text-gray-500">Total de Lojas</div>
            <div className="text-2xl font-bold text-gray-900">{estatisticas.total}</div>
          </div>
          <div className="bg-green-50 rounded-lg shadow p-4 border border-green-200">
            <div className="text-sm text-green-700">✅ Normal</div>
            <div className="text-2xl font-bold text-green-900">{estatisticas.ok}</div>
          </div>
          <div className="bg-yellow-50 rounded-lg shadow p-4 border border-yellow-200">
            <div className="text-sm text-yellow-700">⚠️ Alerta</div>
            <div className="text-2xl font-bold text-yellow-900">{estatisticas.warning}</div>
          </div>
          <div className="bg-red-50 rounded-lg shadow p-4 border border-red-200">
            <div className="text-sm text-red-700">🚫 Crítico</div>
            <div className="text-2xl font-bold text-red-900">{estatisticas.critical}</div>
          </div>
          <div className="bg-purple-50 rounded-lg shadow p-4 border border-purple-200">
            <div className="text-sm text-purple-700">Uso Total</div>
            <div className="text-2xl font-bold text-purple-900">
              {estatisticas.uso_total_gb.toFixed(1)} GB
            </div>
            <div className="text-xs text-purple-600">
              de {estatisticas.limite_total_gb.toFixed(0)} GB
            </div>
          </div>
        </div>

        {/* Controles */}
        <div className="bg-white rounded-lg shadow p-4 mb-6">
          <div className="flex flex-wrap items-center gap-4">
            <div>
              <label className="text-sm text-gray-600 mr-2">Ordenar por:</label>
              <select
                value={ordenacao}
                onChange={(e) => setOrdenacao(e.target.value as any)}
                className="px-3 py-2 border border-gray-300 rounded-lg"
              >
                <option value="percentual">% de Uso (maior primeiro)</option>
                <option value="uso">MB Usado (maior primeiro)</option>
                <option value="nome">Nome (A-Z)</option>
              </select>
            </div>
            <div>
              <label className="text-sm text-gray-600 mr-2">Filtrar por status:</label>
              <select
                value={filtroStatus}
                onChange={(e) => setFiltroStatus(e.target.value as any)}
                className="px-3 py-2 border border-gray-300 rounded-lg"
              >
                <option value="todos">Todos</option>
                <option value="ok">✅ Normal</option>
                <option value="warning">⚠️ Alerta</option>
                <option value="critical">🚫 Crítico</option>
              </select>
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="autoRefresh"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="w-4 h-4"
              />
              <label htmlFor="autoRefresh" className="text-sm text-gray-600">
                Auto-atualizar (30s)
              </label>
            </div>
            <button
              onClick={() => carregarLojas()}
              className="ml-auto px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
            >
              🔄 Atualizar Agora
            </button>
          </div>
        </div>

        {/* Lista de Lojas */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Loja</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Plano</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Uso</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Limite</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Percentual</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Última Verificação</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Ações</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {lojasFiltradas.map((loja) => (
                  <tr key={loja.id} className={!loja.is_active ? 'opacity-50' : ''}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div>
                          <div className="text-sm font-medium text-gray-900">{loja.nome}</div>
                          <div className="text-sm text-gray-500">{loja.slug}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm text-gray-900">{loja.plano_nome}</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm font-medium text-gray-900">
                        {loja.storage_usado_mb.toFixed(2)} MB
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm text-gray-900">
                        {(loja.storage_limite_mb / 1024).toFixed(0)} GB
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        <div className="w-24 bg-gray-200 rounded-full h-2">
                          <div
                            className={`h-2 rounded-full ${
                              loja.storage_status === 'critical'
                                ? 'bg-red-600'
                                : loja.storage_status === 'warning'
                                ? 'bg-yellow-500'
                                : 'bg-green-500'
                            }`}
                            style={{ width: `${Math.min(loja.storage_percentual, 100)}%` }}
                          ></div>
                        </div>
                        <span className="text-sm font-medium text-gray-900">
                          {loja.storage_percentual.toFixed(1)}%
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 py-1 text-xs font-medium rounded-full ${
                          loja.storage_status === 'critical'
                            ? 'bg-red-100 text-red-800'
                            : loja.storage_status === 'warning'
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-green-100 text-green-800'
                        }`}
                      >
                        {loja.storage_status === 'critical' && '🚫'}
                        {loja.storage_status === 'warning' && '⚠️'}
                        {loja.storage_status === 'ok' && '✅'}
                        {' '}
                        {loja.storage_status_texto}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {loja.storage_horas_desde_verificacao !== null
                        ? `há ${loja.storage_horas_desde_verificacao}h`
                        : 'Nunca'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <button
                        onClick={() => verificarLoja(loja.id)}
                        className="text-purple-600 hover:text-purple-900"
                        title="Verificar agora"
                      >
                        🔄
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {lojasFiltradas.length === 0 && (
            <div className="text-center py-12">
              <p className="text-gray-500">Nenhuma loja encontrada com os filtros selecionados</p>
            </div>
          )}
        </div>

        {/* Informações */}
        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="text-sm font-medium text-blue-900 mb-2">ℹ️ Informações</h3>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>• Os dados são atualizados automaticamente a cada 6 horas pelo sistema</li>
            <li>• Você pode verificar uma loja específica clicando no botão 🔄</li>
            <li>• Alertas são enviados quando o uso atinge 80% do limite</li>
            <li>• Lojas são bloqueadas automaticamente quando atingem 100% do limite</li>
            <li>• Esta página atualiza automaticamente a cada 30 segundos (pode desativar)</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
