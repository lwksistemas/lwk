'use client';

import { useState, useEffect } from 'react';
import { clinicaApiClient } from '@/lib/api-client';

interface Agendamento {
  id: number;
  cliente_nome: string;
  cliente_telefone: string;
  profissional_nome: string;
  procedimento_nome: string;
  data: string;
  horario: string;
  status: string;
  valor: number;
  observacoes?: string;
}

interface LojaInfo {
  id: number;
  nome: string;
  slug: string;
  cor_primaria: string;
  cor_secundaria: string;
}

type VisualizacaoTipo = 'dia' | 'semana' | 'mes';

export default function CalendarioAgendamentos({ loja }: { loja: LojaInfo }) {
  const [agendamentos, setAgendamentos] = useState<Agendamento[]>([]);
  const [visualizacao, setVisualizacao] = useState<VisualizacaoTipo>('semana');
  const [dataAtual, setDataAtual] = useState(new Date());
  const [loading, setLoading] = useState(true);
  const [showModalAgendamento, setShowModalAgendamento] = useState(false);
  const [agendamentoSelecionado, setAgendamentoSelecionado] = useState<Agendamento | null>(null);
  const [dataHoraSelecionada, setDataHoraSelecionada] = useState<{data: string, horario: string} | null>(null);

  useEffect(() => {
    carregarAgendamentos();
  }, [dataAtual, visualizacao]);

  const carregarAgendamentos = async () => {
    setLoading(true);
    try {
      const { dataInicio, dataFim } = calcularPeriodo();
      
      const response = await clinicaApiClient.get('/clinica/agendamentos/calendario/', {
        params: {
          data_inicio: dataInicio,
          data_fim: dataFim
        }
      });
      
      setAgendamentos(response.data);
    } catch (error) {
      console.error('Erro ao carregar agendamentos:', error);
    } finally {
      setLoading(false);
    }
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
    if (!confirm(`Tem certeza que deseja excluir o agendamento de ${agendamento.cliente_nome}?`)) {
      return;
    }

    try {
      await clinicaApiClient.delete(`/clinica/agendamentos/${agendamento.id}/`);
      alert('✅ Agendamento excluído com sucesso!');
      carregarAgendamentos();
    } catch (error) {
      console.error('Erro ao excluir agendamento:', error);
      alert('❌ Erro ao excluir agendamento');
    }
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

  // Componente para visualização por dia
  const VisualizacaoDia = () => {
    const agendamentosDoDia = agendamentos.filter(ag => ag.data === formatarData(dataAtual));
    const horarios = Array.from({ length: 24 }, (_, i) => `${i.toString().padStart(2, '0')}:00`);

    return (
      <div className="bg-white rounded-lg shadow">
        <div className="p-4 border-b">
          <h3 className="text-lg font-semibold">Agendamentos do Dia</h3>
        </div>
        <div className="p-4">
          <div className="space-y-2">
            {horarios.map(horario => {
              const agendamento = agendamentosDoDia.find(ag => ag.horario.startsWith(horario.split(':')[0]));
              
              return (
                <div key={horario} className="flex items-center border-b pb-2">
                  <div className="w-16 text-sm text-gray-600 font-mono">
                    {horario}
                  </div>
                  <div className="flex-1 ml-4">
                    {agendamento ? (
                      <div 
                        className="p-3 rounded-lg cursor-pointer hover:opacity-80"
                        style={{ backgroundColor: `${loja.cor_primaria}20`, borderLeft: `4px solid ${loja.cor_primaria}` }}
                        onClick={() => handleEditarAgendamento(agendamento)}
                      >
                        <div className="flex justify-between items-start">
                          <div>
                            <p className="font-semibold text-gray-900">{agendamento.cliente_nome}</p>
                            <p className="text-sm text-gray-600">{agendamento.procedimento_nome}</p>
                            <p className="text-xs text-gray-500">Prof: {agendamento.profissional_nome}</p>
                          </div>
                          <div className="flex space-x-2">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleEditarAgendamento(agendamento);
                              }}
                              className="text-blue-600 hover:text-blue-800 text-sm"
                            >
                              ✏️
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleExcluirAgendamento(agendamento);
                              }}
                              className="text-red-600 hover:text-red-800 text-sm"
                            >
                              🗑️
                            </button>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <button
                        onClick={() => handleNovoAgendamento(formatarData(dataAtual), horario)}
                        className="w-full p-2 text-left text-gray-400 hover:bg-gray-50 rounded border-2 border-dashed border-gray-200 hover:border-gray-300"
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

  // Componente para visualização por semana
  const VisualizacaoSemana = () => {
    const { dataInicio } = calcularPeriodo();
    const inicioSemana = new Date(dataInicio);
    const diasSemana = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb'];
    const horarios = Array.from({ length: 12 }, (_, i) => `${(i + 8).toString().padStart(2, '0')}:00`);

    return (
      <div className="bg-white rounded-lg shadow overflow-x-auto">
        <div className="min-w-full">
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

                return (
                  <div key={i} className="p-2 border-l min-h-[60px]">
                    {agendamento ? (
                      <div
                        className="p-2 rounded text-xs cursor-pointer hover:opacity-80"
                        style={{ backgroundColor: `${loja.cor_primaria}20`, color: loja.cor_primaria }}
                        onClick={() => handleEditarAgendamento(agendamento)}
                      >
                        <div className="font-semibold truncate">{agendamento.cliente_nome}</div>
                        <div className="truncate">{agendamento.procedimento_nome}</div>
                      </div>
                    ) : (
                      <button
                        onClick={() => handleNovoAgendamento(dataStr, horario)}
                        className="w-full h-full text-gray-300 hover:text-gray-500 hover:bg-gray-50 rounded border border-dashed border-transparent hover:border-gray-300"
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
    );
  };

  // Componente para visualização por mês
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

              return (
                <div
                  key={dia}
                  className="h-24 border rounded-lg p-1 hover:bg-gray-50 cursor-pointer"
                  onClick={() => handleNovoAgendamento(dataStr, '09:00')}
                >
                  <div className="text-sm font-semibold text-gray-900 mb-1">
                    {dia}
                  </div>
                  <div className="space-y-1">
                    {agendamentosDoDia.slice(0, 2).map(agendamento => (
                      <div
                        key={agendamento.id}
                        className="text-xs p-1 rounded truncate cursor-pointer"
                        style={{ backgroundColor: `${loja.cor_primaria}20`, color: loja.cor_primaria }}
                        onClick={(e) => {
                          e.stopPropagation();
                          handleEditarAgendamento(agendamento);
                        }}
                      >
                        {agendamento.horario} {agendamento.cliente_nome}
                      </div>
                    ))}
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
    <div className="space-y-6">
      {/* Cabeçalho do Calendário */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0">
          <div>
            <h2 className="text-2xl font-bold" style={{ color: loja.cor_primaria }}>
              📅 Calendário de Agendamentos
            </h2>
            <p className="text-gray-600 mt-1">{obterTituloPeriodo()}</p>
          </div>

          <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-4">
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

            {/* Botão Novo Agendamento */}
            <button
              onClick={() => handleNovoAgendamento()}
              className="px-4 py-2 text-white rounded-lg hover:opacity-90"
              style={{ backgroundColor: loja.cor_primaria }}
            >
              + Novo Agendamento
            </button>
          </div>
        </div>
      </div>

      {/* Visualização do Calendário */}
      {loading ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <div className="text-gray-500">Carregando agendamentos...</div>
        </div>
      ) : (
        renderizarVisualizacao()
      )}

      {/* Modal de Agendamento */}
      {showModalAgendamento && (
        <ModalAgendamento
          loja={loja}
          agendamento={agendamentoSelecionado}
          dataHoraSelecionada={dataHoraSelecionada}
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
function ModalAgendamento({
  loja,
  agendamento,
  dataHoraSelecionada,
  onClose,
  onSuccess
}: {
  loja: LojaInfo;
  agendamento: Agendamento | null;
  dataHoraSelecionada: {data: string, horario: string} | null;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [formData, setFormData] = useState({
    cliente: '',
    profissional: '',
    procedimento: '',
    data: '',
    horario: '',
    valor: '',
    observacoes: ''
  });
  const [clientes, setClientes] = useState<any[]>([]);
  const [profissionais, setProfissionais] = useState<any[]>([]);
  const [procedimentos, setProcedimentos] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingData, setLoadingData] = useState(true);

  const horarios = [
    '08:00', '08:30', '09:00', '09:30', '10:00', '10:30',
    '11:00', '11:30', '12:00', '12:30', '13:00', '13:30',
    '14:00', '14:30', '15:00', '15:30', '16:00', '16:30',
    '17:00', '17:30', '18:00', '18:30', '19:00'
  ];

  useEffect(() => {
    loadFormData();
    
    if (agendamento) {
      setFormData({
        cliente: agendamento.id.toString(),
        profissional: agendamento.id.toString(),
        procedimento: agendamento.id.toString(),
        data: agendamento.data,
        horario: agendamento.horario,
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

  const loadFormData = async () => {
    try {
      const [clientesRes, profissionaisRes, procedimentosRes] = await Promise.all([
        clinicaApiClient.get('/clinica/clientes/'),
        clinicaApiClient.get('/clinica/profissionais/'),
        clinicaApiClient.get('/clinica/procedimentos/')
      ]);
      
      setClientes(clientesRes.data);
      setProfissionais(profissionaisRes.data);
      setProcedimentos(procedimentosRes.data);
    } catch (error) {
      console.error('Erro ao carregar dados do formulário:', error);
    } finally {
      setLoadingData(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));

    // Auto-preencher valor quando procedimento for selecionado
    if (name === 'procedimento' && value) {
      const procedimento = procedimentos.find(p => p.id.toString() === value);
      if (procedimento) {
        setFormData(prev => ({
          ...prev,
          valor: procedimento.preco
        }));
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const cleanedData = Object.fromEntries(
        Object.entries(formData).map(([key, value]) => [
          key, 
          value === '' ? null : value
        ])
      );

      if (agendamento) {
        await clinicaApiClient.put(`/clinica/agendamentos/${agendamento.id}/`, cleanedData);
        alert('✅ Agendamento atualizado com sucesso!');
      } else {
        await clinicaApiClient.post('/clinica/agendamentos/', cleanedData);
        alert('✅ Agendamento criado com sucesso!');
      }
      
      onSuccess();
    } catch (error) {
      console.error('Erro ao salvar agendamento:', error);
      alert('❌ Erro ao salvar agendamento');
    } finally {
      setLoading(false);
    }
  };

  if (loadingData) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8">
          <div className="text-center">Carregando formulário...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg p-8 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <h3 className="text-2xl font-bold mb-6" style={{ color: loja.cor_primaria }}>
          📅 {agendamento ? 'Editar Agendamento' : 'Novo Agendamento'}
        </h3>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Cliente *
              </label>
              <select
                name="cliente"
                value={formData.cliente}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0"
              >
                <option value="">Selecione um cliente...</option>
                {clientes.map(cliente => (
                  <option key={cliente.id} value={cliente.id}>
                    {cliente.nome} - {cliente.telefone}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Profissional *
              </label>
              <select
                name="profissional"
                value={formData.profissional}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0"
              >
                <option value="">Selecione um profissional...</option>
                {profissionais.map(prof => (
                  <option key={prof.id} value={prof.id}>
                    {prof.nome} - {prof.especialidade}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Procedimento *
              </label>
              <select
                name="procedimento"
                value={formData.procedimento}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0"
              >
                <option value="">Selecione um procedimento...</option>
                {procedimentos.map(proc => (
                  <option key={proc.id} value={proc.id}>
                    {proc.nome} - R$ {proc.preco}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Data *
              </label>
              <input
                type="date"
                name="data"
                value={formData.data}
                onChange={handleChange}
                required
                min={new Date().toISOString().split('T')[0]}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Horário *
              </label>
              <select
                name="horario"
                value={formData.horario}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0"
              >
                <option value="">Selecione...</option>
                {horarios.map(hora => (
                  <option key={hora} value={hora}>{hora}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Valor (R$) *
              </label>
              <input
                type="number"
                name="valor"
                value={formData.valor}
                onChange={handleChange}
                required
                min="0"
                step="0.01"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0"
                placeholder="0.00"
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Observações
              </label>
              <textarea
                name="observacoes"
                value={formData.observacoes}
                onChange={handleChange}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0"
                placeholder="Informações adicionais sobre o agendamento..."
              />
            </div>
          </div>

          <div className="flex justify-end space-x-4 pt-4">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="px-6 py-2 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2 text-white rounded-md hover:opacity-90 disabled:opacity-50"
              style={{ backgroundColor: loja.cor_primaria }}
            >
              {loading ? 'Salvando...' : (agendamento ? 'Atualizar' : 'Criar Agendamento')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}