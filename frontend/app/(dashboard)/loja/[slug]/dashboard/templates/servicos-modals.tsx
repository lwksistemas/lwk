// Modais completos para Dashboard de Serviços
// Este arquivo contém todos os modais com CRUD completo

import { useState, useEffect } from 'react';
import { clinicaApiClient } from '@/lib/api-client';
import { useToast } from '@/components/ui/Toast';

interface LojaInfo {
  id: number;
  nome: string;
  slug: string;
  cor_primaria: string;
}

const STATUS_AGENDAMENTO = [
  { value: 'agendado', label: 'Agendado' },
  { value: 'confirmado', label: 'Confirmado' },
  { value: 'em_andamento', label: 'Em Andamento' },
  { value: 'concluido', label: 'Concluído' },
  { value: 'cancelado', label: 'Cancelado' }
];

const STATUS_OS = [
  { value: 'aberta', label: 'Aberta' },
  { value: 'em_andamento', label: 'Em Andamento' },
  { value: 'aguardando_peca', label: 'Aguardando Peça' },
  { value: 'concluida', label: 'Concluída' },
  { value: 'cancelada', label: 'Cancelada' }
];

const STATUS_ORCAMENTO = [
  { value: 'pendente', label: 'Pendente' },
  { value: 'aprovado', label: 'Aprovado' },
  { value: 'recusado', label: 'Recusado' },
  { value: 'expirado', label: 'Expirado' }
];

// ==================== MODAL AGENDAMENTOS ====================
export function ModalAgendamentos({ loja, onClose, onSuccess }: { loja: LojaInfo; onClose: () => void; onSuccess?: () => void }) {
  const toast = useToast();
  const [mostrarFormulario, setMostrarFormulario] = useState(false);
  const [editando, setEditando] = useState<number | null>(null);
  const [agendamentos, setAgendamentos] = useState<any[]>([]);
  const [clientes, setClientes] = useState<any[]>([]);
  const [servicos, setServicos] = useState<any[]>([]);
  const [profissionais, setProfissionais] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingLista, setLoadingLista] = useState(true);
  const [formData, setFormData] = useState({
    cliente_id: '',
    servico_id: '',
    profissional_id: '',
    data: '',
    horario: '',
    status: 'agendado',
    endereco_atendimento: '',
    observacoes: '',
    valor: ''
  });

  useEffect(() => {
    loadDados();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadDados = async () => {
    try {
      setLoadingLista(true);
      const [agendRes, cliRes, servRes, profRes] = await Promise.all([
        clinicaApiClient.get('/servicos/agendamentos/'),
        clinicaApiClient.get('/servicos/clientes/'),
        clinicaApiClient.get('/servicos/servicos/'),
        clinicaApiClient.get('/servicos/profissionais/')
      ]);
      setAgendamentos(Array.isArray(agendRes.data) ? agendRes.data : agendRes.data?.results ?? []);
      setClientes(Array.isArray(cliRes.data) ? cliRes.data : cliRes.data?.results ?? []);
      setServicos(Array.isArray(servRes.data) ? servRes.data : servRes.data?.results ?? []);
      setProfissionais(Array.isArray(profRes.data) ? profRes.data : profRes.data?.results ?? []);
    } catch (error) {
      console.error('Erro ao carregar dados:', error);
      toast.error('Erro ao carregar dados');
    } finally {
      setLoadingLista(false);
    }
  };

  const handleNovo = () => {
    setEditando(null);
    setFormData({ cliente_id: '', servico_id: '', profissional_id: '', data: '', horario: '', status: 'agendado', endereco_atendimento: '', observacoes: '', valor: '' });
    setMostrarFormulario(true);
  };

  const handleEditar = (item: any) => {
    setEditando(item.id);
    setFormData({
      cliente_id: String(item.cliente),
      servico_id: String(item.servico),
      profissional_id: String(item.profissional || ''),
      data: item.data,
      horario: item.horario,
      status: item.status,
      endereco_atendimento: item.endereco_atendimento || '',
      observacoes: item.observacoes || '',
      valor: String(item.valor)
    });
    setMostrarFormulario(true);
  };

  const handleExcluir = async (id: number, nome: string) => {
    if (!confirm(`Excluir agendamento de "${nome}"?`)) return;
    try {
      await clinicaApiClient.delete(`/servicos/agendamentos/${id}/`);
      toast.success('Agendamento excluído');
      loadDados();
      onSuccess?.();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erro ao excluir');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const payload = {
        cliente: parseInt(formData.cliente_id),
        servico: parseInt(formData.servico_id),
        profissional: formData.profissional_id ? parseInt(formData.profissional_id) : null,
        data: formData.data,
        horario: formData.horario,
        status: formData.status,
        endereco_atendimento: formData.endereco_atendimento || null,
        observacoes: formData.observacoes || null,
        valor: parseFloat(formData.valor)
      };
      if (editando) {
        await clinicaApiClient.put(`/servicos/agendamentos/${editando}/`, payload);
        toast.success('Agendamento atualizado');
      } else {
        await clinicaApiClient.post('/servicos/agendamentos/', payload);
        toast.success('Agendamento criado');
      }
      setMostrarFormulario(false);
      loadDados();
      onSuccess?.();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erro ao salvar');
    } finally {
      setLoading(false);
    }
  };

  if (mostrarFormulario) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 sm:p-8 max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-xl">
          <h3 className="text-xl sm:text-2xl font-bold mb-6 text-gray-900 dark:text-white" style={{ color: loja.cor_primaria }}>
            📅 {editando ? 'Editar' : 'Novo'} Agendamento
          </h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Cliente *</label>
                <select name="cliente_id" value={formData.cliente_id} onChange={(e) => setFormData(prev => ({ ...prev, cliente_id: e.target.value }))} required className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md">
                  <option value="">Selecione...</option>
                  {clientes.map(c => <option key={c.id} value={c.id}>{c.nome}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Serviço *</label>
                <select name="servico_id" value={formData.servico_id} onChange={(e) => setFormData(prev => ({ ...prev, servico_id: e.target.value }))} required className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md">
                  <option value="">Selecione...</option>
                  {servicos.map(s => <option key={s.id} value={s.id}>{s.nome}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Profissional</label>
                <select name="profissional_id" value={formData.profissional_id} onChange={(e) => setFormData(prev => ({ ...prev, profissional_id: e.target.value }))} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md">
                  <option value="">Selecione...</option>
                  {profissionais.map(p => <option key={p.id} value={p.id}>{p.nome}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Data *</label>
                <input type="date" name="data" value={formData.data} onChange={(e) => setFormData(prev => ({ ...prev, data: e.target.value }))} required className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Horário *</label>
                <input type="time" name="horario" value={formData.horario} onChange={(e) => setFormData(prev => ({ ...prev, horario: e.target.value }))} required className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Status *</label>
                <select name="status" value={formData.status} onChange={(e) => setFormData(prev => ({ ...prev, status: e.target.value }))} required className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md">
                  {STATUS_AGENDAMENTO.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Valor (R$) *</label>
                <input type="number" name="valor" value={formData.valor} onChange={(e) => setFormData(prev => ({ ...prev, valor: e.target.value }))} required min="0" step="0.01" className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md" />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Endereço de Atendimento</label>
                <input type="text" name="endereco_atendimento" value={formData.endereco_atendimento} onChange={(e) => setFormData(prev => ({ ...prev, endereco_atendimento: e.target.value }))} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md" placeholder="Se o serviço for no local do cliente" />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Observações</label>
                <textarea name="observacoes" value={formData.observacoes} onChange={(e) => setFormData(prev => ({ ...prev, observacoes: e.target.value }))} rows={3} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md" />
              </div>
            </div>
            <div className="flex justify-end gap-3 pt-4">
              <button type="button" onClick={() => setMostrarFormulario(false)} disabled={loading} className="px-6 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-900 dark:text-white min-h-[40px]">Cancelar</button>
              <button type="submit" disabled={loading} className="px-6 py-2 text-white rounded-lg hover:opacity-90 min-h-[40px]" style={{ backgroundColor: loja.cor_primaria }}>{loading ? 'Salvando...' : (editando ? 'Atualizar' : 'Criar')}</button>
            </div>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 sm:p-8 max-w-4xl w-full max-h-[80vh] overflow-y-auto shadow-xl">
        <h3 className="text-xl sm:text-2xl font-bold mb-4 text-gray-900 dark:text-white" style={{ color: loja.cor_primaria }}>📅 Gerenciar Agendamentos</h3>
        {loadingLista ? (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">Carregando...</div>
        ) : agendamentos.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-500 dark:text-gray-400 mb-4">Nenhum agendamento cadastrado</p>
            <button onClick={handleNovo} className="px-6 py-2 text-white rounded-lg hover:opacity-90 min-h-[40px]" style={{ backgroundColor: loja.cor_primaria }}>+ Novo Agendamento</button>
          </div>
        ) : (
          <div className="space-y-4 mb-6">
            {agendamentos.map((item: any) => (
              <div key={item.id} className="flex flex-col sm:flex-row sm:items-center justify-between p-4 border dark:border-gray-600 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700/50 gap-3">
                <div className="flex-1">
                  <p className="font-semibold text-lg text-gray-900 dark:text-white">{item.cliente_nome}</p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">{item.servico_nome} • {item.data} {item.horario}</p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">{item.profissional_nome || 'Sem profissional'}</p>
                  <span className="inline-block mt-2 px-3 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 text-xs font-semibold rounded-full">{STATUS_AGENDAMENTO.find(s => s.value === item.status)?.label}</span>
                </div>
                <div className="flex gap-2">
                  <button onClick={() => handleEditar(item)} className="px-3 py-2 text-sm text-white rounded-lg hover:opacity-90 min-h-[40px]" style={{ backgroundColor: loja.cor_primaria }}>✏️ Editar</button>
                  <button onClick={() => handleExcluir(item.id, item.cliente_nome)} className="px-3 py-2 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700 min-h-[40px]">🗑️ Excluir</button>
                </div>
              </div>
            ))}
          </div>
        )}
        <div className="flex justify-end gap-3 pt-4 border-t dark:border-gray-600">
          <button onClick={onClose} className="px-6 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-900 dark:text-white min-h-[40px]">Fechar</button>
          <button onClick={handleNovo} className="px-6 py-2 text-white rounded-lg hover:opacity-90 min-h-[40px]" style={{ backgroundColor: loja.cor_primaria }}>+ Novo Agendamento</button>
        </div>
      </div>
    </div>
  );
}

// ==================== MODAL CLIENTES ====================
export function ModalClientes({ loja, onClose }: { loja: LojaInfo; onClose: () => void }) {
  const toast = useToast();
  const [mostrarFormulario, setMostrarFormulario] = useState(false);
  const [editando, setEditando] = useState<number | null>(null);
  const [clientes, setClientes] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingLista, setLoadingLista] = useState(true);
  const [formData, setFormData] = useState({
    nome: '',
    email: '',
    telefone: '',
    tipo_cliente: 'pf',
    observacoes: ''
  });

  useEffect(() => {
    loadClientes();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadClientes = async () => {
    try {
      setLoadingLista(true);
      const res = await clinicaApiClient.get('/servicos/clientes/');
      setClientes(Array.isArray(res.data) ? res.data : res.data?.results ?? []);
    } catch (error) {
      toast.error('Erro ao carregar clientes');
    } finally {
      setLoadingLista(false);
    }
  };

  const handleNovo = () => {
    setEditando(null);
    setFormData({ nome: '', email: '', telefone: '', tipo_cliente: 'pf', observacoes: '' });
    setMostrarFormulario(true);
  };

  const handleEditar = (item: any) => {
    setEditando(item.id);
    setFormData({
      nome: item.nome,
      email: item.email || '',
      telefone: item.telefone || '',
      tipo_cliente: item.tipo_cliente || 'pf',
      observacoes: item.observacoes || ''
    });
    setMostrarFormulario(true);
  };

  const handleExcluir = async (id: number, nome: string) => {
    if (!confirm(`Excluir cliente "${nome}"?`)) return;
    try {
      await clinicaApiClient.delete(`/servicos/clientes/${id}/`);
      toast.success('Cliente excluído');
      loadClientes();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erro ao excluir');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const payload = {
        nome: formData.nome,
        email: formData.email || null,
        telefone: formData.telefone || null,
        tipo_cliente: formData.tipo_cliente,
        observacoes: formData.observacoes || null
      };
      if (editando) {
        await clinicaApiClient.put(`/servicos/clientes/${editando}/`, payload);
        toast.success('Cliente atualizado');
      } else {
        await clinicaApiClient.post('/servicos/clientes/', payload);
        toast.success('Cliente criado');
      }
      setMostrarFormulario(false);
      loadClientes();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erro ao salvar');
    } finally {
      setLoading(false);
    }
  };

  if (mostrarFormulario) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 sm:p-8 max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-xl">
          <h3 className="text-xl sm:text-2xl font-bold mb-6 text-gray-900 dark:text-white" style={{ color: loja.cor_primaria }}>
            👤 {editando ? 'Editar' : 'Novo'} Cliente
          </h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nome *</label>
              <input type="text" value={formData.nome} onChange={(e) => setFormData(prev => ({ ...prev, nome: e.target.value }))} required className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md" />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Email</label>
                <input type="email" value={formData.email} onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Telefone</label>
                <input type="tel" value={formData.telefone} onChange={(e) => setFormData(prev => ({ ...prev, telefone: e.target.value }))} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md" />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Tipo *</label>
              <select value={formData.tipo_cliente} onChange={(e) => setFormData(prev => ({ ...prev, tipo_cliente: e.target.value }))} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md">
                <option value="pf">Pessoa Física</option>
                <option value="pj">Pessoa Jurídica</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Observações</label>
              <textarea value={formData.observacoes} onChange={(e) => setFormData(prev => ({ ...prev, observacoes: e.target.value }))} rows={3} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md" />
            </div>
            <div className="flex justify-end gap-3 pt-4">
              <button type="button" onClick={() => setMostrarFormulario(false)} disabled={loading} className="px-6 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-900 dark:text-white min-h-[40px]">Cancelar</button>
              <button type="submit" disabled={loading} className="px-6 py-2 text-white rounded-lg hover:opacity-90 min-h-[40px]" style={{ backgroundColor: loja.cor_primaria }}>{loading ? 'Salvando...' : (editando ? 'Atualizar' : 'Criar')}</button>
            </div>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 sm:p-8 max-w-4xl w-full max-h-[80vh] overflow-y-auto shadow-xl">
        <h3 className="text-xl sm:text-2xl font-bold mb-4 text-gray-900 dark:text-white" style={{ color: loja.cor_primaria }}>👤 Gerenciar Clientes</h3>
        {loadingLista ? (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">Carregando...</div>
        ) : clientes.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-500 dark:text-gray-400 mb-4">Nenhum cliente cadastrado</p>
            <button onClick={handleNovo} className="px-6 py-2 text-white rounded-lg hover:opacity-90 min-h-[40px]" style={{ backgroundColor: loja.cor_primaria }}>+ Novo Cliente</button>
          </div>
        ) : (
          <div className="space-y-4 mb-6">
            {clientes.map((item: any) => (
              <div key={item.id} className="flex flex-col sm:flex-row sm:items-center justify-between p-4 border dark:border-gray-600 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700/50 gap-3">
                <div className="flex-1">
                  <p className="font-semibold text-lg text-gray-900 dark:text-white">{item.nome}</p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">{item.email || 'Sem email'} • {item.telefone || 'Sem telefone'}</p>
                  <span className="inline-block mt-2 px-3 py-1 bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300 text-xs font-semibold rounded-full">{item.tipo_cliente === 'pf' ? 'Pessoa Física' : 'Pessoa Jurídica'}</span>
                </div>
                <div className="flex gap-2">
                  <button onClick={() => handleEditar(item)} className="px-3 py-2 text-sm text-white rounded-lg hover:opacity-90 min-h-[40px]" style={{ backgroundColor: loja.cor_primaria }}>✏️ Editar</button>
                  <button onClick={() => handleExcluir(item.id, item.nome)} className="px-3 py-2 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700 min-h-[40px]">🗑️ Excluir</button>
                </div>
              </div>
            ))}
          </div>
        )}
        <div className="flex justify-end gap-3 pt-4 border-t dark:border-gray-600">
          <button onClick={onClose} className="px-6 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-900 dark:text-white min-h-[40px]">Fechar</button>
          <button onClick={handleNovo} className="px-6 py-2 text-white rounded-lg hover:opacity-90 min-h-[40px]" style={{ backgroundColor: loja.cor_primaria }}>+ Novo Cliente</button>
        </div>
      </div>
    </div>
  );
}

// Continua no próximo arquivo devido ao tamanho...
