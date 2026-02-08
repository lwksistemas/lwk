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

export function ModalConfiguracoes({ loja, onClose }: ModalConfiguracoesProps) {
  const [historico, setHistorico] = useState<HistoricoAcesso[]>([]);
  const [estatisticas, setEstatisticas] = useState<Estatisticas | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingStats, setLoadingStats] = useState(false);
  const [activeTab, setActiveTab] = useState<'historico' | 'estatisticas' | 'geral'>('historico');
  
  // Filtros
  const [filtros, setFiltros] = useState({
    usuario: '',
    acao: '',
    recurso: '',
    data_inicio: '',
    data_fim: '',
    sucesso: ''
  });

  useEffect(() => {
    if (activeTab === 'historico') {
      carregarHistorico();
    } else if (activeTab === 'estatisticas') {
      carregarEstatisticas();
    }
  }, [activeTab, filtros]);

  const carregarHistorico = async () => {
    try {
      setLoading(true);
      
      // Construir query params
      const params = new URLSearchParams();
      if (filtros.usuario) params.append('usuario', filtros.usuario);
      if (filtros.acao) params.append('acao', filtros.acao);
      if (filtros.recurso) params.append('recurso', filtros.recurso);
      if (filtros.data_inicio) params.append('data_inicio', filtros.data_inicio);
      if (filtros.data_fim) params.append('data_fim', filtros.data_fim);
      if (filtros.sucesso) params.append('sucesso', filtros.sucesso);
      
      const response = await apiClient.get(`/clinica/historico-acessos/?${params.toString()}`);
      const data = extractArrayData<HistoricoAcesso>(response);
      setHistorico(data);
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
    } finally {
      setLoadingStats(false);
    }
  };

  const limparFiltros = () => {
    setFiltros({
      usuario: '',
      acao: '',
      recurso: '',
      data_inicio: '',
      data_fim: '',
      sucesso: ''
    });
  };

  const getAcaoIcon = (acao: string) => {
    const icons: Record<string, string> = {
      'login': '🔐',
      'logout': '🚪',
      'criar': '➕',
      'editar': '✏️',
      'excluir': '🗑️',
      'visualizar': '👁️',
      'exportar': '📥',
      'importar': '📤'
    };
    return icons[acao.toLowerCase()] || '📝';
  };
  
  const getAcaoColor = (acao: string) => {
    const colors: Record<string, string> = {
      'login': 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300',
      'logout': 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300',
      'criar': 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300',
      'editar': 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300',
      'excluir': 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300',
    };
    return colors[acao.toLowerCase()] || 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300';
  };

  return (
    <Modal isOpen={true} onClose={onClose} maxWidth="5xl">
      <div className="p-6">
        <h2 className="text-2xl font-bold mb-6 flex items-center gap-2" style={{ color: loja.cor_primaria }}>
          ⚙️ Configurações da Loja
        </h2>

        {/* Tabs */}
        <div className="flex border-b mb-6">
          <button
            onClick={() => setActiveTab('historico')}
            className={`px-6 py-3 font-medium transition-colors ${
              activeTab === 'historico'
                ? 'border-b-2 text-blue-600 dark:text-blue-400'
                : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
            }`}
            style={activeTab === 'historico' ? { borderColor: loja.cor_primaria, color: loja.cor_primaria } : {}}
          >
            📊 Histórico de Login
          </button>
          <button
            onClick={() => setActiveTab('geral')}
            className={`px-6 py-3 font-medium transition-colors ${
              activeTab === 'geral'
                ? 'border-b-2 text-blue-600 dark:text-blue-400'
                : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
            }`}
            style={activeTab === 'geral' ? { borderColor: loja.cor_primaria, color: loja.cor_primaria } : {}}
          >
            ⚙️ Configurações Gerais
          </button>
        </div>

        {/* Conteúdo */}
        {activeTab === 'historico' ? (
          <div>
            <div className="flex items-center justify-between mb-4">
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Histórico de acessos e ações realizadas na loja
              </p>
              <button
                onClick={carregarHistorico}
                className="px-4 py-2 text-sm text-white rounded-lg hover:opacity-90 min-h-[40px]"
                style={{ backgroundColor: loja.cor_primaria }}
              >
                🔄 Atualizar
              </button>
            </div>

            {loading ? (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400">Carregando...</div>
            ) : historico.length === 0 ? (
              <div className="text-center py-12">
                <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
                  <span className="text-3xl">📊</span>
                </div>
                <p className="text-lg mb-2 text-gray-700 dark:text-gray-300">Nenhum registro encontrado</p>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  O histórico de login será registrado automaticamente
                </p>
              </div>
            ) : (
              <div className="space-y-3 max-h-[60vh] overflow-y-auto">
                {historico.map((registro) => (
                  <div
                    key={registro.id}
                    className="flex items-start gap-4 p-4 border dark:border-gray-600 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                  >
                    <div
                      className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 text-xl"
                      style={{ backgroundColor: `${loja.cor_primaria}20` }}
                    >
                      {getAcaoIcon(registro.acao)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <p className="font-semibold text-gray-900 dark:text-white">
                          {registro.usuario_nome}
                        </p>
                        <span className="px-2 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 text-xs font-medium rounded-full">
                          {registro.acao}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                        🌐 IP: {registro.ip_address}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-500">
                        🕐 {formatarDataHora(registro.data_hora)}
                      </p>
                      {registro.detalhes && (
                        <p className="text-sm text-gray-700 dark:text-gray-300 mt-2 p-2 bg-gray-50 dark:bg-gray-700 rounded">
                          {registro.detalhes}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : (
          <div className="text-center py-12">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
              <span className="text-3xl">⚙️</span>
            </div>
            <p className="text-lg mb-2 text-gray-700 dark:text-gray-300">Configurações Gerais</p>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">
              Funcionalidade em desenvolvimento
            </p>
          </div>
        )}

        <div className="flex justify-end gap-3 pt-4 border-t dark:border-gray-600 mt-6">
          <button
            onClick={onClose}
            className="px-6 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-900 dark:text-white min-h-[40px]"
          >
            Fechar
          </button>
        </div>
      </div>
    </Modal>
  );
}
