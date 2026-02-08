'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api-client';
import { logger } from '@/lib/logger';

interface HistoricoAcesso {
  id: number;
  usuario_nome: string;
  usuario_email: string;
  loja_nome: string;
  loja_slug: string;
  acao: string;
  acao_display: string;
  recurso: string;
  ip_address: string;
  navegador: string;
  sucesso: boolean;
  created_at: string;
  data_hora: string;
}

interface Estatisticas {
  periodo: {
    inicio: string;
    fim: string;
  };
  total_acessos: number;
  total_logins: number;
  total_sucesso: number;
  total_erros: number;
  acoes_por_tipo: Array<{ acao: string; total: number }>;
  usuarios_mais_ativos: Array<{ usuario_email: string; usuario_nome: string; total: number }>;
  lojas_mais_ativas: Array<{ loja_id: number; loja_nome: string; loja_slug: string; total: number }>;
}

export default function HistoricoAcessosPage() {
  const [historico, setHistorico] = useState<HistoricoAcesso[]>([]);
  const [estatisticas, setEstatisticas] = useState<Estatisticas | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingStats, setLoadingStats] = useState(true);
  
  // Filtros
  const [filtros, setFiltros] = useState({
    search: '',
    acao: '',
    loja_slug: '',
    data_inicio: '',
    data_fim: '',
    sucesso: '',
  });
  
  // Paginação
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  
  // Tabs
  const [activeTab, setActiveTab] = useState<'historico' | 'estatisticas'>('historico');

  useEffect(() => {
    loadHistorico();
    loadEstatisticas();
  }, [filtros, page]);

  const loadHistorico = async () => {
    try {
      setLoading(true);
      
      // Construir query params
      const params = new URLSearchParams();
      if (filtros.search) params.append('search', filtros.search);
      if (filtros.acao) params.append('acao', filtros.acao);
      if (filtros.loja_slug) params.append('loja_slug', filtros.loja_slug);
      if (filtros.data_inicio) params.append('data_inicio', filtros.data_inicio);
      if (filtros.data_fim) params.append('data_fim', filtros.data_fim);
      if (filtros.sucesso) params.append('sucesso', filtros.sucesso);
      params.append('page', page.toString());
      
      const response = await apiClient.get(`/superadmin/historico-acessos/?${params.toString()}`);
      
      setHistorico(response.data.results || response.data);
      
      // Calcular total de páginas (se houver paginação)
      if (response.data.count) {
        setTotalPages(Math.ceil(response.data.count / 100));
      }
    } catch (error) {
      logger.error('Erro ao carregar histórico:', error);
      alert('Erro ao carregar histórico de acessos');
    } finally {
      setLoading(false);
    }
  };

  const loadEstatisticas = async () => {
    try {
      setLoadingStats(true);
      
      const params = new URLSearchParams();
      if (filtros.data_inicio) params.append('data_inicio', filtros.data_inicio);
      if (filtros.data_fim) params.append('data_fim', filtros.data_fim);
      
      const response = await apiClient.get(`/superadmin/historico-acessos/estatisticas/?${params.toString()}`);
      setEstatisticas(response.data);
    } catch (error) {
      logger.error('Erro ao carregar estatísticas:', error);
    } finally {
      setLoadingStats(false);
    }
  };

  const handleExportar = async () => {
    try {
      const params = new URLSearchParams();
      if (filtros.search) params.append('search', filtros.search);
      if (filtros.acao) params.append('acao', filtros.acao);
      if (filtros.loja_slug) params.append('loja_slug', filtros.loja_slug);
      if (filtros.data_inicio) params.append('data_inicio', filtros.data_inicio);
      if (filtros.data_fim) params.append('data_fim', filtros.data_fim);
      if (filtros.sucesso) params.append('sucesso', filtros.sucesso);
      
      const response = await apiClient.get(`/superadmin/historico-acessos/exportar/?${params.toString()}`, {
        responseType: 'blob',
      });
      
      // Criar link para download
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `historico_acessos_${new Date().toISOString().split('T')[0]}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      alert('✅ Histórico exportado com sucesso!');
    } catch (error) {
      logger.error('Erro ao exportar:', error);
      alert('❌ Erro ao exportar histórico');
    }
  };

  const handleFiltroChange = (key: string, value: string) => {
    setFiltros(prev => ({ ...prev, [key]: value }));
    setPage(1); // Reset para primeira página
  };

  const limparFiltros = () => {
    setFiltros({
      search: '',
      acao: '',
      loja_slug: '',
      data_inicio: '',
      data_fim: '',
      sucesso: '',
    });
    setPage(1);
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          📊 Histórico de Acessos Global
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Monitore todas as ações realizadas no sistema por todos os usuários
        </p>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-200 dark:border-gray-700 mb-6">
        <button
          onClick={() => setActiveTab('historico')}
          className={`px-6 py-3 font-medium transition-colors ${
            activeTab === 'historico'
              ? 'border-b-2 border-blue-500 text-blue-600 dark:text-blue-400'
              : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
          }`}
        >
          📋 Histórico ({historico.length})
        </button>
        <button
          onClick={() => setActiveTab('estatisticas')}
          className={`px-6 py-3 font-medium transition-colors ${
            activeTab === 'estatisticas'
              ? 'border-b-2 border-blue-500 text-blue-600 dark:text-blue-400'
              : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
          }`}
        >
          📈 Estatísticas
        </button>
      </div>

      {/* Tab: Histórico */}
      {activeTab === 'historico' && (
        <>
          {/* Filtros */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              🔍 Filtros
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              {/* Busca */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Buscar (nome, email, loja)
                </label>
                <input
                  type="text"
                  value={filtros.search}
                  onChange={(e) => handleFiltroChange('search', e.target.value)}
                  placeholder="Digite para buscar..."
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md 
                             bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
              </div>

              {/* Ação */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Ação
                </label>
                <select
                  value={filtros.acao}
                  onChange={(e) => handleFiltroChange('acao', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md 
                             bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  <option value="">Todas</option>
                  <option value="login">Login</option>
                  <option value="logout">Logout</option>
                  <option value="criar">Criar</option>
                  <option value="editar">Editar</option>
                  <option value="excluir">Excluir</option>
                </select>
              </div>

              {/* Sucesso */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Status
                </label>
                <select
                  value={filtros.sucesso}
                  onChange={(e) => handleFiltroChange('sucesso', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md 
                             bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  <option value="">Todos</option>
                  <option value="true">Sucesso</option>
                  <option value="false">Erro</option>
                </select>
              </div>

              {/* Data Início */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Data Início
                </label>
                <input
                  type="date"
                  value={filtros.data_inicio}
                  onChange={(e) => handleFiltroChange('data_inicio', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md 
                             bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
              </div>

              {/* Data Fim */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Data Fim
                </label>
                <input
                  type="date"
                  value={filtros.data_fim}
                  onChange={(e) => handleFiltroChange('data_fim', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md 
                             bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
              </div>

              {/* Loja Slug */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Slug da Loja
                </label>
                <input
                  type="text"
                  value={filtros.loja_slug}
                  onChange={(e) => handleFiltroChange('loja_slug', e.target.value)}
                  placeholder="Ex: harmonis-000126"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md 
                             bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
              </div>
            </div>

            {/* Botões */}
            <div className="flex gap-3">
              <button
                onClick={limparFiltros}
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md 
                           text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                🔄 Limpar Filtros
              </button>
              <button
                onClick={handleExportar}
                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
              >
                📥 Exportar CSV
              </button>
            </div>
          </div>

          {/* Tabela */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
            {loading ? (
              <div className="p-8 text-center text-gray-500 dark:text-gray-400">
                Carregando...
              </div>
            ) : historico.length === 0 ? (
              <div className="p-8 text-center text-gray-500 dark:text-gray-400">
                Nenhum registro encontrado
              </div>
            ) : (
              <>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50 dark:bg-gray-700">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                          Data/Hora
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                          Usuário
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                          Loja
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                          Ação
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                          Recurso
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                          IP
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                          Navegador
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                          Status
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                      {historico.map((item) => (
                        <tr key={item.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                          <td className="px-4 py-3 text-sm text-gray-900 dark:text-white whitespace-nowrap">
                            {item.data_hora}
                          </td>
                          <td className="px-4 py-3 text-sm">
                            <div className="text-gray-900 dark:text-white font-medium">
                              {item.usuario_nome}
                            </div>
                            <div className="text-gray-500 dark:text-gray-400 text-xs">
                              {item.usuario_email}
                            </div>
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-900 dark:text-white">
                            {item.loja_nome || 'SuperAdmin'}
                          </td>
                          <td className="px-4 py-3 text-sm">
                            <span className="px-2 py-1 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300">
                              {item.acao_display}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-900 dark:text-white">
                            {item.recurso || '-'}
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">
                            {item.ip_address}
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">
                            {item.navegador}
                          </td>
                          <td className="px-4 py-3 text-sm">
                            {item.sucesso ? (
                              <span className="px-2 py-1 rounded-full text-xs font-medium bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300">
                                ✓ Sucesso
                              </span>
                            ) : (
                              <span className="px-2 py-1 rounded-full text-xs font-medium bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300">
                                ✗ Erro
                              </span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Paginação */}
                {totalPages > 1 && (
                  <div className="px-4 py-3 border-t border-gray-200 dark:border-gray-700 flex items-center justify-between">
                    <button
                      onClick={() => setPage(p => Math.max(1, p - 1))}
                      disabled={page === 1}
                      className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md 
                                 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700
                                 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      ← Anterior
                    </button>
                    <span className="text-sm text-gray-700 dark:text-gray-300">
                      Página {page} de {totalPages}
                    </span>
                    <button
                      onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                      disabled={page === totalPages}
                      className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md 
                                 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700
                                 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Próxima →
                    </button>
                  </div>
                )}
              </>
            )}
          </div>
        </>
      )}

      {/* Tab: Estatísticas */}
      {activeTab === 'estatisticas' && (
        <div className="space-y-6">
          {loadingStats ? (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-8 text-center text-gray-500 dark:text-gray-400">
              Carregando estatísticas...
            </div>
          ) : estatisticas ? (
            <>
              {/* Cards de Resumo */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                  <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">Total de Acessos</div>
                  <div className="text-3xl font-bold text-gray-900 dark:text-white">
                    {estatisticas.total_acessos.toLocaleString()}
                  </div>
                </div>
                
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                  <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">Logins</div>
                  <div className="text-3xl font-bold text-blue-600 dark:text-blue-400">
                    {estatisticas.total_logins.toLocaleString()}
                  </div>
                </div>
                
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                  <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">Sucessos</div>
                  <div className="text-3xl font-bold text-green-600 dark:text-green-400">
                    {estatisticas.total_sucesso.toLocaleString()}
                  </div>
                </div>
                
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                  <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">Erros</div>
                  <div className="text-3xl font-bold text-red-600 dark:text-red-400">
                    {estatisticas.total_erros.toLocaleString()}
                  </div>
                </div>
              </div>

              {/* Ações por Tipo */}
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                  Ações por Tipo
                </h3>
                <div className="space-y-2">
                  {estatisticas.acoes_por_tipo.map((item) => (
                    <div key={item.acao} className="flex items-center justify-between">
                      <span className="text-gray-700 dark:text-gray-300 capitalize">{item.acao}</span>
                      <span className="font-semibold text-gray-900 dark:text-white">
                        {item.total.toLocaleString()}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Usuários Mais Ativos */}
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                  👥 Usuários Mais Ativos (Top 10)
                </h3>
                <div className="space-y-3">
                  {estatisticas.usuarios_mais_ativos.map((item, index) => (
                    <div key={item.usuario_email} className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <span className="text-2xl font-bold text-gray-400 dark:text-gray-600">
                          #{index + 1}
                        </span>
                        <div>
                          <div className="text-gray-900 dark:text-white font-medium">
                            {item.usuario_nome}
                          </div>
                          <div className="text-sm text-gray-500 dark:text-gray-400">
                            {item.usuario_email}
                          </div>
                        </div>
                      </div>
                      <span className="font-semibold text-gray-900 dark:text-white">
                        {item.total.toLocaleString()} ações
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Lojas Mais Ativas */}
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                  🏪 Lojas Mais Ativas (Top 10)
                </h3>
                <div className="space-y-3">
                  {estatisticas.lojas_mais_ativas.map((item, index) => (
                    <div key={item.loja_id} className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <span className="text-2xl font-bold text-gray-400 dark:text-gray-600">
                          #{index + 1}
                        </span>
                        <div>
                          <div className="text-gray-900 dark:text-white font-medium">
                            {item.loja_nome}
                          </div>
                          <div className="text-sm text-gray-500 dark:text-gray-400">
                            {item.loja_slug}
                          </div>
                        </div>
                      </div>
                      <span className="font-semibold text-gray-900 dark:text-white">
                        {item.total.toLocaleString()} ações
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </>
          ) : (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-8 text-center text-gray-500 dark:text-gray-400">
              Nenhuma estatística disponível
            </div>
          )}
        </div>
      )}
    </div>
  );
}
