'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { authService } from '@/lib/auth';
import BotaoSuporte from '@/components/suporte/BotaoSuporte';

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
  loja_nome: string;
  loja_slug: string;
  usuario_nome: string;
  usuario_email: string;
  status: string;
  prioridade: string;
  respostas?: Resposta[];
  created_at: string;
  updated_at: string;
}

export default function SuporteDashboardPage() {
  const router = useRouter();
  const [chamados, setChamados] = useState<Chamado[]>([]);
  const [loading, setLoading] = useState(true);
  const [chamadoSelecionado, setChamadoSelecionado] = useState<Chamado | null>(null);
  const [modalAberto, setModalAberto] = useState(false);
  const [resposta, setResposta] = useState('');
  const [enviandoResposta, setEnviandoResposta] = useState(false);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const userType = authService.getUserType();
      if (userType !== 'suporte') {
        router.push('/suporte/login');
        return;
      }
      loadChamados();
    }
  }, [router]);

  const loadChamados = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/suporte/chamados/');
      setChamados(response.data.results || response.data);
    } catch (error) {
      console.error('Erro ao carregar chamados:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    authService.logout();
    router.push('/suporte/login');
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

  const getPrioridadeColor = (prioridade: string) => {
    const colors: Record<string, string> = {
      'baixa': 'text-gray-600',
      'media': 'text-yellow-600',
      'alta': 'text-orange-600',
      'urgente': 'text-red-600',
    };
    return colors[prioridade] || 'text-gray-600';
  };

  const handleAtender = (chamado: Chamado) => {
    // Recarregar o chamado completo com respostas
    apiClient.get(`/suporte/chamados/${chamado.id}/`)
      .then(response => {
        setChamadoSelecionado(response.data);
        setModalAberto(true);
      })
      .catch(error => {
        console.error('Erro ao carregar chamado:', error);
        // Fallback: usar dados da lista
        setChamadoSelecionado(chamado);
        setModalAberto(true);
      });
  };

  const handleIniciarAtendimento = async (chamadoId: number) => {
    try {
      await apiClient.patch(`/suporte/chamados/${chamadoId}/`, {
        status: 'em_andamento'
      });
      loadChamados();
      alert('Atendimento iniciado!');
    } catch (error) {
      console.error('Erro ao iniciar atendimento:', error);
      alert('Erro ao iniciar atendimento');
    }
  };

  const handleResolver = async (chamadoId: number) => {
    if (!confirm('Deseja marcar este chamado como resolvido?')) return;
    
    try {
      await apiClient.post(`/suporte/chamados/${chamadoId}/resolver/`);
      loadChamados();
      setModalAberto(false);
      alert('Chamado marcado como resolvido!');
    } catch (error) {
      console.error('Erro ao resolver chamado:', error);
      alert('Erro ao resolver chamado');
    }
  };

  const handleEnviarResposta = async () => {
    if (!chamadoSelecionado || !resposta.trim()) return;
    
    try {
      setEnviandoResposta(true);
      await apiClient.post(`/suporte/chamados/${chamadoSelecionado.id}/responder/`, {
        mensagem: resposta
      });
      
      // Recarregar o chamado completo para atualizar as respostas
      const response = await apiClient.get(`/suporte/chamados/${chamadoSelecionado.id}/`);
      setChamadoSelecionado(response.data);
      
      // Atualizar lista de chamados
      loadChamados();
      
      setResposta('');
      alert('Resposta enviada com sucesso!');
    } catch (error) {
      console.error('Erro ao enviar resposta:', error);
      alert('Erro ao enviar resposta');
    } finally {
      setEnviandoResposta(false);
    }
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

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <nav className="bg-blue-900 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div>
              <h1 className="text-2xl font-bold">Portal de Suporte</h1>
              <p className="text-blue-200 text-sm">Gerenciamento de Chamados</p>
            </div>
            <button
              onClick={handleLogout}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded-md transition-colors"
            >
              Sair
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
              <h3 className="text-gray-500 text-sm font-medium">Total de Chamados</h3>
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

          {/* Chamados */}
          <div className="bg-white shadow rounded-lg">
            <div className="px-6 py-4 border-b">
              <h3 className="text-lg font-semibold">Chamados</h3>
            </div>
            <div className="p-6">
              {loading ? (
                <p className="text-center text-gray-500">Carregando...</p>
              ) : chamados.length === 0 ? (
                <p className="text-center text-gray-500 py-12">Nenhum chamado encontrado</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead>
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          ID
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          Título
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          Loja
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          Status
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          Prioridade
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          Ações
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {chamados.map((chamado) => (
                        <tr key={chamado.id}>
                          <td className="px-6 py-4 whitespace-nowrap">#{chamado.id}</td>
                          <td className="px-6 py-4">{chamado.titulo}</td>
                          <td className="px-6 py-4 whitespace-nowrap">{chamado.loja_nome}</td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(chamado.status)}`}>
                              {chamado.status.replace('_', ' ')}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`font-semibold ${getPrioridadeColor(chamado.prioridade)}`}>
                              {chamado.prioridade}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm">
                            <button 
                              onClick={() => handleAtender(chamado)}
                              className="text-blue-600 hover:text-blue-800 font-medium"
                            >
                              Atender
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
      
      {/* Modal de Atendimento */}
      {modalAberto && chamadoSelecionado && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
            {/* Header */}
            <div className="bg-blue-900 text-white px-6 py-4 rounded-t-lg">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="text-xl font-bold">Chamado #{chamadoSelecionado.id}</h3>
                  <p className="text-blue-200 text-sm mt-1">{chamadoSelecionado.titulo}</p>
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
              {/* Informações do Chamado */}
              <div className="grid grid-cols-2 gap-4 mb-6">
                <div>
                  <label className="text-sm font-medium text-gray-500">Loja</label>
                  <p className="text-gray-900">{chamadoSelecionado.loja_nome}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Tipo</label>
                  <p className="text-gray-900">{getTipoDisplay(chamadoSelecionado.tipo)}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Usuário</label>
                  <p className="text-gray-900">{chamadoSelecionado.usuario_nome}</p>
                  <p className="text-sm text-gray-500">{chamadoSelecionado.usuario_email}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Status</label>
                  <p>
                    <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(chamadoSelecionado.status)}`}>
                      {chamadoSelecionado.status.replace('_', ' ')}
                    </span>
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Prioridade</label>
                  <p className={`font-semibold ${getPrioridadeColor(chamadoSelecionado.prioridade)}`}>
                    {chamadoSelecionado.prioridade.toUpperCase()}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Criado em</label>
                  <p className="text-gray-900">
                    {new Date(chamadoSelecionado.created_at).toLocaleString('pt-BR')}
                  </p>
                </div>
              </div>

              {/* Descrição */}
              <div className="mb-6">
                <label className="text-sm font-medium text-gray-500 block mb-2">Descrição</label>
                <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                  <p className="text-gray-900 whitespace-pre-wrap">{chamadoSelecionado.descricao}</p>
                </div>
              </div>

              {/* Ações Rápidas */}
              <div className="flex gap-3 mb-6">
                {chamadoSelecionado.status === 'aberto' && (
                  <button
                    onClick={() => handleIniciarAtendimento(chamadoSelecionado.id)}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                  >
                    Iniciar Atendimento
                  </button>
                )}
                {chamadoSelecionado.status !== 'resolvido' && chamadoSelecionado.status !== 'fechado' && (
                  <button
                    onClick={() => handleResolver(chamadoSelecionado.id)}
                    className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
                  >
                    Marcar como Resolvido
                  </button>
                )}
              </div>

              {/* Histórico de Respostas */}
              <div className="mb-6">
                <label className="text-sm font-medium text-gray-700 block mb-3">
                  Histórico de Respostas ({chamadoSelecionado.respostas?.length || 0})
                </label>
                {chamadoSelecionado.respostas && chamadoSelecionado.respostas.length > 0 ? (
                  <div className="space-y-4 max-h-96 overflow-y-auto">
                    {chamadoSelecionado.respostas.map((resp) => (
                      <div
                        key={resp.id}
                        className={`p-4 rounded-lg ${
                          resp.is_suporte
                            ? 'bg-blue-50 border-l-4 border-blue-500'
                            : 'bg-gray-50 border-l-4 border-gray-300'
                        }`}
                      >
                        <div className="flex justify-between items-start mb-2">
                          <div className="flex items-center gap-2">
                            {resp.is_suporte ? (
                              <span className="text-blue-600 font-semibold">🎧 Suporte - {resp.usuario_nome}</span>
                            ) : (
                              <span className="text-gray-700 font-semibold">👤 Cliente - {resp.usuario_nome}</span>
                            )}
                          </div>
                          <span className="text-xs text-gray-500">
                            {new Date(resp.created_at).toLocaleString('pt-BR')}
                          </span>
                        </div>
                        <p className="text-gray-900 whitespace-pre-wrap">{resp.mensagem}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 bg-gray-50 rounded-lg border border-gray-200">
                    <p className="text-gray-500">Nenhuma resposta ainda</p>
                    <p className="text-sm text-gray-400 mt-1">
                      Seja o primeiro a responder este chamado
                    </p>
                  </div>
                )}
              </div>

              {/* Área de Resposta */}
              <div>
                <label className="text-sm font-medium text-gray-700 block mb-2">
                  Adicionar Resposta
                </label>
                <textarea
                  value={resposta}
                  onChange={(e) => setResposta(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows={4}
                  placeholder="Digite sua resposta ao cliente..."
                />
                <div className="mt-3 flex justify-end">
                  <button
                    onClick={handleEnviarResposta}
                    disabled={!resposta.trim() || enviandoResposta}
                    className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                  >
                    {enviandoResposta ? 'Enviando...' : 'Enviar Resposta'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* Botão Flutuante de Suporte */}
      <BotaoSuporte />
    </div>
  );
}
