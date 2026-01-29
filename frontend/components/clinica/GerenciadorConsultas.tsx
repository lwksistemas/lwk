'use client';

import { useState, useEffect } from 'react';
import { clinicaApiClient } from '@/lib/api-client';

interface Consulta {
  id: number;
  cliente: number;
  profissional: number;
  cliente_nome: string;
  profissional_nome: string;
  procedimento_nome: string;
  agendamento_data: string;
  agendamento_horario: string;
  status: string;
  data_inicio?: string;
  data_fim?: string;
  duracao_minutos?: number;
  valor_consulta: number;
  valor_pago: number;
  forma_pagamento?: string;
  observacoes_gerais?: string;
  total_evolucoes: number;
}

interface EvolucaoPaciente {
  id: number;
  cliente_nome: string;
  profissional_nome: string;
  queixa_principal: string;
  data_evolucao: string;
  imc?: number;
  procedimento_realizado: string;
  satisfacao_paciente?: number;
}

interface LojaInfo {
  id: number;
  nome: string;
  slug: string;
  cor_primaria: string;
  cor_secundaria: string;
}

export default function GerenciadorConsultas({ loja, onClose }: { loja: LojaInfo; onClose: () => void }) {
  const [consultas, setConsultas] = useState<Consulta[]>([]);
  const [consultasFiltered, setConsultasFiltered] = useState<Consulta[]>([]);
  const [profissionais, setProfissionais] = useState<any[]>([]);
  const [profissionalSelecionado, setProfissionalSelecionado] = useState<string>('');
  const [consultaSelecionada, setConsultaSelecionada] = useState<Consulta | null>(null);
  const [evolucoes, setEvolucoes] = useState<EvolucaoPaciente[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'consultas' | 'evolucao'>('consultas');
  const [showFormEvolucao, setShowFormEvolucao] = useState(false);
  const [modoFullscreen, setModoFullscreen] = useState(false);
  const [showAgendaProfissional, setShowAgendaProfissional] = useState(false);
  const [startingConsultaId, setStartingConsultaId] = useState<number | null>(null);
  const [finishingConsultaId, setFinishingConsultaId] = useState<number | null>(null);

  // Estados do formulário de evolução
  const [formEvolucao, setFormEvolucao] = useState({
    queixa_principal: '',
    historico_medico: '',
    medicamentos_uso: '',
    alergias: '',
    peso: '',
    altura: '',
    pressao_arterial: '',
    tipo_pele: '',
    condicoes_pele: '',
    areas_tratamento: '',
    procedimento_realizado: '',
    produtos_utilizados: '',
    parametros_equipamento: '',
    reacao_imediata: '',
    orientacoes_dadas: '',
    proxima_sessao: '',
    satisfacao_paciente: ''
  });

  useEffect(() => {
    loadConsultas();
    loadProfissionais();
  }, []);

  useEffect(() => {
    // Filtrar consultas quando mudar o profissional selecionado
    if (profissionalSelecionado === '') {
      setConsultasFiltered(consultas);
    } else {
      const filtered = consultas.filter(consulta => 
        consulta.profissional.toString() === profissionalSelecionado
      );
      setConsultasFiltered(filtered);
    }
  }, [consultas, profissionalSelecionado]);

  const loadConsultas = async () => {
    try {
      const response = await clinicaApiClient.get('/clinica/consultas/');
      let data = response.data ?? [];

      // Se não houver consultas, sincronizar com agendamentos (cria Consulta para cada Agendamento)
      if (Array.isArray(data) && data.length === 0) {
        try {
          await clinicaApiClient.post('/clinica/consultas/sync_from_agendamentos/');
          const res = await clinicaApiClient.get('/clinica/consultas/');
          data = res.data ?? [];
        } catch (_) {
          // ignora erro do sync (ex.: contexto sem loja)
        }
      }

      setConsultas(data);
      setConsultasFiltered(data);
    } catch (error) {
      console.error('Erro ao carregar consultas:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadProfissionais = async () => {
    try {
      const response = await clinicaApiClient.get('/clinica/profissionais/');
      setProfissionais(response.data);
    } catch (error) {
      console.error('Erro ao carregar profissionais:', error);
    }
  };

  const loadEvolucoes = async (consultaId: number) => {
    try {
      const response = await clinicaApiClient.get(`/clinica/evolucoes/?consulta_id=${consultaId}`);
      setEvolucoes(response.data);
    } catch (error) {
      console.error('Erro ao carregar evoluções:', error);
    }
  };

  const iniciarConsulta = async (consulta: Consulta) => {
    if (startingConsultaId === consulta.id) return;
    try {
      setStartingConsultaId(consulta.id);
      const response = await clinicaApiClient.post(`/clinica/consultas/${consulta.id}/iniciar_consulta/`);
      const consultaAtualizada: Consulta = response.data;
      alert('✅ Consulta iniciada com sucesso!');
      // Atualizar estado local imediatamente (evita clique duplo em "Iniciar")
      setConsultas((prev) => prev.map((c) => (c.id === consulta.id ? { ...c, ...consultaAtualizada } : c)));

      // Abrir a "página" do profissional: modo fullscreen + evolução
      setConsultaSelecionada(consultaAtualizada);
      setModoFullscreen(true);
      setActiveTab('evolucao');
      setShowFormEvolucao(true);
      loadEvolucoes(consultaAtualizada.id);

      // Recarregar em background para garantir consistência
      loadConsultas();
    } catch (error: any) {
      console.error('Erro ao iniciar consulta:', error);

      const status = error?.response?.status;
      const serverMsg = error?.response?.data?.error || error?.response?.data?.detail || error?.message;

      // Caso comum: usuário clicou em "Iniciar" numa consulta que já não está mais agendada
      if (status === 400 && typeof serverMsg === 'string' && serverMsg.toLowerCase().includes('agendada')) {
        try {
          const res = await clinicaApiClient.get(`/clinica/consultas/${consulta.id}/`);
          const atual: Consulta = res.data;
          // Se já está em andamento, apenas abrir a tela correta
          if (atual?.status === 'em_andamento') {
            setConsultaSelecionada(atual);
            setModoFullscreen(true);
            setActiveTab('evolucao');
            loadEvolucoes(atual.id);
            return;
          }
        } catch (_) {
          // ignora
        }
      }

      alert(`❌ Erro ao iniciar consulta${serverMsg ? `: ${serverMsg}` : ''}`);
    } finally {
      setStartingConsultaId(null);
    }
  };

  const finalizarConsulta = async (consulta: Consulta, dadosPagamento: any) => {
    if (finishingConsultaId === consulta.id) return;
    try {
      setFinishingConsultaId(consulta.id);
      const response = await clinicaApiClient.post(
        `/clinica/consultas/${consulta.id}/finalizar_consulta/`,
        dadosPagamento
      );
      const consultaAtualizada: Consulta = response.data;
      alert('✅ Consulta finalizada com sucesso!');
      // Atualizar estado local imediatamente (evita re-clique com status antigo)
      setConsultas((prev) => prev.map((c) => (c.id === consulta.id ? { ...c, ...consultaAtualizada } : c)));
      loadConsultas();
      // Sair do modo fullscreen quando finalizar consulta
      setModoFullscreen(false);
    } catch (error: any) {
      console.error('Erro ao finalizar consulta:', error);
      const status = error?.response?.status;
      const serverMsg =
        error?.response?.data?.error || error?.response?.data?.detail || error?.message;

      // Caso comum: tentou finalizar uma consulta que não está mais "em_andamento"
      if (status === 400 && typeof serverMsg === 'string' && serverMsg.toLowerCase().includes('andamento')) {
        try {
          const res = await clinicaApiClient.get(`/clinica/consultas/${consulta.id}/`);
          const atual: Consulta = res.data;
          setConsultas((prev) => prev.map((c) => (c.id === consulta.id ? { ...c, ...atual } : c)));
          // Se já estiver concluída, apenas informar e fechar o fullscreen
          if (atual?.status === 'concluida') {
            alert('ℹ️ Esta consulta já foi finalizada.');
            setModoFullscreen(false);
            loadConsultas();
            return;
          }
        } catch (_) {
          // ignora
        }
      }

      alert(`❌ Erro ao finalizar consulta${serverMsg ? `: ${serverMsg}` : ''}`);
    } finally {
      setFinishingConsultaId(null);
    }
  };

  const excluirConsulta = async (consulta: Consulta) => {
    if (!confirm(`Tem certeza que deseja excluir a consulta de ${consulta.cliente_nome}?`)) {
      return;
    }

    try {
      await clinicaApiClient.delete(`/clinica/consultas/${consulta.id}/`);
      
      // Recarregar consultas
      loadConsultas();
      
      alert('✅ Consulta excluída com sucesso!');
    } catch (error) {
      console.error('Erro ao excluir consulta:', error);
      alert('❌ Erro ao excluir consulta');
    }
  };

  const selecionarConsulta = (consulta: Consulta) => {
    setConsultaSelecionada(consulta);
    loadEvolucoes(consulta.id);
    setActiveTab('consultas');
    // Ativar modo fullscreen se a consulta estiver em andamento
    if (consulta.status === 'em_andamento') {
      setModoFullscreen(true);
    }
  };

  const handleSubmitEvolucao = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!consultaSelecionada) return;

    try {
      const cleanedData = Object.fromEntries(
        Object.entries(formEvolucao).map(([key, value]) => {
          // Para campos de texto, manter string vazia em vez de null
          const textFields = ['historico_medico', 'medicamentos_uso', 'alergias', 'pressao_arterial', 
                             'tipo_pele', 'condicoes_pele', 'produtos_utilizados', 'parametros_equipamento',
                             'reacao_imediata', 'orientacoes_dadas'];
          
          if (textFields.includes(key)) {
            return [key, value || ''];  // String vazia para campos de texto
          }
          
          // Para outros campos, null se vazio
          return [key, value === '' ? null : value];
        })
      );

      const evolucaoData = {
        ...cleanedData,
        consulta: consultaSelecionada.id,
        cliente: consultaSelecionada.cliente, // ID correto do cliente
        profissional: consultaSelecionada.profissional, // ID correto do profissional
      };

      await clinicaApiClient.post('/clinica/evolucoes/', evolucaoData);
      alert('✅ Evolução registrada com sucesso!');
      
      // Recarregar evoluções
      loadEvolucoes(consultaSelecionada.id);
      setShowFormEvolucao(false);
      
      // Limpar formulário
      setFormEvolucao({
        queixa_principal: '',
        historico_medico: '',
        medicamentos_uso: '',
        alergias: '',
        peso: '',
        altura: '',
        pressao_arterial: '',
        tipo_pele: '',
        condicoes_pele: '',
        areas_tratamento: '',
        procedimento_realizado: '',
        produtos_utilizados: '',
        parametros_equipamento: '',
        reacao_imediata: '',
        orientacoes_dadas: '',
        proxima_sessao: '',
        satisfacao_paciente: ''
      });
      
    } catch (error) {
      console.error('Erro ao registrar evolução:', error);
      alert('❌ Erro ao registrar evolução');
    }
  };

  const handleChangeEvolucao = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    setFormEvolucao(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'agendada': return 'bg-blue-100 text-blue-800';
      case 'em_andamento': return 'bg-yellow-100 text-yellow-800';
      case 'concluida': return 'bg-green-100 text-green-800';
      case 'cancelada': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'agendada': return 'Agendada';
      case 'em_andamento': return 'Em Andamento';
      case 'concluida': return 'Concluída';
      case 'cancelada': return 'Cancelada';
      default: return status;
    }
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8">
          <div className="text-center">Carregando consultas...</div>
        </div>
      </div>
    );
  }

  // Modo Fullscreen - Apenas consulta e evolução
  if (modoFullscreen && consultaSelecionada) {
    return (
      <div className="fixed inset-0 bg-white z-50 flex flex-col">
        {/* Header fixo */}
        <div className="bg-white border-b px-6 py-4 flex justify-between items-center shadow-sm">
          <div>
            <h2 className="text-xl font-bold" style={{ color: loja.cor_primaria }}>
              🏥 Consulta em Andamento - {consultaSelecionada.cliente_nome}
            </h2>
            <p className="text-sm text-gray-600">
              {consultaSelecionada.procedimento_nome} • {consultaSelecionada.profissional_nome}
            </p>
          </div>
          <div className="flex items-center space-x-4">
            <button
              onClick={() => setModoFullscreen(false)}
              className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
            >
              📋 Ver Lista
            </button>
            <button
              onClick={onClose}
              className="px-4 py-2 bg-red-500 text-white rounded-md hover:bg-red-600"
            >
              ✕ Sair
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="bg-white border-b px-6">
          <div className="flex">
            <button
              onClick={() => setActiveTab('consultas')}
              className={`px-6 py-3 font-medium border-b-2 ${
                activeTab === 'consultas'
                  ? 'border-current text-current'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
              style={{
                borderBottomColor: activeTab === 'consultas' ? loja.cor_primaria : 'transparent',
                color: activeTab === 'consultas' ? loja.cor_primaria : undefined
              }}
            >
              🏥 Detalhes da Consulta
            </button>
            <button
              onClick={() => setActiveTab('evolucao')}
              className={`px-6 py-3 font-medium border-b-2 ${
                activeTab === 'evolucao'
                  ? 'border-current text-current'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
              style={{
                borderBottomColor: activeTab === 'evolucao' ? loja.cor_primaria : 'transparent',
                color: activeTab === 'evolucao' ? loja.cor_primaria : undefined
              }}
            >
              📊 Evolução do Paciente
            </button>
          </div>
        </div>

        {/* Conteúdo principal */}
        <div className="flex-1 overflow-y-auto p-6">
          {activeTab === 'consultas' && (
            <ConsultaDetalhes 
              consulta={consultaSelecionada}
              loja={loja}
              onIniciar={iniciarConsulta}
              onFinalizar={finalizarConsulta}
            />
          )}

          {activeTab === 'evolucao' && (
            <EvolucaoDetalhes
              consulta={consultaSelecionada}
              evolucoes={evolucoes}
              loja={loja}
              showForm={showFormEvolucao}
              onShowForm={setShowFormEvolucao}
              formData={formEvolucao}
              onFormChange={handleChangeEvolucao}
              onSubmit={handleSubmitEvolucao}
            />
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-white dark:bg-gray-900 z-50 flex flex-col">
      <div className="flex-1 overflow-y-auto flex flex-col min-h-0 px-4 sm:px-6 pb-6">
        <div className="flex justify-between items-center mb-6 pt-4 sm:pt-6 flex-shrink-0">
          <h3 className="text-2xl font-bold" style={{ color: loja.cor_primaria }}>
            🏥 Sistema de Consultas
          </h3>
          <div className="flex items-center space-x-4">
            <button
              onClick={() => setShowAgendaProfissional(true)}
              className="px-4 py-2 text-white rounded-md hover:opacity-90"
              style={{ backgroundColor: loja.cor_primaria }}
            >
              📅 Agenda por Profissional
            </button>
            <button
              onClick={onClose}
              className="px-4 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600"
            >
              ✕ Fechar
            </button>
          </div>
        </div>

        {/* Filtros */}
        <div className="mb-6 p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center space-x-4">
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Filtrar por Profissional
              </label>
              <select
                value={profissionalSelecionado}
                onChange={(e) => setProfissionalSelecionado(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0"
                style={{ '--tw-ring-color': loja.cor_primaria } as React.CSSProperties}
              >
                <option value="">Todos os profissionais</option>
                {profissionais.map(prof => (
                  <option key={prof.id} value={prof.id}>
                    {prof.nome} - {prof.especialidade}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex items-end">
              <button
                onClick={() => setProfissionalSelecionado('')}
                className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                🔄 Limpar Filtro
              </button>
            </div>
          </div>
          
          {profissionalSelecionado && (
            <div className="mt-2 text-sm text-gray-600">
              Mostrando {consultasFiltered.length} consulta(s) de {profissionais.find(p => p.id.toString() === profissionalSelecionado)?.nome}
            </div>
          )}
        </div>

        {/* Lista de Consultas - Tela Cheia */}
        <div className="w-full">
          <h4 className="text-lg font-semibold mb-4">📋 Lista de Consultas</h4>
          
          {consultasFiltered.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              {profissionalSelecionado ? (
                <>
                  <p className="mb-2">Nenhuma consulta encontrada para este profissional</p>
                  <p className="text-sm">Selecione outro profissional ou limpe o filtro</p>
                </>
              ) : (
                <>
                  <p className="mb-2">Nenhuma consulta encontrada</p>
                  <p className="text-sm">As consultas são criadas automaticamente a partir dos agendamentos</p>
                </>
              )}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {consultasFiltered.map((consulta) => (
                <div
                  key={consulta.id}
                  className="p-4 border rounded-lg hover:bg-gray-50 bg-white shadow-sm"
                >
                  <div className="flex justify-between items-start mb-3">
                    <div className="flex-1">
                      <h5 className="font-semibold text-lg mb-1">{consulta.cliente_nome}</h5>
                      <p className="text-sm text-gray-600 mb-2">{consulta.procedimento_nome}</p>
                      <div className="space-y-1">
                        <p className="text-xs text-gray-500 flex items-center">
                          📅 {consulta.agendamento_data} às {consulta.agendamento_horario}
                        </p>
                        <p className="text-xs text-gray-500 flex items-center">
                          👨‍⚕️ {consulta.profissional_nome}
                        </p>
                        {consulta.total_evolucoes > 0 && (
                          <p className="text-xs text-green-600 flex items-center">
                            📊 {consulta.total_evolucoes} evolução(ões)
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex justify-between items-center">
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(consulta.status)}`}>
                      {getStatusText(consulta.status)}
                    </span>
                    
                    {/* Ações da Consulta */}
                    <div className="flex space-x-2">
                      {consulta.status === 'agendada' && (
                        <button
                          onClick={() => iniciarConsulta(consulta)}
                          disabled={startingConsultaId === consulta.id}
                          className="px-4 py-2 text-sm text-white rounded-md hover:opacity-90 font-medium disabled:opacity-60 disabled:cursor-not-allowed"
                          style={{ backgroundColor: loja.cor_primaria }}
                        >
                          {startingConsultaId === consulta.id ? 'Iniciando...' : '▶️ Iniciar Consulta'}
                        </button>
                      )}
                      
                      {consulta.status === 'em_andamento' && (
                        <>
                          <button
                            onClick={() => {
                              setConsultaSelecionada(consulta);
                              loadEvolucoes(consulta.id);
                              setModoFullscreen(true);
                              setActiveTab('evolucao');
                            }}
                            className="px-4 py-2 text-sm bg-yellow-600 text-white rounded-md hover:bg-yellow-700 font-medium"
                          >
                            ⏳ Continuar Consulta
                          </button>
                          <button
                            onClick={() => {
                              setConsultaSelecionada(consulta);
                              loadEvolucoes(consulta.id);
                              const dadosPagamento = {
                                valor_pago: consulta.valor_consulta.toString(),
                                forma_pagamento: 'dinheiro',
                                observacoes_gerais: 'Consulta finalizada via lista'
                              };
                              finalizarConsulta(consulta, dadosPagamento);
                            }}
                            disabled={finishingConsultaId === consulta.id}
                            className="px-4 py-2 text-sm bg-green-600 text-white rounded-md hover:bg-green-700 font-medium disabled:opacity-60 disabled:cursor-not-allowed"
                          >
                            {finishingConsultaId === consulta.id ? 'Finalizando...' : '✅ Finalizar Consulta'}
                          </button>
                        </>
                      )}
                      
                      {consulta.status === 'concluida' && (
                        <>
                          <button
                            onClick={() => selecionarConsulta(consulta)}
                            className="px-4 py-2 text-sm border border-gray-300 rounded-md hover:bg-gray-50 font-medium"
                          >
                            👁️ Ver Histórico
                          </button>
                          <button
                            onClick={() => excluirConsulta(consulta)}
                            className="px-3 py-2 text-sm bg-red-500 text-white rounded-md hover:bg-red-600 font-medium"
                          >
                            🗑️ Excluir
                          </button>
                        </>
                      )}
                      
                      {(consulta.status === 'agendada' || consulta.status === 'em_andamento') && (
                        <button
                          onClick={() => excluirConsulta(consulta)}
                          className="px-3 py-2 text-sm bg-red-500 text-white rounded-md hover:bg-red-600 font-medium"
                        >
                          🗑️ Excluir
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Modal de Detalhes - Apenas quando uma consulta for selecionada */}
        {consultaSelecionada && !modoFullscreen && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg p-8 max-w-4xl w-full max-h-[80vh] overflow-y-auto">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-xl font-bold" style={{ color: loja.cor_primaria }}>
                  📋 Detalhes da Consulta - {consultaSelecionada.cliente_nome}
                </h3>
                <button
                  onClick={() => setConsultaSelecionada(null)}
                  className="px-4 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600"
                >
                  ✕ Fechar
                </button>
              </div>

              {/* Tabs */}
              <div className="flex border-b mb-4">
                <button
                  onClick={() => setActiveTab('consultas')}
                  className={`px-4 py-2 font-medium ${
                    activeTab === 'consultas'
                      ? 'border-b-2 text-blue-600'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                  style={{
                    borderBottomColor: activeTab === 'consultas' ? loja.cor_primaria : 'transparent',
                    color: activeTab === 'consultas' ? loja.cor_primaria : undefined
                  }}
                >
                  🏥 Consulta
                </button>
                <button
                  onClick={() => setActiveTab('evolucao')}
                  className={`px-4 py-2 font-medium ${
                    activeTab === 'evolucao'
                      ? 'border-b-2 text-blue-600'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                  style={{
                    borderBottomColor: activeTab === 'evolucao' ? loja.cor_primaria : 'transparent',
                    color: activeTab === 'evolucao' ? loja.cor_primaria : undefined
                  }}
                >
                  📊 Evolução do Paciente
                </button>
              </div>

              {/* Conteúdo das Tabs */}
              {activeTab === 'consultas' && (
                <ConsultaDetalhes 
                  consulta={consultaSelecionada}
                  loja={loja}
                  onIniciar={iniciarConsulta}
                  onFinalizar={finalizarConsulta}
                />
              )}

              {activeTab === 'evolucao' && (
                <EvolucaoDetalhes
                  consulta={consultaSelecionada}
                  evolucoes={evolucoes}
                  loja={loja}
                  showForm={showFormEvolucao}
                  onShowForm={setShowFormEvolucao}
                  formData={formEvolucao}
                  onFormChange={handleChangeEvolucao}
                  onSubmit={handleSubmitEvolucao}
                />
              )}
            </div>
          </div>
        )}

        {/* Agenda por Profissional */}
        {showAgendaProfissional && (
          <AgendaProfissional 
            loja={loja}
            profissionais={profissionais}
            onClose={() => setShowAgendaProfissional(false)}
          />
        )}
      </div>
    </div>
  );
}

// Componente para detalhes da consulta
function ConsultaDetalhes({ 
  consulta, 
  loja, 
  onIniciar, 
  onFinalizar 
}: { 
  consulta: Consulta; 
  loja: LojaInfo; 
  onIniciar: (consulta: Consulta) => void;
  onFinalizar: (consulta: Consulta, dados: any) => void;
}) {
  const [showFinalizarForm, setShowFinalizarForm] = useState(false);
  const [dadosPagamento, setDadosPagamento] = useState({
    valor_pago: consulta.valor_pago.toString(),
    forma_pagamento: consulta.forma_pagamento || '',
    observacoes_gerais: consulta.observacoes_gerais || ''
  });

  const handleFinalizar = () => {
    onFinalizar(consulta, dadosPagamento);
    setShowFinalizarForm(false);
  };

  return (
    <div className="space-y-6">
      {/* Informações da Consulta */}
      <div className="bg-gray-50 p-4 rounded-lg">
        <h5 className="font-semibold mb-3" style={{ color: loja.cor_primaria }}>
          Informações da Consulta
        </h5>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="font-medium">Cliente:</span> {consulta.cliente_nome}
          </div>
          <div>
            <span className="font-medium">Profissional:</span> {consulta.profissional_nome}
          </div>
          <div>
            <span className="font-medium">Procedimento:</span> {consulta.procedimento_nome}
          </div>
          <div>
            <span className="font-medium">Data/Hora:</span> {consulta.agendamento_data} {consulta.agendamento_horario}
          </div>
          <div>
            <span className="font-medium">Status:</span> 
            <span className={`ml-2 px-2 py-1 rounded-full text-xs ${
              consulta.status === 'agendada' ? 'bg-blue-100 text-blue-800' :
              consulta.status === 'em_andamento' ? 'bg-yellow-100 text-yellow-800' :
              consulta.status === 'concluida' ? 'bg-green-100 text-green-800' :
              'bg-red-100 text-red-800'
            }`}>
              {consulta.status === 'agendada' ? 'Agendada' :
               consulta.status === 'em_andamento' ? 'Em Andamento' :
               consulta.status === 'concluida' ? 'Concluída' : 'Cancelada'}
            </span>
          </div>
          <div>
            <span className="font-medium">Valor:</span> R$ {consulta.valor_consulta}
          </div>
          {consulta.duracao_minutos && (
            <div>
              <span className="font-medium">Duração:</span> {consulta.duracao_minutos} min
            </div>
          )}
        </div>
      </div>

      {/* Ações da Consulta */}
      <div className="flex space-x-4">
        {consulta.status === 'agendada' && (
          <button
            onClick={() => onIniciar(consulta)}
            className="px-6 py-2 text-white rounded-md hover:opacity-90"
            style={{ backgroundColor: loja.cor_primaria }}
          >
            ▶️ Iniciar Consulta
          </button>
        )}

        {consulta.status === 'em_andamento' && (
          <button
            onClick={() => setShowFinalizarForm(true)}
            className="px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
          >
            ✅ Finalizar Consulta
          </button>
        )}
      </div>

      {/* Formulário de Finalização */}
      {showFinalizarForm && (
        <div className="bg-gray-50 p-4 rounded-lg">
          <h6 className="font-semibold mb-4">Finalizar Consulta</h6>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Valor Pago (R$)</label>
              <input
                type="number"
                step="0.01"
                value={dadosPagamento.valor_pago}
                onChange={(e) => setDadosPagamento(prev => ({ ...prev, valor_pago: e.target.value }))}
                className="w-full px-3 py-2 border rounded-md"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Forma de Pagamento</label>
              <select
                value={dadosPagamento.forma_pagamento}
                onChange={(e) => setDadosPagamento(prev => ({ ...prev, forma_pagamento: e.target.value }))}
                className="w-full px-3 py-2 border rounded-md"
              >
                <option value="">Selecione...</option>
                <option value="dinheiro">Dinheiro</option>
                <option value="cartao_debito">Cartão de Débito</option>
                <option value="cartao_credito">Cartão de Crédito</option>
                <option value="pix">PIX</option>
                <option value="transferencia">Transferência</option>
              </select>
            </div>
            <div className="col-span-2">
              <label className="block text-sm font-medium mb-1">Observações</label>
              <textarea
                value={dadosPagamento.observacoes_gerais}
                onChange={(e) => setDadosPagamento(prev => ({ ...prev, observacoes_gerais: e.target.value }))}
                rows={3}
                className="w-full px-3 py-2 border rounded-md"
                placeholder="Observações sobre a consulta..."
              />
            </div>
          </div>
          <div className="flex justify-end space-x-4 mt-4">
            <button
              onClick={() => setShowFinalizarForm(false)}
              className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Cancelar
            </button>
            <button
              onClick={handleFinalizar}
              className="px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
            >
              ✅ Confirmar Finalização
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// Componente para evolução do paciente
function EvolucaoDetalhes({
  consulta,
  evolucoes,
  loja,
  showForm,
  onShowForm,
  formData,
  onFormChange,
  onSubmit
}: {
  consulta: Consulta;
  evolucoes: EvolucaoPaciente[];
  loja: LojaInfo;
  showForm: boolean;
  onShowForm: (show: boolean) => void;
  formData: any;
  onFormChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => void;
  onSubmit: (e: React.FormEvent) => void;
}) {
  if (showForm) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h5 className="font-semibold" style={{ color: loja.cor_primaria }}>
            📊 Registrar Evolução do Paciente
          </h5>
          <button
            onClick={() => onShowForm(false)}
            className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
          >
            Cancelar
          </button>
        </div>

        <form onSubmit={onSubmit} className="space-y-4">
          {/* Avaliação Inicial */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <h6 className="font-semibold mb-3">Avaliação Inicial</h6>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2">
                <label className="block text-sm font-medium mb-1">Queixa Principal *</label>
                <textarea
                  name="queixa_principal"
                  value={formData.queixa_principal}
                  onChange={onFormChange}
                  required
                  rows={3}
                  className="w-full px-3 py-2 border rounded-md"
                  placeholder="Descreva a queixa principal do paciente..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Histórico Médico</label>
                <textarea
                  name="historico_medico"
                  value={formData.historico_medico}
                  onChange={onFormChange}
                  rows={2}
                  className="w-full px-3 py-2 border rounded-md"
                  placeholder="Histórico médico relevante..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Medicamentos em Uso</label>
                <textarea
                  name="medicamentos_uso"
                  value={formData.medicamentos_uso}
                  onChange={onFormChange}
                  rows={2}
                  className="w-full px-3 py-2 border rounded-md"
                  placeholder="Medicamentos que o paciente está usando..."
                />
              </div>
            </div>
          </div>

          {/* Avaliação Física */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <h6 className="font-semibold mb-3">Avaliação Física</h6>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">Peso (kg)</label>
                <input
                  type="number"
                  step="0.1"
                  name="peso"
                  value={formData.peso}
                  onChange={onFormChange}
                  className="w-full px-3 py-2 border rounded-md"
                  placeholder="70.5"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Altura (m)</label>
                <input
                  type="number"
                  step="0.01"
                  name="altura"
                  value={formData.altura}
                  onChange={onFormChange}
                  className="w-full px-3 py-2 border rounded-md"
                  placeholder="1.70"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Pressão Arterial</label>
                <input
                  type="text"
                  name="pressao_arterial"
                  value={formData.pressao_arterial}
                  onChange={onFormChange}
                  className="w-full px-3 py-2 border rounded-md"
                  placeholder="120x80"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Tipo de Pele</label>
                <select
                  name="tipo_pele"
                  value={formData.tipo_pele}
                  onChange={onFormChange}
                  className="w-full px-3 py-2 border rounded-md"
                >
                  <option value="">Selecione...</option>
                  <option value="oleosa">Oleosa</option>
                  <option value="seca">Seca</option>
                  <option value="mista">Mista</option>
                  <option value="normal">Normal</option>
                  <option value="sensivel">Sensível</option>
                </select>
              </div>
            </div>
          </div>

          {/* Procedimento Realizado */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <h6 className="font-semibold mb-3">Procedimento Realizado</h6>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Áreas de Tratamento *</label>
                <textarea
                  name="areas_tratamento"
                  value={formData.areas_tratamento}
                  onChange={onFormChange}
                  required
                  rows={2}
                  className="w-full px-3 py-2 border rounded-md"
                  placeholder="Descreva as áreas tratadas..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Procedimento Realizado *</label>
                <textarea
                  name="procedimento_realizado"
                  value={formData.procedimento_realizado}
                  onChange={onFormChange}
                  required
                  rows={3}
                  className="w-full px-3 py-2 border rounded-md"
                  placeholder="Descreva detalhadamente o procedimento realizado..."
                />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Produtos Utilizados</label>
                  <textarea
                    name="produtos_utilizados"
                    value={formData.produtos_utilizados}
                    onChange={onFormChange}
                    rows={2}
                    className="w-full px-3 py-2 border rounded-md"
                    placeholder="Liste os produtos utilizados..."
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Parâmetros de Equipamento</label>
                  <textarea
                    name="parametros_equipamento"
                    value={formData.parametros_equipamento}
                    onChange={onFormChange}
                    rows={2}
                    className="w-full px-3 py-2 border rounded-md"
                    placeholder="Parâmetros utilizados nos equipamentos..."
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Resultados e Orientações */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <h6 className="font-semibold mb-3">Resultados e Orientações</h6>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">Reação Imediata</label>
                <textarea
                  name="reacao_imediata"
                  value={formData.reacao_imediata}
                  onChange={onFormChange}
                  rows={2}
                  className="w-full px-3 py-2 border rounded-md"
                  placeholder="Como o paciente reagiu ao procedimento..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Orientações Dadas</label>
                <textarea
                  name="orientacoes_dadas"
                  value={formData.orientacoes_dadas}
                  onChange={onFormChange}
                  rows={2}
                  className="w-full px-3 py-2 border rounded-md"
                  placeholder="Orientações dadas ao paciente..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Próxima Sessão</label>
                <input
                  type="date"
                  name="proxima_sessao"
                  value={formData.proxima_sessao}
                  onChange={onFormChange}
                  className="w-full px-3 py-2 border rounded-md"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Satisfação do Paciente (1-5)</label>
                <select
                  name="satisfacao_paciente"
                  value={formData.satisfacao_paciente}
                  onChange={onFormChange}
                  className="w-full px-3 py-2 border rounded-md"
                >
                  <option value="">Selecione...</option>
                  <option value="1">1 - Muito Insatisfeito</option>
                  <option value="2">2 - Insatisfeito</option>
                  <option value="3">3 - Neutro</option>
                  <option value="4">4 - Satisfeito</option>
                  <option value="5">5 - Muito Satisfeito</option>
                </select>
              </div>
            </div>
          </div>

          <div className="flex justify-end space-x-4">
            <button
              type="button"
              onClick={() => onShowForm(false)}
              className="px-6 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="px-6 py-2 text-white rounded-md hover:opacity-90"
              style={{ backgroundColor: loja.cor_primaria }}
            >
              💾 Salvar Evolução
            </button>
          </div>
        </form>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h5 className="font-semibold" style={{ color: loja.cor_primaria }}>
          📊 Evolução do Paciente - {consulta.cliente_nome}
        </h5>
        <button
          onClick={() => onShowForm(true)}
          className="px-4 py-2 text-white rounded-md hover:opacity-90"
          style={{ backgroundColor: loja.cor_primaria }}
        >
          + Nova Evolução
        </button>
      </div>

      {evolucoes.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <p className="text-lg mb-2">Nenhuma evolução registrada</p>
          <p className="text-sm mb-4">Registre a evolução do paciente após o procedimento</p>
          <button
            onClick={() => onShowForm(true)}
            className="px-6 py-3 text-white rounded-md hover:opacity-90"
            style={{ backgroundColor: loja.cor_primaria }}
          >
            + Registrar Primeira Evolução
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {evolucoes.map((evolucao) => (
            <div key={evolucao.id} className="border rounded-lg p-4 hover:bg-gray-50">
              <div className="flex justify-between items-start mb-3">
                <div>
                  <h6 className="font-semibold">{evolucao.queixa_principal}</h6>
                  <p className="text-sm text-gray-600">
                    📅 {new Date(evolucao.data_evolucao).toLocaleDateString('pt-BR')} às {new Date(evolucao.data_evolucao).toLocaleTimeString('pt-BR')}
                  </p>
                </div>
                {evolucao.satisfacao_paciente && (
                  <div className="flex items-center">
                    <span className="text-sm text-gray-600 mr-2">Satisfação:</span>
                    <div className="flex">
                      {[1, 2, 3, 4, 5].map((star) => (
                        <span
                          key={star}
                          className={star <= evolucao.satisfacao_paciente! ? 'text-yellow-400' : 'text-gray-300'}
                        >
                          ⭐
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="font-medium">Procedimento:</span>
                  <p className="text-gray-700">{evolucao.procedimento_realizado}</p>
                </div>
                {evolucao.imc && (
                  <div>
                    <span className="font-medium">IMC:</span> {evolucao.imc}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// Componente para Agenda por Profissional
function AgendaProfissional({ 
  loja, 
  profissionais, 
  onClose 
}: { 
  loja: LojaInfo; 
  profissionais: any[]; 
  onClose: () => void; 
}) {
  const [profissionalSelecionado, setProfissionalSelecionado] = useState<string>('');
  const [dataAtual, setDataAtual] = useState(new Date());
  const [agendamentos, setAgendamentos] = useState<any[]>([]);
  const [bloqueios, setBloqueios] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [showBloqueioForm, setShowBloqueioForm] = useState(false);
  const [bloqueioForm, setBloqueioForm] = useState({
    data_inicio: '',
    data_fim: '',
    horario_inicio: '',
    horario_fim: '',
    motivo: '',
    tipo: 'periodo' // 'periodo' ou 'dia_completo'
  });

  const diasSemana = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb'];
  const horarios = Array.from({ length: 12 }, (_, i) => {
    const hora = 8 + i;
    return `${hora.toString().padStart(2, '0')}:00`;
  });

  useEffect(() => {
    if (profissionalSelecionado) {
      loadAgendaProfissional();
    }
  }, [profissionalSelecionado, dataAtual]);

  const loadAgendaProfissional = async () => {
    setLoading(true);
    try {
      const dataFormatada = dataAtual.toISOString().split('T')[0];
      
      // Carregar agendamentos do profissional
      const responseAgendamentos = await clinicaApiClient.get(
        `/clinica/agendamentos/?profissional_id=${profissionalSelecionado}`
      );
      setAgendamentos(responseAgendamentos.data);

      // Carregar bloqueios da agenda
      const responseBloqueios = await clinicaApiClient.get(
        `/clinica/bloqueios/?profissional_id=${profissionalSelecionado}`
      );
      setBloqueios(responseBloqueios.data);
    } catch (error) {
      console.error('Erro ao carregar agenda:', error);
    } finally {
      setLoading(false);
    }
  };

  const excluirBloqueio = async (bloqueioId: number) => {
    if (!confirm('Tem certeza que deseja excluir este bloqueio?')) {
      return;
    }

    try {
      await clinicaApiClient.delete(`/clinica/bloqueios/${bloqueioId}/`);
      
      // Recarregar bloqueios
      loadAgendaProfissional();
      
      alert('✅ Bloqueio excluído com sucesso!');
    } catch (error) {
      console.error('Erro ao excluir bloqueio:', error);
      alert('❌ Erro ao excluir bloqueio');
    }
  };

  const criarBloqueio = async () => {
    try {
      const bloqueioData = {
        titulo: bloqueioForm.motivo || 'Bloqueio de agenda',
        tipo: bloqueioForm.tipo === 'dia_completo' ? 'feriado' : 'outros',
        profissional: parseInt(profissionalSelecionado),
        data_inicio: bloqueioForm.data_inicio,
        data_fim: bloqueioForm.data_fim,
        horario_inicio: bloqueioForm.tipo === 'periodo' ? bloqueioForm.horario_inicio : null,
        horario_fim: bloqueioForm.tipo === 'periodo' ? bloqueioForm.horario_fim : null,
        observacoes: bloqueioForm.motivo
      };
      
      await clinicaApiClient.post('/clinica/bloqueios/', bloqueioData);
      
      // Recarregar bloqueios
      loadAgendaProfissional();
      
      setShowBloqueioForm(false);
      setBloqueioForm({
        data_inicio: '',
        data_fim: '',
        horario_inicio: '',
        horario_fim: '',
        motivo: '',
        tipo: 'periodo'
      });
      
      alert('✅ Bloqueio criado com sucesso!');
    } catch (error) {
      console.error('Erro ao criar bloqueio:', error);
      alert('❌ Erro ao criar bloqueio');
    }
  };

  const navegarSemana = (direcao: number) => {
    const novaData = new Date(dataAtual);
    novaData.setDate(novaData.getDate() + (direcao * 7));
    setDataAtual(novaData);
  };

  const getInicioSemana = (data: Date) => {
    const inicio = new Date(data);
    inicio.setDate(data.getDate() - data.getDay());
    return inicio;
  };

  const getDiasSemana = () => {
    const inicioSemana = getInicioSemana(dataAtual);
    return Array.from({ length: 7 }, (_, i) => {
      const dia = new Date(inicioSemana);
      dia.setDate(inicioSemana.getDate() + i);
      return dia;
    });
  };

  const getBloqueioHorario = (dia: Date, horario: string) => {
    const dataStr = dia.toISOString().split('T')[0];
    return bloqueios.find(bloqueio => {
      if (bloqueio.tipo === 'feriado' || !bloqueio.horario_inicio || !bloqueio.horario_fim) {
        // Bloqueio de dia completo
        return dataStr >= bloqueio.data_inicio && dataStr <= bloqueio.data_fim;
      } else {
        // Bloqueio de período específico
        return dataStr >= bloqueio.data_inicio && 
               dataStr <= bloqueio.data_fim &&
               horario >= bloqueio.horario_inicio.substring(0, 5) && 
               horario <= bloqueio.horario_fim.substring(0, 5);
      }
    });
  };

  const isHorarioBloqueado = (dia: Date, horario: string) => {
    const dataStr = dia.toISOString().split('T')[0];
    return bloqueios.some(bloqueio => {
      if (bloqueio.tipo === 'feriado' || !bloqueio.horario_inicio || !bloqueio.horario_fim) {
        // Bloqueio de dia completo
        return dataStr >= bloqueio.data_inicio && dataStr <= bloqueio.data_fim;
      } else {
        // Bloqueio de período específico
        return dataStr >= bloqueio.data_inicio && 
               dataStr <= bloqueio.data_fim &&
               horario >= bloqueio.horario_inicio.substring(0, 5) && 
               horario <= bloqueio.horario_fim.substring(0, 5);
      }
    });
  };

  const getAgendamentoHorario = (dia: Date, horario: string) => {
    const dataStr = dia.toISOString().split('T')[0];
    return agendamentos.find(ag => 
      ag.data === dataStr && ag.horario === horario + ':00'
    );
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg p-8 max-w-7xl w-full max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-2xl font-bold" style={{ color: loja.cor_primaria }}>
            📅 Agenda por Profissional
          </h3>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600"
          >
            ✕ Fechar
          </button>
        </div>

        {/* Seleção de Profissional */}
        <div className="mb-6 p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center justify-between">
            <div className="flex-1 mr-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Selecionar Profissional
              </label>
              <select
                value={profissionalSelecionado}
                onChange={(e) => setProfissionalSelecionado(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0"
                style={{ '--tw-ring-color': loja.cor_primaria } as React.CSSProperties}
              >
                <option value="">Selecione um profissional...</option>
                {profissionais.map(prof => (
                  <option key={prof.id} value={prof.id}>
                    {prof.nome} - {prof.especialidade}
                  </option>
                ))}
              </select>
            </div>
            
            {profissionalSelecionado && (
              <button
                onClick={() => setShowBloqueioForm(true)}
                className="px-4 py-2 bg-red-500 text-white rounded-md hover:bg-red-600"
              >
                🚫 Bloquear Horário
              </button>
            )}
          </div>
        </div>

        {profissionalSelecionado ? (
          <div>
            {/* Navegação da Semana */}
            <div className="flex justify-between items-center mb-4">
              <button
                onClick={() => navegarSemana(-1)}
                className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                ← Semana Anterior
              </button>
              
              <h4 className="text-lg font-semibold">
                Semana de {getInicioSemana(dataAtual).toLocaleDateString('pt-BR')}
              </h4>
              
              <button
                onClick={() => navegarSemana(1)}
                className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Próxima Semana →
              </button>
            </div>

            {loading ? (
              <div className="text-center py-8">Carregando agenda...</div>
            ) : (
              /* Grade da Agenda */
              <div className="overflow-x-auto">
                <table className="w-full border-collapse border border-gray-300">
                  <thead>
                    <tr>
                      <th className="border border-gray-300 p-2 bg-gray-100 w-20">Horário</th>
                      {getDiasSemana().map((dia, index) => (
                        <th key={index} className="border border-gray-300 p-2 bg-gray-100 min-w-32">
                          <div className="text-center">
                            <div className="font-semibold">{diasSemana[dia.getDay()]}</div>
                            <div className="text-sm text-gray-600">
                              {dia.getDate()}/{(dia.getMonth() + 1).toString().padStart(2, '0')}
                            </div>
                          </div>
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {horarios.map(horario => (
                      <tr key={horario}>
                        <td className="border border-gray-300 p-2 bg-gray-50 text-center font-medium">
                          {horario}
                        </td>
                        {getDiasSemana().map((dia, diaIndex) => {
                          const agendamento = getAgendamentoHorario(dia, horario);
                          const bloqueado = isHorarioBloqueado(dia, horario);
                          const bloqueio = getBloqueioHorario(dia, horario);
                          
                          return (
                            <td key={diaIndex} className="border border-gray-300 p-1">
                              {bloqueado && bloqueio ? (
                                <div className="bg-red-200 text-red-800 p-2 rounded text-xs">
                                  <div className="text-center mb-1">🚫 Bloqueado</div>
                                  <div className="text-center">
                                    <button
                                      onClick={() => excluirBloqueio(bloqueio.id)}
                                      className="px-2 py-1 bg-red-500 text-white rounded text-xs hover:bg-red-600"
                                      title="Excluir bloqueio"
                                    >
                                      🗑️
                                    </button>
                                  </div>
                                </div>
                              ) : agendamento ? (
                                <div className="bg-blue-100 text-blue-800 p-2 rounded text-xs">
                                  <div className="font-semibold">{agendamento.cliente_nome}</div>
                                  <div>{agendamento.procedimento_nome}</div>
                                  <div className="text-xs">Status: {agendamento.status}</div>
                                </div>
                              ) : (
                                <div className="h-16 bg-green-50 hover:bg-green-100 cursor-pointer rounded flex items-center justify-center text-green-600">
                                  <span className="text-xs">Disponível</span>
                                </div>
                              )}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        ) : (
          <div className="text-center py-12 text-gray-500">
            <p className="text-lg mb-2">Selecione um profissional</p>
            <p className="text-sm">Escolha um profissional acima para visualizar sua agenda</p>
          </div>
        )}

        {/* Modal de Bloqueio */}
        {showBloqueioForm && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
              <h4 className="text-lg font-bold mb-4" style={{ color: loja.cor_primaria }}>
                🚫 Bloquear Horário
              </h4>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Tipo de Bloqueio</label>
                  <select
                    value={bloqueioForm.tipo}
                    onChange={(e) => setBloqueioForm(prev => ({ ...prev, tipo: e.target.value }))}
                    className="w-full px-3 py-2 border rounded-md"
                  >
                    <option value="periodo">Período Específico</option>
                    <option value="dia_completo">Dia Completo</option>
                  </select>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Data Início</label>
                    <input
                      type="date"
                      value={bloqueioForm.data_inicio}
                      onChange={(e) => setBloqueioForm(prev => ({ ...prev, data_inicio: e.target.value }))}
                      className="w-full px-3 py-2 border rounded-md"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Data Fim</label>
                    <input
                      type="date"
                      value={bloqueioForm.data_fim}
                      onChange={(e) => setBloqueioForm(prev => ({ ...prev, data_fim: e.target.value }))}
                      className="w-full px-3 py-2 border rounded-md"
                    />
                  </div>
                </div>

                {bloqueioForm.tipo === 'periodo' && (
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-1">Horário Início</label>
                      <input
                        type="time"
                        value={bloqueioForm.horario_inicio}
                        onChange={(e) => setBloqueioForm(prev => ({ ...prev, horario_inicio: e.target.value }))}
                        className="w-full px-3 py-2 border rounded-md"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">Horário Fim</label>
                      <input
                        type="time"
                        value={bloqueioForm.horario_fim}
                        onChange={(e) => setBloqueioForm(prev => ({ ...prev, horario_fim: e.target.value }))}
                        className="w-full px-3 py-2 border rounded-md"
                      />
                    </div>
                  </div>
                )}

                <div>
                  <label className="block text-sm font-medium mb-1">Motivo</label>
                  <textarea
                    value={bloqueioForm.motivo}
                    onChange={(e) => setBloqueioForm(prev => ({ ...prev, motivo: e.target.value }))}
                    rows={3}
                    className="w-full px-3 py-2 border rounded-md"
                    placeholder="Ex: Férias, Curso, Compromisso pessoal..."
                  />
                </div>
              </div>

              <div className="flex justify-end space-x-4 mt-6">
                <button
                  onClick={() => setShowBloqueioForm(false)}
                  className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
                >
                  Cancelar
                </button>
                <button
                  onClick={criarBloqueio}
                  className="px-4 py-2 bg-red-500 text-white rounded-md hover:bg-red-600"
                >
                  🚫 Criar Bloqueio
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}