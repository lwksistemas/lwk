'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { formatDateTime } from '@/lib/financeiro-helpers';

interface Resposta {
  id: number;
  usuario_nome: string;
  mensagem: string;
  is_suporte: boolean;
  created_at: string;
}

interface Chamado {
  id: number;
  titulo: string;
  descricao: string;
  tipo: string;
  status: string;
  prioridade: string;
  loja_slug: string;
  loja_nome: string;
  usuario_nome: string;
  usuario_email: string;
  respostas: Resposta[];
  created_at: string;
  updated_at: string;
  resolvido_em?: string;
}

export default function SuperadminSuportePage() {
  const router = useRouter();
  const [chamados, setChamados] = useState<Chamado[]>([]);
  const [loading, setLoading] = useState(true);
  const [chamadoSelecionado, setChamadoSelecionado] = useState<Chamado | null>(null);
  const [modalAberto, setModalAberto] = useState(false);
  const [resposta, setResposta] = useState('');
  const [enviandoResposta, setEnviandoResposta] = useState(false);
  const [filtroStatus, setFiltroStatus] = useState<string>('');

  useEffect(() => {
    loadChamados();
  }, [filtroStatus]);

  const loadChamados = async () => {
    try {
      setLoading(true);
      const params = filtroStatus ? { status: filtroStatus } : {};
      const response = await apiClient.get('/suporte/meus-chamados/', { params });
      setChamados(response.data);
    } catch (error) {
      console.error('Erro ao carregar chamados:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleVerDetalhes = (chamado: Chamado) => {
    setChamadoSelecionado(chamado);
    setModalAberto(true);
  };

  const handleEnviarResposta = async () => {
    if (!chamadoSelecionado || !resposta.trim()) return;
    
    try {
      setEnviandoResposta(true);
      await apiClient.post(`/suporte/chamados/${chamadoSelecionado.id}/responder/`, {
        mensagem: resposta
      });
      
      const response = await apiClient.get(`/suporte/chamados/${chamadoSelecionado.id}/`);
      setChamadoSelecionado(response.data);
      await loadChamados();
      setResposta('');
      alert('Resposta enviada com sucesso!');
    } catch (error) {
      console.error('Erro ao enviar resposta:', error);
      alert('Erro ao enviar resposta. Tente novamente.');
    } finally {
      setEnviandoResposta(false);
    }
  };

  const handleAlterarStatus = async (novoStatus: string) => {
    if (!chamadoSelecionado) return;
    
    try {
      await apiClient.patch(`/suporte/chamados/${chamadoSelecionado.id}/`, {
        status: novoStatus
      });
      
      const response = await apiClient.get(`/suporte/chamados/${chamadoSelecionado.id}/`);
      setChamadoSelecionado(response.data);
      await loadChamados();
      alert('Status atualizado com sucesso!');
    } catch (error) {
      console.error('Erro ao alterar status:', error);
      alert('Erro ao alterar status. Tente novamente.');
    }
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      'aberto': 'bg-yellow-100 text-yellow-800',
      'em_andamento': 'bg-blue-100 text-blue-800',
      'resolvido': 'bg-green-100 text-green-800',
      'fechado': 'bg-gray-100 text-gray-800',
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getStatusDisplay = (status: string) => {
    const displays: Record<string, string> = {
      'aberto': 'Aberto',
      'em_andamento': 'Em Andamento',
      'resolvido': 'Resolvido',
      'fechado': 'Fechado',
    };
    return displays[status] || status;
  };

  const getTipoDisplay = (tipo: string) => {
    const tipos: Record<string, string> = {
      'duvida': 'Dúvida',
      'treinamento': 'Treinamento',
      'problema': 'Problema Técnico',
      'sugestao': 'Sugestão',
      'outro': 'Outro'
    };
    return tipos[tipo] || tipo;
  };

  const getPrioridadeColor = (prioridade: string) => {
    const colors: Record<string, string> = {
      'baixa': 'text-green-600',
      'media': 'text-yellow-600',
      'alta': 'text-orange-600',
      'urgente': 'text-red-600',
    };
    return colors[prioridade] || 'text-gray-600';
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <nav className="bg-blue-600 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div>
              <h1 className="text-2xl font-bold">🎧 Suporte - Todos os Chamados</h1>
              <p className="text-blue-100 text-sm">Gerenciar chamados de todas as lojas</p>
            </div>
            <button
              onClick={() => router.push('/superadmin/dashboard')}
              className="px-4 py-2 bg-blue-700 hover:bg-blue-800 rounded-md transition-colors"
            >
              Voltar ao Dashboard
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {/* Estatísticas */}
          <div className="grid grid-cols-1 md:grid-cols-5 gap-6 mb-8">
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-gray-500 text-sm font-medium">Total</h3>
              <p className="text-3xl font-bold text-blue-600 mt-2">{chamados.length}</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-gray-500 text-sm font-medium">Abertos</h3>
              <p className="text-3xl font-bold text-yellow-600 mt-2">
                {chamados.filter(c => c.status === 'aberto').length}
              </p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-gray-500 text-sm font-medium">Em Andamento</h3>
              <p className="text-3xl font-bold text-blue-600 mt-2">
                {chamados.filter(c => c.status === 'em_andamento').length}
              </p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-gray-500 text-sm font-medium">Resolvidos</h3>
              <p className="text-3xl font-bold text-green-600 mt-2">
                {chamados.filter(c => c.status === 'resolvido').length}
              </p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-gray-500 text-sm font-medium">Fechados</h3>
              <p className="text-3xl font-bold text-gray-600 mt-2">
                {chamados.filter(c => c.status === 'fechado').length}
              </p>
            </div>
          </div>

          {/* Filtros */}
          <div className="bg-white shadow rounded-lg p-4 mb-6">
            <div className="flex items-center gap-4">
              <label className="text-sm font-medium text-gray-700">Filtrar por Status:</label>
              <select
                value={filtroStatus}
                onChange={(e) => setFiltroStatus(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Todos</option>
                <option value="aberto">Abertos</option>
                <option value="em_andamento">Em Andamento</option>
                <option value="resolvido">Resolvidos</option>
                <option value="fechado">Fechados</option>
              </select>
            </div>
          </div>

          {/* Lista de Chamados */}
          <div className="bg-white shadow rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Chamados de Suporte</h3>
            </div>
            <div className="p-6">
              {loading ? (
                <p className="text-center text-gray-500 py-12">Carregando...</p>
              ) : chamados.length === 0 ? (
                <div className="text-center py-12">
                  <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                  </svg>
                  <p className="mt-4 text-gray-500">Nenhum chamado encontrado</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {chamados.map((chamado) => (
                    <div
                      key={chamado.id}
                      className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer bg-gray-50/50"
                      onClick={() => handleVerDetalhes(chamado)}
                    >
                      <div className="flex justify-between items-start mb-2">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2 flex-wrap">
                            <span className="text-sm font-medium text-gray-500">#{chamado.id}</span>
                            <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(chamado.status)}`}>
                              {getStatusDisplay(chamado.status)}
                            </span>
                            <span className="text-xs text-gray-500">{getTipoDisplay(chamado.tipo)}</span>
                            <span className={`text-xs font-semibold ${getPrioridadeColor(chamado.prioridade)}`}>
                              {chamado.prioridade.toUpperCase()}
                            </span>
                          </div>
                          <h4 className="text-lg font-semibold text-gray-900 mb-1">{chamado.titulo}</h4>
                          <p className="text-sm text-gray-600 line-clamp-2 mb-2">{chamado.descricao}</p>
                          <div className="flex items-center gap-4 text-xs text-gray-500">
                            <span>🏪 {chamado.loja_nome}</span>
                            <span>👤 {chamado.usuario_nome}</span>
                            <span>📧 {chamado.usuario_email}</span>
                          </div>
                        </div>
                      </div>
                      <div className="flex justify-between items-center mt-3 pt-3 border-t border-gray-100">
                        <div className="flex items-center gap-4 text-sm text-gray-500">
                          <span>📅 {new Date(chamado.created_at).toLocaleDateString('pt-BR')}</span>
                          {chamado.respostas && chamado.respostas.length > 0 && (
                            <span className="flex items-center gap-1">
                              💬 {chamado.respostas.length} {chamado.respostas.length === 1 ? 'resposta' : 'respostas'}
                            </span>
                          )}
                        </div>
                        <button className="text-blue-600 hover:text-blue-800 text-sm font-medium">
                          Ver Detalhes →
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </main>

      {/* Modal de Detalhes */}
      {modalAberto && chamadoSelecionado && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            {/* Header */}
            <div className="bg-blue-600 text-white px-6 py-4 rounded-t-lg sticky top-0">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="text-xl font-bold">Chamado #{chamadoSelecionado.id}</h3>
                  <p className="text-blue-100 text-sm mt-1">{chamadoSelecionado.titulo}</p>
                  <p className="text-blue-200 text-xs mt-1">
                    🏪 {chamadoSelecionado.loja_nome} • 👤 {chamadoSelecionado.usuario_nome}
                  </p>
                </div>
                <button
                  onClick={() => setModalAberto(false)}
                  className="text-white hover:text-gray-200"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>

            {/* Conteúdo */}
            <div className="p-6">
              {/* Ações de Status */}
              <div className="mb-6 pb-6 border-b">
                <label className="text-sm font-medium text-gray-700 block mb-2">Alterar Status</label>
                <div className="flex gap-2 flex-wrap">
                  <button
                    onClick={() => handleAlterarStatus('aberto')}
                    disabled={chamadoSelecionado.status === 'aberto'}
                    className="px-4 py-2 bg-yellow-100 text-yellow-800 rounded-md hover:bg-yellow-200 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                  >
                    Aberto
                  </button>
                  <button
                    onClick={() => handleAlterarStatus('em_andamento')}
                    disabled={chamadoSelecionado.status === 'em_andamento'}
                    className="px-4 py-2 bg-blue-100 text-blue-800 rounded-md hover:bg-blue-200 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                  >
                    Em Andamento
                  </button>
                  <button
                    onClick={() => handleAlterarStatus('resolvido')}
                    disabled={chamadoSelecionado.status === 'resolvido'}
                    className="px-4 py-2 bg-green-100 text-green-800 rounded-md hover:bg-green-200 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                  >
                    Resolvido
                  </button>
                  <button
                    onClick={() => handleAlterarStatus('fechado')}
                    disabled={chamadoSelecionado.status === 'fechado'}
                    className="px-4 py-2 bg-gray-100 text-gray-800 rounded-md hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                  >
                    Fechado
                  </button>
                </div>
              </div>

              {/* Informações */}
              <div className="grid grid-cols-2 gap-4 mb-6 pb-6 border-b">
                <div>
                  <label className="text-sm font-medium text-gray-500">Status</label>
                  <p>
                    <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(chamadoSelecionado.status)}`}>
                      {getStatusDisplay(chamadoSelecionado.status)}
                    </span>
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Tipo</label>
                  <p className="text-gray-900">{getTipoDisplay(chamadoSelecionado.tipo)}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Prioridade</label>
                  <p className={`font-semibold ${getPrioridadeColor(chamadoSelecionado.prioridade)}`}>
                    {chamadoSelecionado.prioridade.toUpperCase()}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Loja</label>
                  <p className="text-gray-900">{chamadoSelecionado.loja_nome}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Criado em</label>
                  <p className="text-gray-900">
                    {formatDateTime(chamadoSelecionado.created_at)}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Última atualização</label>
                  <p className="text-gray-900">
                    {formatDateTime(chamadoSelecionado.updated_at)}
                  </p>
                </div>
              </div>

              {/* Descrição */}
              <div className="mb-6">
                <label className="text-sm font-medium text-gray-700 block mb-2">Descrição do Problema</label>
                <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                  <p className="text-gray-900 whitespace-pre-wrap">{chamadoSelecionado.descricao}</p>
                </div>
              </div>

              {/* Respostas */}
              <div className="mb-6">
                <label className="text-sm font-medium text-gray-700 block mb-3">
                  Histórico de Respostas ({chamadoSelecionado.respostas?.length || 0})
                </label>
                {chamadoSelecionado.respostas && chamadoSelecionado.respostas.length > 0 ? (
                  <div className="space-y-4">
                    {chamadoSelecionado.respostas.map((resposta) => (
                      <div
                        key={resposta.id}
                        className={`p-4 rounded-lg ${
                          resposta.is_suporte
                            ? 'bg-blue-50 border-l-4 border-blue-500'
                            : 'bg-gray-50 border-l-4 border-gray-300'
                        }`}
                      >
                        <div className="flex justify-between items-start mb-2">
                          <div className="flex items-center gap-2">
                            {resposta.is_suporte ? (
                              <span className="text-blue-600 font-semibold">🎧 Suporte</span>
                            ) : (
                              <span className="text-gray-700 font-semibold">👤 {resposta.usuario_nome}</span>
                            )}
                          </div>
                          <span className="text-xs text-gray-500">
                            {formatDateTime(resposta.created_at)}
                          </span>
                        </div>
                        <p className="text-gray-900 whitespace-pre-wrap">{resposta.mensagem}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 bg-gray-50 rounded-lg border border-gray-200">
                    <p className="text-gray-500">Nenhuma resposta ainda</p>
                    <p className="text-sm text-gray-400 mt-1">Seja o primeiro a responder este chamado</p>
                  </div>
                )}
              </div>

              {/* Área de Resposta do Suporte */}
              {chamadoSelecionado.status !== 'fechado' && (
                <div className="border-t pt-6">
                  <label className="text-sm font-medium text-gray-700 block mb-2">
                    Responder ao Cliente
                  </label>
                  <textarea
                    value={resposta}
                    onChange={(e) => setResposta(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                    rows={4}
                    placeholder="Digite sua resposta..."
                    disabled={enviandoResposta}
                  />
                  <div className="mt-3 flex justify-end">
                    <button
                      onClick={handleEnviarResposta}
                      disabled={!resposta.trim() || enviandoResposta}
                      className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                    >
                      {enviandoResposta ? 'Enviando...' : '📨 Enviar Resposta'}
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
