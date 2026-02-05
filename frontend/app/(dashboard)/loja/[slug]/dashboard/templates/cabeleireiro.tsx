'use client';

import { useState, useEffect, lazy, Suspense } from 'react';
import { useRouter } from 'next/navigation';
import { useToast } from '@/components/ui/Toast';
import { ThemeToggle } from '@/components/ui/ThemeProvider';
import { DashboardSkeleton, AgendamentosListSkeleton } from '@/components/ui/Skeleton';
import CalendarioAgendamentos from '@/components/calendario/CalendarioAgendamentos';
import { useDashboardData } from '@/hooks/useDashboardData';
import { useModals } from '@/hooks/useModals';
import { Modal } from '@/components/ui/Modal';
import { LojaInfo } from '@/types/dashboard';
import { ensureArray } from '@/lib/array-helpers';
import apiClient from '@/lib/api-client';
import { ModalProduto, ModalVenda, ModalHorarios, ModalBloqueios } from '@/components/cabeleireiro/modals';

// Lazy loading do modal de configurações
const ConfiguracoesModal = lazy(() => import('@/components/clinica/modals/ConfiguracoesModal').then(m => ({ default: m.ConfiguracoesModal })));

// Componente de loading para modais
function ModalLoadingFallback() {
  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-xl p-8 shadow-2xl">
        <div className="flex items-center gap-3">
          <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          <span className="text-gray-700 dark:text-gray-300">Carregando...</span>
        </div>
      </div>
    </div>
  );
}

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
    'agendamento', 'cliente', 'servico',
    'produto', 'venda', 'funcionarios', 'horarios', 'bloqueios', 'calendario', 'configuracoes'
  ] as const);

  // Estados de navegação
  const [showCalendario, setShowCalendario] = useState(false);

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
  const handleProdutos = () => openModal('produto');
  const handleVendas = () => openModal('venda');
  const handleFuncionarios = () => openModal('funcionarios');
  const handleHorarios = () => openModal('horarios');
  const handleBloqueios = () => openModal('bloqueios');
  const handleCalendario = () => setShowCalendario(true);
  const handleConfiguracoes = () => openModal('configuracoes');
  const handleRelatorios = () => router.push(`/loja/${loja.slug}/relatorios`);

  // Loading inicial
  if (loading) {
    return <DashboardSkeleton />;
  }

  // Calendário
  if (showCalendario) {
    return (
      <div className="px-2 sm:px-0">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-4 sm:mb-6 gap-3">
          <h2 className="text-xl sm:text-2xl font-bold dark:text-white" style={{ color: loja.cor_primaria }}>
            📅 Calendário - Cabeleireiro
          </h2>
          <button
            onClick={() => setShowCalendario(false)}
            className="px-4 sm:px-6 py-2 sm:py-3 min-h-[44px] bg-gray-500 text-white rounded-xl hover:bg-gray-600 transition-all btn-press shadow-lg text-sm sm:text-base"
          >
            ← Voltar ao Dashboard
          </button>
        </div>
        <CalendarioAgendamentos loja={loja} />
      </div>
    );
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
          <ActionButton onClick={handleCalendario} color="#3B82F6" icon="📅" label="Calendário" />
          <ActionButton onClick={handleNovoAgendamento} color="#06B6D4" icon="➕" label="Agendamento" />
          <ActionButton onClick={handleNovoCliente} color="#F59E0B" icon="👤" label="Cliente" />
          <ActionButton onClick={handleServicos} color="#8B5CF6" icon="✂️" label="Serviços" />
          <ActionButton onClick={handleProdutos} color="#10B981" icon="🧴" label="Produtos" />
          <ActionButton onClick={handleVendas} color="#EC4899" icon="💰" label="Vendas" />
          <ActionButton onClick={handleFuncionarios} color="#6366F1" icon="👥" label="Funcionários" />
          <ActionButton onClick={handleHorarios} color="#14B8A6" icon="🕐" label="Horários" />
          <ActionButton onClick={handleBloqueios} color="#EF4444" icon="🚫" label="Bloqueios" />
          <ActionButton onClick={handleConfiguracoes} color="#9333EA" icon="⚙️" label="Configurações" />
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

      {/* Modal de Serviços */}
      {modals.servico && (
        <ModalServico loja={loja} onClose={() => {
          closeModal('servico');
          reload();
        }} />
      )}

      {/* Modais funcionais */}
      {modals.produto && <ModalProduto loja={loja} onClose={() => { closeModal('produto'); reload(); }} />}
      {modals.venda && <ModalVenda loja={loja} onClose={() => { closeModal('venda'); reload(); }} />}
      {modals.horarios && <ModalHorarios loja={loja} onClose={() => { closeModal('horarios'); reload(); }} />}
      {modals.bloqueios && <ModalBloqueios loja={loja} onClose={() => { closeModal('bloqueios'); reload(); }} />}
      
      {/* Modal Configurações */}
      {modals.configuracoes && (
        <Suspense fallback={<ModalLoadingFallback />}>
          <ConfiguracoesModal loja={loja} onClose={() => closeModal('configuracoes')} />
        </Suspense>
      )}
      
      <Modal isOpen={modals.funcionarios} onClose={() => closeModal('funcionarios')} maxWidth="4xl">
        <ModalFuncionarios loja={loja} onClose={() => {
          closeModal('funcionarios');
          reload();
        }} />
      </Modal>
      {modals.horarios && <ModalHorarios loja={loja} onClose={() => { closeModal('horarios'); reload(); }} />}
      {modals.bloqueios && <ModalBloqueios loja={loja} onClose={() => { closeModal('bloqueios'); reload(); }} />}
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

// Modal de Agendamento
function ModalAgendamento({ loja, onClose }: { loja: LojaInfo; onClose: () => void }) {
  const toast = useToast();
  const [agendamentos, setAgendamentos] = useState<any[]>([]);
  const [clientes, setClientes] = useState<any[]>([]);
  const [profissionais, setProfissionais] = useState<any[]>([]);
  const [servicos, setServicos] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editando, setEditando] = useState<any | null>(null);
  const [formData, setFormData] = useState({
    cliente: '',
    profissional: '',
    servico: '',
    data: '',
    horario: '',
    observacoes: '',
    status: 'agendado'
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
      const agendamentosData = ensureArray(agendamentosRes.data);
      setAgendamentos(agendamentosData);
      setClientes(ensureArray(clientesRes.data));
      const profissionaisAtivos = ensureArray(profissionaisRes.data).filter((p: any) => p.is_active !== false);
      setProfissionais(profissionaisAtivos);
      const todosServicos = ensureArray(servicosRes.data);
      const servicosAtivos = todosServicos.filter((s: any) => s.is_active !== false);
      setServicos(servicosAtivos);
      // ✅ Só mostrar formulário na primeira carga se não tem dados
      if (agendamentosData.length === 0 && !showForm) {
        setShowForm(true);
      }
    } catch (error) {
      console.error('Erro ao carregar dados:', error);
      toast.error('Erro ao carregar dados');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      // ✅ Buscar o serviço selecionado para pegar o preço
      const servicoSelecionado = servicos.find(s => s.id === parseInt(formData.servico));
      const valorServico = servicoSelecionado ? Number(servicoSelecionado.preco) : 0;
      
      const dataToSend = {
        cliente: parseInt(formData.cliente),  // ✅ Converter para número
        profissional: parseInt(formData.profissional),  // ✅ Converter para número
        servico: parseInt(formData.servico),  // ✅ Converter para número
        data: formData.data,
        horario: formData.horario,
        observacoes: formData.observacoes,
        status: formData.status,
        valor: valorServico  // ✅ Adicionar valor do serviço
      };
      
      console.log('📤 Enviando agendamento:', dataToSend);
      
      if (editando) {
        await apiClient.put(`/cabeleireiro/agendamentos/${editando.id}/`, dataToSend);
        toast.success('Agendamento atualizado!');
      } else {
        await apiClient.post('/cabeleireiro/agendamentos/', dataToSend);
        toast.success('Agendamento criado!');
      }
      setFormData({ cliente: '', profissional: '', servico: '', data: '', horario: '', observacoes: '', status: 'agendado' });
      setEditando(null);
      setShowForm(false); // ✅ Voltar para lista após salvar
      await carregarDados();
    } catch (error: any) {
      console.error('❌ Erro ao salvar agendamento:', error);
      console.error('❌ Resposta do servidor:', error.response?.data);
      const errorMsg = error.response?.data?.detail 
        || error.response?.data?.error 
        || JSON.stringify(error.response?.data)
        || 'Erro ao salvar agendamento';
      toast.error(errorMsg);
    }
  };

  const handleEditar = (agendamento: any) => {
    setEditando(agendamento);
    setFormData({
      cliente: agendamento.cliente || '',
      profissional: agendamento.profissional || '',
      servico: agendamento.servico || '',
      data: agendamento.data || '',
      horario: agendamento.horario || '',
      observacoes: agendamento.observacoes || '',
      status: agendamento.status || 'agendado'
    });
    setShowForm(true);
  };

  const handleExcluir = async (id: number) => {
    if (!confirm('Deseja realmente excluir este agendamento?')) return;
    try {
      await apiClient.delete(`/cabeleireiro/agendamentos/${id}/`);
      toast.success('Agendamento excluído!');
      carregarDados();
    } catch (error) {
      console.error('Erro ao excluir agendamento:', error);
      toast.error('Erro ao excluir agendamento');
    }
  };

  const handleCancelar = () => {
    setEditando(null);
    setFormData({ cliente: '', profissional: '', servico: '', data: '', horario: '', observacoes: '', status: 'agendado' });
    setShowForm(false);
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      agendado: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
      confirmado: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
      em_atendimento: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300',
      concluido: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
      cancelado: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300'
    };
    return colors[status] || colors.agendado;
  };

  // Se está mostrando formulário
  if (showForm) {
    return (
      <Modal isOpen={true} onClose={onClose} maxWidth="4xl">
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-xl font-bold text-gray-900 dark:text-white">
              {editando ? '✏️ Editar Agendamento' : '➕ Novo Agendamento'}
            </h3>
            <button onClick={onClose} className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 p-2 rounded">✕</button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1 dark:text-white">Cliente *</label>
                <select
                  value={formData.cliente}
                  onChange={(e) => setFormData({ ...formData, cliente: e.target.value })}
                  required
                  className="w-full px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                >
                  <option value="">Selecione um cliente</option>
                  {clientes.map((c) => (
                    <option key={c.id} value={c.id}>{c.nome}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1 dark:text-white">Profissional *</label>
                <select
                  value={formData.profissional}
                  onChange={(e) => setFormData({ ...formData, profissional: e.target.value })}
                  required
                  className="w-full px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                >
                  <option value="">Selecione um profissional</option>
                  {profissionais.map((p) => (
                    <option key={p.id} value={p.id}>{p.nome}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1 dark:text-white">Serviço *</label>
                <select
                  value={formData.servico}
                  onChange={(e) => setFormData({ ...formData, servico: e.target.value })}
                  required
                  className="w-full px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                >
                  <option value="">Selecione um serviço</option>
                  {servicos.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.nome} - R$ {Number(s.preco || 0).toFixed(2)}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1 dark:text-white">Data *</label>
                <input
                  type="date"
                  value={formData.data}
                  onChange={(e) => setFormData({ ...formData, data: e.target.value })}
                  required
                  className="w-full px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1 dark:text-white">Horário *</label>
                <input
                  type="time"
                  value={formData.horario}
                  onChange={(e) => setFormData({ ...formData, horario: e.target.value })}
                  required
                  className="w-full px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1 dark:text-white">Status</label>
                <select
                  value={formData.status}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                  className="w-full px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                >
                  <option value="agendado">Agendado</option>
                  <option value="confirmado">Confirmado</option>
                  <option value="em_atendimento">Em Atendimento</option>
                  <option value="concluido">Concluído</option>
                  <option value="cancelado">Cancelado</option>
                </select>
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium mb-1 dark:text-white">Observações</label>
                <textarea
                  value={formData.observacoes}
                  onChange={(e) => setFormData({ ...formData, observacoes: e.target.value })}
                  className="w-full px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                  rows={2}
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-4 border-t">
              <button type="button" onClick={handleCancelar} className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 dark:text-white">
                Cancelar
              </button>
              <button type="submit" className="px-6 py-2 text-white rounded-lg" style={{ backgroundColor: loja.cor_primaria }}>
                {editando ? 'Atualizar' : 'Criar Agendamento'}
              </button>
            </div>
          </form>
        </div>
      </Modal>
    );
  }

  // Mostrando lista
  return (
    <Modal isOpen={true} onClose={onClose} maxWidth="4xl">
      <div className="p-6">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-xl font-bold text-gray-900 dark:text-white">📅 Agendamentos</h3>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 p-2 rounded">✕</button>
        </div>

        {loading ? (
          <p className="text-center text-gray-500 py-8">Carregando...</p>
        ) : agendamentos.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <p className="text-lg mb-4">Nenhum agendamento cadastrado</p>
            <button 
              onClick={() => setShowForm(true)} 
              className="px-6 py-3 rounded-lg text-white" 
              style={{ backgroundColor: loja.cor_primaria }}
            >
              + Criar Primeiro Agendamento
            </button>
          </div>
        ) : (
          <>
            <div className="space-y-2 mb-6 max-h-96 overflow-y-auto">
              {agendamentos.map((agendamento) => (
                <div key={agendamento.id} className="flex justify-between items-center p-3 bg-white dark:bg-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <p className="font-semibold dark:text-white">{agendamento.cliente_nome}</p>
                      <span className={`text-xs px-2 py-1 rounded-full ${getStatusColor(agendamento.status)}`}>
                        {agendamento.status}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {agendamento.servico_nome} • {agendamento.profissional_nome}
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-500">
                      📅 {agendamento.data} às {agendamento.horario}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <button onClick={() => handleEditar(agendamento)} className="px-3 py-1 bg-blue-500 text-white rounded text-sm hover:bg-blue-600">Editar</button>
                    <button onClick={() => handleExcluir(agendamento.id)} className="px-3 py-1 bg-red-500 text-white rounded text-sm hover:bg-red-600">Excluir</button>
                  </div>
                </div>
              ))}
            </div>

            <div className="flex justify-end gap-2 pt-4 border-t">
              <button onClick={onClose} className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 dark:text-white">
                Fechar
              </button>
              <button 
                onClick={() => setShowForm(true)} 
                className="px-6 py-2 text-white rounded-lg" 
                style={{ backgroundColor: loja.cor_primaria }}
              >
                + Novo Agendamento
              </button>
            </div>
          </>
        )}
      </div>
    </Modal>
  );
}

// Modal de Cliente
function ModalCliente({ loja, onClose }: { loja: LojaInfo; onClose: () => void }) {
  const toast = useToast();
  const [clientes, setClientes] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editando, setEditando] = useState<any | null>(null);
  const [formData, setFormData] = useState({ nome: '', telefone: '', email: '', cpf: '', data_nascimento: '', observacoes: '' });

  useEffect(() => {
    carregarClientes();
  }, []);

  const carregarClientes = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/cabeleireiro/clientes/');
      const data = ensureArray(response.data);
      setClientes(data);
      // ✅ Só mostrar formulário na primeira carga se não tem dados
      if (data.length === 0 && !showForm) {
        setShowForm(true);
      }
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
        toast.success('Cliente atualizado com sucesso!');
      } else {
        await apiClient.post('/cabeleireiro/clientes/', formData);
        toast.success('Cliente cadastrado com sucesso!');
      }
      // Limpar formulário e voltar para lista
      setFormData({ nome: '', telefone: '', email: '', cpf: '', data_nascimento: '', observacoes: '' });
      setEditando(null);
      setShowForm(false); // ✅ Voltar para lista após salvar
      await carregarClientes(); // Recarregar lista
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
    setShowForm(true);
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

  const handleCancelar = () => {
    setEditando(null);
    setFormData({ nome: '', telefone: '', email: '', cpf: '', data_nascimento: '', observacoes: '' });
    setShowForm(false);
  };

  // Se está mostrando formulário
  if (showForm) {
    return (
      <Modal isOpen={true} onClose={onClose} maxWidth="4xl">
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-xl font-bold text-gray-900 dark:text-white">
              {editando ? '✏️ Editar Cliente' : '➕ Novo Cliente'}
            </h3>
            <button onClick={onClose} className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 p-2 rounded">✕</button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
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
            <div className="flex justify-end gap-2 pt-4 border-t">
              <button type="button" onClick={handleCancelar} className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 dark:text-white">
                Cancelar
              </button>
              <button type="submit" className="px-6 py-2 text-white rounded-lg" style={{ backgroundColor: loja.cor_primaria }}>
                {editando ? 'Atualizar' : 'Cadastrar'}
              </button>
            </div>
          </form>
        </div>
      </Modal>
    );
  }

  // Mostrando lista
  return (
    <Modal isOpen={true} onClose={onClose} maxWidth="4xl">
      <div className="p-6">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-xl font-bold text-gray-900 dark:text-white">👤 Clientes</h3>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 p-2 rounded">✕</button>
        </div>

        {loading ? (
          <p className="text-center text-gray-500 py-8">Carregando...</p>
        ) : clientes.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <p className="text-lg mb-4">Nenhum cliente cadastrado</p>
            <button 
              onClick={() => setShowForm(true)} 
              className="px-6 py-3 rounded-lg text-white" 
              style={{ backgroundColor: loja.cor_primaria }}
            >
              + Cadastrar Primeiro Cliente
            </button>
          </div>
        ) : (
          <>
            <div className="space-y-2 mb-6 max-h-96 overflow-y-auto">
              {clientes.map((cliente) => (
                <div key={cliente.id} className="flex justify-between items-center p-3 bg-white dark:bg-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600">
                  <div>
                    <p className="font-semibold dark:text-white">{cliente.nome}</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">{cliente.telefone} {cliente.email && `• ${cliente.email}`}</p>
                  </div>
                  <div className="flex gap-2">
                    <button onClick={() => handleEditar(cliente)} className="px-3 py-1 bg-blue-500 text-white rounded text-sm hover:bg-blue-600">Editar</button>
                    <button onClick={() => handleExcluir(cliente.id)} className="px-3 py-1 bg-red-500 text-white rounded text-sm hover:bg-red-600">Excluir</button>
                  </div>
                </div>
              ))}
            </div>

            <div className="flex justify-end gap-2 pt-4 border-t">
              <button onClick={onClose} className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 dark:text-white">
                Fechar
              </button>
              <button 
                onClick={() => setShowForm(true)} 
                className="px-6 py-2 text-white rounded-lg" 
                style={{ backgroundColor: loja.cor_primaria }}
              >
                + Novo Cliente
              </button>
            </div>
          </>
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
  const [showForm, setShowForm] = useState(false);
  const [editando, setEditando] = useState<any | null>(null);
  const [primeiraVez, setPrimeiraVez] = useState(true);  // ✅ Controlar primeira carga
  const [formData, setFormData] = useState({ 
    nome: '', 
    descricao: '', 
    categoria: 'corte',  // ✅ Adicionar categoria obrigatória
    duracao_minutos: '', 
    preco: '' 
  });

  useEffect(() => {
    carregarServicos();
  }, []);

  const carregarServicos = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/cabeleireiro/servicos/');
      const data = ensureArray(response.data);
      setServicos(data);
      // ✅ Só mostrar formulário se for primeira vez E não tem serviços
      if (primeiraVez && data.length === 0) {
        setShowForm(true);
      }
      setPrimeiraVez(false);  // ✅ Marcar que já carregou
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
      setFormData({ nome: '', descricao: '', categoria: 'corte', duracao_minutos: '', preco: '' });
      setEditando(null);
      setShowForm(false); // ✅ Voltar para lista após salvar
      await carregarServicos();
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
      categoria: servico.categoria || 'corte',  // ✅ Incluir categoria
      duracao_minutos: servico.duracao_minutos || '',
      preco: servico.preco || ''
    });
    setShowForm(true);
  };

  const handleExcluir = async (id: number) => {
    if (!confirm('Deseja realmente excluir este serviço?')) return;
    try {
      await apiClient.delete(`/cabeleireiro/servicos/${id}/`);
      toast.success('Serviço excluído!');
      // ✅ Recarregar mas NÃO mostrar formulário automaticamente
      const response = await apiClient.get('/cabeleireiro/servicos/');
      const data = ensureArray(response.data);
      setServicos(data);
      // NÃO mudar showForm aqui - deixar o usuário decidir
    } catch (error) {
      console.error('Erro ao excluir serviço:', error);
      toast.error('Erro ao excluir serviço');
    }
  };

  const handleCancelar = () => {
    setEditando(null);
    setFormData({ nome: '', descricao: '', categoria: 'corte', duracao_minutos: '', preco: '' });
    setShowForm(false);
  };

  // Se está mostrando formulário
  if (showForm) {
    return (
      <Modal isOpen={true} onClose={onClose} maxWidth="4xl">
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-xl font-bold text-gray-900 dark:text-white">
              {editando ? '✏️ Editar Serviço' : '➕ Novo Serviço'}
            </h3>
            <button onClick={onClose} className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 p-2 rounded">✕</button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <input
                type="text"
                placeholder="Nome do Serviço *"
                value={formData.nome}
                onChange={(e) => setFormData({ ...formData, nome: e.target.value })}
                required
                className="px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              />
              <select
                value={formData.categoria}
                onChange={(e) => setFormData({ ...formData, categoria: e.target.value })}
                required
                className="px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              >
                <option value="corte">Corte</option>
                <option value="coloracao">Coloração</option>
                <option value="tratamento">Tratamento</option>
                <option value="penteado">Penteado</option>
                <option value="manicure">Manicure/Pedicure</option>
                <option value="barba">Barba</option>
                <option value="depilacao">Depilação</option>
                <option value="maquiagem">Maquiagem</option>
                <option value="outros">Outros</option>
              </select>
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
            <div className="flex justify-end gap-2 pt-4 border-t">
              <button type="button" onClick={handleCancelar} className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 dark:text-white">
                Cancelar
              </button>
              <button type="submit" className="px-6 py-2 text-white rounded-lg" style={{ backgroundColor: loja.cor_primaria }}>
                {editando ? 'Atualizar' : 'Cadastrar'}
              </button>
            </div>
          </form>
        </div>
      </Modal>
    );
  }

  // Mostrando lista
  return (
    <Modal isOpen={true} onClose={onClose} maxWidth="4xl">
      <div className="p-6">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-xl font-bold text-gray-900 dark:text-white">✂️ Serviços</h3>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 p-2 rounded">✕</button>
        </div>

        {loading ? (
          <p className="text-center text-gray-500 py-8">Carregando...</p>
        ) : servicos.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <p className="text-lg mb-4">Nenhum serviço cadastrado</p>
            <button 
              onClick={() => setShowForm(true)} 
              className="px-6 py-3 rounded-lg text-white" 
              style={{ backgroundColor: loja.cor_primaria }}
            >
              + Cadastrar Primeiro Serviço
            </button>
          </div>
        ) : (
          <>
            <div className="space-y-2 mb-6 max-h-96 overflow-y-auto">
              {servicos.map((servico) => (
                <div key={servico.id} className="flex justify-between items-center p-3 bg-white dark:bg-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600">
                  <div>
                    <p className="font-semibold dark:text-white">{servico.nome}</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {servico.duracao_minutos} min • R$ {parseFloat(servico.preco).toFixed(2)}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <button onClick={() => handleEditar(servico)} className="px-3 py-1 bg-blue-500 text-white rounded text-sm hover:bg-blue-600">Editar</button>
                    <button onClick={() => handleExcluir(servico.id)} className="px-3 py-1 bg-red-500 text-white rounded text-sm hover:bg-red-600">Excluir</button>
                  </div>
                </div>
              ))}
            </div>

            <div className="flex justify-end gap-2 pt-4 border-t">
              <button onClick={onClose} className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 dark:text-white">
                Fechar
              </button>
              <button 
                onClick={() => setShowForm(true)} 
                className="px-6 py-2 text-white rounded-lg" 
                style={{ backgroundColor: loja.cor_primaria }}
              >
                + Novo Serviço
              </button>
            </div>
          </>
        )}
      </div>
    </Modal>
  );
}

// Funções auxiliares para badges de função
function getFuncaoBadge(funcao: string): string {
  const badges: Record<string, string> = {
    administrador: 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300',
    gerente: 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300',
    atendente: 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300',
    profissional: 'bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-300',
    caixa: 'bg-orange-100 dark:bg-orange-900/30 text-orange-800 dark:text-orange-300',
    estoquista: 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300',
    visualizador: 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
  };
  return badges[funcao] || badges.atendente;
}

function getFuncaoIcon(funcao: string): string {
  const icons: Record<string, string> = {
    administrador: '👤',
    gerente: '👔',
    atendente: '📞',
    profissional: '💇',
    caixa: '💰',
    estoquista: '📦',
    visualizador: '👁️'
  };
  return icons[funcao] || '👤';
}

function getFuncaoLabel(funcao: string): string {
  const labels: Record<string, string> = {
    administrador: 'Administrador',
    gerente: 'Gerente',
    atendente: 'Atendente',
    profissional: 'Profissional',
    caixa: 'Caixa',
    estoquista: 'Estoquista',
    visualizador: 'Visualizador'
  };
  return labels[funcao] || 'Atendente';
}

// Modal de Funcionários
function ModalFuncionarios({ loja, onClose }: { loja: LojaInfo; onClose: () => void }) {
  const toast = useToast();
  const [funcionarios, setFuncionarios] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editando, setEditando] = useState<any | null>(null);
  const [formData, setFormData] = useState({ 
    nome: '', 
    email: '', 
    telefone: '', 
    cargo: '', 
    funcao: 'atendente',
    especialidade: '',
    comissao_percentual: '0.00',
    data_admissao: new Date().toISOString().split('T')[0]
  });

  useEffect(() => {
    carregarFuncionarios();
  }, []);

  const carregarFuncionarios = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/cabeleireiro/funcionarios/');
      const data = ensureArray(response.data);
      setFuncionarios(data);
      // ✅ Só mostrar formulário na primeira carga se não tem dados
      if (data.length === 0 && !showForm) {
        setShowForm(true);
      }
    } catch (error) {
      console.error('Erro ao carregar funcionários:', error);
      toast.error('Erro ao carregar funcionários');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editando) {
        await apiClient.put(`/cabeleireiro/funcionarios/${editando.id}/`, formData);
        toast.success('Funcionário atualizado!');
      } else {
        await apiClient.post('/cabeleireiro/funcionarios/', formData);
        toast.success('Funcionário cadastrado!');
      }
      resetForm();
      await carregarFuncionarios(); // ✅ Aguardar carregar antes de voltar para lista
    } catch (error) {
      console.error('Erro ao salvar funcionário:', error);
      toast.error('Erro ao salvar funcionário');
    }
  };

  const handleEditar = (funcionario: any) => {
    // Proteção: não permitir editar administrador
    if (funcionario.is_admin) {
      alert('⚠️ O administrador da loja não pode ser editado por aqui.\n\nPara alterar dados do administrador, acesse as configurações da loja no painel do SuperAdmin.');
      return;
    }
    
    setEditando(funcionario);
    setFormData({
      nome: funcionario.nome || '',
      email: funcionario.email || '',
      telefone: funcionario.telefone || '',
      cargo: funcionario.cargo || '',
      funcao: funcionario.funcao || 'atendente',
      especialidade: funcionario.especialidade || '',
      comissao_percentual: funcionario.comissao_percentual || '0.00',
      data_admissao: funcionario.data_admissao || new Date().toISOString().split('T')[0]
    });
    setShowForm(true);
  };

  const handleExcluir = async (funcionario: any) => {
    // Proteção: não permitir excluir administrador
    if (funcionario.is_admin) {
      alert('⚠️ O administrador da loja não pode ser excluído.\n\nO administrador é vinculado automaticamente ao criar a loja.');
      return;
    }
    
    if (!confirm(`Deseja realmente excluir o funcionário ${funcionario.nome}?`)) return;
    try {
      await apiClient.delete(`/cabeleireiro/funcionarios/${funcionario.id}/`);
      toast.success('Funcionário excluído!');
      carregarFuncionarios();
    } catch (error) {
      console.error('Erro ao excluir funcionário:', error);
      toast.error('Erro ao excluir funcionário');
    }
  };

  const resetForm = () => {
    setFormData({ 
      nome: '', 
      email: '', 
      telefone: '', 
      cargo: '', 
      funcao: 'atendente',
      especialidade: '',
      comissao_percentual: '0.00',
      data_admissao: new Date().toISOString().split('T')[0]
    });
    setEditando(null);
    setShowForm(false);
  };

  if (showForm) {
    return (
      <div className="p-6">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-xl font-bold text-gray-900 dark:text-white">
            {editando ? '✏️ Editar Funcionário' : '➕ Novo Funcionário'}
          </h3>
          <button onClick={resetForm} className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 p-2 rounded">✕</button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="md:col-span-2">
              <label className="block text-sm font-medium mb-1 dark:text-white">Nome Completo *</label>
              <input
                type="text"
                value={formData.nome}
                onChange={(e) => setFormData({ ...formData, nome: e.target.value })}
                required
                placeholder="Ex: Maria Silva"
                className="w-full px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1 dark:text-white">Email *</label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                required
                placeholder="email@exemplo.com"
                className="w-full px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1 dark:text-white">Telefone *</label>
              <input
                type="tel"
                value={formData.telefone}
                onChange={(e) => setFormData({ ...formData, telefone: e.target.value })}
                required
                placeholder="(00) 00000-0000"
                className="w-full px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1 dark:text-white">Função no Sistema *</label>
              <select
                value={formData.funcao}
                onChange={(e) => setFormData({ ...formData, funcao: e.target.value })}
                required
                className="w-full px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              >
                <option value="administrador">👤 Administrador (Acesso Total)</option>
                <option value="gerente">👔 Gerente</option>
                <option value="atendente">📞 Atendente/Recepcionista</option>
                <option value="profissional">💇 Profissional/Cabeleireiro</option>
                <option value="caixa">💰 Caixa</option>
                <option value="estoquista">📦 Estoquista</option>
                <option value="visualizador">👁️ Visualizador (Apenas Leitura)</option>
              </select>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Define as permissões de acesso ao sistema
              </p>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1 dark:text-white">Cargo (Descritivo) *</label>
              <input
                type="text"
                value={formData.cargo}
                onChange={(e) => setFormData({ ...formData, cargo: e.target.value })}
                required
                placeholder="Ex: Cabeleireiro, Manicure, Recepcionista"
                className="w-full px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Cargo para identificação interna
              </p>
            </div>
            
            {/* Campos condicionais para profissionais */}
            {formData.funcao === 'profissional' && (
              <>
                <div>
                  <label className="block text-sm font-medium mb-1 dark:text-white">Especialidade</label>
                  <input
                    type="text"
                    value={formData.especialidade}
                    onChange={(e) => setFormData({ ...formData, especialidade: e.target.value })}
                    placeholder="Ex: Coloração, Corte Masculino, Penteados"
                    className="w-full px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                  />
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    Especialidade do profissional
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1 dark:text-white">Comissão (%)</label>
                  <input
                    type="number"
                    value={formData.comissao_percentual}
                    onChange={(e) => setFormData({ ...formData, comissao_percentual: e.target.value })}
                    placeholder="0.00"
                    step="0.01"
                    min="0"
                    max="100"
                    className="w-full px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                  />
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    Comissão sobre serviços realizados
                  </p>
                </div>
              </>
            )}
            
            <div>
              <label className="block text-sm font-medium mb-1 dark:text-white">Data de Admissão *</label>
              <input
                type="date"
                value={formData.data_admissao}
                onChange={(e) => setFormData({ ...formData, data_admissao: e.target.value })}
                required
                className="w-full px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              />
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-4 border-t">
            <button type="button" onClick={resetForm} className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 dark:text-white">
              Cancelar
            </button>
            <button type="submit" className="px-6 py-2 text-white rounded-lg" style={{ backgroundColor: loja.cor_primaria }}>
              {editando ? 'Atualizar' : 'Cadastrar'}
            </button>
          </div>
        </form>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-xl font-bold text-gray-900 dark:text-white">👥 Gerenciar Funcionários</h3>
        <button onClick={onClose} className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 p-2 rounded">✕</button>
      </div>

      {loading ? (
        <p className="text-center text-gray-500 py-8">Carregando funcionários...</p>
      ) : funcionarios.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <p className="text-lg mb-2">Nenhum funcionário cadastrado</p>
          <p className="text-sm mb-4">O administrador da loja é automaticamente cadastrado como funcionário</p>
          <button 
            onClick={() => setShowForm(true)} 
            className="px-6 py-3 rounded-lg text-white" 
            style={{ backgroundColor: loja.cor_primaria }}
          >
            + Cadastrar Funcionário
          </button>
        </div>
      ) : (
        <>
          <div className="space-y-3 mb-6 max-h-96 overflow-y-auto">
            {funcionarios.map((func) => (
              <div 
                key={func.id} 
                className={`flex items-center justify-between p-4 border rounded-lg ${
                  func.is_admin 
                    ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800' 
                    : 'bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600'
                }`}
              >
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <p className="font-semibold text-lg dark:text-white">{func.nome}</p>
                    {func.is_admin ? (
                      <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 text-xs font-semibold rounded-full">
                        👤 Administrador
                      </span>
                    ) : (
                      <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getFuncaoBadge(func.funcao)}`}>
                        {getFuncaoIcon(func.funcao)} {getFuncaoLabel(func.funcao)}
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">{func.cargo}</p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">{func.email} • {func.telefone}</p>
                  {func.funcao === 'profissional' && func.especialidade && (
                    <p className="text-xs text-purple-600 dark:text-purple-400 mt-1">
                      ✂️ {func.especialidade} {func.comissao_percentual && `• Comissão: ${func.comissao_percentual}%`}
                    </p>
                  )}
                  {func.is_admin && (
                    <p className="text-xs text-blue-600 dark:text-blue-400 mt-2">
                      ℹ️ Administrador vinculado automaticamente à loja (não pode ser editado ou excluído)
                    </p>
                  )}
                </div>
                <div className="flex gap-2">
                  {func.is_admin ? (
                    <button 
                      disabled
                      className="px-4 py-2 text-sm bg-gray-300 dark:bg-gray-600 text-gray-500 dark:text-gray-400 rounded-lg cursor-not-allowed"
                      title="Administrador não pode ser editado"
                    >
                      🔒 Protegido
                    </button>
                  ) : (
                    <>
                      <button 
                        onClick={() => handleEditar(func)} 
                        className="px-4 py-2 text-sm bg-blue-500 text-white rounded-lg hover:bg-blue-600"
                      >
                        ✏️ Editar
                      </button>
                      <button 
                        onClick={() => handleExcluir(func)} 
                        className="px-4 py-2 text-sm bg-red-500 text-white rounded-lg hover:bg-red-600"
                      >
                        🗑️ Excluir
                      </button>
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>

          <div className="flex justify-end gap-2 pt-4 border-t">
            <button onClick={onClose} className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 dark:text-white">
              Fechar
            </button>
            <button 
              onClick={() => setShowForm(true)} 
              className="px-6 py-2 text-white rounded-lg" 
              style={{ backgroundColor: loja.cor_primaria }}
            >
              + Novo Funcionário
            </button>
          </div>
        </>
      )}
    </div>
  );
}