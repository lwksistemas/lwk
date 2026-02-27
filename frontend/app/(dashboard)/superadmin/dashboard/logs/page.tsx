'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { authService } from '@/lib/auth';
import { formatDateTime } from '@/lib/financeiro-helpers';

interface Log {
  id: number;
  usuario_nome: string;
  usuario_email: string;
  loja_nome: string;
  acao: string;
  recurso: string;
  detalhes: string;
  ip_address: string;
  user_agent: string;
  url: string;
  metodo_http: string;
  status_code: number;
  sucesso: boolean;
  created_at: string;
}

interface BuscaSalva {
  nome: string;
  filtros: FiltrosBusca;
}

interface FiltrosBusca {
  q?: string;
  data_inicio?: string;
  data_fim?: string;
  loja_nome?: string;
  usuario_email?: string;
  acao?: string;
  sucesso?: string;
}

export default function BuscaLogsPage() {
  const router = useRouter();
  const [logs, setLogs] = useState<Log[]>([]);
  const [loading, setLoading] = useState(false);
  const [filtros, setFiltros] = useState<FiltrosBusca>({});
  const [logSelecionado, setLogSelecionado] = useState<Log | null>(null);
  const [mostrarDetalhes, setMostrarDetalhes] = useState(false);
  const [contextoTemporal, setContextoTemporal] = useState<{ antes: Log[]; depois: Log[] } | null>(null);
  const [buscasSalvas, setBuscasSalvas] = useState<BuscaSalva[]>([]);
  const [nomeBusca, setNomeBusca] = useState('');
  const [mostrarSalvarBusca, setMostrarSalvarBusca] = useState(false);

  useEffect(() => {
    if (typeof window !== 'undefined' && authService.getUserType() !== 'superadmin') {
      router.push('/superadmin/login');
      return;
    }
    carregarBuscasSalvas();
  }, [router]);

  const carregarBuscasSalvas = () => {
    if (typeof window !== 'undefined') {
      const salvas = localStorage.getItem('buscas_logs_salvas');
      if (salvas) {
        setBuscasSalvas(JSON.parse(salvas));
      }
    }
  };

  const buscarLogs = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      Object.entries(filtros).forEach(([key, value]) => {
        if (value) params.append(key, value);
      });

      const endpoint = filtros.q 
        ? `/superadmin/historico-acessos/busca_avancada/?${params}`
        : `/superadmin/historico-acessos/?${params}`;

      const response = await apiClient.get(endpoint);
      
      // Busca avançada retorna formato diferente: { resultados: [...] }
      // Busca normal retorna: { results: [...] } ou array direto
      let data;
      if (filtros.q && response.data.resultados) {
        data = response.data.resultados;
      } else if (response.data.results) {
        data = response.data.results;
      } else if (Array.isArray(response.data)) {
        data = response.data;
      } else {
        data = [];
      }
      
      setLogs(data);
    } catch (error) {
      console.error('Erro ao buscar logs:', error);
      setLogs([]);
    } finally {
      setLoading(false);
    }
  };

  const exportarCSV = async () => {
    try {
      const params = new URLSearchParams();
      Object.entries(filtros).forEach(([key, value]) => {
        if (value) params.append(key, value);
      });

      const response = await apiClient.get(
        `/superadmin/historico-acessos/exportar/?${params}`,
        { responseType: 'blob' }
      );

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `logs_${new Date().toISOString()}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Erro ao exportar CSV:', error);
    }
  };

  const exportarJSON = async () => {
    try {
      const params = new URLSearchParams();
      Object.entries(filtros).forEach(([key, value]) => {
        if (value) params.append(key, value);
      });

      const response = await apiClient.get(
        `/superadmin/historico-acessos/exportar_json/?${params}`
      );

      const dataStr = JSON.stringify(response.data, null, 2);
      const dataBlob = new Blob([dataStr], { type: 'application/json' });
      const url = window.URL.createObjectURL(dataBlob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `logs_${new Date().toISOString()}.json`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Erro ao exportar JSON:', error);
    }
  };

  const carregarContextoTemporal = async (logId: number) => {
    try {
      const response = await apiClient.get(
        `/superadmin/historico-acessos/${logId}/contexto_temporal/?antes=10&depois=10`
      );
      setContextoTemporal(response.data);
    } catch (error) {
      console.error('Erro ao carregar contexto temporal:', error);
      setContextoTemporal({ antes: [], depois: [] });
    }
  };

  const salvarBusca = () => {
    if (!nomeBusca.trim()) return;

    const novaBusca: BuscaSalva = {
      nome: nomeBusca,
      filtros: { ...filtros }
    };

    const novasBuscas = [...buscasSalvas, novaBusca];
    setBuscasSalvas(novasBuscas);
    
    if (typeof window !== 'undefined') {
      localStorage.setItem('buscas_logs_salvas', JSON.stringify(novasBuscas));
    }

    setNomeBusca('');
    setMostrarSalvarBusca(false);
  };

  const carregarBusca = (busca: BuscaSalva) => {
    setFiltros(busca.filtros);
  };

  const excluirBusca = (index: number) => {
    const novasBuscas = buscasSalvas.filter((_, i) => i !== index);
    setBuscasSalvas(novasBuscas);
    
    if (typeof window !== 'undefined') {
      localStorage.setItem('buscas_logs_salvas', JSON.stringify(novasBuscas));
    }
  };

  const abrirDetalhes = async (log: Log) => {
    setLogSelecionado(log);
    setMostrarDetalhes(true);
    await carregarContextoTemporal(log.id);
  };

  const highlightText = (text: string | null | undefined, query?: string) => {
    if (!text) return text || '';
    if (!query) return text;
    
    try {
      const parts = text.split(new RegExp(`(${query})`, 'gi'));
      return parts.map((part, i) => 
        part.toLowerCase() === query.toLowerCase() 
          ? <mark key={i} className="bg-yellow-200">{part}</mark>
          : part
      );
    } catch (error) {
      console.error('Erro ao destacar texto:', error);
      return text;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <nav className="bg-purple-900 dark:bg-purple-950 text-white shadow-lg">
        <div className="w-full max-w-full px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => router.push('/superadmin/dashboard')}
                className="text-purple-200 hover:text-white"
              >
                ← Voltar
              </button>
              <h1 className="text-2xl font-bold">Busca de Logs</h1>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="w-full max-w-full py-6 px-4 sm:px-6 lg:px-8">
        {/* Formulário de Busca */}
        <div className="bg-white p-6 rounded-lg shadow mb-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">Filtros de Busca</h2>
            <div className="flex gap-2">
              <button
                onClick={() => setMostrarSalvarBusca(true)}
                className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
              >
                💾 Salvar Busca
              </button>
              {buscasSalvas.length > 0 && (
                <div className="relative group">
                  <button className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
                    📋 Buscas Salvas ({buscasSalvas.length})
                  </button>
                  <div className="hidden group-hover:block absolute right-0 mt-2 w-64 bg-white rounded-lg shadow-xl z-10 max-h-96 overflow-y-auto">
                    {buscasSalvas.map((busca, index) => (
                      <div key={index} className="p-3 hover:bg-gray-50 border-b flex justify-between items-center">
                        <button
                          onClick={() => carregarBusca(busca)}
                          className="text-left flex-1"
                        >
                          <div className="font-medium text-gray-900">{busca.nome}</div>
                          <div className="text-xs text-gray-500">
                            {Object.keys(busca.filtros).length} filtros
                          </div>
                        </button>
                        <button
                          onClick={() => excluirBusca(index)}
                          className="text-red-600 hover:text-red-800 ml-2"
                        >
                          🗑️
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Busca por Texto
              </label>
              <input
                type="text"
                value={filtros.q || ''}
                onChange={(e) => setFiltros({ ...filtros, q: e.target.value })}
                placeholder="Buscar em todos os campos..."
                className="w-full px-3 py-2 border rounded-md"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Data Início
              </label>
              <input
                type="date"
                value={filtros.data_inicio || ''}
                onChange={(e) => setFiltros({ ...filtros, data_inicio: e.target.value })}
                className="w-full px-3 py-2 border rounded-md"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Data Fim
              </label>
              <input
                type="date"
                value={filtros.data_fim || ''}
                onChange={(e) => setFiltros({ ...filtros, data_fim: e.target.value })}
                className="w-full px-3 py-2 border rounded-md"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Loja
              </label>
              <input
                type="text"
                value={filtros.loja_nome || ''}
                onChange={(e) => setFiltros({ ...filtros, loja_nome: e.target.value })}
                placeholder="Nome da loja..."
                className="w-full px-3 py-2 border rounded-md"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Email do Usuário
              </label>
              <input
                type="text"
                value={filtros.usuario_email || ''}
                onChange={(e) => setFiltros({ ...filtros, usuario_email: e.target.value })}
                placeholder="email@exemplo.com"
                className="w-full px-3 py-2 border rounded-md"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Ação
              </label>
              <input
                type="text"
                value={filtros.acao || ''}
                onChange={(e) => setFiltros({ ...filtros, acao: e.target.value })}
                placeholder="Ex: login, criar, editar..."
                className="w-full px-3 py-2 border rounded-md"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Status
              </label>
              <select
                value={filtros.sucesso || ''}
                onChange={(e) => setFiltros({ ...filtros, sucesso: e.target.value })}
                className="w-full px-3 py-2 border rounded-md"
              >
                <option value="">Todos</option>
                <option value="true">Sucesso</option>
                <option value="false">Erro</option>
              </select>
            </div>
          </div>

          <div className="flex gap-2">
            <button
              onClick={buscarLogs}
              disabled={loading}
              className="px-6 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 disabled:bg-gray-400"
            >
              {loading ? 'Buscando...' : '🔍 Buscar'}
            </button>
            <button
              onClick={() => setFiltros({})}
              className="px-6 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
            >
              🔄 Limpar
            </button>
            <button
              onClick={exportarCSV}
              disabled={logs.length === 0}
              className="px-6 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-gray-400"
            >
              📥 CSV
            </button>
            <button
              onClick={exportarJSON}
              disabled={logs.length === 0}
              className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400"
            >
              📥 JSON
            </button>
          </div>
        </div>

        {/* Resultados */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-4 border-b">
            <h2 className="text-xl font-semibold">
              Resultados {logs.length > 0 && `(${logs.length})`}
            </h2>
          </div>

          {loading ? (
            <div className="p-8 text-center text-gray-500">
              Carregando...
            </div>
          ) : logs.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              Nenhum log encontrado. Use os filtros acima para buscar.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Data/Hora</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Usuário</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Loja</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Ação</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Recurso</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">IP</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Ações</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {logs.map((log) => (
                    <tr key={log.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm">
                        {formatDateTime(log.created_at)}
                      </td>
                      <td className="px-4 py-3 text-sm">
                        <div className="font-medium">{highlightText(log.usuario_nome, filtros.q)}</div>
                        <div className="text-gray-500 text-xs">{highlightText(log.usuario_email, filtros.q)}</div>
                      </td>
                      <td className="px-4 py-3 text-sm">
                        {highlightText(log.loja_nome, filtros.q)}
                      </td>
                      <td className="px-4 py-3 text-sm">
                        <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">
                          {highlightText(log.acao, filtros.q)}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm">
                        {highlightText(log.recurso, filtros.q)}
                      </td>
                      <td className="px-4 py-3 text-sm">
                        <span className={`px-2 py-1 rounded text-xs ${
                          log.sucesso 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {log.sucesso ? '✓ Sucesso' : '✗ Erro'}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-500">
                        {log.ip_address}
                      </td>
                      <td className="px-4 py-3 text-sm">
                        <button
                          onClick={() => abrirDetalhes(log)}
                          className="text-purple-600 hover:text-purple-800"
                        >
                          Ver Detalhes
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

      </main>

      {/* Modal de Detalhes */}
      {mostrarDetalhes && logSelecionado && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b flex justify-between items-center sticky top-0 bg-white">
              <h2 className="text-2xl font-bold">Detalhes do Log</h2>
              <button
                onClick={() => {
                  setMostrarDetalhes(false);
                  setLogSelecionado(null);
                  setContextoTemporal(null);
                }}
                className="text-gray-500 hover:text-gray-700 text-2xl"
              >
                ×
              </button>
            </div>

            <div className="p-6">
              {/* Informações Principais */}
              <div className="grid grid-cols-2 gap-4 mb-6">
                <div>
                  <label className="block text-sm font-medium text-gray-500">Data/Hora</label>
                  <p className="text-lg">{formatDateTime(logSelecionado.created_at)}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-500">Status</label>
                  <span className={`inline-block px-3 py-1 rounded text-sm ${
                    logSelecionado.sucesso 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {logSelecionado.sucesso ? '✓ Sucesso' : '✗ Erro'} ({logSelecionado.status_code})
                  </span>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-500">Usuário</label>
                  <p className="text-lg">{logSelecionado.usuario_nome || 'N/A'}</p>
                  <p className="text-sm text-gray-600">{logSelecionado.usuario_email || 'N/A'}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-500">Loja</label>
                  <p className="text-lg">{logSelecionado.loja_nome || 'N/A'}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-500">Ação</label>
                  <p className="text-lg">{logSelecionado.acao || 'N/A'}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-500">Recurso</label>
                  <p className="text-lg">{logSelecionado.recurso || 'N/A'}</p>
                </div>
                <div className="col-span-2">
                  <label className="block text-sm font-medium text-gray-500">URL</label>
                  <p className="text-sm font-mono bg-gray-100 p-2 rounded">
                    {logSelecionado.metodo_http || 'GET'} {logSelecionado.url || 'N/A'}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-500">IP Address</label>
                  <p className="text-lg">{logSelecionado.ip_address || 'N/A'}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-500">User Agent</label>
                  <p className="text-sm text-gray-600 truncate" title={logSelecionado.user_agent || ''}>
                    {logSelecionado.user_agent || 'N/A'}
                  </p>
                </div>
              </div>

              {/* Detalhes JSON */}
              {logSelecionado.detalhes && (
                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-500 mb-2">Detalhes</label>
                  <pre className="bg-gray-100 p-4 rounded text-sm overflow-x-auto">
                    {(() => {
                      try {
                        return JSON.stringify(JSON.parse(logSelecionado.detalhes), null, 2);
                      } catch (error) {
                        return logSelecionado.detalhes;
                      }
                    })()}
                  </pre>
                </div>
              )}

              {/* Contexto Temporal */}
              {contextoTemporal && (
                <div>
                  <h3 className="text-lg font-semibold mb-4">Contexto Temporal</h3>
                  
                  {/* Logs Anteriores */}
                  {contextoTemporal.antes && contextoTemporal.antes.length > 0 && (
                    <div className="mb-4">
                      <h4 className="text-sm font-medium text-gray-700 mb-2">
                        ⬆️ Ações Anteriores ({contextoTemporal.antes.length})
                      </h4>
                      <div className="space-y-2">
                        {contextoTemporal.antes.map((log) => (
                          <div key={log.id} className="bg-blue-50 p-3 rounded text-sm">
                            <div className="flex justify-between items-start">
                              <div>
                                <span className="font-medium">{log.acao || 'N/A'}</span>
                                <span className="text-gray-600"> - {log.recurso || 'N/A'}</span>
                              </div>
                              <span className="text-xs text-gray-500">
                                {new Date(log.created_at).toLocaleTimeString('pt-BR')}
                              </span>
                            </div>
                            <div className="text-xs text-gray-600 mt-1">
                              {log.usuario_nome || 'N/A'} • {log.loja_nome || 'N/A'}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Log Atual */}
                  <div className="bg-purple-100 border-2 border-purple-500 p-3 rounded mb-4">
                    <div className="flex items-center gap-2">
                      <span className="text-2xl">📍</span>
                      <div>
                        <div className="font-semibold">Log Atual</div>
                        <div className="text-sm text-gray-600">
                          {logSelecionado.acao || 'N/A'} - {logSelecionado.recurso || 'N/A'}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Logs Posteriores */}
                  {contextoTemporal.depois && contextoTemporal.depois.length > 0 && (
                    <div>
                      <h4 className="text-sm font-medium text-gray-700 mb-2">
                        ⬇️ Ações Posteriores ({contextoTemporal.depois.length})
                      </h4>
                      <div className="space-y-2">
                        {contextoTemporal.depois.map((log) => (
                          <div key={log.id} className="bg-green-50 p-3 rounded text-sm">
                            <div className="flex justify-between items-start">
                              <div>
                                <span className="font-medium">{log.acao || 'N/A'}</span>
                                <span className="text-gray-600"> - {log.recurso || 'N/A'}</span>
                              </div>
                              <span className="text-xs text-gray-500">
                                {new Date(log.created_at).toLocaleTimeString('pt-BR')}
                              </span>
                            </div>
                            <div className="text-xs text-gray-600 mt-1">
                              {log.usuario_nome || 'N/A'} • {log.loja_nome || 'N/A'}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Modal Salvar Busca */}
      {mostrarSalvarBusca && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h3 className="text-xl font-bold mb-4">Salvar Busca</h3>
            <input
              type="text"
              value={nomeBusca}
              onChange={(e) => setNomeBusca(e.target.value)}
              placeholder="Nome da busca..."
              className="w-full px-3 py-2 border rounded-md mb-4"
              autoFocus
            />
            <div className="flex gap-2 justify-end">
              <button
                onClick={() => {
                  setMostrarSalvarBusca(false);
                  setNomeBusca('');
                }}
                className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
              >
                Cancelar
              </button>
              <button
                onClick={salvarBusca}
                disabled={!nomeBusca.trim()}
                className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-gray-400"
              >
                Salvar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
