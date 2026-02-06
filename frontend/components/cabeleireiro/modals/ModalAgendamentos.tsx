'use client';

import { useState, useEffect } from 'react';
import { Modal } from '@/components/ui/Modal';
import apiClient from '@/lib/api-client';

interface LojaInfo {
  id: number;
  nome: string;
  slug: string;
  cor_primaria: string;
}

interface Agendamento {
  id: number;
  cliente: number;
  cliente_nome: string;
  profissional: number;
  profissional_nome: string;
  servico: number;
  servico_nome: string;
  data: string;
  horario: string;
  status: string;
  observacoes?: string;
}

export function ModalAgendamentos({ loja, onClose }: { loja: LojaInfo; onClose: () => void }) {
  const [agendamentos, setAgendamentos] = useState<Agendamento[]>([]);
  const [clientes, setClientes] = useState<any[]>([]);
  const [profissionais, setProfissionais] = useState<any[]>([]);
  const [servicos, setServicos] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editando, setEditando] = useState<Agendamento | null>(null);
  const [formData, setFormData] = useState({
    cliente: '',
    profissional: '',
    servico: '',
    data: '',
    horario: '',
    status: 'agendado',
    observacoes: ''
  });

  useEffect(() => {
    carregarDados();
  }, []);

  const carregarDados = async () => {
    try {
      setLoading(true);
      const [agendamentosRes, clientesRes, profissionaisRes, servicosRes] = await Promise.all([
        apiClient.get('/cabeleireiro/agendamentos/'),
        apiClient.get('/cabeleireiro/clientes/'),
        apiClient.get('/cabeleireiro/profissionais/'),
        apiClient.get('/cabeleireiro/servicos/')
      ]);
      
      setAgendamentos(agendamentosRes.data);
      setClientes(clientesRes.data);
      setProfissionais(profissionaisRes.data);
      setServicos(servicosRes.data);
    } catch (error) {
      console.error('Erro ao carregar dados:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editando) {
        await apiClient.put(`/cabeleireiro/agendamentos/${editando.id}/`, formData);
      } else {
        await apiClient.post('/cabeleireiro/agendamentos/', formData);
      }
      await carregarDados();
      setFormData({
        cliente: '',
        profissional: '',
        servico: '',
        data: '',
        horario: '',
        status: 'agendado',
        observacoes: ''
      });
      setEditando(null);
      setShowForm(false);
    } catch (error) {
      console.error('Erro ao salvar agendamento:', error);
      alert('Erro ao salvar agendamento');
    }
  };

  const handleEditar = (agendamento: Agendamento) => {
    setFormData({
      cliente: agendamento.cliente.toString(),
      profissional: agendamento.profissional.toString(),
      servico: agendamento.servico.toString(),
      data: agendamento.data,
      horario: agendamento.horario,
      status: agendamento.status,
      observacoes: agendamento.observacoes || ''
    });
    setEditando(agendamento);
    setShowForm(true);
  };

  const handleExcluir = async (id: number, nome: string) => {
    if (!confirm(`Deseja excluir o agendamento de ${nome}?`)) return;
    
    try {
      await apiClient.delete(`/cabeleireiro/agendamentos/${id}/`);
      await carregarDados();
    } catch (error) {
      console.error('Erro ao excluir agendamento:', error);
      alert('Erro ao excluir agendamento');
    }
  };

  if (showForm) {
    return (
      <Modal isOpen={true} onClose={onClose} maxWidth="2xl">
        <div className="p-6">
          <h2 className="text-2xl font-bold mb-6 flex items-center gap-2" style={{ color: loja.cor_primaria }}>
            📅 {editando ? 'Editar Agendamento' : 'Novo Agendamento'}
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
                    <option key={c.id} value={c.id}>{c.nome}</option>
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
                  onChange={(e) => setFormData({ ...formData, servico: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg"
                  required
                >
                  <option value="">Selecione...</option>
                  {servicos.map(s => (
                    <option key={s.id} value={s.id}>{s.nome} - R$ {s.preco}</option>
                  ))}
                </select>
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
                <input
                  type="time"
                  value={formData.horario}
                  onChange={(e) => setFormData({ ...formData, horario: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg"
                  required
                />
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
                onClick={() => {
                  setShowForm(false);
                  setEditando(null);
                }}
                className="px-6 py-2 border rounded-lg hover:bg-gray-50"
              >
                Cancelar
              </button>
              <button
                type="submit"
                className="px-6 py-2 text-white rounded-lg hover:opacity-90"
                style={{ backgroundColor: loja.cor_primaria }}
              >
                {editando ? 'Atualizar' : 'Salvar'}
              </button>
            </div>
          </form>
        </div>
      </Modal>
    );
  }

  return (
    <Modal isOpen={true} onClose={onClose} maxWidth="4xl">
      <div className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold flex items-center gap-2" style={{ color: loja.cor_primaria }}>
            📅 Agendamentos
          </h2>
          <button
            onClick={() => setShowForm(true)}
            className="px-6 py-2 text-white rounded-lg hover:opacity-90"
            style={{ backgroundColor: loja.cor_primaria }}
          >
            + Novo Agendamento
          </button>
        </div>

        {loading ? (
          <div className="text-center py-8">Carregando...</div>
        ) : agendamentos.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-lg mb-4">Nenhum agendamento cadastrado</p>
            <button 
              onClick={() => setShowForm(true)} 
              className="px-6 py-3 rounded-lg text-white" 
              style={{ backgroundColor: loja.cor_primaria }}
            >
              + Adicionar Primeiro Agendamento
            </button>
          </div>
        ) : (
          <div className="space-y-3 max-h-[60vh] overflow-y-auto">
            {agendamentos.map((agendamento) => (
              <div key={agendamento.id} className="flex flex-col sm:flex-row sm:items-center justify-between p-4 border rounded-xl hover:bg-gray-50 gap-3">
                <div className="flex-1">
                  <p className="font-semibold text-lg">{agendamento.cliente_nome}</p>
                  <p className="text-sm text-gray-600">
                    ✂️ {agendamento.servico_nome} • 👤 {agendamento.profissional_nome}
                  </p>
                  <p className="text-sm text-gray-600">
                    📅 {new Date(agendamento.data).toLocaleDateString('pt-BR')} às {agendamento.horario}
                  </p>
                  <span className={`inline-block mt-2 px-3 py-1 text-xs font-semibold rounded-full ${
                    agendamento.status === 'concluido' ? 'bg-green-100 text-green-800' :
                    agendamento.status === 'cancelado' ? 'bg-red-100 text-red-800' :
                    agendamento.status === 'em_atendimento' ? 'bg-blue-100 text-blue-800' :
                    'bg-yellow-100 text-yellow-800'
                  }`}>
                    {agendamento.status.replace('_', ' ').toUpperCase()}
                  </span>
                </div>
                <div className="flex gap-2">
                  <button onClick={() => handleEditar(agendamento)} className="px-3 py-2 text-sm text-white rounded-lg hover:opacity-90" style={{ backgroundColor: loja.cor_primaria }}>✏️ Editar</button>
                  <button onClick={() => handleExcluir(agendamento.id, agendamento.cliente_nome)} className="px-3 py-2 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700">🗑️ Excluir</button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </Modal>
  );
}
