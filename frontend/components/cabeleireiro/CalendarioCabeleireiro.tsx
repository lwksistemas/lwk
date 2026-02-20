'use client';

import { useState, useEffect } from 'react';
import { ChevronLeft, ChevronRight, Plus, Calendar as CalendarIcon } from 'lucide-react';
import apiClient from '@/lib/api-client';
import { LojaInfo } from '@/types/dashboard';

interface Agendamento {
  id: number;
  cliente_nome: string;
  cliente_telefone: string;
  profissional_nome: string;
  servico_nome: string;
  data: string;
  horario: string;
  status: string;
  valor: number;
  observacoes?: string;
}

interface BloqueioAgenda {
  id: number;
  profissional_nome: string;
  data: string;
  horario_inicio: string;
  horario_fim: string;
  motivo: string;
}

type VisualizacaoTipo = 'dia' | 'semana' | 'mes';

const getStatusColor = (status: string): string => {
  switch (status) {
    case 'agendado':
      return '#3B82F6';
    case 'confirmado':
      return '#10B981';
    case 'em_atendimento':
      return '#F59E0B';
    case 'concluido':
      return '#10B981';
    case 'faltou':
      return '#A855F7';
    case 'cancelado':
      return '#F59E0B';
    default:
      return '#6B7280';
  }
};

const getStatusText = (status: string): string => {
  const statusMap: Record<string, string> = {
    'agendado': 'Agendado',
    'confirmado': 'Confirmado',
    'em_atendimento': 'Em Atendimento',
    'concluido': 'Concluído',
    'faltou': 'Faltou',
    'cancelado': 'Cancelado',
  };
  return statusMap[status] || status;
};

export default function CalendarioCabeleireiro({ loja, onNovoAgendamento }: { loja: LojaInfo; onNovoAgendamento?: () => void }) {
  const [agendamentos, setAgendamentos] = useState<Agendamento[]>([]);
  const [bloqueios, setBloqueios] = useState<BloqueioAgenda[]>([]);
  const [dataAtual, setDataAtual] = useState(new Date());
  const [visualizacao, setVisualizacao] = useState<VisualizacaoTipo>('dia');
  const [loading, setLoading] = useState(true);
  const [agendamentoSelecionado, setAgendamentoSelecionado] = useState<Agendamento | null>(null);

  useEffect(() => {
    carregarAgendamentos();
    // carregarAgendamentos omitido: definido abaixo
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dataAtual, visualizacao]);

  const carregarAgendamentos = async () => {
    try {
      setLoading(true);
      const dataFormatada = dataAtual.toISOString().split('T')[0];
      
      const response = await apiClient.get('/cabeleireiro/agendamentos/', {
        params: {
          data: dataFormatada,
          visualizacao: visualizacao,
        }
      });

      setAgendamentos(Array.isArray(response.data) ? response.data : []);
    } catch (error) {
      console.error('Erro ao carregar agendamentos:', error);
      setAgendamentos([]);
    } finally {
      setLoading(false);
    }
  };

  const mudarData = (dias: number) => {
    const novaData = new Date(dataAtual);
    if (visualizacao === 'dia') {
      novaData.setDate(novaData.getDate() + dias);
    } else if (visualizacao === 'semana') {
      novaData.setDate(novaData.getDate() + (dias * 7));
    } else {
      novaData.setMonth(novaData.getMonth() + dias);
    }
    setDataAtual(novaData);
  };

  const hoje = () => {
    setDataAtual(new Date());
  };

  const formatarData = () => {
    const opcoes: Intl.DateTimeFormatOptions = { 
      weekday: 'long', 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    };
    return dataAtual.toLocaleDateString('pt-BR', opcoes);
  };

  const gerarHorarios = () => {
    const horarios = [];
    for (let h = 8; h <= 20; h++) {
      horarios.push(`${h.toString().padStart(2, '0')}:00`);
      horarios.push(`${h.toString().padStart(2, '0')}:30`);
    }
    return horarios;
  };

  const horarios = gerarHorarios();

  const getAgendamentosPorHorario = (horario: string) => {
    return agendamentos.filter(a => a.horario === horario);
  };

  const atualizarStatus = async (agendamento: Agendamento, novoStatus: string) => {
    try {
      await apiClient.patch(`/cabeleireiro/agendamentos/${agendamento.id}/`, {
        status: novoStatus
      });
      carregarAgendamentos();
    } catch (error) {
      console.error('Erro ao atualizar status:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-purple-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Carregando agenda...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm">
      {/* Header do Calendário */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div className="flex items-center gap-3">
            <button
              onClick={() => mudarData(-1)}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
            <button
              onClick={hoje}
              className="px-4 py-2 bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400 rounded-lg hover:bg-purple-200 dark:hover:bg-purple-900/50 transition-colors font-medium"
            >
              Hoje
            </button>
            <button
              onClick={() => mudarData(1)}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            >
              <ChevronRight className="w-5 h-5" />
            </button>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white capitalize">
              {formatarData()}
            </h2>
          </div>

          <div className="flex items-center gap-3 w-full sm:w-auto">
            <div className="flex bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
              <button
                onClick={() => setVisualizacao('dia')}
                className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
                  visualizacao === 'dia'
                    ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow-sm'
                    : 'text-gray-600 dark:text-gray-400'
                }`}
              >
                Dia
              </button>
              <button
                onClick={() => setVisualizacao('semana')}
                className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
                  visualizacao === 'semana'
                    ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow-sm'
                    : 'text-gray-600 dark:text-gray-400'
                }`}
              >
                Semana
              </button>
              <button
                onClick={() => setVisualizacao('mes')}
                className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
                  visualizacao === 'mes'
                    ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow-sm'
                    : 'text-gray-600 dark:text-gray-400'
                }`}
              >
                Mês
              </button>
            </div>

            {onNovoAgendamento && (
              <button
                onClick={onNovoAgendamento}
                className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium"
              >
                <Plus className="w-5 h-5" />
                <span className="hidden sm:inline">Novo Agendamento</span>
                <span className="sm:hidden">Novo</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Grid de Horários */}
      <div className="p-4 overflow-x-auto">
        <div className="min-w-[600px]">
          {horarios.map((horario) => {
            const agendamentosHorario = getAgendamentosPorHorario(horario);
            
            return (
              <div
                key={horario}
                className="flex border-b border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
              >
                <div className="w-20 py-3 px-2 text-sm font-medium text-gray-600 dark:text-gray-400">
                  {horario}
                </div>
                <div className="flex-1 py-2 px-2">
                  {agendamentosHorario.length === 0 ? (
                    <div className="h-12 flex items-center text-gray-400 dark:text-gray-600 text-sm">
                      Disponível
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {agendamentosHorario.map((agendamento) => (
                        <div
                          key={agendamento.id}
                          onClick={() => setAgendamentoSelecionado(agendamento)}
                          className="p-3 rounded-lg cursor-pointer hover:shadow-md transition-all"
                          style={{ 
                            backgroundColor: getStatusColor(agendamento.status) + '20',
                            borderLeft: `4px solid ${getStatusColor(agendamento.status)}`
                          }}
                        >
                          <div className="flex justify-between items-start">
                            <div className="flex-1">
                              <p className="font-semibold text-gray-900 dark:text-white">
                                {agendamento.cliente_nome}
                              </p>
                              <p className="text-sm text-gray-600 dark:text-gray-400">
                                {agendamento.servico_nome}
                              </p>
                              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                com {agendamento.profissional_nome}
                              </p>
                            </div>
                            <span 
                              className="px-2 py-1 rounded-full text-xs font-medium text-white"
                              style={{ backgroundColor: getStatusColor(agendamento.status) }}
                            >
                              {getStatusText(agendamento.status)}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Modal de Detalhes do Agendamento */}
      {agendamentoSelecionado && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl max-w-md w-full p-6">
            <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
              Detalhes do Agendamento
            </h3>
            
            <div className="space-y-3">
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">Cliente</p>
                <p className="font-semibold text-gray-900 dark:text-white">
                  {agendamentoSelecionado.cliente_nome}
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {agendamentoSelecionado.cliente_telefone}
                </p>
              </div>

              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">Serviço</p>
                <p className="font-semibold text-gray-900 dark:text-white">
                  {agendamentoSelecionado.servico_nome}
                </p>
              </div>

              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">Profissional</p>
                <p className="font-semibold text-gray-900 dark:text-white">
                  {agendamentoSelecionado.profissional_nome}
                </p>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Data</p>
                  <p className="font-semibold text-gray-900 dark:text-white">
                    {new Date(agendamentoSelecionado.data).toLocaleDateString('pt-BR')}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Horário</p>
                  <p className="font-semibold text-gray-900 dark:text-white">
                    {agendamentoSelecionado.horario}
                  </p>
                </div>
              </div>

              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">Alterar Status</p>
                <div className="grid grid-cols-2 gap-2">
                  {['confirmado', 'em_atendimento', 'concluido', 'faltou', 'cancelado'].map((status) => (
                    <button
                      key={status}
                      onClick={() => {
                        atualizarStatus(agendamentoSelecionado, status);
                        setAgendamentoSelecionado(null);
                      }}
                      className="px-3 py-2 rounded-lg text-sm font-medium text-white transition-colors"
                      style={{ backgroundColor: getStatusColor(status) }}
                    >
                      {getStatusText(status)}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <button
              onClick={() => setAgendamentoSelecionado(null)}
              className="mt-6 w-full px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
            >
              Fechar
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
