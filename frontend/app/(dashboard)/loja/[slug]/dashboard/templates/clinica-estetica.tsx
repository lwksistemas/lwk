'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';

interface LojaInfo {
  id: number;
  nome: string;
  slug: string;
  tipo_loja_nome: string;
  cor_primaria: string;
  cor_secundaria: string;
  logo?: string;
}

interface Agendamento {
  id: number;
  cliente: string;
  procedimento: string;
  horario: string;
  data: string;
}

interface Estatisticas {
  agendamentos_hoje: number;
  clientes_ativos: number;
  procedimentos: number;
  receita_mensal: number;
}

export default function DashboardClinicaEstetica({ loja }: { loja: LojaInfo }) {
  const router = useRouter();
  const [estatisticas, setEstatisticas] = useState<Estatisticas>({
    agendamentos_hoje: 0,
    clientes_ativos: 0,
    procedimentos: 0,
    receita_mensal: 0
  });
  const [proximosAgendamentos, setProximosAgendamentos] = useState<Agendamento[]>([]);

  const [showModalAgendamento, setShowModalAgendamento] = useState(false);
  const [showModalCliente, setShowModalCliente] = useState(false);
  const [showModalProcedimentos, setShowModalProcedimentos] = useState(false);
  const [showModalProfissional, setShowModalProfissional] = useState(false);
  const [showModalFuncionario, setShowModalFuncionario] = useState(false);

  // State de clientes movido para o componente pai para persistir entre aberturas do modal
  const [clientes, setClientes] = useState<any[]>([]);

  // Carregar dados reais (quando implementado)
  useEffect(() => {
    // loadEstatisticas();
    // loadProximosAgendamentos();
  }, []);

  const handleNovoAgendamento = () => {
    setShowModalAgendamento(true);
  };

  const handleNovoCliente = () => {
    setShowModalCliente(true);
  };

  const handleProcedimentos = () => {
    setShowModalProcedimentos(true);
  };

  const handleRelatorios = () => {
    router.push(`/loja/${loja.slug}/relatorios`);
  };

  const handleNovoProfissional = () => {
    setShowModalProfissional(true);
  };

  const handleNovoFuncionario = () => {
    setShowModalFuncionario(true);
  };

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6" style={{ color: loja.cor_primaria }}>
        Dashboard - Clínica de Estética
      </h2>
      
      {/* Estatísticas */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow hover:shadow-lg transition-shadow">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-gray-500 text-sm font-medium">Agendamentos Hoje</h3>
              <p className="text-3xl font-bold mt-2" style={{ color: loja.cor_primaria }}>
                {estatisticas.agendamentos_hoje}
              </p>
            </div>
            <div 
              className="w-12 h-12 rounded-full flex items-center justify-center"
              style={{ backgroundColor: `${loja.cor_primaria}20` }}
            >
              <span className="text-2xl">📅</span>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow hover:shadow-lg transition-shadow">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-gray-500 text-sm font-medium">Clientes Ativos</h3>
              <p className="text-3xl font-bold mt-2" style={{ color: loja.cor_primaria }}>
                {estatisticas.clientes_ativos}
              </p>
            </div>
            <div 
              className="w-12 h-12 rounded-full flex items-center justify-center"
              style={{ backgroundColor: `${loja.cor_primaria}20` }}
            >
              <span className="text-2xl">👥</span>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow hover:shadow-lg transition-shadow">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-gray-500 text-sm font-medium">Procedimentos</h3>
              <p className="text-3xl font-bold mt-2" style={{ color: loja.cor_primaria }}>
                {estatisticas.procedimentos}
              </p>
            </div>
            <div 
              className="w-12 h-12 rounded-full flex items-center justify-center"
              style={{ backgroundColor: `${loja.cor_primaria}20` }}
            >
              <span className="text-2xl">💆</span>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow hover:shadow-lg transition-shadow">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-gray-500 text-sm font-medium">Receita Mensal</h3>
              <p className="text-3xl font-bold mt-2" style={{ color: loja.cor_primaria }}>
                R$ {estatisticas.receita_mensal.toLocaleString('pt-BR')}
              </p>
            </div>
            <div 
              className="w-12 h-12 rounded-full flex items-center justify-center"
              style={{ backgroundColor: `${loja.cor_primaria}20` }}
            >
              <span className="text-2xl">💰</span>
            </div>
          </div>
        </div>
      </div>

      {/* Ações Rápidas */}
      <div className="bg-white p-6 rounded-lg shadow mb-8">
        <h3 className="text-lg font-semibold mb-4">Ações Rápidas</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <button 
            onClick={handleNovoAgendamento}
            className="p-4 rounded-lg text-white font-semibold hover:opacity-90 transition-all transform hover:scale-105 shadow-md"
            style={{ backgroundColor: loja.cor_primaria }}
          >
            <div className="text-3xl mb-2">📅</div>
            <div className="text-sm">Novo Agendamento</div>
          </button>
          
          <button 
            onClick={handleNovoCliente}
            className="p-4 rounded-lg text-white font-semibold hover:opacity-90 transition-all transform hover:scale-105 shadow-md"
            style={{ backgroundColor: loja.cor_primaria }}
          >
            <div className="text-3xl mb-2">👤</div>
            <div className="text-sm">Novo Cliente</div>
          </button>
          
          <button 
            onClick={handleNovoProfissional}
            className="p-4 rounded-lg text-white font-semibold hover:opacity-90 transition-all transform hover:scale-105 shadow-md"
            style={{ backgroundColor: loja.cor_primaria }}
          >
            <div className="text-3xl mb-2">�‍⚕️</div>
            <div className="text-sm">Novo Profissional</div>
          </button>

          <button 
            onClick={handleNovoFuncionario}
            className="p-4 rounded-lg text-white font-semibold hover:opacity-90 transition-all transform hover:scale-105 shadow-md"
            style={{ backgroundColor: loja.cor_primaria }}
          >
            <div className="text-3xl mb-2">�</div>
            <div className="text-sm">Novo Funcionário</div>
          </button>
          
          <button 
            onClick={handleProcedimentos}
            className="p-4 rounded-lg text-white font-semibold hover:opacity-90 transition-all transform hover:scale-105 shadow-md"
            style={{ backgroundColor: loja.cor_primaria }}
          >
            <div className="text-3xl mb-2">💆</div>
            <div className="text-sm">Procedimentos</div>
          </button>
          
          <button 
            onClick={handleRelatorios}
            className="p-4 rounded-lg text-white font-semibold hover:opacity-90 transition-all transform hover:scale-105 shadow-md"
            style={{ backgroundColor: loja.cor_primaria }}
          >
            <div className="text-3xl mb-2">📊</div>
            <div className="text-sm">Relatórios</div>
          </button>
        </div>
      </div>

      {/* Próximos Agendamentos */}
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Próximos Agendamentos</h3>
          <button
            onClick={handleNovoAgendamento}
            className="text-sm px-4 py-2 rounded-md text-white hover:opacity-90"
            style={{ backgroundColor: loja.cor_primaria }}
          >
            + Novo
          </button>
        </div>
        
        {proximosAgendamentos.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <p className="text-lg mb-2">Nenhum agendamento cadastrado</p>
            <p className="text-sm mb-4">Comece adicionando seu primeiro agendamento</p>
            <button
              onClick={handleNovoAgendamento}
              className="px-6 py-3 rounded-md text-white hover:opacity-90"
              style={{ backgroundColor: loja.cor_primaria }}
            >
              + Adicionar Primeiro Agendamento
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            {proximosAgendamentos.map((agendamento) => (
              <div 
                key={agendamento.id}
                className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer"
              >
                <div className="flex items-center space-x-4">
                  <div 
                    className="w-12 h-12 rounded-full flex items-center justify-center text-white font-bold"
                    style={{ backgroundColor: loja.cor_primaria }}
                  >
                    {agendamento.cliente.charAt(0)}
                  </div>
                  <div>
                    <p className="font-semibold text-gray-900">{agendamento.cliente}</p>
                    <p className="text-sm text-gray-600">{agendamento.procedimento}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="font-semibold" style={{ color: loja.cor_primaria }}>
                    {agendamento.horario}
                  </p>
                  <p className="text-sm text-gray-600">{agendamento.data}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Modais */}
      {showModalAgendamento && (
        <ModalNovoAgendamento 
          loja={loja}
          onClose={() => setShowModalAgendamento(false)}
        />
      )}

      {showModalCliente && (
        <ModalNovoCliente 
          loja={loja}
          clientes={clientes}
          setClientes={setClientes}
          onClose={() => setShowModalCliente(false)}
        />
      )}

      {showModalProfissional && (
        <ModalNovoProfissional 
          loja={loja}
          onClose={() => setShowModalProfissional(false)}
        />
      )}

      {showModalFuncionario && (
        <ModalNovoFuncionario 
          loja={loja}
          onClose={() => setShowModalFuncionario(false)}
        />
      )}

      {showModalProcedimentos && (
        <ModalProcedimentos 
          loja={loja}
          onClose={() => setShowModalProcedimentos(false)}
        />
      )}
    </div>
  );
}

// Modal Novo Agendamento
function ModalNovoAgendamento({ loja, onClose }: { loja: LojaInfo; onClose: () => void }) {
  const [formData, setFormData] = useState({
    cliente: '',
    telefone: '',
    procedimento: '',
    data: '',
    horario: '',
    observacoes: ''
  });
  const [loading, setLoading] = useState(false);

  const procedimentos = [
    'Limpeza de Pele',
    'Massagem Relaxante',
    'Drenagem Linfática',
    'Peeling Químico',
    'Hidratação Facial',
    'Depilação',
    'Outro'
  ];

  const horarios = [
    '08:00', '08:30', '09:00', '09:30', '10:00', '10:30',
    '11:00', '11:30', '12:00', '12:30', '13:00', '13:30',
    '14:00', '14:30', '15:00', '15:30', '16:00', '16:30',
    '17:00', '17:30', '18:00', '18:30', '19:00'
  ];

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      // Aqui você conectaria com a API
      // await apiClient.post('/agendamentos/', formData);
      
      // Simulação de sucesso
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      alert(`✅ Agendamento criado com sucesso!\n\nCliente: ${formData.cliente}\nProcedimento: ${formData.procedimento}\nData: ${formData.data}\nHorário: ${formData.horario}`);
      onClose();
    } catch (error) {
      alert('❌ Erro ao criar agendamento');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg p-8 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <h3 className="text-2xl font-bold mb-6" style={{ color: loja.cor_primaria }}>
          📅 Novo Agendamento
        </h3>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Nome do Cliente *
              </label>
              <input
                type="text"
                name="cliente"
                value={formData.cliente}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0"
                placeholder="Ex: Maria Silva"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Telefone *
              </label>
              <input
                type="tel"
                name="telefone"
                value={formData.telefone}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0"
                placeholder="(00) 00000-0000"
              />
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
                <option value="">Selecione...</option>
                {procedimentos.map(proc => (
                  <option key={proc} value={proc}>{proc}</option>
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
              {loading ? 'Criando...' : 'Criar Agendamento'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// Modal Gerenciar Clientes (Listar, Criar, Editar, Excluir)
function ModalNovoCliente({ 
  loja, 
  clientes, 
  setClientes, 
  onClose 
}: { 
  loja: LojaInfo; 
  clientes: any[]; 
  setClientes: React.Dispatch<React.SetStateAction<any[]>>; 
  onClose: () => void;
}) {
  const [mostrarFormulario, setMostrarFormulario] = useState(false);
  const [clienteEditando, setClienteEditando] = useState<number | null>(null);
  const [formData, setFormData] = useState({
    nome: '',
    email: '',
    telefone: '',
    cpf: '',
    data_nascimento: '',
    endereco: '',
    cidade: '',
    estado: '',
    observacoes: ''
  });
  const [loading, setLoading] = useState(false);

  const estados = [
    'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
    'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
    'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
  ];

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleNovo = () => {
    setClienteEditando(null);
    setFormData({ nome: '', email: '', telefone: '', cpf: '', data_nascimento: '', endereco: '', cidade: '', estado: '', observacoes: '' });
    setMostrarFormulario(true);
  };

  const handleEditar = (cliente: any) => {
    setClienteEditando(cliente.id);
    setFormData({
      nome: cliente.nome,
      email: cliente.email,
      telefone: cliente.telefone,
      cpf: cliente.cpf,
      data_nascimento: cliente.data_nascimento,
      endereco: cliente.endereco || '',
      cidade: cliente.cidade,
      estado: cliente.estado,
      observacoes: cliente.observacoes || ''
    });
    setMostrarFormulario(true);
  };

  const handleExcluir = async (clienteId: number, clienteNome: string) => {
    if (!confirm(`Tem certeza que deseja excluir o cliente "${clienteNome}"?`)) return;
    
    try {
      await new Promise(resolve => setTimeout(resolve, 500));
      // Remover cliente do array
      setClientes(prev => prev.filter(c => c.id !== clienteId));
      alert(`✅ Cliente "${clienteNome}" excluído com sucesso!`);
    } catch (error) {
      alert('❌ Erro ao excluir cliente');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 1000));
      if (clienteEditando) {
        // Atualizar cliente existente
        setClientes(prev => prev.map(c => 
          c.id === clienteEditando 
            ? { ...c, ...formData }
            : c
        ));
        alert(`✅ Cliente atualizado com sucesso!\n\nNome: ${formData.nome}\nEmail: ${formData.email}\nTelefone: ${formData.telefone}`);
      } else {
        // Adicionar novo cliente
        const novoCliente = {
          id: Math.max(...clientes.map(c => c.id), 0) + 1,
          ...formData
        };
        setClientes(prev => [...prev, novoCliente]);
        alert(`✅ Cliente cadastrado com sucesso!\n\nNome: ${formData.nome}\nEmail: ${formData.email}\nTelefone: ${formData.telefone}`);
      }
      setMostrarFormulario(false);
      setClienteEditando(null);
      setFormData({ nome: '', email: '', telefone: '', cpf: '', data_nascimento: '', endereco: '', cidade: '', estado: '', observacoes: '' });
    } catch (error) {
      alert('❌ Erro ao salvar cliente');
    } finally {
      setLoading(false);
    }
  };

  if (mostrarFormulario) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-lg p-8 max-w-3xl w-full max-h-[90vh] overflow-y-auto">
          <h3 className="text-2xl font-bold mb-6" style={{ color: loja.cor_primaria }}>
            👤 {clienteEditando ? 'Editar' : 'Novo'} Cliente
          </h3>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <h4 className="text-lg font-semibold mb-3 text-gray-700">Dados Pessoais</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Nome Completo *</label>
                  <input type="text" name="nome" value={formData.nome} onChange={handleChange} required className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" placeholder="Ex: Maria Silva Santos" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Email *</label>
                  <input type="email" name="email" value={formData.email} onChange={handleChange} required className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" placeholder="email@exemplo.com" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Telefone *</label>
                  <input type="tel" name="telefone" value={formData.telefone} onChange={handleChange} required className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" placeholder="(00) 00000-0000" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">CPF</label>
                  <input type="text" name="cpf" value={formData.cpf} onChange={handleChange} className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" placeholder="000.000.000-00" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Data de Nascimento</label>
                  <input type="date" name="data_nascimento" value={formData.data_nascimento} onChange={handleChange} className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" />
                </div>
              </div>
            </div>
            <div>
              <h4 className="text-lg font-semibold mb-3 text-gray-700">Endereço</h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Endereço Completo</label>
                  <input type="text" name="endereco" value={formData.endereco} onChange={handleChange} className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" placeholder="Rua, número, bairro" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Estado</label>
                  <select name="estado" value={formData.estado} onChange={handleChange} className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0">
                    <option value="">Selecione...</option>
                    {estados.map(uf => (<option key={uf} value={uf}>{uf}</option>))}
                  </select>
                </div>
                <div className="md:col-span-3">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Cidade</label>
                  <input type="text" name="cidade" value={formData.cidade} onChange={handleChange} className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" placeholder="Ex: São Paulo" />
                </div>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Observações</label>
              <textarea name="observacoes" value={formData.observacoes} onChange={handleChange} rows={3} className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" placeholder="Informações adicionais sobre o cliente (alergias, preferências, etc.)" />
            </div>
            <div className="flex justify-end space-x-4 pt-4 border-t">
              <button type="button" onClick={() => { setMostrarFormulario(false); setClienteEditando(null); }} disabled={loading} className="px-6 py-2 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50">Cancelar</button>
              <button type="submit" disabled={loading} className="px-6 py-2 text-white rounded-md hover:opacity-90 disabled:opacity-50" style={{ backgroundColor: loja.cor_primaria }}>{loading ? 'Salvando...' : (clienteEditando ? 'Atualizar' : 'Cadastrar')}</button>
            </div>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg p-8 max-w-4xl w-full max-h-[80vh] overflow-y-auto">
        <h3 className="text-2xl font-bold mb-4" style={{ color: loja.cor_primaria }}>👤 Gerenciar Clientes</h3>
        
        <div className="space-y-4 mb-6">
          {clientes.map((cliente) => (
            <div key={cliente.id} className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50">
              <div className="flex-1">
                <p className="font-semibold text-lg">{cliente.nome}</p>
                <p className="text-sm text-gray-600">{cliente.email} • {cliente.telefone}</p>
                <p className="text-sm text-gray-600">CPF: {cliente.cpf} • {cliente.cidade}/{cliente.estado}</p>
              </div>
              <div className="flex items-center space-x-2">
                <button onClick={() => handleEditar(cliente)} className="px-4 py-2 text-sm text-white rounded-md hover:opacity-90 transition-opacity" style={{ backgroundColor: loja.cor_primaria }}>✏️ Editar</button>
                <button onClick={() => handleExcluir(cliente.id, cliente.nome)} className="px-4 py-2 text-sm bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors">🗑️ Excluir</button>
              </div>
            </div>
          ))}
        </div>

        <div className="flex justify-end space-x-4">
          <button onClick={onClose} className="px-6 py-2 border border-gray-300 rounded-md hover:bg-gray-50">Fechar</button>
          <button onClick={handleNovo} className="px-6 py-2 text-white rounded-md hover:opacity-90" style={{ backgroundColor: loja.cor_primaria }}>+ Novo Cliente</button>
        </div>
      </div>
    </div>
  );
}

// Modal Procedimentos
function ModalProcedimentos({ loja, onClose }: { loja: LojaInfo; onClose: () => void }) {
  const [mostrarFormulario, setMostrarFormulario] = useState(false);
  const [procedimentoEditando, setProcedimentoEditando] = useState<number | null>(null);
  const [formData, setFormData] = useState({
    nome: '',
    descricao: '',
    duracao: '',
    preco: '',
    categoria: ''
  });
  const [loading, setLoading] = useState(false);

  const procedimentos = [
    { id: 1, nome: 'Limpeza de Pele', duracao: '60', preco: '150.00', categoria: 'Facial', descricao: 'Limpeza profunda da pele' },
    { id: 2, nome: 'Massagem Relaxante', duracao: '90', preco: '200.00', categoria: 'Massagem', descricao: 'Massagem para relaxamento' },
    { id: 3, nome: 'Drenagem Linfática', duracao: '60', preco: '180.00', categoria: 'Corporal', descricao: 'Drenagem para redução de inchaço' },
    { id: 4, nome: 'Peeling Químico', duracao: '45', preco: '250.00', categoria: 'Estética Avançada', descricao: 'Renovação celular' },
  ];

  const categorias = [
    'Facial',
    'Corporal',
    'Massagem',
    'Estética Avançada',
    'Depilação',
    'Outro'
  ];

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
  };

  const handleNovo = () => {
    setProcedimentoEditando(null);
    setFormData({ nome: '', descricao: '', duracao: '', preco: '', categoria: '' });
    setMostrarFormulario(true);
  };

  const handleEditar = (proc: any) => {
    setProcedimentoEditando(proc.id);
    setFormData({
      nome: proc.nome,
      descricao: proc.descricao,
      duracao: proc.duracao,
      preco: proc.preco,
      categoria: proc.categoria
    });
    setMostrarFormulario(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      if (procedimentoEditando) {
        alert(`✅ Procedimento atualizado com sucesso!\n\nNome: ${formData.nome}\nDuração: ${formData.duracao} min\nPreço: R$ ${formData.preco}`);
      } else {
        alert(`✅ Procedimento cadastrado com sucesso!\n\nNome: ${formData.nome}\nDuração: ${formData.duracao} min\nPreço: R$ ${formData.preco}`);
      }
      
      setMostrarFormulario(false);
      setProcedimentoEditando(null);
      setFormData({ nome: '', descricao: '', duracao: '', preco: '', categoria: '' });
    } catch (error) {
      alert('❌ Erro ao salvar procedimento');
    } finally {
      setLoading(false);
    }
  };

  if (mostrarFormulario) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-lg p-8 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
          <h3 className="text-2xl font-bold mb-6" style={{ color: loja.cor_primaria }}>
            💆 {procedimentoEditando ? 'Editar' : 'Novo'} Procedimento
          </h3>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Nome do Procedimento *
              </label>
              <input
                type="text"
                name="nome"
                value={formData.nome}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0"
                placeholder="Ex: Hidratação Facial"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Categoria *
              </label>
              <select
                name="categoria"
                value={formData.categoria}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0"
              >
                <option value="">Selecione...</option>
                {categorias.map(cat => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Descrição
              </label>
              <textarea
                name="descricao"
                value={formData.descricao}
                onChange={handleChange}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0"
                placeholder="Descreva o procedimento..."
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Duração (minutos) *
                </label>
                <input
                  type="number"
                  name="duracao"
                  value={formData.duracao}
                  onChange={handleChange}
                  required
                  min="15"
                  step="15"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0"
                  placeholder="60"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Preço (R$) *
                </label>
                <input
                  type="number"
                  name="preco"
                  value={formData.preco}
                  onChange={handleChange}
                  required
                  min="0"
                  step="0.01"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0"
                  placeholder="150.00"
                />
              </div>
            </div>

            <div className="flex justify-end space-x-4 pt-4">
              <button
                type="button"
                onClick={() => {
                  setMostrarFormulario(false);
                  setProcedimentoEditando(null);
                }}
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
                {loading ? 'Salvando...' : (procedimentoEditando ? 'Atualizar' : 'Cadastrar')}
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg p-8 max-w-2xl w-full max-h-[80vh] overflow-y-auto">
        <h3 className="text-2xl font-bold mb-4" style={{ color: loja.cor_primaria }}>
          💆 Procedimentos Disponíveis
        </h3>
        
        <div className="space-y-4 mb-6">
          {procedimentos.map((proc) => (
            <div key={proc.id} className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50">
              <div className="flex-1">
                <p className="font-semibold">{proc.nome}</p>
                <p className="text-sm text-gray-600">{proc.duracao} min • {proc.categoria}</p>
              </div>
              <div className="flex items-center space-x-4">
                <div className="text-right">
                  <p className="font-bold" style={{ color: loja.cor_primaria }}>R$ {proc.preco}</p>
                </div>
                <button
                  onClick={() => handleEditar(proc)}
                  className="px-4 py-2 text-sm text-white rounded-md hover:opacity-90 transition-opacity"
                  style={{ backgroundColor: loja.cor_primaria }}
                >
                  ✏️ Editar
                </button>
              </div>
            </div>
          ))}
        </div>

        <div className="flex justify-end space-x-4">
          <button
            onClick={onClose}
            className="px-6 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
          >
            Fechar
          </button>
          <button
            onClick={handleNovo}
            className="px-6 py-2 text-white rounded-md hover:opacity-90"
            style={{ backgroundColor: loja.cor_primaria }}
          >
            + Novo Procedimento
          </button>
        </div>
      </div>
    </div>
  );
}

// Modal Novo Profissional
function ModalNovoProfissional({ loja, onClose }: { loja: LojaInfo; onClose: () => void }) {
  const [formData, setFormData] = useState({
    nome: '',
    email: '',
    telefone: '',
    cpf: '',
    especialidade: '',
    registro_profissional: '',
    data_admissao: '',
    horario_inicio: '',
    horario_fim: '',
    dias_trabalho: [] as string[],
    observacoes: ''
  });
  const [loading, setLoading] = useState(false);

  const especialidades = [
    'Esteticista',
    'Massoterapeuta',
    'Dermatologista',
    'Fisioterapeuta',
    'Cosmetólogo(a)',
    'Maquiador(a)',
    'Outro'
  ];

  const diasSemana = [
    { value: 'seg', label: 'Segunda' },
    { value: 'ter', label: 'Terça' },
    { value: 'qua', label: 'Quarta' },
    { value: 'qui', label: 'Quinta' },
    { value: 'sex', label: 'Sexta' },
    { value: 'sab', label: 'Sábado' },
    { value: 'dom', label: 'Domingo' }
  ];

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
  };

  const handleDiaToggle = (dia: string) => {
    setFormData(prev => ({
      ...prev,
      dias_trabalho: prev.dias_trabalho.includes(dia)
        ? prev.dias_trabalho.filter(d => d !== dia)
        : [...prev.dias_trabalho, dia]
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      alert(`✅ Profissional cadastrado com sucesso!\n\nNome: ${formData.nome}\nEspecialidade: ${formData.especialidade}\nDias: ${formData.dias_trabalho.join(', ')}`);
      onClose();
    } catch (error) {
      alert('❌ Erro ao cadastrar profissional');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg p-8 max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        <h3 className="text-2xl font-bold mb-6" style={{ color: loja.cor_primaria }}>
          👨‍⚕️ Novo Profissional
        </h3>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Dados Pessoais */}
          <div>
            <h4 className="text-lg font-semibold mb-3 text-gray-700">Dados Pessoais</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nome Completo *
                </label>
                <input
                  type="text"
                  name="nome"
                  value={formData.nome}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0"
                  placeholder="Ex: Dr. João Silva"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email *
                </label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0"
                  placeholder="email@exemplo.com"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Telefone *
                </label>
                <input
                  type="tel"
                  name="telefone"
                  value={formData.telefone}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0"
                  placeholder="(00) 00000-0000"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  CPF *
                </label>
                <input
                  type="text"
                  name="cpf"
                  value={formData.cpf}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0"
                  placeholder="000.000.000-00"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Especialidade *
                </label>
                <select
                  name="especialidade"
                  value={formData.especialidade}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0"
                >
                  <option value="">Selecione...</option>
                  {especialidades.map(esp => (
                    <option key={esp} value={esp}>{esp}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Dados Profissionais */}
          <div>
            <h4 className="text-lg font-semibold mb-3 text-gray-700">Dados Profissionais</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Registro Profissional
                </label>
                <input
                  type="text"
                  name="registro_profissional"
                  value={formData.registro_profissional}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0"
                  placeholder="Ex: CRF 12345"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Data de Admissão *
                </label>
                <input
                  type="date"
                  name="data_admissao"
                  value={formData.data_admissao}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Horário Início *
                </label>
                <input
                  type="time"
                  name="horario_inicio"
                  value={formData.horario_inicio}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Horário Fim *
                </label>
                <input
                  type="time"
                  name="horario_fim"
                  value={formData.horario_fim}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Dias de Trabalho *
                </label>
                <div className="flex flex-wrap gap-2">
                  {diasSemana.map(dia => (
                    <button
                      key={dia.value}
                      type="button"
                      onClick={() => handleDiaToggle(dia.value)}
                      className={`px-4 py-2 rounded-md border transition-colors ${
                        formData.dias_trabalho.includes(dia.value)
                          ? 'text-white border-transparent'
                          : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                      }`}
                      style={formData.dias_trabalho.includes(dia.value) ? { backgroundColor: loja.cor_primaria } : {}}
                    >
                      {dia.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Observações */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Observações
            </label>
            <textarea
              name="observacoes"
              value={formData.observacoes}
              onChange={handleChange}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0"
              placeholder="Informações adicionais sobre o profissional..."
            />
          </div>

          <div className="flex justify-end space-x-4 pt-4 border-t">
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
              {loading ? 'Cadastrando...' : 'Cadastrar Profissional'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// Modal Novo Funcionário
function ModalNovoFuncionario({ loja, onClose }: { loja: LojaInfo; onClose: () => void }) {
  const [formData, setFormData] = useState({
    nome: '',
    email: '',
    telefone: '',
    cpf: '',
    cargo: '',
    setor: '',
    data_admissao: '',
    salario: '',
    horario_inicio: '',
    horario_fim: '',
    dias_trabalho: [] as string[],
    observacoes: ''
  });
  const [loading, setLoading] = useState(false);

  const cargos = [
    'Recepcionista',
    'Auxiliar Administrativo',
    'Gerente',
    'Coordenador(a)',
    'Auxiliar de Limpeza',
    'Assistente',
    'Outro'
  ];

  const setores = [
    'Administrativo',
    'Atendimento',
    'Financeiro',
    'Operacional',
    'Limpeza',
    'Outro'
  ];

  const diasSemana = [
    { value: 'seg', label: 'Segunda' },
    { value: 'ter', label: 'Terça' },
    { value: 'qua', label: 'Quarta' },
    { value: 'qui', label: 'Quinta' },
    { value: 'sex', label: 'Sexta' },
    { value: 'sab', label: 'Sábado' },
    { value: 'dom', label: 'Domingo' }
  ];

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
  };

  const handleDiaToggle = (dia: string) => {
    setFormData(prev => ({
      ...prev,
      dias_trabalho: prev.dias_trabalho.includes(dia)
        ? prev.dias_trabalho.filter(d => d !== dia)
        : [...prev.dias_trabalho, dia]
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      alert(`✅ Funcionário cadastrado com sucesso!\n\nNome: ${formData.nome}\nCargo: ${formData.cargo}\nSetor: ${formData.setor}`);
      onClose();
    } catch (error) {
      alert('❌ Erro ao cadastrar funcionário');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg p-8 max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        <h3 className="text-2xl font-bold mb-6" style={{ color: loja.cor_primaria }}>
          👔 Novo Funcionário
        </h3>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Dados Pessoais */}
          <div>
            <h4 className="text-lg font-semibold mb-3 text-gray-700">Dados Pessoais</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nome Completo *
                </label>
                <input
                  type="text"
                  name="nome"
                  value={formData.nome}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0"
                  placeholder="Ex: Maria Santos"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email *
                </label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0"
                  placeholder="email@exemplo.com"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Telefone *
                </label>
                <input
                  type="tel"
                  name="telefone"
                  value={formData.telefone}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0"
                  placeholder="(00) 00000-0000"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  CPF *
                </label>
                <input
                  type="text"
                  name="cpf"
                  value={formData.cpf}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0"
                  placeholder="000.000.000-00"
                />
              </div>
            </div>
          </div>

          {/* Dados do Cargo */}
          <div>
            <h4 className="text-lg font-semibold mb-3 text-gray-700">Dados do Cargo</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Cargo *
                </label>
                <select
                  name="cargo"
                  value={formData.cargo}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0"
                >
                  <option value="">Selecione...</option>
                  {cargos.map(cargo => (
                    <option key={cargo} value={cargo}>{cargo}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Setor *
                </label>
                <select
                  name="setor"
                  value={formData.setor}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0"
                >
                  <option value="">Selecione...</option>
                  {setores.map(setor => (
                    <option key={setor} value={setor}>{setor}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Data de Admissão *
                </label>
                <input
                  type="date"
                  name="data_admissao"
                  value={formData.data_admissao}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Salário *
                </label>
                <input
                  type="text"
                  name="salario"
                  value={formData.salario}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0"
                  placeholder="R$ 0,00"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Horário Início *
                </label>
                <input
                  type="time"
                  name="horario_inicio"
                  value={formData.horario_inicio}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Horário Fim *
                </label>
                <input
                  type="time"
                  name="horario_fim"
                  value={formData.horario_fim}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Dias de Trabalho *
                </label>
                <div className="flex flex-wrap gap-2">
                  {diasSemana.map(dia => (
                    <button
                      key={dia.value}
                      type="button"
                      onClick={() => handleDiaToggle(dia.value)}
                      className={`px-4 py-2 rounded-md border transition-colors ${
                        formData.dias_trabalho.includes(dia.value)
                          ? 'text-white border-transparent'
                          : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                      }`}
                      style={formData.dias_trabalho.includes(dia.value) ? { backgroundColor: loja.cor_primaria } : {}}
                    >
                      {dia.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Observações */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Observações
            </label>
            <textarea
              name="observacoes"
              value={formData.observacoes}
              onChange={handleChange}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0"
              placeholder="Informações adicionais sobre o funcionário..."
            />
          </div>

          <div className="flex justify-end space-x-4 pt-4 border-t">
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
              {loading ? 'Cadastrando...' : 'Cadastrar Funcionário'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
