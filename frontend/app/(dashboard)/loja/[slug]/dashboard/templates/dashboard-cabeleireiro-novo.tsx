'use client';

// v565 - DASHBOARD COMPLETAMENTE NOVO - ARQUIVO RENOMEADO
// Criado do zero para forçar Vercel a reconhecer

import { useState, useEffect, lazy, Suspense } from 'react';
import { useRouter } from 'next/navigation';
import { useToast } from '@/components/ui/Toast';
import { ThemeToggle } from '@/components/ui/ThemeProvider';
import { DashboardSkeleton, AgendamentosListSkeleton } from '@/components/ui/Skeleton';
import CalendarioCabeleireiro from '@/components/cabeleireiro/CalendarioCabeleireiro';
import { useDashboardData } from '@/hooks/useDashboardData';
import { useModals } from '@/hooks/useModals';
import { LojaInfo } from '@/types/dashboard';
import apiClient from '@/lib/api-client';
import { ModalProduto, ModalVenda, ModalHorarios, ModalBloqueios, ModalClientes, ModalServicos, ModalAgendamentos, ModalFuncionarios } from '@/components/cabeleireiro/modals';
import { 
  UserRole, 
  getRolePermissions, 
  canView, 
  canCreate, 
  canEdit, 
  canDelete,
  getRoleName,
  getRoleIcon,
  getRoleColor,
  filterActionsByRole
} from '@/lib/roles-cabeleireiro';

const ConfiguracoesModal = lazy(() => import('@/components/clinica/modals/ConfiguracoesModal').then(m => ({ default: m.ConfiguracoesModal })));

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

interface ActionButtonConfig {
  onClick: () => void;
  color: string;
  icon: string;
  label: string;
  permission?: keyof import('@/lib/roles-cabeleireiro').RolePermissions;
}

interface StatCardConfig {
  title: string;
  value: string | number;
  icon: string;
  trend?: string;
}

interface StatusConfig {
  bg: string;
  text: string;
  label: string;
}

const STATUS_CONFIG: Record<string, StatusConfig> = {
  confirmado: { bg: 'bg-green-100 dark:bg-green-900/30', text: 'text-green-800 dark:text-green-300', label: 'Confirmado' },
  agendado: { bg: 'bg-blue-100 dark:bg-blue-900/30', text: 'text-blue-800 dark:text-blue-300', label: 'Agendado' },
  cancelado: { bg: 'bg-red-100 dark:bg-red-900/30', text: 'text-red-800 dark:text-red-300', label: 'Cancelado' },
  em_atendimento: { bg: 'bg-yellow-100 dark:bg-yellow-900/30', text: 'text-yellow-800 dark:text-yellow-300', label: 'Em Atendimento' },
  concluido: { bg: 'bg-gray-100 dark:bg-gray-700', text: 'text-gray-800 dark:text-gray-300', label: 'Concluído' },
};

const DEFAULT_STATUS: StatusConfig = { bg: 'bg-gray-100 dark:bg-gray-700', text: 'text-gray-800 dark:text-gray-300', label: 'Desconhecido' };

export default function DashboardCabeleireiro({ loja }: { loja: LojaInfo }) {
  const router = useRouter();
  const toast = useToast();

  useEffect(() => {
    console.log('🚀🚀🚀 DASHBOARD NOVO v565 - ARQUIVO RENOMEADO 🚀🚀🚀');
    console.log('📍 Arquivo: dashboard-cabeleireiro-novo.tsx');
  }, []);

  const [showCalendario, setShowCalendario] = useState(false);
  const [agendamentoIdEditando, setAgendamentoIdEditando] = useState<number | null>(null);
  const [userRole, setUserRole] = useState<UserRole>('administrador');
  const [userName, setUserName] = useState<string>('');

  const { modals, openModal, closeModal } = useModals([
    'agendamento', 'cliente', 'servico',
    'produto', 'venda', 'funcionarios', 'horarios', 'bloqueios', 'calendario', 'configuracoes'
  ] as const);

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
    transformResponse: (responseData) => {
      const stats = responseData?.estatisticas || {
        agendamentos_hoje: 0,
        agendamentos_mes: 0,
        clientes_ativos: 0,
        servicos_ativos: 0,
        receita_mensal: 0
      };
      
      let proximos = responseData?.proximos;
      if (!Array.isArray(proximos)) {
        proximos = [];
      }
      
      return { stats, data: proximos };
    }
  });

  useEffect(() => {
    if (typeof window !== 'undefined' && loja?.id) {
      const current = sessionStorage.getItem('current_loja_id');
      if (current !== String(loja.id)) {
        sessionStorage.setItem('current_loja_id', String(loja.id));
      }
      if (loja.slug) sessionStorage.setItem('loja_slug', loja.slug);
      
      setUserRole('administrador');
      setUserName(loja.nome);
    }
  }, [loja?.id, loja?.slug, loja?.nome]);

  const permissions = getRolePermissions(userRole);

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

  const handleEditarAgendamento = (agendamento: AgendamentoCabeleireiro) => {
    setAgendamentoIdEditando(agendamento.id);
    openModal('agendamento');
  };

  const handleExcluirAgendamento = async (id: number, clienteNome: string) => {
    if (!confirm(`Deseja excluir o agendamento de ${clienteNome}?`)) return;
    
    try {
      await apiClient.delete(`/cabeleireiro/agendamentos/${id}/`);
      toast.success('Agendamento excluído!');
      reload();
    } catch (error) {
      toast.error('Erro ao excluir agendamento');
    }
  };

  const handleMudarStatus = async (id: number, novoStatus: string) => {
    try {
      await apiClient.patch(`/cabeleireiro/agendamentos/${id}/`, { status: novoStatus });
      toast.success('Status atualizado!');
      reload();
    } catch (error) {
      toast.error('Erro ao atualizar status');
    }
  };

  const allActionButtons: ActionButtonConfig[] = [
    { onClick: handleCalendario, color: '#3B82F6', icon: '📅', label: 'Calendário', permission: 'agendamentos' },
    { onClick: handleNovoAgendamento, color: '#06B6D4', icon: '➕', label: 'Agendamento', permission: 'agendamentos' },
    { onClick: handleNovoCliente, color: '#F59E0B', icon: '👤', label: 'Cliente', permission: 'clientes' },
    { onClick: handleServicos, color: '#8B5CF6', icon: '✂️', label: 'Serviços', permission: 'servicos' },
    { onClick: handleProdutos, color: '#10B981', icon: '🧴', label: 'Produtos', permission: 'produtos' },
    { onClick: handleVendas, color: '#EC4899', icon: '💰', label: 'Vendas', permission: 'vendas' },
    { onClick: handleFuncionarios, color: '#6366F1', icon: '👥', label: 'Funcionários', permission: 'funcionarios' },
    { onClick: handleHorarios, color: '#14B8A6', icon: '🕐', label: 'Horários', permission: 'horarios' },
    { onClick: handleBloqueios, color: '#EF4444', icon: '🚫', label: 'Bloqueios', permission: 'bloqueios' },
    { onClick: handleConfiguracoes, color: '#9333EA', icon: '⚙️', label: 'Configurações', permission: 'configuracoes' },
    { onClick: handleRelatorios, color: '#059669', icon: '📊', label: 'Relatórios' },
  ];

  const actionButtons = filterActionsByRole(allActionButtons, userRole);

  const allStatCards: StatCardConfig[] = [
    { title: 'Agendamentos Hoje', value: stats.agendamentos_hoje, icon: '📅', trend: '+15%' },
    { title: 'Clientes Ativos', value: stats.clientes_ativos, icon: '👥' },
    { title: 'Serviços', value: stats.servicos_ativos, icon: '✂️' },
    { title: 'Receita Mensal', value: `R$ ${stats.receita_mensal.toLocaleString('pt-BR')}`, icon: '💰', trend: '+10%' },
  ];

  const statCards = allStatCards.filter(card => {
    if (card.title === 'Receita Mensal') {
      return permissions.verFaturamento;
    }
    return permissions.verEstatisticas;
  });

  if (loading) {
    return <DashboardSkeleton />;
  }

  if (showCalendario) {
    return <CalendarioCabeleireiro loja={loja} onClose={() => setShowCalendario(false)} />;
  }

  return (
    <div className="space-y-6 sm:space-y-8 px-2 sm:px-4 lg:px-8">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">
            Dashboard - {loja.nome}
          </h1>
          {userName && (
            <div className="flex items-center gap-2 mt-2">
              <span className="text-sm text-gray-600 dark:text-gray-400">
                Bem-vindo, <strong>{userName}</strong>
              </span>
              <span 
                className="text-xs px-2 py-1 rounded-full text-white font-medium"
                style={{ backgroundColor: getRoleColor(userRole) }}
              >
                {getRoleIcon(userRole)} {getRoleName(userRole)}
              </span>
            </div>
          )}
        </div>
        <ThemeToggle />
      </div>

      <div className="bg-white dark:bg-gray-800 p-4 sm:p-6 rounded-xl shadow-lg card-hover">
        <h3 className="text-base sm:text-lg font-semibold mb-3 sm:mb-4 text-gray-900 dark:text-white" style={{ color: loja.cor_primaria }}>
          🚀 DASHBOARD NOVO v565 - SISTEMA DE ROLES
        </h3>
        <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 gap-2 sm:gap-3 md:gap-4">
          {actionButtons.map((button, index) => (
            <ActionButton key={index} {...button} />
          ))}
        </div>
        
        <div className="mt-3 sm:mt-4 p-2 sm:p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
          <p className="text-[10px] sm:text-xs text-gray-600 dark:text-gray-400 text-center">
            💡 <strong>Dashboard Cabeleireiro v565</strong> - Gerencie agendamentos, clientes, serviços e profissionais
          </p>
        </div>
      </div>

      {statCards.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4 md:gap-6">
          {statCards.map((card, index) => (
            <StatCard key={index} {...card} cor={loja.cor_primaria} />
          ))}
        </div>
      )}

      {canView(userRole, 'agendamentos') && (
        <div className="bg-white dark:bg-gray-800 p-4 sm:p-6 rounded-xl shadow-lg">
          <div className="flex items-center justify-between mb-3 sm:mb-4">
            <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white">
              {permissions.verApenasPropriosAgendamentos ? 'Minha Agenda' : 'Próximos Agendamentos'}
            </h3>
            {canCreate(userRole, 'agendamentos') && (
              <button
                onClick={handleNovoAgendamento}
                className="text-xs sm:text-sm px-3 sm:px-4 py-2 min-h-[40px] rounded-lg text-white hover:opacity-90 transition-all btn-press shadow-md"
                style={{ backgroundColor: loja.cor_primaria }}
              >
                + Novo
              </button>
            )}
          </div>
          
          {loadingData ? (
            <AgendamentosListSkeleton count={3} />
          ) : !Array.isArray(data) || data.length === 0 ? (
            <EmptyState 
              message={permissions.verApenasPropriosAgendamentos ? "Você não tem agendamentos" : "Nenhum agendamento cadastrado"}
              subMessage={permissions.verApenasPropriosAgendamentos ? "Aguarde novos agendamentos" : "Comece adicionando seu primeiro agendamento"}
              actionLabel="+ Adicionar Primeiro Agendamento"
              onAction={handleNovoAgendamento}
              cor={loja.cor_primaria}
              showAction={canCreate(userRole, 'agendamentos')}
            />
          ) : (
            <div className="space-y-4">
              {data.map((agendamento) => (
                <AgendamentoCard 
                  key={agendamento.id} 
                  agendamento={agendamento} 
                  cor={loja.cor_primaria}
                  onEditar={() => handleEditarAgendamento(agendamento)}
                  onExcluir={() => handleExcluirAgendamento(agendamento.id, agendamento.cliente_nome)}
                  onMudarStatus={(novoStatus) => handleMudarStatus(agendamento.id, novoStatus)}
                  canEdit={canEdit(userRole, 'agendamentos')}
                  canDelete={canDelete(userRole, 'agendamentos')}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {modals.calendario && (
        <ModalAgendamentos loja={loja} onClose={() => {
          closeModal('calendario');
          reload();
        }} />
      )}

      {modals.agendamento && agendamentoIdEditando && (
        <ModalAgendamentos 
          loja={loja} 
          agendamentoId={agendamentoIdEditando}
          onClose={() => {
            closeModal('agendamento');
            setAgendamentoIdEditando(null);
            reload();
          }} 
        />
      )}

      {modals.cliente && (
        <ModalClientes loja={loja} onClose={() => {
          closeModal('cliente');
          reload();
        }} />
      )}

      {modals.servico && (
        <ModalServicos loja={loja} onClose={() => {
          closeModal('servico');
          reload();
        }} />
      )}

      {modals.produto && <ModalProduto loja={loja} onClose={() => { closeModal('produto'); reload(); }} />}
      {modals.venda && <ModalVenda loja={loja} onClose={() => { closeModal('venda'); reload(); }} />}
      {modals.horarios && <ModalHorarios loja={loja} onClose={() => { closeModal('horarios'); reload(); }} />}
      {modals.bloqueios && <ModalBloqueios loja={loja} onClose={() => { closeModal('bloqueios'); reload(); }} />}
      {modals.funcionarios && <ModalFuncionarios loja={loja} onClose={() => { closeModal('funcionarios'); reload(); }} />}
      
      {modals.configuracoes && (
        <Suspense fallback={<ModalLoadingFallback />}>
          <ConfiguracoesModal loja={loja} onClose={() => closeModal('configuracoes')} />
        </Suspense>
      )}
    </div>
  );
}

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

function ActionButton({ onClick, color, icon, label }: ActionButtonConfig) {
  return (
    <button 
      onClick={onClick}
      className="group p-2 sm:p-3 md:p-4 rounded-lg sm:rounded-xl text-white font-semibold 
                 transition-all duration-200 transform hover:scale-105 active:scale-95
                 shadow-md sm:shadow-lg hover:shadow-xl btn-press
                 relative overflow-hidden min-h-[70px] sm:min-h-[80px] md:min-h-[100px]"
      style={{ backgroundColor: color }}
      aria-label={label}
    >
      <div className="absolute inset-0 bg-white/0 group-hover:bg-white/10 transition-colors duration-200" />
      <div className="relative flex flex-col items-center justify-center h-full">
        <div className="text-xl sm:text-2xl md:text-3xl mb-1 sm:mb-2 transform group-hover:scale-110 transition-transform duration-200" aria-hidden="true">
          {icon}
        </div>
        <div className="text-[10px] sm:text-xs md:text-sm leading-tight text-center">{label}</div>
      </div>
    </button>
  );
}

function StatCard({ title, value, icon, cor, trend }: StatCardConfig & { cor: string }) {
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
          aria-hidden="true"
        >
          <span className="text-xl sm:text-2xl md:text-3xl">{icon}</span>
        </div>
      </div>
    </div>
  );
}

function AgendamentoCard({ 
  agendamento, 
  cor,
  onEditar,
  onExcluir,
  onMudarStatus,
  canEdit = true,
  canDelete = true,
}: { 
  agendamento: AgendamentoCabeleireiro; 
  cor: string;
  onEditar: () => void;
  onExcluir: () => void;
  onMudarStatus: (status: string) => void;
  canEdit?: boolean;
  canDelete?: boolean;
}) {
  const [showStatusMenu, setShowStatusMenu] = useState(false);
  
  const status = STATUS_CONFIG[agendamento.status] || DEFAULT_STATUS;

  const handleStatusChange = (novoStatus: string) => {
    setShowStatusMenu(false);
    onMudarStatus(novoStatus);
  };

  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between p-3 sm:p-4 bg-gray-50 dark:bg-gray-700/50 rounded-xl 
                    hover:bg-gray-100 dark:hover:bg-gray-700 transition-all duration-200 
                    group card-hover gap-3 sm:gap-4">
      <div className="flex items-center space-x-3 sm:space-x-4 flex-1 cursor-pointer" onClick={onEditar}>
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
      
      <div className="flex items-center gap-2 sm:gap-3 pl-13 sm:pl-0">
        <div className="sm:text-right">
          <p className="font-bold text-base sm:text-lg" style={{ color: cor }}>
            {agendamento.horario}
          </p>
          <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">{agendamento.data}</p>
        </div>
        
        {canEdit ? (
          <div className="relative">
            <button
              onClick={() => setShowStatusMenu(!showStatusMenu)}
              className={`text-[10px] sm:text-xs px-2 sm:px-3 py-1 rounded-full font-medium whitespace-nowrap ${status.bg} ${status.text} hover:opacity-80 transition-all`}
              aria-label={`Status: ${status.label}`}
            >
              {status.label} ▼
            </button>
            
            {showStatusMenu && (
              <div className="absolute right-0 mt-1 bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 z-10 min-w-[150px]">
                {Object.entries(STATUS_CONFIG).map(([key, config]) => (
                  <button
                    key={key}
                    onClick={() => handleStatusChange(key)}
                    className={`w-full text-left px-3 py-2 text-xs hover:bg-gray-100 dark:hover:bg-gray-700 first:rounded-t-lg last:rounded-b-lg ${config.text}`}
                  >
                    {config.label}
                  </button>
                ))}
              </div>
            )}
          </div>
        ) : (
          <span className={`text-[10px] sm:text-xs px-2 sm:px-3 py-1 rounded-full font-medium whitespace-nowrap ${status.bg} ${status.text}`}>
            {status.label}
          </span>
        )}
        
        {canDelete && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onExcluir();
            }}
            className="p-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-all"
            title="Excluir agendamento"
            aria-label="Excluir agendamento"
          >
            🗑️
          </button>
        )}
      </div>
    </div>
  );
}

function EmptyState({ message, subMessage, actionLabel, onAction, cor, showAction = true }: { 
  message: string; 
  subMessage: string; 
  actionLabel: string; 
  onAction: () => void; 
  cor: string;
  showAction?: boolean;
}) {
  return (
    <div className="text-center py-8 sm:py-12 px-4">
      <div className="w-12 h-12 sm:w-16 sm:h-16 mx-auto mb-3 sm:mb-4 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
        <span className="text-2xl sm:text-3xl" aria-hidden="true">📅</span>
      </div>
      <p className="text-base sm:text-lg mb-1 sm:mb-2 text-gray-700 dark:text-gray-300">{message}</p>
      <p className="text-xs sm:text-sm mb-4 text-gray-500 dark:text-gray-500">{subMessage}</p>
      {showAction && (
        <button
          onClick={onAction}
          className="px-4 sm:px-6 py-2.5 sm:py-3 min-h-[44px] rounded-xl text-white hover:opacity-90 transition-all btn-press shadow-lg text-sm sm:text-base active:scale-95"
          style={{ backgroundColor: cor }}
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
}
