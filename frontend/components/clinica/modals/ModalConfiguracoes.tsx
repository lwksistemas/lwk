'use client';

import { useState, useEffect } from 'react';
import { Modal } from '@/components/ui/Modal';
import apiClient from '@/lib/api-client';
import { extractArrayData, formatApiError } from '@/lib/api-helpers';

interface LojaInfo {
  id: number;
  nome: string;
  slug: string;
  cor_primaria: string;
}

interface HistoricoAcesso {
  id: number;
  usuario_nome: string;
  usuario_email: string;
  acao: string;
  acao_display: string;
  recurso: string;
  recurso_id: number | null;
  ip_address: string;
  navegador: string;
  sucesso: boolean;
  data_hora: string;
  detalhes?: string;
}

interface Estatisticas {
  total_acoes: number;
  acoes_por_tipo: Array<{ acao: string; total: number }>;
  usuarios_mais_ativos: Array<{ usuario_nome: string; usuario_email: string; total: number }>;
  recursos_mais_acessados: Array<{ recurso: string; total: number }>;
}

interface ModalConfiguracoesProps {
  loja: LojaInfo;
  onClose: () => void;
}

type TabType = 'historico' | 'estatisticas' | 'geral';

export default function ModalConfiguracoes({ loja, onClose }: ModalConfiguracoesProps) {
  const [historico, setHistorico] = useState<HistoricoAcesso[]>([]);
  const [estatisticas, setEstatisticas] = useState<Estatisticas | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingStats, setLoadingStats] = useState(false);
  const [activeTab, setActiveTab] = useState<TabType>('historico');
  const [filtros, setFiltros] = useState({
    usuario: '',
    acao: '',
    recurso: '',
    data_inicio: '',
    data_fim: '',
    sucesso: ''
  });

  useEffect(() => {
    if (activeTab === 'historico') carregarHistorico();
    else if (activeTab === 'estatisticas') carregarEstatisticas();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab, filtros]);

  const carregarHistorico = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (filtros.usuario) params.append('usuario', filtros.usuario);
      if (filtros.acao) params.append('acao', filtros.acao);
      if (filtros.recurso) params.append('recurso', filtros.recurso);
      if (filtros.data_inicio) params.append('data_inicio', filtros.data_inicio);
      if (filtros.data_fim) params.append('data_fim', filtros.data_fim);
      if (filtros.sucesso) params.append('sucesso', filtros.sucesso);
      
      const response = await apiClient.get(`/clinica/historico-acessos/?${params.toString()}`);
      setHistorico(extractArrayData<HistoricoAcesso>(response));
    } catch (error) {
      console.error('Erro ao carregar histórico:', error);
      alert(formatApiError(error));
      setHistorico([]);
    } finally {
      setLoading(false);
    }
  };
  
  const carregarEstatisticas = async () => {
    try {
      setLoadingStats(true);
      const params = new URLSearchParams();
      if (filtros.data_inicio) params.append('data_inicio', filtros.data_inicio);
      if (filtros.data_fim) params.append('data_fim', filtros.data_fim);
      const response = await apiClient.get(`/clinica/historico-acessos/estatisticas/?${params.toString()}`);
      setEstatisticas(response.data);
    } catch (error) {
      console.error('Erro ao carregar estatísticas:', error);
      setEstatisticas(null);
    } finally {
      setLoadingStats(false);
    }
  };

  return (
    <Modal isOpen={true} onClose={onClose} maxWidth="5xl">
      <div className="p-6">
        <h2 className="text-2xl font-bold mb-6" style={{ color: loja.cor_primaria }}>
          ⚙️ Configurações da Loja
        </h2>

        {/* Tabs */}
        <div className="flex border-b mb-6">
          {[
            { id: 'historico' as TabType, label: 'Histórico de Acessos', icon: '📊' },
            { id: 'estatisticas' as TabType, label: 'Estatísticas', icon: '📈' },
            { id: 'geral' as TabType, label: 'Configurações Gerais', icon: '⚙️' }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-6 py-3 font-medium transition-colors ${
                activeTab === tab.id ? 'border-b-2' : 'text-gray-500 hover:text-gray-700 dark:text-gray-400'
              }`}
              style={activeTab === tab.id ? { borderColor: loja.cor_primaria, color: loja.cor_primaria } : {}}
            >
              {tab.icon} {tab.label}
            </button>
          ))}
        </div>

        {/* Histórico Tab */}
        {activeTab === 'historico' && (
          <div>
            {/* Filtros */}
            <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 mb-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-3">
                <input
                  type="text"
                  placeholder="Buscar usuário..."
                  value={filtros.usuario}
                  onChange={(e) => setFiltros({ ...filtros, usuario: e.target.value })}
                  className="px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                />
                <select
                  value={filtros.acao}
                  onChange={(e) => setFiltros({ ...filtros, acao: e.target.value })}
                  className="px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                >
                  <option value="">Todas as ações</option>
                  <option value="criar">Criar</option>
                  <option value="editar">Editar</option>
                  <option value="excluir">Excluir</option>
                </select>
                <input
                  type="text"
                  placeholder="Recurso..."
                  value={filtros.recurso}
                  onChange={(e) => setFiltros({ ...filtros, recurso: e.target.value })}
                  className="px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                />
              </div>
              <div className="flex gap-3">
                <input
                  type="date"
                  value={filtros.data_inicio}
                  onChange={(e) => setFiltros({ ...filtros, data_inicio: e.target.value })}
                  className="px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                />
                <input
                  type="date"
                  value={filtros.data_fim}
                  onChange={(e) => setFiltros({ ...filtros, data_fim: e.target.value })}
                  className="px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                />
                <button
                  onClick={() => setFiltros({ usuario: '', acao: '', recurso: '', data_inicio: '', data_fim: '', sucesso: '' })}
                  className="px-4 py-2 border rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
                >
                  🔄 Limpar
                </button>
              </div>
            </div>

            {/* Lista */}
            {loading ? (
              <div className="text-center py-8">Carregando...</div>
            ) : historico.length === 0 ? (
              <div className="text-center py-12">
                <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
                  <span className="text-3xl">📊</span>
                </div>
                <p className="text-lg mb-2">Nenhum registro encontrado</p>
                <p className="text-sm text-gray-500">O histórico será registrado automaticamente</p>
              </div>
            ) : (
              <div className="space-y-3 max-h-[60vh] overflow-y-auto">
                {historico.map((reg) => (
                  <div key={reg.id} className="flex items-start gap-4 p-4 border dark:border-gray-600 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700/50">
                    <div className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 text-xl" style={{ backgroundColor: `${loja.cor_primaria}20` }}>
                      {reg.acao === 'criar' ? '➕' : reg.acao === 'editar' ? '✏️' : reg.acao === 'excluir' ? '🗑️' : '📝'}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1 flex-wrap">
                        <p className="font-semibold">{reg.usuario_nome}</p>
                        <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300">
                          {reg.acao_display}
                        </span>
                        {reg.recurso && (
                          <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-300">
                            {reg.recurso}{reg.recurso_id && ` #${reg.recurso_id}`}
                          </span>
                        )}
                        <span className={`text-xs ${reg.sucesso ? 'text-green-600' : 'text-red-600'}`}>
                          {reg.sucesso ? '✓ Sucesso' : '✗ Erro'}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        🌐 {reg.ip_address} • {reg.navegador}
                      </p>
                      <p className="text-xs text-gray-500">
                        🕐 {reg.data_hora}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Estatísticas Tab */}
        {activeTab === 'estatisticas' && (
          <div>
            {loadingStats ? (
              <div className="text-center py-8">Carregando...</div>
            ) : !estatisticas ? (
              <div className="text-center py-12">Nenhuma estatística disponível</div>
            ) : (
              <div className="space-y-6">
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 border dark:border-gray-700">
                  <div className="text-sm text-gray-500 mb-1">Total de Ações</div>
                  <div className="text-3xl font-bold" style={{ color: loja.cor_primaria }}>
                    {estatisticas.total_acoes.toLocaleString()}
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 border dark:border-gray-700">
                    <h3 className="text-lg font-semibold mb-4">Ações por Tipo</h3>
                    <div className="space-y-2">
                      {estatisticas.acoes_por_tipo.map((item) => (
                        <div key={item.acao} className="flex justify-between">
                          <span className="capitalize">{item.acao}</span>
                          <span className="font-semibold">{item.total}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 border dark:border-gray-700">
                    <h3 className="text-lg font-semibold mb-4">👥 Usuários Mais Ativos</h3>
                    <div className="space-y-3">
                      {estatisticas.usuarios_mais_ativos.map((item, idx) => (
                        <div key={item.usuario_email} className="flex justify-between">
                          <div>
                            <div className="font-medium">{item.usuario_nome}</div>
                            <div className="text-sm text-gray-500">{item.usuario_email}</div>
                          </div>
                          <span className="font-semibold">{item.total}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 border dark:border-gray-700">
                    <h3 className="text-lg font-semibold mb-4">📊 Recursos Mais Acessados</h3>
                    <div className="space-y-2">
                      {estatisticas.recursos_mais_acessados.map((item) => (
                        <div key={item.recurso} className="flex justify-between">
                          <span>{item.recurso}</span>
                          <span className="font-semibold">{item.total}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Geral Tab */}
        {activeTab === 'geral' && (
          <div className="text-center py-12">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
              <span className="text-3xl">⚙️</span>
            </div>
            <p className="text-lg mb-2">Configurações Gerais</p>
            <p className="text-sm text-gray-500">Funcionalidade em desenvolvimento</p>
          </div>
        )}

        {/* Footer */}
        <div className="flex justify-end gap-3 pt-4 border-t dark:border-gray-600 mt-6">
          <button
            onClick={onClose}
            className="px-6 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
          >
            Fechar
          </button>
        </div>
      </div>
    </Modal>
  );
}
