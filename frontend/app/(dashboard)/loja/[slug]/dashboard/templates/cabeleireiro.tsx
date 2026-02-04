'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useToast } from '@/components/ui/Toast';
import { ThemeToggle } from '@/components/ui/ThemeProvider';
import { DashboardSkeleton, AgendamentosListSkeleton } from '@/components/ui/Skeleton';
import { useDashboardData } from '@/hooks/useDashboardData';
import { useModals } from '@/hooks/useModals';
import { Modal } from '@/components/ui/Modal';
import { LojaInfo } from '@/types/dashboard';
import { ensureArray } from '@/lib/array-helpers';
import apiClient from '@/lib/api-client';

// Types específicos do Cabeleireiro
interface EstatisticasCabeleireiro {
  agendamentos_hoje: number;
  agendamentos_mes: number;
  clientes_ativos: number;
  servicos_ativos: number;
  receita_mensal: number;
}

interface AgendamentoCabeleireiro {
  id: number;
  cliente_nome: string;
  cliente_telefone: string;
  profissional_nome: string;
  servico_nome: string;
  data: string;
  horario: string;
  status: string;
  valor: number;
}

export default function DashboardCabeleireiro({ loja }: { loja: LojaInfo }) {
  const router = useRouter();
  const toast = useToast();

  // Hook para gerenciar modais
  const { modals, openModal, closeModal } = useModals([
    'agendamento', 'cliente', 'servico', 'profissional',
    'produto', 'venda', 'funcionarios', 'horarios', 'bloqueios', 'calendario'
  ] as const);

  // Hook para carregar dados do dashboard
  const { loading, loadingData, stats, data, reload } = useDashboardData<EstatisticasCabeleireiro, AgendamentoCabeleireiro>({
    endpoint: '/cabeleireiro/agendamentos/dashboard/',
    initialStats: {
      agendamentos_hoje: 0,
      agendamentos_mes: 0,
      clientes_ativos: 0,
      servicos_ativos: 0,
      receita_mensal: 0
    },
    initialData: [],
    transformResponse: (responseData) => ({
      stats: responseData.estatisticas || {
        agendamentos_hoje: 0,
        agendamentos_mes: 0,
        clientes_ativos: 0,
        servicos_ativos: 0,
        receita_mensal: 0
      },
      data: ensureArray<AgendamentoCabeleireiro>(responseData.proximos)
    })
  });

  // Garantir que o backend receba X-Loja-ID
  useEffect(() => {
    if (typeof window !== 'undefined' && loja?.id) {
      const current = sessionStorage.getItem('current_loja_id');
      if (current !== String(loja.id)) {
        sessionStorage.setItem('current_loja_id', String(loja.id));
      }
      if (loja.slug) sessionStorage.setItem('loja_slug', loja.slug);
    }
  }, [loja?.id, loja?.slug]);

  // Handlers
  const handleNovoAgendamento = () => openModal('calendario');
  const handleNovoCliente = () => openModal('cliente');
  const handleServicos = () => openModal('servico');
  const handleNovoProfissional = () => openModal('profissional');
  const handleProdutos = () => openModal('produto');
  const handleVendas = () => openModal('venda');
  const handleFuncionarios = () => openModal('funcionarios');
  const handleHorarios = () => openModal('horarios');
  const handleBloqueios = () => openModal('bloqueios');
  const handleRelatorios = () => router.push(`/loja/${loja.slug}/relatorios`);

  // Loading inicial
  if (loading) {
    return <DashboardSkeleton />;
  }

  return (
    <div className="space-y-6 sm:space-y-8 px-2 sm:px-4 lg:px-8">
      {/* Header com toggle de tema */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
        <h1 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">
          Dashboard - {loja.nome}
        </h1>
        <ThemeToggle />
      </div>

      {/* Ações Rápidas */}
      <div className="bg-white dark:bg-gray-800 p-4 sm:p-6 rounded-xl shadow-lg card-hover">
        <h3 className="text-base sm:text-lg font-semibold mb-3 sm:mb-4 text-gray-900 dark:text-white" style={{ color: loja.cor_primaria }}>
          💇 Ações Rápidas
        </h3>
        <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 gap-2 sm:gap-3 md:gap-4">
          <ActionButton onClick={handleNovoAgendamento} color="#3B82F6" icon="📅" label="Agendamento" />
          <ActionButton onClick={handleNovoCliente} color="#F59E0B" icon="👤" label="Cliente" />
          <ActionButton onClick={handleNovoProfissional} color="#EF4444" icon="💇" label="Profissional" />
          <ActionButton onClick={handleServicos} color="#06B6D4" icon="✂️" label="Serviços" />
          <ActionButton onClick={handleProdutos} color="#8B5CF6" icon="🧴" label="Produtos" />
          <ActionButton onClick={handleVendas} color="#10B981" icon="💰" label="Vendas" />
          <ActionButton onClick={handleFuncionarios} color="#EC4899" icon="👥" label="Funcionários" />
          <ActionButton onClick={handleHorarios} color="#6366F1" icon="🕐" label="Horários" />
          <ActionButton onClick={handleBloqueios} color="#EF4444" icon="🚫" label="Bloqueios" />
          <ActionButton onClick={handleRelatorios} color="#059669" icon="📊" label="Relatórios" />
        </div>
        
        <div className="mt-3 sm:mt-4 p-2 sm:p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
          <p className="text-[10px] sm:text-xs text-gray-600 dark:text-gray-400 text-center">
            💡 <strong>Dashboard Cabeleireiro</strong> - Gerencie agendamentos, clientes, serviços e profissionais
          </p>
        </div>
      </div>

      {/* Estatísticas */}
      <div className="grid grid-cols-2 sm:grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4 md:gap-6">
        <StatCard title="Agendamentos Hoje" value={stats.agendamentos_hoje} icon="📅" cor={loja.cor_primaria} trend="+15%" />
        <StatCard title="Clientes Ativos" value={stats.clientes_ativos} icon="👥" cor={loja.cor_primaria} />
        <StatCard title="Serviços" value={stats.servicos_ativos} icon="✂️" cor={loja.cor_primaria} />
        <StatCard title="Receita Mensal" value={`R$ ${stats.receita_mensal.toLocaleString('pt-BR')}`} icon="💰" cor={loja.cor_primaria} trend="+10%" />
      </div>

      {/* Próximos Agendamentos */}
      <div className="bg-white dark:bg-gray-800 p-4 sm:p-6 rounded-xl shadow-lg">
        <div className="flex items-center justify-between mb-3 sm:mb-4">
          <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white">Próximos Agendamentos</h3>
          <button
            onClick={handleNovoAgendamento}
            className="text-xs sm:text-sm px-3 sm:px-4 py-2 min-h-[40px] rounded-lg text-white hover:opacity-90 transition-all btn-press shadow-md"
            style={{ backgroundColor: loja.cor_primaria }}
          >
            + Novo
          </button>
        </div>
        
        {loadingData ? (
          <AgendamentosListSkeleton count={3} />
        ) : data.length === 0 ? (
          <EmptyState 
            message="Nenhum agendamento cadastrado"
            subMessage="Comece adicionando seu primeiro agendamento"
            actionLabel="+ Adicionar Primeiro Agendamento"
            onAction={handleNovoAgendamento}
            cor={loja.cor_primaria}
          />
        ) : (
          <div className="space-y-4">
            {data.map((agendamento) => (
              <AgendamentoCard key={agendamento.id} agendamento={agendamento} cor={loja.cor_primaria} />
            ))}
          </div>
        )}
      </div>

      {/* Modal de Calendário/Agendamentos */}
      {modals.calendario && (
        <ModalAgendamento loja={loja} onClose={() => {
          closeModal('calendario');
          reload();
        }} />
      )}

      {/* Modal de Clientes */}
      {modals.cliente && (
        <ModalCliente loja={loja} onClose={() => {
          closeModal('cliente');
          reload();
        }} />
      )}

      {/* Modal de Profissionais */}
      {modals.profissional && (
        <ModalProfissional loja={loja} onClose={() => {
          closeModal('profissional');
          reload();
        }} />
      )}

      {/* Modal de Serviços */}
      {modals.servico && (
        <ModalServico loja={loja} onClose={() => {
          closeModal('servico');
          reload();
        }} />
      )}

      {/* Modais simples "Em breve" para funcionalidades ainda não implementadas */}
      <Modal isOpen={modals.produto} onClose={() => closeModal('produto')} maxWidth="md">
        <div className="p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">🧴 Produtos</h3>
            <button onClick={() => closeModal('produto')} className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 p-1 rounded">✕</button>
          </div>
          <p className="text-gray-600 dark:text-gray-400 text-sm">Em breve você poderá gerenciar produtos por aqui.</p>
          <button onClick={() => closeModal('produto')} className="mt-4 px-4 py-2 rounded-lg text-white text-sm" style={{ backgroundColor: loja.cor_primaria }}>Fechar</button>
        </div>
      </Modal>
      <Modal isOpen={modals.venda} onClose={() => closeModal('venda')} maxWidth="md">
        <div className="p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">� Nova Venda</h3>
            <button onClick={() => closeModal('venda')} className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 p-1 rounded">✕</button>
          </div>
          <p className="text-gray-600 dark:text-gray-400 text-sm">Em breve você poderá registrar vendas por aqui.</p>
          <button onClick={() => closeModal('venda')} className="mt-4 px-4 py-2 rounded-lg text-white text-sm" style={{ backgroundColor: loja.cor_primaria }}>Fechar</button>
        </div>
      </Modal>
      <Modal isOpen={modals.funcionarios} onClose={() => closeModal('funcionarios')} maxWidth="md">
        <div className="p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">👥 Funcionários</h3>
            <button onClick={() => closeModal('funcionarios')} className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 p-1 rounded">✕</button>
          </div>
          <p className="text-gray-600 dark:text-gray-400 text-sm">Em breve você poderá gerenciar funcionários por aqui.</p>
          <button onClick={() => closeModal('funcionarios')} className="mt-4 px-4 py-2 rounded-lg text-white text-sm" style={{ backgroundColor: loja.cor_primaria }}>Fechar</button>
        </div>
      </Modal>
      <Modal isOpen={modals.horarios} onClose={() => closeModal('horarios')} maxWidth="md">
        <div className="p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">� Horários de Funcionamento</h3>
            <button onClick={() => closeModal('horarios')} className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 p-1 rounded">✕</button>
          </div>
          <p className="text-gray-600 dark:text-gray-400 text-sm">Em breve você poderá configurar horários por aqui.</p>
          <button onClick={() => closeModal('horarios')} className="mt-4 px-4 py-2 rounded-lg text-white text-sm" style={{ backgroundColor: loja.cor_primaria }}>Fechar</button>
        </div>
      </Modal>
      <Modal isOpen={modals.bloqueios} onClose={() => closeModal('bloqueios')} maxWidth="md">
        <div className="p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">🚫 Bloqueios de Agenda</h3>
            <button onClick={() => closeModal('bloqueios')} className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 p-1 rounded">✕</button>
          </div>
          <p className="text-gray-600 dark:text-gray-400 text-sm">Em breve você poderá gerenciar bloqueios de agenda por aqui.</p>
          <button onClick={() => closeModal('bloqueios')} className="mt-4 px-4 py-2 rounded-lg text-white text-sm" style={{ backgroundColor: loja.cor_primaria }}>Fechar</button>
        </div>
      </Modal>
    </div>
  );
}

// Componente de botão de ação rápida
function ActionButton({ onClick, color, icon, label }: { onClick: () => void; color: string; icon: string; label: string }) {
  return (
    <button 
      onClick={onClick}
      className="group p-2 sm:p-3 md:p-4 rounded-lg sm:rounded-xl text-white font-semibold 
                 transition-all duration-200 transform hover:scale-105 active:scale-95
                 shadow-md sm:shadow-lg hover:shadow-xl btn-press
                 relative overflow-hidden min-h-[70px] sm:min-h-[80px] md:min-h-[100px]"
      style={{ backgroundColor: color }}
    >
      <div className="absolute inset-0 bg-white/0 group-hover:bg-white/10 transition-colors duration-200" />
      <div className="relative flex flex-col items-center justify-center h-full">
        <div className="text-xl sm:text-2xl md:text-3xl mb-1 sm:mb-2 transform group-hover:scale-110 transition-transform duration-200">{icon}</div>
        <div className="text-[10px] sm:text-xs md:text-sm leading-tight text-center">{label}</div>
      </div>
    </button>
  );
}

// Componente de card de estatísticas
function StatCard({ title, value, icon, cor, trend }: { title: string; value: string | number; icon: string; cor: string; trend?: string }) {
  return (
    <div className="bg-white dark:bg-gray-800 p-3 sm:p-4 md:p-6 rounded-xl shadow-lg hover:shadow-xl transition-all duration-200 card-hover group">
      <div className="flex items-center justify-between gap-2">
        <div className="min-w-0 flex-1">
          <h3 className="text-gray-500 dark:text-gray-400 text-xs sm:text-sm font-medium truncate">{title}</h3>
          <p className="text-xl sm:text-2xl md:text-3xl font-bold mt-1 sm:mt-2 text-gray-900 dark:text-white truncate" style={{ color: cor }}>
            {value}
          </p>
          {trend && (
            <span className="text-[10px] sm:text-xs text-green-500 dark:text-green-400 font-medium mt-1 inline-block">
              {trend} vs mês anterior
            </span>
          )}
        </div>
        <div 
          className="w-10 h-10 sm:w-12 sm:h-12 md:w-14 md:h-14 rounded-lg sm:rounded-xl flex items-center justify-center flex-shrink-0
                     transform group-hover:scale-110 transition-transform duration-200"
          style={{ backgroundColor: `${cor}20` }}
        >
          <span className="text-xl sm:text-2xl md:text-3xl">{icon}</span>
        </div>
      </div>
    </div>
  );
}

// Componente de card de agendamento
function AgendamentoCard({ agendamento, cor }: { agendamento: AgendamentoCabeleireiro; cor: string }) {
  const statusConfig: Record<string, { bg: string; text: string }> = {
    confirmado: { bg: 'bg-green-100 dark:bg-green-900/30', text: 'text-green-800 dark:text-green-300' },
    agendado: { bg: 'bg-blue-100 dark:bg-blue-900/30', text: 'text-blue-800 dark:text-blue-300' },
    cancelado: { bg: 'bg-red-100 dark:bg-red-900/30', text: 'text-red-800 dark:text-red-300' },
    em_atendimento: { bg: 'bg-yellow-100 dark:bg-yellow-900/30', text: 'text-yellow-800 dark:text-yellow-300' },
    concluido: { bg: 'bg-gray-100 dark:bg-gray-700', text: 'text-gray-800 dark:text-gray-300' },
  };
  
  const status = statusConfig[agendamento.status] || { bg: 'bg-gray-100 dark:bg-gray-700', text: 'text-gray-800 dark:text-gray-300' };

  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between p-3 sm:p-4 bg-gray-50 dark:bg-gray-700/50 rounded-xl 
                    hover:bg-gray-100 dark:hover:bg-gray-700 transition-all duration-200 
                    cursor-pointer group card-hover gap-3 sm:gap-4">
      <div className="flex items-center space-x-3 sm:space-x-4">
        <div 
          className="w-10 h-10 sm:w-12 sm:h-12 rounded-lg sm:rounded-xl flex items-center justify-center text-white font-bold text-base sm:text-lg flex-shrink-0
                     transform group-hover:scale-105 transition-transform duration-200 shadow-md"
          style={{ backgroundColor: cor }}
        >
          {agendamento.cliente_nome.charAt(0)}
        </div>
        <div className="min-w-0 flex-1">
          <p className="font-semibold text-gray-900 dark:text-white text-sm sm:text-base truncate">{agendamento.cliente_nome}</p>
          <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400 truncate">{agendamento.servico_nome}</p>
          <p className="text-[10px] sm:text-xs text-gray-500 dark:text-gray-500 truncate">Prof: {agendamento.profissional_nome}</p>
        </div>
      </div>
      <div className="flex sm:flex-col items-center sm:items-end justify-between sm:justify-start gap-2 sm:gap-1 pl-13 sm:pl-0">
        <div className="sm:text-right">
          <p className="font-bold text-base sm:text-lg" style={{ color: cor }}>
            {agendamento.horario}
          </p>
          <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">{agendamento.data}</p>
        </div>
        <span className={`text-[10px] sm:text-xs px-2 sm:px-3 py-1 rounded-full font-medium whitespace-nowrap ${status.bg} ${status.text}`}>
          {agendamento.status}
        </span>
      </div>
    </div>
  );
}

// Componente de estado vazio
function EmptyState({ message, subMessage, actionLabel, onAction, cor }: { 
  message: string; 
  subMessage: string; 
  actionLabel: string; 
  onAction: () => void; 
  cor: string;
}) {
  return (
    <div className="text-center py-8 sm:py-12 px-4">
      <div className="w-12 h-12 sm:w-16 sm:h-16 mx-auto mb-3 sm:mb-4 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
        <span className="text-2xl sm:text-3xl">📅</span>
      </div>
      <p className="text-base sm:text-lg mb-1 sm:mb-2 text-gray-700 dark:text-gray-300">{message}</p>
      <p className="text-xs sm:text-sm mb-4 text-gray-500 dark:text-gray-500">{subMessage}</p>
      <button
        onClick={onAction}
        className="px-4 sm:px-6 py-2.5 sm:py-3 min-h-[44px] rounded-xl text-white hover:opacity-90 transition-all btn-press shadow-lg text-sm sm:text-base active:scale-95"
        style={{ backgroundColor: cor }}
      >
        {actionLabel}
      </button>
    </div>
  );
}

// Modal de Agendamento (placeholder - será implementado depois)
function ModalAgendamento({ loja, onClose }: { loja: LojaInfo; onClose: () => void }) {
  return (
    <Modal isOpen={true} onClose={onClose} maxWidth="md">
      <div className="p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">📅 Novo Agendamento</h3>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 p-1 rounded">✕</button>
        </div>
        <p className="text-gray-600 dark:text-gray-400 text-sm">
          Em breve você poderá criar agendamentos por aqui. Por enquanto, use o sistema de agendamentos da clínica.
        </p>
        <button onClick={onClose} className="mt-4 px-4 py-2 rounded-lg text-white text-sm" style={{ backgroundColor: loja.cor_primaria }}>Fechar</button>
      </div>
    </Modal>
  );
}

// Modal de Cliente
function ModalCliente({ loja, onClose }: { loja: LojaInfo; onClose: () => void }) {
  const toast = useToast();
  const [clientes, setClientes] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [editando, setEditando] = useState<any | null>(null);
  const [formData, setFormData] = useState({ nome: '', telefone: '', email: '', cpf: '', data_nascimento: '', observacoes: '' });

  useEffect(() => {
    carregarClientes();
  }, []);

  const carregarClientes = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/cabeleireiro/clientes/');
      setClientes(ensureArray(response.data));
    } catch (error) {
      console.error('Erro ao carregar clientes:', error);
      toast.error('Erro ao carregar clientes');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editando) {
        await apiClient.put(`/cabeleireiro/clientes/${editando.id}/`, formData);
        toast.success('Cliente atualizado!');
      } else {
        await apiClient.post('/cabeleireiro/clientes/', formData);
        toast.success('Cliente cadastrado!');
      }
      setFormData({ nome: '', telefone: '', email: '', cpf: '', data_nascimento: '', observacoes: '' });
      setEditando(null);
      carregarClientes();
    } catch (error) {
      console.error('Erro ao salvar cliente:', error);
      toast.error('Erro ao salvar cliente');
    }
  };

  const handleEditar = (cliente: any) => {
    setEditando(cliente);
    setFormData({
      nome: cliente.nome || '',
      telefone: cliente.telefone || '',
      email: cliente.email || '',
      cpf: cliente.cpf || '',
      data_nascimento: cliente.data_nascimento || '',
      observacoes: cliente.observacoes || ''
    });
  };

  const handleExcluir = async (id: number) => {
    if (!confirm('Deseja realmente excluir este cliente?')) return;
    try {
      await apiClient.delete(`/cabeleireiro/clientes/${id}/`);
      toast.success('Cliente excluído!');
      carregarClientes();
    } catch (error) {
      console.error('Erro ao excluir cliente:', error);
      toast.error('Erro ao excluir cliente');
    }
  };

  return (
    <Modal isOpen={true} onClose={onClose} maxWidth="4xl">
      <div className="p-6">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-xl font-bold text-gray-900 dark:text-white">👤 Clientes</h3>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 p-2 rounded">✕</button>
        </div>

        {/* Formulário */}
        <form onSubmit={handleSubmit} className="mb-6 p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <input
              type="text"
              placeholder="Nome *"
              value={formData.nome}
              onChange={(e) => setFormData({ ...formData, nome: e.target.value })}
              required
              className="px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            />
            <input
              type="tel"
              placeholder="Telefone *"
              value={formData.telefone}
              onChange={(e) => setFormData({ ...formData, telefone: e.target.value })}
              required
              className="px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            />
            <input
              type="email"
              placeholder="E-mail"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            />
            <input
              type="text"
              placeholder="CPF"
              value={formData.cpf}
              onChange={(e) => setFormData({ ...formData, cpf: e.target.value })}
              className="px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            />
            <input
              type="date"
              placeholder="Data de Nascimento"
              value={formData.data_nascimento}
              onChange={(e) => setFormData({ ...formData, data_nascimento: e.target.value })}
              className="px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            />
            <textarea
              placeholder="Observações"
              value={formData.observacoes}
              onChange={(e) => setFormData({ ...formData, observacoes: e.target.value })}
              className="px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              rows={2}
            />
          </div>
          <div className="flex gap-2 mt-4">
            <button type="submit" className="px-4 py-2 rounded-lg text-white" style={{ backgroundColor: loja.cor_primaria }}>
              {editando ? 'Atualizar' : 'Cadastrar'}
            </button>
            {editando && (
              <button type="button" onClick={() => { setEditando(null); setFormData({ nome: '', telefone: '', email: '', cpf: '', data_nascimento: '', observacoes: '' }); }} className="px-4 py-2 bg-gray-500 text-white rounded-lg">
                Cancelar
              </button>
            )}
          </div>
        </form>

        {/* Lista */}
        {loading ? (
          <p className="text-center text-gray-500">Carregando...</p>
        ) : clientes.length === 0 ? (
          <p className="text-center text-gray-500">Nenhum cliente cadastrado</p>
        ) : (
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {clientes.map((cliente) => (
              <div key={cliente.id} className="flex justify-between items-center p-3 bg-white dark:bg-gray-700 rounded-lg">
                <div>
                  <p className="font-semibold dark:text-white">{cliente.nome}</p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">{cliente.telefone} {cliente.email && `• ${cliente.email}`}</p>
                </div>
                <div className="flex gap-2">
                  <button onClick={() => handleEditar(cliente)} className="px-3 py-1 bg-blue-500 text-white rounded text-sm">Editar</button>
                  <button onClick={() => handleExcluir(cliente.id)} className="px-3 py-1 bg-red-500 text-white rounded text-sm">Excluir</button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </Modal>
  );
}

// Modal de Profissional
function ModalProfissional({ loja, onClose }: { loja: LojaInfo; onClose: () => void }) {
  const toast = useToast();
  const [profissionais, setProfissionais] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [editando, setEditando] = useState<any | null>(null);
  const [formData, setFormData] = useState({ nome: '', telefone: '', email: '', especialidade: '', comissao_percentual: '' });

  useEffect(() => {
    carregarProfissionais();
  }, []);

  const carregarProfissionais = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/cabeleireiro/profissionais/');
      setProfissionais(ensureArray(response.data));
    } catch (error) {
      console.error('Erro ao carregar profissionais:', error);
      toast.error('Erro ao carregar profissionais');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editando) {
        await apiClient.put(`/cabeleireiro/profissionais/${editando.id}/`, formData);
        toast.success('Profissional atualizado!');
      } else {
        await apiClient.post('/cabeleireiro/profissionais/', formData);
        toast.success('Profissional cadastrado!');
      }
      setFormData({ nome: '', telefone: '', email: '', especialidade: '', comissao_percentual: '' });
      setEditando(null);
      carregarProfissionais();
    } catch (error) {
      console.error('Erro ao salvar profissional:', error);
      toast.error('Erro ao salvar profissional');
    }
  };

  const handleEditar = (profissional: any) => {
    setEditando(profissional);
    setFormData({
      nome: profissional.nome || '',
      telefone: profissional.telefone || '',
      email: profissional.email || '',
      especialidade: profissional.especialidade || '',
      comissao_percentual: profissional.comissao_percentual || ''
    });
  };

  const handleExcluir = async (id: number) => {
    if (!confirm('Deseja realmente excluir este profissional?')) return;
    try {
      await apiClient.delete(`/cabeleireiro/profissionais/${id}/`);
      toast.success('Profissional excluído!');
      carregarProfissionais();
    } catch (error) {
      console.error('Erro ao excluir profissional:', error);
      toast.error('Erro ao excluir profissional');
    }
  };

  return (
    <Modal isOpen={true} onClose={onClose} maxWidth="4xl">
      <div className="p-6">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-xl font-bold text-gray-900 dark:text-white">💇 Profissionais</h3>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 p-2 rounded">✕</button>
        </div>

        {/* Formulário */}
        <form onSubmit={handleSubmit} className="mb-6 p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <input
              type="text"
              placeholder="Nome *"
              value={formData.nome}
              onChange={(e) => setFormData({ ...formData, nome: e.target.value })}
              required
              className="px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            />
            <input
              type="tel"
              placeholder="Telefone *"
              value={formData.telefone}
              onChange={(e) => setFormData({ ...formData, telefone: e.target.value })}
              required
              className="px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            />
            <input
              type="email"
              placeholder="E-mail"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            />
            <input
              type="text"
              placeholder="Especialidade"
              value={formData.especialidade}
              onChange={(e) => setFormData({ ...formData, especialidade: e.target.value })}
              className="px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            />
            <input
              type="number"
              placeholder="Comissão (%)"
              value={formData.comissao_percentual}
              onChange={(e) => setFormData({ ...formData, comissao_percentual: e.target.value })}
              step="0.01"
              className="px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            />
          </div>
          <div className="flex gap-2 mt-4">
            <button type="submit" className="px-4 py-2 rounded-lg text-white" style={{ backgroundColor: loja.cor_primaria }}>
              {editando ? 'Atualizar' : 'Cadastrar'}
            </button>
            {editando && (
              <button type="button" onClick={() => { setEditando(null); setFormData({ nome: '', telefone: '', email: '', especialidade: '', comissao_percentual: '' }); }} className="px-4 py-2 bg-gray-500 text-white rounded-lg">
                Cancelar
              </button>
            )}
          </div>
        </form>

        {/* Lista */}
        {loading ? (
          <p className="text-center text-gray-500">Carregando...</p>
        ) : profissionais.length === 0 ? (
          <p className="text-center text-gray-500">Nenhum profissional cadastrado</p>
        ) : (
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {profissionais.map((profissional) => (
              <div key={profissional.id} className="flex justify-between items-center p-3 bg-white dark:bg-gray-700 rounded-lg">
                <div>
                  <p className="font-semibold dark:text-white">{profissional.nome}</p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {profissional.telefone} {profissional.especialidade && `• ${profissional.especialidade}`}
                  </p>
                </div>
                <div className="flex gap-2">
                  <button onClick={() => handleEditar(profissional)} className="px-3 py-1 bg-blue-500 text-white rounded text-sm">Editar</button>
                  <button onClick={() => handleExcluir(profissional.id)} className="px-3 py-1 bg-red-500 text-white rounded text-sm">Excluir</button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </Modal>
  );
}

// Modal de Serviço
function ModalServico({ loja, onClose }: { loja: LojaInfo; onClose: () => void }) {
  const toast = useToast();
  const [servicos, setServicos] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [editando, setEditando] = useState<any | null>(null);
  const [formData, setFormData] = useState({ nome: '', descricao: '', duracao_minutos: '', preco: '' });

  useEffect(() => {
    carregarServicos();
  }, []);

  const carregarServicos = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/cabeleireiro/servicos/');
      setServicos(ensureArray(response.data));
    } catch (error) {
      console.error('Erro ao carregar serviços:', error);
      toast.error('Erro ao carregar serviços');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editando) {
        await apiClient.put(`/cabeleireiro/servicos/${editando.id}/`, formData);
        toast.success('Serviço atualizado!');
      } else {
        await apiClient.post('/cabeleireiro/servicos/', formData);
        toast.success('Serviço cadastrado!');
      }
      setFormData({ nome: '', descricao: '', duracao_minutos: '', preco: '' });
      setEditando(null);
      carregarServicos();
    } catch (error) {
      console.error('Erro ao salvar serviço:', error);
      toast.error('Erro ao salvar serviço');
    }
  };

  const handleEditar = (servico: any) => {
    setEditando(servico);
    setFormData({
      nome: servico.nome || '',
      descricao: servico.descricao || '',
      duracao_minutos: servico.duracao_minutos || '',
      preco: servico.preco || ''
    });
  };

  const handleExcluir = async (id: number) => {
    if (!confirm('Deseja realmente excluir este serviço?')) return;
    try {
      await apiClient.delete(`/cabeleireiro/servicos/${id}/`);
      toast.success('Serviço excluído!');
      carregarServicos();
    } catch (error) {
      console.error('Erro ao excluir serviço:', error);
      toast.error('Erro ao excluir serviço');
    }
  };

  return (
    <Modal isOpen={true} onClose={onClose} maxWidth="4xl">
      <div className="p-6">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-xl font-bold text-gray-900 dark:text-white">✂️ Serviços</h3>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 p-2 rounded">✕</button>
        </div>

        {/* Formulário */}
        <form onSubmit={handleSubmit} className="mb-6 p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <input
              type="text"
              placeholder="Nome do Serviço *"
              value={formData.nome}
              onChange={(e) => setFormData({ ...formData, nome: e.target.value })}
              required
              className="px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            />
            <input
              type="number"
              placeholder="Duração (minutos) *"
              value={formData.duracao_minutos}
              onChange={(e) => setFormData({ ...formData, duracao_minutos: e.target.value })}
              required
              className="px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            />
            <input
              type="number"
              placeholder="Preço (R$) *"
              value={formData.preco}
              onChange={(e) => setFormData({ ...formData, preco: e.target.value })}
              required
              step="0.01"
              className="px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            />
            <textarea
              placeholder="Descrição"
              value={formData.descricao}
              onChange={(e) => setFormData({ ...formData, descricao: e.target.value })}
              className="px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white md:col-span-2"
              rows={2}
            />
          </div>
          <div className="flex gap-2 mt-4">
            <button type="submit" className="px-4 py-2 rounded-lg text-white" style={{ backgroundColor: loja.cor_primaria }}>
              {editando ? 'Atualizar' : 'Cadastrar'}
            </button>
            {editando && (
              <button type="button" onClick={() => { setEditando(null); setFormData({ nome: '', descricao: '', duracao_minutos: '', preco: '' }); }} className="px-4 py-2 bg-gray-500 text-white rounded-lg">
                Cancelar
              </button>
            )}
          </div>
        </form>

        {/* Lista */}
        {loading ? (
          <p className="text-center text-gray-500">Carregando...</p>
        ) : servicos.length === 0 ? (
          <p className="text-center text-gray-500">Nenhum serviço cadastrado</p>
        ) : (
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {servicos.map((servico) => (
              <div key={servico.id} className="flex justify-between items-center p-3 bg-white dark:bg-gray-700 rounded-lg">
                <div>
                  <p className="font-semibold dark:text-white">{servico.nome}</p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {servico.duracao_minutos} min • R$ {parseFloat(servico.preco).toFixed(2)}
                  </p>
                </div>
                <div className="flex gap-2">
                  <button onClick={() => handleEditar(servico)} className="px-3 py-1 bg-blue-500 text-white rounded text-sm">Editar</button>
                  <button onClick={() => handleExcluir(servico.id)} className="px-3 py-1 bg-red-500 text-white rounded text-sm">Excluir</button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </Modal>
  );
}

