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
  const [consultaSelecionada, setConsultaSelecionada] = useState<Consulta | null>(null);
  const [evolucoes, setEvolucoes] = useState<EvolucaoPaciente[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'consultas' | 'evolucao'>('consultas');
  const [showFormEvolucao, setShowFormEvolucao] = useState(false);
  const [modoFullscreen, setModoFullscreen] = useState(false);

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
  }, []);

  const loadConsultas = async () => {
    try {
      const response = await clinicaApiClient.get('/clinica/consultas/');
      setConsultas(response.data);
    } catch (error) {
      console.error('Erro ao carregar consultas:', error);
    } finally {
      setLoading(false);
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
    try {
      await clinicaApiClient.post(`/clinica/consultas/${consulta.id}/iniciar_consulta/`);
      alert('✅ Consulta iniciada com sucesso!');
      loadConsultas();
      // Ativar modo fullscreen quando iniciar consulta
      setModoFullscreen(true);
      setActiveTab('consultas');
    } catch (error) {
      console.error('Erro ao iniciar consulta:', error);
      alert('❌ Erro ao iniciar consulta');
    }
  };

  const finalizarConsulta = async (consulta: Consulta, dadosPagamento: any) => {
    try {
      await clinicaApiClient.post(`/clinica/consultas/${consulta.id}/finalizar_consulta/`, dadosPagamento);
      alert('✅ Consulta finalizada com sucesso!');
      loadConsultas();
      // Sair do modo fullscreen quando finalizar consulta
      setModoFullscreen(false);
    } catch (error) {
      console.error('Erro ao finalizar consulta:', error);
      alert('❌ Erro ao finalizar consulta');
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
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg p-8 max-w-7xl w-full max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-2xl font-bold" style={{ color: loja.cor_primaria }}>
            🏥 Sistema de Consultas
          </h3>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600"
          >
            ✕ Fechar
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Lista de Consultas - Expandida */}
          <div className="lg:col-span-1">
            <h4 className="text-lg font-semibold mb-4">📋 Lista de Consultas</h4>
            
            {consultas.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <p className="mb-2">Nenhuma consulta encontrada</p>
                <p className="text-sm">As consultas são criadas automaticamente a partir dos agendamentos</p>
              </div>
            ) : (
              <div className="space-y-3">
                {consultas.map((consulta) => (
                  <div
                    key={consulta.id}
                    className={`p-4 border rounded-lg hover:bg-gray-50 ${
                      consultaSelecionada?.id === consulta.id ? 'ring-2 ring-offset-1' : ''
                    }`}
                    style={{
                      '--tw-ring-color': consultaSelecionada?.id === consulta.id ? loja.cor_primaria : 'transparent'
                    } as React.CSSProperties}
                  >
                    <div className="flex justify-between items-start mb-2">
                      <div className="flex-1">
                        <h5 className="font-semibold text-sm">{consulta.cliente_nome}</h5>
                        <p className="text-xs text-gray-600 mb-1">{consulta.procedimento_nome}</p>
                        <p className="text-xs text-gray-500">
                          📅 {consulta.agendamento_data} {consulta.agendamento_horario}
                        </p>
                        <p className="text-xs text-gray-500">
                          👨‍⚕️ {consulta.profissional_nome}
                        </p>
                        {consulta.total_evolucoes > 0 && (
                          <p className="text-xs text-green-600 mt-1">
                            📊 {consulta.total_evolucoes} evolução(ões)
                          </p>
                        )}
                      </div>
                      <div className="flex flex-col items-end space-y-2">
                        <span className={`px-2 py-1 rounded-full text-xs ${getStatusColor(consulta.status)}`}>
                          {getStatusText(consulta.status)}
                        </span>
                        
                        {/* Ações da Consulta */}
                        <div className="flex flex-col space-y-1">
                          {consulta.status === 'agendada' && (
                            <button
                              onClick={() => iniciarConsulta(consulta)}
                              className="px-3 py-1 text-xs text-white rounded-md hover:opacity-90"
                              style={{ backgroundColor: loja.cor_primaria }}
                            >
                              ▶️ Iniciar Exame
                            </button>
                          )}
                          
                          {consulta.status === 'em_andamento' && (
                            <>
                              <button
                                onClick={() => {
                                  setConsultaSelecionada(consulta);
                                  loadEvolucoes(consulta.id);
                                  setModoFullscreen(true);
                                  setActiveTab('consultas');
                                }}
                                className="px-3 py-1 text-xs bg-yellow-600 text-white rounded-md hover:bg-yellow-700"
                              >
                                ⏳ Continuar Exame
                              </button>
                              <button
                                onClick={() => {
                                  setConsultaSelecionada(consulta);
                                  loadEvolucoes(consulta.id);
                                  // Simular finalização rápida
                                  const dadosPagamento = {
                                    valor_pago: consulta.valor_consulta.toString(),
                                    forma_pagamento: 'dinheiro',
                                    observacoes_gerais: 'Exame finalizado via lista'
                                  };
                                  finalizarConsulta(consulta, dadosPagamento);
                                }}
                                className="px-3 py-1 text-xs bg-green-600 text-white rounded-md hover:bg-green-700"
                              >
                                ✅ Finalizar Exame
                              </button>
                            </>
                          )}
                          
                          <button
                            onClick={() => selecionarConsulta(consulta)}
                            className="px-3 py-1 text-xs border border-gray-300 rounded-md hover:bg-gray-50"
                          >
                            👁️ Ver Detalhes
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Detalhes da Consulta - Quando Selecionada */}
          <div className="lg:col-span-1">
            {consultaSelecionada ? (
              <div>
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
            ) : (
              <div className="text-center py-12 text-gray-500">
                <p className="text-lg mb-2">Selecione uma consulta</p>
                <p className="text-sm">Clique em uma consulta à esquerda para ver os detalhes</p>
              </div>
            )}
          </div>
        </div>
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