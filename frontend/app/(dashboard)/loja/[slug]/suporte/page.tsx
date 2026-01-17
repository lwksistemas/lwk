'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { authService } from '@/lib/auth';

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
  loja_nome: string;
  usuario_nome: string;
  respostas: Resposta[];
  created_at: string;
  updated_at: string;
  resolvido_em?: string;
}

export default function SuporteHistoricoPage() {
  const router = useRouter();
  const params = useParams();
  const slug = params.slug as string;
  
  const [chamados, setChamados] = useState<Chamado[]>([]);
  const [loading, setLoading] = useState(true);
  const [chamadoSelecionado, setChamadoSelecionado] = useState<Chamado | null>(null);
  const [modalAberto, setModalAberto] = useState(false);
  const [resposta, setResposta] = useState('');
  const [enviandoResposta, setEnviandoResposta] = useState(false);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const userType = authService.getUserType();
      if (userType !== 'loja') {
        router.push(`/loja/${slug}/login`);
        return;
      }
      loadChamados();
    }
  }, [router, slug]);

  const loadChamados = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/suporte/meus-chamados/');
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

  const handleEnviarResposta = async () => {
    if (!chamadoSelecionado || !resposta.trim()) return;
    
    try {
      setEnviandoResposta(true);
      await apiClient.post(`/suporte/chamados/${chamadoSelecionado.id}/responder/`, {
        mensagem: resposta
      });
      
      // Recarregar o chamado específico para atualizar o histórico
      const response = await apiClient.get(`/suporte/chamados/${chamadoSelecionado.id}/`);
      setChamadoSelecionado(response.data);
      
      // Atualizar também a lista de chamados
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

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <nav className="bg-blue-600 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div>
              <h1 className="text-2xl font-bold">Meus Chamados de Suporte</h1>
              <p className="text-blue-100 text-sm">Histórico e acompanhamento</p>
            </div>
            <button
              onClick={() => router.push(`/loja/${slug}/dashboard`)}
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
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
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
          </div>

          {/* Lista de Chamados */}
          <div className="bg-white shadow rounded-lg">
            <div className="px-6 py-4 border-b">
              <h3 className="text-lg font-semibold">Histórico de Chamados</h3>
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
                  <p className="text-sm text-gray-400 mt-2">Use o botão flutuante para abrir um novo chamado</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {chamados.map((chamado) => (
                    <div
                      key={chamado.id}
                      className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
                      onClick={() => handleVerDetalhes(chamado)}
                    >
                      <div className="flex justify-between items-start mb-2">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <span className="text-sm font-medium text-gray-500">#{chamado.id}</span>
                            <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(chamado.status)}`}>
                              {getStatusDisplay(chamado.status)}
                            </span>
                            <span className="text-xs text-gray-500">{getTipoDisplay(chamado.tipo)}</span>
                          </div>
                          <h4 className="text-lg font-semibold text-gray-900 mb-1">{chamado.titulo}</h4>
                          <p className="text-sm text-gray-600 line-clamp-2">{chamado.descricao}</p>
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
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            {/* Header */}
            <div className="bg-blue-600 text-white px-6 py-4 rounded-t-lg sticky top-0">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="text-xl font-bold">Chamado #{chamadoSelecionado.id}</h3>
                  <p className="text-blue-100 text-sm mt-1">{chamadoSelecionado.titulo}</p>
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
                  <label className="text-sm font-medium text-gray-500">Criado em</label>
                  <p className="text-gray-900">
                    {new Date(chamadoSelecionado.created_at).toLocaleString('pt-BR')}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Última atualização</label>
                  <p className="text-gray-900">
                    {new Date(chamadoSelecionado.updated_at).toLocaleString('pt-BR')}
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
                            {new Date(resposta.created_at).toLocaleString('pt-BR')}
                          </span>
                        </div>
                        <p className="text-gray-900 whitespace-pre-wrap">{resposta.mensagem}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 bg-gray-50 rounded-lg border border-gray-200">
                    <p className="text-gray-500">Nenhuma resposta ainda</p>
                    <p className="text-sm text-gray-400 mt-1">
                      {chamadoSelecionado.status === 'aberto' 
                        ? 'Aguardando atendimento do suporte'
                        : 'O suporte está analisando seu chamado'}
                    </p>
                  </div>
                )}
              </div>

              {/* Área de Resposta do Usuário */}
              {chamadoSelecionado.status !== 'fechado' && (
                <div className="border-t pt-6">
                  <label className="text-sm font-medium text-gray-700 block mb-2">
                    Adicionar Comentário
                  </label>
                  <p className="text-xs text-gray-500 mb-3">
                    Use este campo para responder ao suporte ou adicionar informações ao chamado
                  </p>
                  <textarea
                    value={resposta}
                    onChange={(e) => setResposta(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    rows={4}
                    placeholder="Digite sua mensagem..."
                    disabled={enviandoResposta}
                  />
                  <div className="mt-3 flex justify-end">
                    <button
                      onClick={handleEnviarResposta}
                      disabled={!resposta.trim() || enviandoResposta}
                      className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                    >
                      {enviandoResposta ? 'Enviando...' : 'Enviar Resposta'}
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
