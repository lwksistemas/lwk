'use client';

import { useState, useEffect } from 'react';
import { Modal } from '@/components/ui/Modal';
import apiClient from '@/lib/api-client';
import { extractArrayData, formatApiError } from '@/lib/api-helpers';
import { formatCurrency } from '@/lib/financeiro-helpers';

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

export function ModalAgendamentos({ 
  loja, 
  onClose,
  agendamentoId 
}: { 
  loja: LojaInfo; 
  onClose: () => void;
  agendamentoId?: number;
}) {
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
    valor: '',
    observacoes: ''
  });

  useEffect(() => {
    carregarDados();
  }, []);

  // Carregar agendamento específico para edição
  useEffect(() => {
    if (agendamentoId) {
      carregarAgendamentoParaEdicao(agendamentoId);
    }
  }, [agendamentoId]);

  const carregarAgendamentoParaEdicao = async (id: number) => {
    try {
      const response = await apiClient.get(`/cabeleireiro/agendamentos/${id}/`);
      const agendamento = response.data;
      
      setFormData({
        cliente: agendamento.cliente.toString(),
        profissional: agendamento.profissional?.toString() || '',
        servico: agendamento.servico.toString(),
        data: agendamento.data,
        horario: agendamento.horario,
        status: agendamento.status,
        valor: agendamento.valor?.toString() || '',
        observacoes: agendamento.observacoes || ''
      });
      setEditando(agendamento);
      setShowForm(true);
    } catch (error) {
      console.error('Erro ao carregar agendamento:', error);
      alert(formatApiError(error));
    }
  };

  const carregarDados = async () => {
    try {
      setLoading(true);
      
      // Carregar dados em paralelo
      const [agendamentosRes, clientesRes, profissionaisRes, servicosRes] = await Promise.all([
        apiClient.get('/cabeleireiro/agendamentos/'),
        apiClient.get('/cabeleireiro/clientes/'),
        apiClient.get('/cabeleireiro/profissionais/'),
        apiClient.get('/cabeleireiro/servicos/')
      ]);
      
      // Extrair arrays de forma segura
      const agendamentosArray = extractArrayData<Agendamento>(agendamentosRes);
      const clientesArray = extractArrayData(clientesRes);
      const profissionaisArray = extractArrayData(profissionaisRes);
      const servicosArray = extractArrayData(servicosRes);
      console.log('✅ [ModalAgendamentos] Profissionais:', profissionaisArray.length);
      console.log('✅ [ModalAgendamentos] Serviços:', servicosArray.length);
      
      setAgendamentos(agendamentosArray);
      setClientes(clientesArray);
      setProfissionais(profissionaisArray);
      setServicos(servicosArray);
    } catch (error) {
      console.error('❌ [ModalAgendamentos] Erro ao carregar dados:', error);
      alert(formatApiError(error));
      
      // Garantir arrays vazios em caso de erro
      setAgendamentos([]);
      setClientes([]);
      setProfissionais([]);
      setServicos([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
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

      if (editando) {
        await apiClient.put(`/cabeleireiro/agendamentos/${editando.id}/`, payload);
      } else {
        await apiClient.post('/cabeleireiro/agendamentos/', payload);
      }
      
      // Recarregar dados
      await carregarDados();
      
      // Resetar formulário
      setFormData({
        cliente: '',
        profissional: '',
        servico: '',
        data: '',
        horario: '',
        status: 'agendado',
        valor: '',
        observacoes: ''
      });
      setEditando(null);
      setShowForm(false);
    } catch (error) {
      console.error('Erro ao salvar agendamento:', error);
      alert(formatApiError(error));
    }
  };

  const handleEditar = (agendamento: Agendamento) => {
    setFormData({
      cliente: agendamento.cliente.toString(),
      profissional: agendamento.profissional?.toString() || '',
      servico: agendamento.servico.toString(),
      data: agendamento.data,
      horario: agendamento.horario,
      status: agendamento.status,
      valor: agendamento.valor?.toString() || '',
      observacoes: agendamento.observacoes || ''
    });
    setEditando(agendamento);
    setShowForm(true);
  };

  const handleServicoChange = (servicoId: string) => {
    setFormData({ ...formData, servico: servicoId });
    
    // Preencher valor automaticamente com o preço do serviço
    const servico = servicos.find(s => s.id.toString() === servicoId);
    if (servico && servico.preco) {
      setFormData(prev => ({ ...prev, servico: servicoId, valor: servico.preco.toString() }));
    }
  };

  const handleExcluir = async (id: number, nome: string) => {
    if (!confirm(`Deseja excluir o agendamento de ${nome}?`)) return;
    
    try {
      await apiClient.delete(`/cabeleireiro/agendamentos/${id}/`);
      await carregarDados();
    } catch (error) {
      console.error('Erro ao excluir agendamento:', error);
      alert(formatApiError(error));
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
                  onChange={(e) => handleServicoChange(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg"
                  required
                >
                  <option value="">Selecione...</option>
                  {servicos.map(s => (
                    <option key={s.id} value={s.id}>{s.nome} - {formatCurrency(s.preco)}</option>
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
            {agendamentos.map((agendamento) => {
              // Definir cores por status
              const statusColors: Record<string, { bg: string; text: string; label: string }> = {
                agendado: { bg: 'bg-blue-100', text: 'text-blue-800', label: 'Agendado' },
                confirmado: { bg: 'bg-green-100', text: 'text-green-800', label: 'Confirmado' },
                em_atendimento: { bg: 'bg-orange-100', text: 'text-orange-800', label: 'Em Atendimento' },
                concluido: { bg: 'bg-gray-100', text: 'text-gray-800', label: 'Concluído' },
                cancelado: { bg: 'bg-red-100', text: 'text-red-800', label: 'Cancelado' }
              };
              
              const statusColor = statusColors[agendamento.status] || statusColors.agendado;
              
              return (
                <div key={agendamento.id} className="flex flex-col sm:flex-row sm:items-center justify-between p-4 border rounded-xl hover:bg-gray-50 gap-3 transition-all">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <p className="font-semibold text-lg">{agendamento.cliente_nome}</p>
                      <span className={`px-3 py-1 text-xs font-semibold rounded-full ${statusColor.bg} ${statusColor.text}`}>
                        {statusColor.label}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mb-1">
                      ✂️ {agendamento.servico_nome} • 👤 {agendamento.profissional_nome}
                    </p>
                    <p className="text-sm text-gray-600 mb-1">
                      📅 {new Date(agendamento.data + 'T00:00:00').toLocaleDateString('pt-BR')} às {agendamento.horario}
                    </p>
                    <p className="text-sm font-semibold" style={{ color: loja.cor_primaria }}>
                      💰 {formatCurrency(agendamento.valor)}
                    </p>
                    {agendamento.observacoes && (
                      <p className="text-xs text-gray-500 mt-1">📝 {agendamento.observacoes}</p>
                    )}
                  </div>
                  <div className="flex gap-2">
                    <button 
                      onClick={() => handleEditar(agendamento)} 
                      className="px-3 py-2 text-sm text-white rounded-lg hover:opacity-90 transition-all" 
                      style={{ backgroundColor: loja.cor_primaria }}
                    >
                      ✏️ Editar
                    </button>
                    <button 
                      onClick={() => handleExcluir(agendamento.id, agendamento.cliente_nome)} 
                      className="px-3 py-2 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700 transition-all"
                    >
                      🗑️ Excluir
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </Modal>
  );
}
