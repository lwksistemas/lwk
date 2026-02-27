'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { authService } from '@/lib/auth';

interface Violacao {
  id: number;
  tipo: string;
  tipo_display: string;
  tipo_display_friendly: string;
  criticidade: string;
  criticidade_display: string;
  criticidade_color: string;
  status: string;
  status_display: string;
  usuario_nome: string;
  usuario_email: string;
  loja_nome: string;
  descricao: string;
  ip_address: string;
  data_hora: string;
  logs_relacionados_count: number;
  resolvido_por_nome: string | null;
  data_resolucao_formatada: string | null;
}

interface Estatisticas {
  total: number;
  por_status: { [key: string]: number };
  por_criticidade: { [key: string]: number };
  por_tipo: { [key: string]: number };
}

export default function AlertasPage() {
  const router = useRouter();
  const [violacoes, setViolacoes] = useState<Violacao[]>([]);
  const [stats, setStats] = useState<Estatisticas | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedViolacao, setSelectedViolacao] = useState<Violacao | null>(null);
  const [showModal, setShowModal] = useState(false);
  
  // Filtros
  const [filtroStatus, setFiltroStatus] = useState('');
  const [filtroCriticidade, setFiltroCriticidade] = useState('');
  const [filtroTipo, setFiltroTipo] = useState('');

  useEffect(() => {
    if (typeof window !== 'undefined' && authService.getUserType() !== 'superadmin') {
      router.push('/superadmin/login');
      return;
    }
    loadData();
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
    // loadData omitido: definido abaixo e usa filtros do estado
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [router, filtroStatus, filtroCriticidade, filtroTipo]);

  const loadData = async () => {
    try {
      // Construir query params
      const params = new URLSearchParams();
      if (filtroStatus) params.append('status', filtroStatus);
      if (filtroCriticidade) params.append('criticidade', filtroCriticidade);
      if (filtroTipo) params.append('tipo', filtroTipo);
      
      const [violacoesRes, statsRes] = await Promise.all([
        apiClient.get(`/superadmin/violacoes-seguranca/?${params.toString()}`),
        apiClient.get('/superadmin/violacoes-seguranca/estatisticas/')
      ]);
      
      setViolacoes(violacoesRes.data.results || violacoesRes.data);
      setStats(statsRes.data);
    } catch (error) {
      console.error('Erro ao carregar alertas:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleResolver = async (id: number) => {
    try {
      await apiClient.post(`/superadmin/violacoes-seguranca/${id}/resolver/`, {
        notas: 'Resolvido via dashboard'
      });
      loadData();
      setShowModal(false);
    } catch (error) {
      console.error('Erro ao resolver violação:', error);
      alert('Erro ao resolver violação');
    }
  };

  const handleFalsoPositivo = async (id: number) => {
    try {
      await apiClient.post(`/superadmin/violacoes-seguranca/${id}/marcar_falso_positivo/`);
      loadData();
      setShowModal(false);
    } catch (error) {
      console.error('Erro ao marcar como falso positivo:', error);
      alert('Erro ao marcar como falso positivo');
    }
  };

  const getCriticidadeClass = (criticidade: string) => {
    const classes = {
      'critica': 'bg-red-100 text-red-800 border-red-300',
      'alta': 'bg-orange-100 text-orange-800 border-orange-300',
      'media': 'bg-yellow-100 text-yellow-800 border-yellow-300',
      'baixa': 'bg-green-100 text-green-800 border-green-300',
    };
    return classes[criticidade as keyof typeof classes] || 'bg-gray-100 text-gray-800';
  };

  const getStatusClass = (status: string) => {
    const classes = {
      'nova': 'bg-red-100 text-red-800',
      'investigando': 'bg-yellow-100 text-yellow-800',
      'resolvida': 'bg-green-100 text-green-800',
      'falso_positivo': 'bg-gray-100 text-gray-800',
    };
    return classes[status as keyof typeof classes] || 'bg-gray-100 text-gray-800';
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-xl">Carregando alertas...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">🚨 Alertas de Segurança</h1>
              <p className="mt-1 text-sm text-gray-500">
                Monitoramento de violações e atividades suspeitas
              </p>
            </div>
            <button
              onClick={() => router.push('/superadmin/dashboard')}
              className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-md transition-colors"
            >
              ← Voltar
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Estatísticas */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-gray-500 text-sm font-medium">Total de Violações</h3>
              <p className="text-3xl font-bold text-purple-600 mt-2">{stats.total}</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-gray-500 text-sm font-medium">Novas</h3>
              <p className="text-3xl font-bold text-red-600 mt-2">
                {stats.por_status.nova || 0}
              </p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-gray-500 text-sm font-medium">Críticas</h3>
              <p className="text-3xl font-bold text-red-600 mt-2">
                {stats.por_criticidade.critica || 0}
              </p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-gray-500 text-sm font-medium">Resolvidas</h3>
              <p className="text-3xl font-bold text-green-600 mt-2">
                {stats.por_status.resolvida || 0}
              </p>
            </div>
          </div>
        )}

        {/* Filtros */}
        <div className="bg-white p-6 rounded-lg shadow mb-6">
          <h3 className="text-lg font-semibold mb-4">Filtros</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Status
              </label>
              <select
                value={filtroStatus}
                onChange={(e) => setFiltroStatus(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <option value="">Todos</option>
                <option value="nova">Nova</option>
                <option value="investigando">Investigando</option>
                <option value="resolvida">Resolvida</option>
                <option value="falso_positivo">Falso Positivo</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Criticidade
              </label>
              <select
                value={filtroCriticidade}
                onChange={(e) => setFiltroCriticidade(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <option value="">Todas</option>
                <option value="critica">Crítica</option>
                <option value="alta">Alta</option>
                <option value="media">Média</option>
                <option value="baixa">Baixa</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Tipo
              </label>
              <select
                value={filtroTipo}
                onChange={(e) => setFiltroTipo(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <option value="">Todos</option>
                <option value="brute_force">Brute Force</option>
                <option value="rate_limit_exceeded">Rate Limit</option>
                <option value="acesso_cross_tenant">Cross-Tenant</option>
                <option value="privilege_escalation">Escalação de Privilégios</option>
                <option value="mass_deletion">Exclusão em Massa</option>
                <option value="ip_change">Mudança de IP</option>
              </select>
            </div>
          </div>
        </div>

        {/* Lista de Violações */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold">
              Violações Detectadas ({violacoes.length})
            </h3>
          </div>
          
          {violacoes.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <p className="text-lg">✅ Nenhuma violação encontrada</p>
              <p className="text-sm mt-2">O sistema está seguro!</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {violacoes.map((violacao) => (
                <div
                  key={violacao.id}
                  className="p-6 hover:bg-gray-50 cursor-pointer transition-colors"
                  onClick={() => {
                    setSelectedViolacao(violacao);
                    setShowModal(true);
                  }}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${getCriticidadeClass(violacao.criticidade)}`}>
                          {violacao.criticidade_display.toUpperCase()}
                        </span>
                        <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getStatusClass(violacao.status)}`}>
                          {violacao.status_display}
                        </span>
                        <span className="text-sm text-gray-500">{violacao.data_hora}</span>
                      </div>
                      
                      <h4 className="text-lg font-semibold text-gray-900 mb-1">
                        {violacao.tipo_display}
                      </h4>
                      
                      <p className="text-gray-700 mb-2">{violacao.descricao}</p>
                      
                      <div className="flex items-center gap-4 text-sm text-gray-600">
                        <span>👤 {violacao.usuario_nome}</span>
                        <span>📧 {violacao.usuario_email}</span>
                        <span>🌐 {violacao.ip_address}</span>
                        {violacao.loja_nome && <span>🏪 {violacao.loja_nome}</span>}
                        <span>📋 {violacao.logs_relacionados_count} logs</span>
                      </div>
                    </div>
                    
                    <div className="ml-4">
                      <button className="text-purple-600 hover:text-purple-800 font-medium">
                        Ver Detalhes →
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Modal de Detalhes */}
      {showModal && selectedViolacao && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <div className="flex justify-between items-start">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">
                    {selectedViolacao.tipo_display}
                  </h2>
                  <p className="text-sm text-gray-500 mt-1">{selectedViolacao.data_hora}</p>
                </div>
                <button
                  onClick={() => setShowModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>
            </div>
            
            <div className="p-6 space-y-4">
              <div>
                <h3 className="font-semibold text-gray-900 mb-2">Criticidade e Status</h3>
                <div className="flex gap-2">
                  <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${getCriticidadeClass(selectedViolacao.criticidade)}`}>
                    {selectedViolacao.criticidade_display.toUpperCase()}
                  </span>
                  <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getStatusClass(selectedViolacao.status)}`}>
                    {selectedViolacao.status_display}
                  </span>
                </div>
              </div>
              
              <div>
                <h3 className="font-semibold text-gray-900 mb-2">Descrição</h3>
                <p className="text-gray-700">{selectedViolacao.descricao}</p>
              </div>
              
              <div>
                <h3 className="font-semibold text-gray-900 mb-2">Informações do Usuário</h3>
                <div className="bg-gray-50 p-4 rounded-md space-y-2">
                  <p><strong>Nome:</strong> {selectedViolacao.usuario_nome}</p>
                  <p><strong>Email:</strong> {selectedViolacao.usuario_email}</p>
                  <p><strong>IP:</strong> {selectedViolacao.ip_address}</p>
                  {selectedViolacao.loja_nome && (
                    <p><strong>Loja:</strong> {selectedViolacao.loja_nome}</p>
                  )}
                </div>
              </div>
              
              <div>
                <h3 className="font-semibold text-gray-900 mb-2">Logs Relacionados</h3>
                <p className="text-gray-700">
                  {selectedViolacao.logs_relacionados_count} log(s) relacionado(s)
                </p>
              </div>
              
              {selectedViolacao.resolvido_por_nome && (
                <div>
                  <h3 className="font-semibold text-gray-900 mb-2">Resolução</h3>
                  <div className="bg-green-50 p-4 rounded-md space-y-2">
                    <p><strong>Resolvido por:</strong> {selectedViolacao.resolvido_por_nome}</p>
                    <p><strong>Data:</strong> {selectedViolacao.data_resolucao_formatada}</p>
                  </div>
                </div>
              )}
            </div>
            
            {selectedViolacao.status === 'nova' && (
              <div className="p-6 border-t border-gray-200 flex gap-3">
                <button
                  onClick={() => handleResolver(selectedViolacao.id)}
                  className="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-md transition-colors"
                >
                  ✓ Marcar como Resolvida
                </button>
                <button
                  onClick={() => handleFalsoPositivo(selectedViolacao.id)}
                  className="flex-1 px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-md transition-colors"
                >
                  ⚠ Falso Positivo
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
