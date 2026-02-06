'use client';

import { useState, useEffect } from 'react';
import apiClient from '@/lib/api-client';
import { extractArrayData, formatApiError } from '@/lib/api-helpers';
import { Modal } from '@/components/ui/Modal';

interface Agendamento {
  id: number;
  cliente: number;
  cliente_nome: string;
  profissional: number | null;
  profissional_nome: string;
  servico: number;
  servico_nome: string;
  data: string;
  horario: string;
  status: string;
  valor: string | number;
  observacoes?: string;
}

interface Bloqueio {
  id: number;
  profissional: number | null;
  profissional_nome: string | null;
  data_inicio: string;
  data_fim: string;
  horario_inicio: string | null;
  horario_fim: string | null;
  motivo: string;
  observacoes?: string;
}

interface Profissional {
  id: number;
  nome: string;
}

interface Cliente {
  id: number;
  nome: string;
  telefone: string;
}

interface Servico {
  id: number;
  nome: string;
  preco: string;
  duracao: number;
}

interface LojaInfo {
  id: number;
  nome: string;
  slug: string;
  cor_primaria: string;
}

type VisualizacaoTipo = 'dia' | 'semana' | 'mes';

// Configuração de cores por status
const STATUS_COLORS = {
  agendado: { bg: '#3B82F6', text: 'white', label: 'Agendado' },
  confirmado: { bg: '#10B981', text: 'white', label: 'Confirmado' },
  em_atendimento: { bg: '#F59E0B', text: 'white', label: 'Em Atendimento' },
  concluido: { bg: '#6B7280', text: 'white', label: 'Concluído' },
  cancelado: { bg: '#EF4444', text: 'white', label: 'Cancelado' },
  atrasado: { bg: '#DC2626', text: 'white', label: 'Atrasado' }
};

export default function CalendarioCabeleireiro({ loja, onClose }: { loja: LojaInfo; onClose: () => void }) {
  const [agendamentos, setAgendamentos] = useState<Agendamento[]>([]);
  const [bloqueios, setBloqueios] = useState<Bloqueio[]>([]);
  const [profissionais, setProfissionais] = useState<Profissional[]>([]);
  const [clientes, setClientes] = useState<Cliente[]>([]);
  const [servicos, setServicos] = useState<Servico[]>([]);
  const [profissionalSelecionado, setProfissionalSelecionado] = useState<string>('');
  const [visualizacao, setVisualizacao] = useState<VisualizacaoTipo>('semana');
  const [dataAtual, setDataAtual] = useState(new Date());
  const [loading, setLoading] = useState(true);
  const [showModalAgendamento, setShowModalAgendamento] = useState(false);
  const [agendamentoSelecionado, setAgendamentoSelecionado] = useState<Agendamento | null>(null);
  const [dataHoraSelecionada, setDataHoraSelecionada] = useState<{data: string, horario: string} | null>(null);

  useEffect(() => {
    carregarDadosIniciais();
  }, []);

  useEffect(() => {
    carregarAgendamentos();
  }, [dataAtual, visualizacao, profissionalSelecionado]);

  const carregarDadosIniciais = async () => {
    try {
      const [profRes, clientesRes, servicosRes] = await Promise.all([
        apiClient.get('/cabeleireiro/profissionais/'),
        apiClient.get('/cabeleireiro/clientes/'),
        apiClient.get('/cabeleireiro/servicos/')
      ]);
      
      setProfissionais(extractArrayData<Profissional>(profRes));
      setClientes(extractArrayData<Cliente>(clientesRes));
      setServicos(extractArrayData<Servico>(servicosRes));
    } catch (error) {
      console.error('Erro ao carregar dados iniciais:', error);
    }
  };

  const carregarAgendamentos = async () => {
    setLoading(true);
    try {
      const { dataInicio, dataFim } = calcularPeriodo();

      const params: Record<string, string> = {
        data_inicio: dataInicio,
        data_fim: dataFim,
      };
      if (profissionalSelecionado) {
        params.profissional_id = profissionalSelecionado;
      }

      const [agendamentosRes, bloqueiosRes] = await Promise.all([
        apiClient.get('/cabeleireiro/agendamentos/', { params }),
        apiClient.get('/cabeleireiro/bloqueios/', { params })
      ]);

      setAgendamentos(extractArrayData<Agendamento>(agendamentosRes));
      setBloqueios(extractArrayData<Bloqueio>(bloqueiosRes));
    } catch (error) {
      console.error('Erro ao carregar agendamentos:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleNovoAgendamento = (data?: string, horario?: string) => {
    setAgendamentoSelecionado(null);
    setDataHoraSelecionada(data && horario ? { data, horario } : null);
    setShowModalAgendamento(true);
  };

  const handleEditarAgendamento = (agendamento: Agendamento) => {
    setAgendamentoSelecionado(agendamento);
    setDataHoraSelecionada(null);
    setShowModalAgendamento(true);
  };

  const handleExcluirAgendamento = async (agendamento: Agendamento) => {
    if (!confirm(`Deseja excluir o agendamento de ${agendamento.cliente_nome}?`)) return;
    
    try {
      await apiClient.delete(`/cabeleireiro/agendamentos/${agendamento.id}/`);
      alert('✅ Agendamento excluído com sucesso!');
      carregarAgendamentos();
    } catch (error) {
      console.error('Erro ao excluir agendamento:', error);
      alert(formatApiError(error));
    }
  };

  const getStatusColor = (status: string) => {
    return STATUS_COLORS[status as keyof typeof STATUS_COLORS] || STATUS_COLORS.agendado;
  };

  const verificarAtrasado = (agendamento: Agendamento): boolean => {
    if (agendamento.status === 'concluido' || agendamento.status === 'cancelado') return false;
    
    const agora = new Date();
    const dataAgendamento = new Date(`${agendamento.data}T${agendamento.horario}`);
    
    return dataAgendamento < agora;
  };

  const getBloqueioAt = (dataStr: string, horario: string): Bloqueio | undefined => {
    return bloqueios.find((b) => {
      if (dataStr < b.data_inicio || dataStr > b.data_fim) return false;
      
      if (!b.horario_inicio) return true;
      
      const horarioMin = parseInt(horario.split(':')[0]) * 60 + parseInt(horario.split(':')[1]);
      const inicioMin = parseInt(b.horario_inicio.split(':')[0]) * 60 + parseInt(b.horario_inicio.split(':')[1]);
      const fimMin = b.horario_fim ? parseInt(b.horario_fim.split(':')[0]) * 60 + parseInt(b.horario_fim.split(':')[1]) : inicioMin;
      
      return horarioMin >= inicioMin && horarioMin <= fimMin;
    });
  };

  const calcularPeriodo = () => {
    const hoje = new Date(dataAtual);
    let dataInicio: string;
    let dataFim: string;

    switch (visualizacao) {
      case 'dia':
        dataInicio = dataFim = formatarData(hoje);
        break;
      
      case 'semana':
        const inicioSemana = new Date(hoje);
        inicioSemana.setDate(hoje.getDate() - hoje.getDay());
        const fimSemana = new Date(inicioSemana);
        fimSemana.setDate(inicioSemana.getDate() + 6);
        
        dataInicio = formatarData(inicioSemana);
        dataFim = formatarData(fimSemana);
        break;
      
      case 'mes':
        const inicioMes = new Date(hoje.getFullYear(), hoje.getMonth(), 1);
        const fimMes = new Date(hoje.getFullYear(), hoje.getMonth() + 1, 0);
        
        dataInicio = formatarData(inicioMes);
        dataFim = formatarData(fimMes);
        break;
    }

    return { dataInicio, dataFim };
  };

  const formatarData = (data: Date): string => {
    return data.toISOString().split('T')[0];
  };

  const navegarPeriodo = (direcao: 'anterior' | 'proximo') => {
    const novaData = new Date(dataAtual);
    
    switch (visualizacao) {
      case 'dia':
        novaData.setDate(novaData.getDate() + (direcao === 'proximo' ? 1 : -1));
        break;
      case 'semana':
        novaData.setDate(novaData.getDate() + (direcao === 'proximo' ? 7 : -7));
        break;
      case 'mes':
        novaData.setMonth(novaData.getMonth() + (direcao === 'proximo' ? 1 : -1));
        break;
    }
    
    setDataAtual(novaData);
  };

  const obterTituloPeriodo = (): string => {
    const opcoes: Intl.DateTimeFormatOptions = { 
      year: 'numeric', 
      month: 'long',
      day: visualizacao === 'dia' ? 'numeric' : undefined
    };
    
    if (visualizacao === 'semana') {
      const { dataInicio, dataFim } = calcularPeriodo();
      const inicio = new Date(dataInicio);
      const fim = new Date(dataFim);
      
      return `${inicio.getDate()} - ${fim.getDate()} de ${inicio.toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' })}`;
    }
    
    return dataAtual.toLocaleDateString('pt-BR', opcoes);
  };

  const renderizarVisualizacao = () => {
    switch (visualizacao) {
      case 'dia':
        return <VisualizacaoDia />;
      case 'semana':
        return <VisualizacaoSemana />;
      case 'mes':
        return <VisualizacaoMes />;
    }
  };

  // Visualização por dia
  const VisualizacaoDia = () => {
    const agendamentosDoDia = agendamentos.filter(ag => ag.data === formatarData(dataAtual));
    const horarios = Array.from({ length: 13 }, (_, i) => `${(i + 8).toString().padStart(2, '0')}:00`);

    return (
      <div className="bg-white rounded-lg shadow">
        <div className="p-4 border-b">
          <h3 className="text-lg font-semibold">Agendamentos do Dia</h3>
        </div>
        <div className="p-4 max-h-[500px] overflow-y-auto">
          <div className="space-y-2">
            {horarios.map(horario => {
              const agendamento = agendamentosDoDia.find(ag => ag.horario.startsWith(horario.split(':')[0]));
              const bloqueio = getBloqueioAt(formatarData(dataAtual), horario);
              const isAtrasado = agendamento ? verificarAtrasado(agendamento) : false;
              const statusFinal = isAtrasado ? 'atrasado' : agendamento?.status || '';
              const statusColor = agendamento ? getStatusColor(statusFinal) : null;
              
              return (
                <div key={horario} className="flex items-center border-b pb-2">
                  <div className="w-16 text-sm text-gray-600 font-mono">
                    {horario}
                  </div>
                  <div className="flex-1 ml-4">
                    {bloqueio ? (
                      <div className="p-3 rounded-lg bg-red-50 border-2 border-red-200">
                        <p className="font-semibold text-red-800">🚫 Bloqueado</p>
                        <p className="text-sm text-red-600">{bloqueio.motivo}</p>
                        {bloqueio.profissional_nome && (
                          <p className="text-xs text-red-500">Prof: {bloqueio.profissional_nome}</p>
                        )}
                      </div>
                    ) : agendamento ? (
                      <div 
                        className="p-3 rounded-lg cursor-pointer hover:opacity-90 transition-all"
                        style={{ backgroundColor: statusColor?.bg, color: statusColor?.text }}
                        onClick={() => handleEditarAgendamento(agendamento)}
                      >
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <p className="font-semibold">{agendamento.cliente_nome}</p>
                            <p className="text-sm opacity-90">{agendamento.servico_nome}</p>
                            <p className="text-xs opacity-80">Prof: {agendamento.profissional_nome}</p>
                            <p className="text-xs font-semibold mt-1">
                              R$ {typeof agendamento.valor === 'number' ? agendamento.valor.toFixed(2) : parseFloat(agendamento.valor).toFixed(2)}
                            </p>
                          </div>
                          <div className="flex flex-col gap-1">
                            <span className="text-xs px-2 py-1 bg-white/20 rounded">
                              {statusColor?.label}
                            </span>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleExcluirAgendamento(agendamento);
                              }}
                              className="text-xs px-2 py-1 bg-white/20 hover:bg-white/30 rounded"
                            >
                              🗑️
                            </button>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <button
                        onClick={() => handleNovoAgendamento(formatarData(dataAtual), horario)}
                        className="w-full p-2 text-left text-gray-400 hover:bg-gray-50 rounded border-2 border-dashed border-gray-200 hover:border-gray-300 transition-all"
                      >
                        + Agendar
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    );
  };

  // Visualização por semana
  const VisualizacaoSemana = () => {
    const { dataInicio } = calcularPeriodo();
    const inicioSemana = new Date(dataInicio);
    const diasSemana = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb'];
    const horarios = Array.from({ length: 13 }, (_, i) => `${(i + 8).toString().padStart(2, '0')}:00`);

    return (
      <div className="bg-white rounded-lg shadow overflow-x-auto">
        <div className="min-w-[800px]">
          {/* Cabeçalho dos dias */}
          <div className="grid grid-cols-8 border-b">
            <div className="p-3 text-sm font-semibold text-gray-600">Horário</div>
            {Array.from({ length: 7 }, (_, i) => {
              const dia = new Date(inicioSemana);
              dia.setDate(inicioSemana.getDate() + i);
              
              return (
                <div key={i} className="p-3 text-center border-l">
                  <div className="text-sm font-semibold text-gray-900">
                    {diasSemana[dia.getDay()]}
                  </div>
                  <div className="text-lg font-bold" style={{ color: loja.cor_primaria }}>
                    {dia.getDate()}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Grade de horários */}
          <div className="max-h-[500px] overflow-y-auto">
            {horarios.map(horario => (
              <div key={horario} className="grid grid-cols-8 border-b">
                <div className="p-3 text-sm text-gray-600 font-mono border-r">
                  {horario}
                </div>
                {Array.from({ length: 7 }, (_, i) => {
                  const dia = new Date(inicioSemana);
                  dia.setDate(inicioSemana.getDate() + i);
                  const dataStr = formatarData(dia);
                  
                  const agendamento = agendamentos.find(ag => 
                    ag.data === dataStr && ag.horario.startsWith(horario.split(':')[0])
                  );
                  const bloqueio = getBloqueioAt(dataStr, horario);
                  const isAtrasado = agendamento ? verificarAtrasado(agendamento) : false;
                  const statusFinal = isAtrasado ? 'atrasado' : agendamento?.status || '';
                  const statusColor = agendamento ? getStatusColor(statusFinal) : null;

                  return (
                    <div key={i} className="p-2 border-l min-h-[60px]">
                      {bloqueio ? (
                        <div className="p-2 rounded text-xs bg-red-50 border border-red-200 text-red-800">
                          <div className="font-semibold truncate">🚫 Bloqueado</div>
                          <div className="truncate">{bloqueio.motivo}</div>
                        </div>
                      ) : agendamento ? (
                        <div
                          className="p-2 rounded text-xs cursor-pointer hover:opacity-90 transition-all"
                          style={{ backgroundColor: statusColor?.bg, color: statusColor?.text }}
                          onClick={() => handleEditarAgendamento(agendamento)}
                        >
                          <div className="font-semibold truncate">{agendamento.cliente_nome}</div>
                          <div className="truncate opacity-90">{agendamento.servico_nome}</div>
                          <div className="text-[10px] mt-1 opacity-80">{statusColor?.label}</div>
                        </div>
                      ) : (
                        <button
                          onClick={() => handleNovoAgendamento(dataStr, horario)}
                          className="w-full h-full text-gray-300 hover:text-gray-500 hover:bg-gray-50 rounded border border-dashed border-transparent hover:border-gray-300 transition-all"
                        >
                          +
                        </button>
                      )}
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  // Visualização por mês
  const VisualizacaoMes = () => {
    const ano = dataAtual.getFullYear();
    const mes = dataAtual.getMonth();
    const primeiroDia = new Date(ano, mes, 1);
    const ultimoDia = new Date(ano, mes + 1, 0);
    const diasNoMes = ultimoDia.getDate();
    const diaSemanaInicio = primeiroDia.getDay();

    const dias = [];
    
    // Dias vazios do início
    for (let i = 0; i < diaSemanaInicio; i++) {
      dias.push(null);
    }
    
    // Dias do mês
    for (let dia = 1; dia <= diasNoMes; dia++) {
      dias.push(dia);
    }

    return (
      <div className="bg-white rounded-lg shadow">
        <div className="p-4 border-b">
          <div className="grid grid-cols-7 gap-2">
            {['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb'].map(dia => (
              <div key={dia} className="text-center text-sm font-semibold text-gray-600 p-2">
                {dia}
              </div>
            ))}
          </div>
        </div>
        
        <div className="p-4">
          <div className="grid grid-cols-7 gap-2">
            {dias.map((dia, index) => {
              if (!dia) {
                return <div key={index} className="h-24"></div>;
              }

              const dataStr = formatarData(new Date(ano, mes, dia));
              const agendamentosDoDia = agendamentos.filter(ag => ag.data === dataStr);
              const bloqueiosDoDia = bloqueios.filter(b => dataStr >= b.data_inicio && dataStr <= b.data_fim);

              return (
                <div
                  key={dia}
                  className="h-24 border rounded-lg p-1 hover:bg-gray-50 cursor-pointer transition-all"
                  onClick={() => handleNovoAgendamento(dataStr, '09:00')}
                >
                  <div className="text-sm font-semibold text-gray-900 mb-1">
                    {dia}
                  </div>
                  <div className="space-y-1">
                    {bloqueiosDoDia.length > 0 && (
                      <div className="text-[10px] px-1 py-0.5 rounded bg-red-100 text-red-800 truncate">
                        🚫 {bloqueiosDoDia.length} bloqueio(s)
                      </div>
                    )}
                    {agendamentosDoDia.slice(0, 2).map(agendamento => {
                      const isAtrasado = verificarAtrasado(agendamento);
                      const statusFinal = isAtrasado ? 'atrasado' : agendamento.status;
                      const statusColor = getStatusColor(statusFinal);
                      
                      return (
                        <div
                          key={agendamento.id}
                          className="text-xs p-1 rounded truncate cursor-pointer"
                          style={{ backgroundColor: statusColor.bg, color: statusColor.text }}
                          onClick={(e) => {
                            e.stopPropagation();
                            handleEditarAgendamento(agendamento);
                          }}
                        >
                          {agendamento.horario} {agendamento.cliente_nome}
                        </div>
                      );
                    })}
                    {agendamentosDoDia.length > 2 && (
                      <div className="text-xs text-gray-500">
                        +{agendamentosDoDia.length - 2} mais
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg w-full max-w-7xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Cabeçalho */}
        <div className="p-6 border-b">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0">
            <div>
              <h2 className="text-2xl font-bold hidden sm:block" style={{ color: loja.cor_primaria }}>
                📅 Calendário - Cabeleireiro
              </h2>
              <p className="text-gray-600 dark:text-gray-400 mt-1 hidden sm:block">{obterTituloPeriodo()}</p>
            </div>

            <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-4">
              {/* Filtro de Profissional */}
              <select
                value={profissionalSelecionado}
                onChange={(e) => setProfissionalSelecionado(e.target.value)}
                className="px-3 py-2 border rounded-lg text-sm bg-white"
              >
                <option value="">Todos os profissionais</option>
                {profissionais.map((p) => (
                  <option key={p.id} value={String(p.id)}>
                    {p.nome}
                  </option>
                ))}
              </select>

              {/* Botões de Visualização */}
              <div className="flex rounded-lg border">
                {(['dia', 'semana', 'mes'] as VisualizacaoTipo[]).map((tipo) => (
                  <button
                    key={tipo}
                    onClick={() => setVisualizacao(tipo)}
                    className={`px-4 py-2 text-sm font-medium capitalize ${
                      visualizacao === tipo
                        ? 'text-white'
                        : 'text-gray-700 hover:text-gray-900'
                    }`}
                    style={{
                      backgroundColor: visualizacao === tipo ? loja.cor_primaria : 'transparent'
                    }}
                  >
                    {tipo}
                  </button>
                ))}
              </div>

              {/* Navegação */}
              <div className="flex space-x-2">
                <button
                  onClick={() => navegarPeriodo('anterior')}
                  className="px-3 py-2 border rounded-lg hover:bg-gray-50"
                >
                  ←
                </button>
                <button
                  onClick={() => setDataAtual(new Date())}
                  className="px-4 py-2 border rounded-lg hover:bg-gray-50 text-sm"
                >
                  Hoje
                </button>
                <button
                  onClick={() => navegarPeriodo('proximo')}
                  className="px-3 py-2 border rounded-lg hover:bg-gray-50"
                >
                  →
                </button>
              </div>

              {/* Botão Fechar */}
              <button
                onClick={onClose}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
              >
                ✕ Fechar
              </button>
            </div>
          </div>
        </div>

        {/* Conteúdo do Calendário */}
        <div className="flex-1 overflow-auto p-6">
          {loading ? (
            <div className="bg-white rounded-lg shadow p-12 text-center">
              <div className="text-gray-500">Carregando agendamentos...</div>
            </div>
          ) : (
            renderizarVisualizacao()
          )}
        </div>
      </div>

      {/* Modal de Agendamento */}
      {showModalAgendamento && (
        <ModalAgendamentoCalendario
          loja={loja}
          agendamento={agendamentoSelecionado}
          dataHoraSelecionada={dataHoraSelecionada}
          clientes={clientes}
          profissionais={profissionais}
          servicos={servicos}
          onClose={() => setShowModalAgendamento(false)}
          onSuccess={() => {
            carregarAgendamentos();
            setShowModalAgendamento(false);
          }}
        />
      )}
    </div>
  );
}

// Modal para criar/editar agendamentos
function ModalAgendamentoCalendario({
  loja,
  agendamento,
  dataHoraSelecionada,
  clientes,
  profissionais,
  servicos,
  onClose,
  onSuccess
}: {
  loja: LojaInfo;
  agendamento: Agendamento | null;
  dataHoraSelecionada: {data: string, horario: string} | null;
  clientes: Cliente[];
  profissionais: Profissional[];
  servicos: Servico[];
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [formData, setFormData] = useState({
    cliente: '',
    profissional: '',
    servico: '',
    data: '',
    horario: '',
    status: 'agendado',
    valor: '',
    observacoes: ''
  });
  const [loading, setLoading] = useState(false);

  const horarios = [
    '08:00', '08:30', '09:00', '09:30', '10:00', '10:30',
    '11:00', '11:30', '12:00', '12:30', '13:00', '13:30',
    '14:00', '14:30', '15:00', '15:30', '16:00', '16:30',
    '17:00', '17:30', '18:00', '18:30', '19:00', '19:30', '20:00'
  ];

  useEffect(() => {
    if (agendamento) {
      setFormData({
        cliente: agendamento.cliente.toString(),
        profissional: agendamento.profissional?.toString() || '',
        servico: agendamento.servico.toString(),
        data: agendamento.data,
        horario: agendamento.horario,
        status: agendamento.status,
        valor: agendamento.valor.toString(),
        observacoes: agendamento.observacoes || ''
      });
    } else if (dataHoraSelecionada) {
      setFormData(prev => ({
        ...prev,
        data: dataHoraSelecionada.data,
        horario: dataHoraSelecionada.horario
      }));
    }
  }, [agendamento, dataHoraSelecionada]);

  const handleServicoChange = (servicoId: string) => {
    setFormData({ ...formData, servico: servicoId });
    
    const servico = servicos.find(s => s.id.toString() === servicoId);
    if (servico && servico.preco) {
      setFormData(prev => ({ ...prev, servico: servicoId, valor: servico.preco.toString() }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const payload = {
        cliente: parseInt(formData.cliente),
        profissional: formData.profissional ? parseInt(formData.profissional) : null,
        servico: parseInt(formData.servico),
        data: formData.data,
        horario: formData.horario,
        status: formData.status,
        valor: parseFloat(formData.valor),
        observacoes: formData.observacoes || null
      };

      if (agendamento) {
        await apiClient.put(`/cabeleireiro/agendamentos/${agendamento.id}/`, payload);
        alert('✅ Agendamento atualizado com sucesso!');
      } else {
        await apiClient.post('/cabeleireiro/agendamentos/', payload);
        alert('✅ Agendamento criado com sucesso!');
      }
      
      onSuccess();
    } catch (error) {
      console.error('Erro ao salvar agendamento:', error);
      alert(formatApiError(error));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal isOpen={true} onClose={onClose} maxWidth="2xl">
      <div className="p-6">
        <h2 className="text-2xl font-bold mb-6 flex items-center gap-2" style={{ color: loja.cor_primaria }}>
          📅 {agendamento ? 'Editar Agendamento' : 'Novo Agendamento'}
        </h2>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Cliente *</label>
              <select
                value={formData.cliente}
                onChange={(e) => setFormData({ ...formData, cliente: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
                required
              >
                <option value="">Selecione...</option>
                {clientes.map(c => (
                  <option key={c.id} value={c.id}>{c.nome} - {c.telefone}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Profissional *</label>
              <select
                value={formData.profissional}
                onChange={(e) => setFormData({ ...formData, profissional: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
                required
              >
                <option value="">Selecione...</option>
                {profissionais.map(p => (
                  <option key={p.id} value={p.id}>{p.nome}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Serviço *</label>
              <select
                value={formData.servico}
                onChange={(e) => handleServicoChange(e.target.value)}
                className="w-full px-3 py-2 border rounded-lg"
                required
              >
                <option value="">Selecione...</option>
                {servicos.map(s => (
                  <option key={s.id} value={s.id}>{s.nome} - R$ {parseFloat(s.preco).toFixed(2)}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Valor (R$) *</label>
              <input
                type="number"
                value={formData.valor}
                onChange={(e) => setFormData({ ...formData, valor: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
                required
                min="0"
                step="0.01"
                placeholder="0.00"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Status *</label>
              <select
                value={formData.status}
                onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
                required
              >
                <option value="agendado">Agendado</option>
                <option value="confirmado">Confirmado</option>
                <option value="em_atendimento">Em Atendimento</option>
                <option value="concluido">Concluído</option>
                <option value="cancelado">Cancelado</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Data *</label>
              <input
                type="date"
                value={formData.data}
                onChange={(e) => setFormData({ ...formData, data: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Horário *</label>
              <select
                value={formData.horario}
                onChange={(e) => setFormData({ ...formData, horario: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
                required
              >
                <option value="">Selecione...</option>
                {horarios.map(h => (
                  <option key={h} value={h}>{h}</option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Observações</label>
            <textarea
              value={formData.observacoes}
              onChange={(e) => setFormData({ ...formData, observacoes: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg"
              rows={3}
            />
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-6 py-2 border rounded-lg hover:bg-gray-50"
              disabled={loading}
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="px-6 py-2 text-white rounded-lg hover:opacity-90 disabled:opacity-50"
              style={{ backgroundColor: loja.cor_primaria }}
              disabled={loading}
            >
              {loading ? 'Salvando...' : agendamento ? 'Atualizar' : 'Salvar'}
            </button>
          </div>
        </form>
      </div>
    </Modal>
  );
}
