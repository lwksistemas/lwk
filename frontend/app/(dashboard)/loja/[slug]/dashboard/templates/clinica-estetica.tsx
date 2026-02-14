'use client';

import { useState, useEffect, lazy, Suspense } from 'react';
import { useRouter } from 'next/navigation';
import { useToast } from '@/components/ui/Toast';
import { DashboardSkeleton, AgendamentosListSkeleton } from '@/components/ui/Skeleton';
import CalendarioAgendamentos from '@/components/calendario/CalendarioAgendamentos';
import GerenciadorConsultas from '@/components/clinica/GerenciadorConsultas';
import { useDashboardData } from '@/hooks/useDashboardData';
import { useModals } from '@/hooks/useModals';
import { LojaInfo, EstatisticasClinica, Agendamento } from '@/types/dashboard';
import { ensureArray } from '@/lib/array-helpers';
import { clinicaApiClient } from '@/lib/api-client';

// Lazy loading dos modais - carrega apenas quando necessário
const ModalClientes = lazy(() => import('@/components/clinica/modals/ModalClientes').then(m => ({ default: m.ModalClientes })));
const ModalProfissionais = lazy(() => import('@/components/clinica/modals/ModalProfissionais').then(m => ({ default: m.ModalProfissionais })));
const ModalProcedimentos = lazy(() => import('@/components/clinica/modals/ModalProcedimentos').then(m => ({ default: m.ModalProcedimentos })));
const ModalProtocolos = lazy(() => import('@/components/clinica/modals/ModalProtocolos').then(m => ({ default: m.ModalProtocolos })));
const ModalAnamnese = lazy(() => import('@/components/clinica/modals/ModalAnamnese').then(m => ({ default: m.ModalAnamnese })));
const ModalFuncionarios = lazy(() => import('@/components/clinica/modals/ModalFuncionarios').then(m => ({ default: m.ModalFuncionarios })));
const ConfiguracoesModal = lazy(() => import('@/components/clinica/modals/ConfiguracoesModal').then(m => ({ default: m.ConfiguracoesModal })));
const ModalConfiguracoes = lazy(() => import('@/components/clinica/modals/ModalConfiguracoes'));
const ModalFinanceiro = lazy(() => import('@/components/clinica/modals/ModalFinanceiro'));

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

export default function DashboardClinicaEstetica({ loja }: { loja: LojaInfo }) {
  const router = useRouter();
  const toast = useToast();

  // Hook para gerenciar modais
  const { modals, openModal, closeModal } = useModals([
    'cliente', 'procedimentos', 'profissional',
    'protocolos', 'anamnese', 'configuracoes', 'funcionarios', 'assinatura', 'financeiro'
  ] as const);

  // Estados de navegação
  const [showCalendario, setShowCalendario] = useState(false);
  const [showConsultas, setShowConsultas] = useState(false);
  const [showListaCompleta, setShowListaCompleta] = useState(false);

  // Hook para carregar dados do dashboard
  const { loading, loadingData, stats, data, reload, error } = useDashboardData<EstatisticasClinica, Agendamento>({
    endpoint: '/clinica/agendamentos/dashboard/',
    initialStats: {
    agendamentos_hoje: 0,
    agendamentos_mes: 0,
    clientes_ativos: 0,
    procedimentos_ativos: 0,
    receita_mensal: 0
    },
    initialData: [],
    transformResponse: (responseData) => {
      return {
        stats: responseData.estatisticas || {
          agendamentos_hoje: 0,
          agendamentos_mes: 0,
          clientes_ativos: 0,
          procedimentos_ativos: 0,
          receita_mensal: 0
        },
        data: ensureArray<Agendamento>(responseData.proximos)
      };
    }
  });

  // Garantir que o backend receba X-Loja-ID (e loja_slug como fallback) antes de qualquer requisição da clínica
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
  const handleNovoAgendamento = () => setShowCalendario(true);
  const handleNovoCliente = () => openModal('cliente');
  const handleProcedimentos = () => openModal('procedimentos');
  const handleNovoProfissional = () => openModal('profissional');
  const handleProtocolos = () => openModal('protocolos');
  const handleAnamnese = () => openModal('anamnese');
  const handleConfiguracoes = () => openModal('configuracoes');
  const handleAssinatura = () => openModal('assinatura');
  const handleFuncionarios = () => openModal('funcionarios');
  const handleCalendario = () => setShowCalendario(true);
  const handleConsultas = () => setShowConsultas(true);
  const handleFinanceiro = () => openModal('financeiro');
  const handleRelatorios = () => router.push(`/loja/${loja.slug}/relatorios`);
  const handleVerTodos = () => setShowListaCompleta(true);

  // Handler para excluir agendamento
  const handleDeleteAgendamento = async (id: number) => {
    try {
      await clinicaApiClient.delete(`/clinica/agendamentos/${id}/`);
      toast.success('Agendamento excluído com sucesso!');
      reload();
    } catch (error) {
      console.error('Erro ao excluir agendamento:', error);
      toast.error('Erro ao excluir agendamento');
    }
  };

  // Handler para alterar status do agendamento
  const handleStatusChange = async (id: number, novoStatus: string) => {
    try {
      await clinicaApiClient.patch(`/clinica/agendamentos/${id}/`, { status: novoStatus });
      toast.success('Status atualizado com sucesso!');
      reload();
    } catch (error) {
      console.error('Erro ao atualizar status:', error);
      toast.error('Erro ao atualizar status');
    }
  };

  // Loading inicial
  if (loading) {
    return <DashboardSkeleton />;
  }

  // Erro ao carregar
  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 p-4">
        <div className="text-center max-w-md">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
            <span className="text-3xl">⚠️</span>
          </div>
          <h2 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white mb-4">
            Erro ao carregar dashboard
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Não foi possível carregar os dados do dashboard. Verifique sua conexão e tente novamente.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <button
              onClick={() => {
                sessionStorage.clear();
                window.location.href = `/loja/${loja.slug}/login`;
              }}
              className="px-6 py-3 min-h-[44px] bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors btn-press"
            >
              Fazer Login Novamente
            </button>
            <button
              onClick={() => window.location.reload()}
              className="px-6 py-3 min-h-[44px] bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors btn-press"
            >
              Recarregar Página
          </button>
        </div>
        </div>
      </div>
    );
  }

  // Calendário - com barra superior integrada
  if (showCalendario) {
    return (
      <div className="fixed inset-0 bg-gray-50 dark:bg-gray-900 flex flex-col">
        {/* Barra Superior Roxa */}
        <nav 
          className="text-white shadow-lg flex-shrink-0"
          style={{ backgroundColor: loja.cor_primaria }}
        >
          <div className="max-w-full px-3 sm:px-4 md:px-6 lg:px-8">
            <div className="flex flex-col sm:flex-row justify-between min-h-[56px] sm:h-16 py-2 sm:py-0 items-start sm:items-center gap-2 sm:gap-0">
              <div className="w-full sm:w-auto">
                <h1 className="text-lg sm:text-xl md:text-2xl font-bold truncate">{loja.nome}</h1>
                <p className="text-xs sm:text-sm opacity-90">{loja.tipo_loja_nome}</p>
              </div>
              <div className="flex items-center gap-2 sm:gap-3 w-full sm:w-auto">
          <button 
                  onClick={() => router.push(`/loja/${loja.slug}/suporte`)}
                  className="flex-1 sm:flex-none px-3 sm:px-4 py-2 min-h-[40px] bg-white bg-opacity-20 hover:bg-opacity-30 rounded-md transition-colors flex items-center justify-center gap-2 text-sm active:scale-95"
                  title="Ver meus chamados de suporte"
                >
                  <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                  </svg>
                  <span>Chamados</span>
          </button>
          <button 
                  onClick={() => {
                    const html = document.documentElement;
                    const isDark = html.classList.contains('dark');
                    if (isDark) {
                      html.classList.remove('dark');
                      localStorage.setItem('theme', 'light');
                    } else {
                      html.classList.add('dark');
                      localStorage.setItem('theme', 'dark');
                    }
                  }}
                  className="flex-1 sm:flex-none px-3 sm:px-4 py-2 min-h-[40px] bg-white bg-opacity-20 hover:bg-opacity-30 rounded-md transition-colors flex items-center justify-center gap-2 text-sm active:scale-95"
                  title="Alternar modo escuro/claro"
                >
                  <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                  </svg>
                  <span className="hidden sm:inline">Tema</span>
          </button>
          <button 
                  onClick={() => setShowCalendario(false)}
                  className="flex-1 sm:flex-none px-3 sm:px-4 py-2 min-h-[40px] bg-white bg-opacity-20 hover:bg-opacity-30 rounded-md transition-colors flex items-center justify-center gap-2 text-sm active:scale-95"
                  title="Voltar ao dashboard"
                >
                  <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                  </svg>
                  <span className="hidden sm:inline">Voltar</span>
          </button>
          <button 
                  onClick={() => {
                    sessionStorage.clear();
                    router.push(`/loja/${loja.slug}/login`);
                  }}
                  className="flex-1 sm:flex-none px-3 sm:px-4 py-2 min-h-[40px] bg-red-600 hover:bg-red-700 rounded-md transition-colors text-sm active:scale-95"
                >
                  Sair
          </button>
        </div>
        </div>
      </div>
        </nav>

        {/* Conteúdo do Calendário - ocupa o resto da tela */}
        <div className="flex-1 overflow-auto px-2 sm:px-4 lg:px-8 py-6">
          <CalendarioAgendamentos loja={loja} />
            </div>
            </div>
    );
  }

  // Consultas
  if (showConsultas) {
    return (
      <GerenciadorConsultas 
        loja={loja} 
        onClose={() => setShowConsultas(false)} 
      />
    );
  }

  // Lista Completa de Agendamentos
  if (showListaCompleta) {
    return (
      <div className="fixed inset-0 bg-white dark:bg-gray-900 z-50 flex flex-col">
        {/* Header */}
        <div className="bg-white dark:bg-gray-800 border-b dark:border-gray-700 px-6 py-4 flex justify-between items-center shadow-sm">
            <div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white" style={{ color: loja.cor_primaria }}>
              📋 Todos os Agendamentos
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mt-1">
              {data.length} agendamento{data.length !== 1 ? 's' : ''} encontrado{data.length !== 1 ? 's' : ''}
              </p>
            </div>
          <button
            onClick={() => setShowListaCompleta(false)}
            className="px-4 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600"
          >
            ✕ Fechar
          </button>
        </div>

        {/* Lista Completa */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="max-w-7xl mx-auto space-y-4">
            {data.map((agendamento) => (
              <AgendamentoCard 
                key={agendamento.id} 
                agendamento={agendamento} 
                cor={loja.cor_primaria}
                onDelete={handleDeleteAgendamento}
                onStatusChange={handleStatusChange}
              />
            ))}
            </div>
            </div>
          </div>
    );
  }

  return (
    <div className="space-y-6 sm:space-y-8 px-2 sm:px-4 lg:px-8">
      {/* Ações Rápidas */}
      <div className="bg-white dark:bg-gray-800 p-4 sm:p-6 rounded-xl shadow-lg card-hover">
        <h3 className="text-base sm:text-lg font-semibold mb-3 sm:mb-4 text-gray-900 dark:text-white" style={{ color: loja.cor_primaria }}>
          🚀 Ações Rápidas
        </h3>
        <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 gap-2 sm:gap-3 md:gap-4">
          <ActionButton onClick={handleCalendario} color="#10B981" icon="🗓️" label="Calendário" />
          <ActionButton onClick={handleConsultas} color="#8B5CF6" icon="🏥" label="Consultas" />
          <ActionButton onClick={handleNovoCliente} color="#F59E0B" icon="👤" label="Cliente" />
          <ActionButton onClick={handleNovoProfissional} color="#EF4444" icon="👨‍⚕️" label="Profissional" />
          <ActionButton onClick={handleProcedimentos} color="#06B6D4" icon="💆" label="Procedimentos" />
          <ActionButton onClick={handleFuncionarios} color="#EC4899" icon="👥" label="Funcionários" />
          <ActionButton onClick={handleProtocolos} color="#8B5A2B" icon="📋" label="Protocolos" />
          <ActionButton onClick={handleAnamnese} color="#7C3AED" icon="📝" label="Anamnese" />
          <ActionButton onClick={handleFinanceiro} color="#10B981" icon="💰" label="Financeiro" />
          <ActionButton onClick={handleAssinatura} color="#F97316" icon="✍️" label="Assinatura" />
          <ActionButton onClick={handleConfiguracoes} color="#6B7280" icon="⚙️" label="Configurações" />
          <ActionButton onClick={handleRelatorios} color="#059669" icon="📈" label="Relatórios" />
        </div>

        <div className="mt-3 sm:mt-4 p-2 sm:p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
          <p className="text-[10px] sm:text-xs text-gray-600 dark:text-gray-400 text-center">
            💡 <strong>Dashboard Clínica de Estética</strong> - Clique nas ações para gerenciar sua clínica
              </p>
            </div>
            </div>

      {/* Estatísticas */}
      <div className="grid grid-cols-2 sm:grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4 md:gap-6">
        <StatCard title="Agendamentos Hoje" value={stats.agendamentos_hoje} icon="📅" cor={loja.cor_primaria} trend="+12%" />
        <StatCard title="Clientes Ativos" value={stats.clientes_ativos} icon="👥" cor={loja.cor_primaria} />
        <StatCard title="Procedimentos" value={stats.procedimentos_ativos} icon="💆" cor={loja.cor_primaria} />
        <StatCard title="Receita Mensal" value={`R$ ${stats.receita_mensal.toLocaleString('pt-BR')}`} icon="💰" cor={loja.cor_primaria} trend="+8%" />
      </div>

      {/* Próximos Agendamentos */}
      <div className="bg-white dark:bg-gray-800 p-4 sm:p-6 rounded-xl shadow-lg">
        <div className="flex items-center justify-between mb-3 sm:mb-4">
          <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white">Próximos Agendamentos</h3>
          <div className="flex gap-2">
          <button
              onClick={handleVerTodos}
              className="text-xs sm:text-sm px-3 sm:px-4 py-2 min-h-[40px] rounded-lg border-2 hover:bg-gray-50 dark:hover:bg-gray-700 transition-all btn-press shadow-md text-gray-700 dark:text-gray-300"
              style={{ borderColor: loja.cor_primaria }}
              title="Ver todos os agendamentos em lista"
            >
              📋 Ver Todos
          </button>
            <button
              onClick={handleNovoAgendamento}
              className="text-xs sm:text-sm px-3 sm:px-4 py-2 min-h-[40px] rounded-lg text-white hover:opacity-90 transition-all btn-press shadow-md"
              style={{ backgroundColor: loja.cor_primaria }}
            >
              + Novo
            </button>
          </div>
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
            {data.slice(0, 10).map((agendamento) => (
              <AgendamentoCard 
                key={agendamento.id}
                agendamento={agendamento} 
                cor={loja.cor_primaria}
                onDelete={handleDeleteAgendamento}
                onStatusChange={handleStatusChange}
              />
            ))}
            {data.length > 10 && (
              <div className="text-center pt-2">
                <button
                  onClick={handleVerTodos}
                  className="text-sm px-6 py-2 rounded-lg border-2 hover:bg-gray-50 dark:hover:bg-gray-700 transition-all text-gray-700 dark:text-gray-300"
                  style={{ borderColor: loja.cor_primaria }}
                >
                  Ver mais {data.length - 10} agendamentos
                </button>
                  </div>
            )}
          </div>
        )}
      </div>

      {/* Modais com Lazy Loading */}
      <Suspense fallback={<ModalLoadingFallback />}>
        {modals.cliente && (
          <ModalClientes 
          loja={loja}
            onClose={() => closeModal('cliente')}
            onSuccess={() => {
              reload();
              toast.success('Cliente salvo com sucesso!');
            }}
          />
        )}

        {modals.profissional && (
          <ModalProfissionais 
          loja={loja}
            onClose={() => closeModal('profissional')}
        />
      )}

        {modals.procedimentos && (
          <ModalProcedimentos 
          loja={loja}
            onClose={() => closeModal('procedimentos')}
            onSuccess={() => {
              reload();
              toast.success('Procedimento salvo com sucesso!');
            }}
          />
        )}

        {modals.protocolos && (
          <ModalProtocolos 
          loja={loja}
            onClose={() => closeModal('protocolos')}
        />
      )}

        {modals.anamnese && (
          <ModalAnamnese 
          loja={loja}
            onClose={() => closeModal('anamnese')}
        />
      )}

        {modals.assinatura && (
          <ConfiguracoesModal 
          loja={loja}
            onClose={() => closeModal('assinatura')}
        />
      )}

        {modals.configuracoes && (
        <ModalConfiguracoes 
          loja={loja}
            onClose={() => closeModal('configuracoes')}
        />
      )}

        {modals.funcionarios && (
        <ModalFuncionarios 
          loja={loja}
            onClose={() => closeModal('funcionarios')}
          />
        )}

        {modals.financeiro && (
          <ModalFinanceiro 
            loja={loja}
            onClose={() => closeModal('financeiro')}
          />
        )}
      </Suspense>
      </div>
    );
  }

// Componente de botão de ação rápida - Modernizado e Responsivo
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
      {/* Efeito de brilho no hover */}
      <div className="absolute inset-0 bg-white/0 group-hover:bg-white/10 transition-colors duration-200" />
      <div className="relative flex flex-col items-center justify-center h-full">
        <div className="text-xl sm:text-2xl md:text-3xl mb-1 sm:mb-2 transform group-hover:scale-110 transition-transform duration-200">{icon}</div>
        <div className="text-[10px] sm:text-xs md:text-sm leading-tight text-center">{label}</div>
          </div>
                    </button>
  );
}

// Componente de card de estatísticas - Modernizado e Responsivo
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

// Componente de card de agendamento - Modernizado e Responsivo
function AgendamentoCard({ agendamento, cor, onDelete, onStatusChange }: { 
  agendamento: Agendamento; 
  cor: string;
  onDelete?: (id: number) => void;
  onStatusChange?: (id: number, novoStatus: string) => void;
}) {
  const [showStatusMenu, setShowStatusMenu] = useState(false);

  const statusConfig: Record<string, { bg: string; text: string; label: string }> = {
    confirmado: { bg: 'bg-green-100 dark:bg-green-900/30', text: 'text-green-800 dark:text-green-300', label: 'Confirmado' },
    agendado: { bg: 'bg-blue-100 dark:bg-blue-900/30', text: 'text-blue-800 dark:text-blue-300', label: 'Agendado' },
    cancelado: { bg: 'bg-red-100 dark:bg-red-900/30', text: 'text-red-800 dark:text-red-300', label: 'Cancelado' },
    concluido: { bg: 'bg-purple-100 dark:bg-purple-900/30', text: 'text-purple-800 dark:text-purple-300', label: 'Concluído' },
    em_atendimento: { bg: 'bg-yellow-100 dark:bg-yellow-900/30', text: 'text-yellow-800 dark:text-yellow-300', label: 'Em Atendimento' },
    faltou: { bg: 'bg-orange-100 dark:bg-orange-900/30', text: 'text-orange-800 dark:text-orange-300', label: 'Faltou' },
  };
  
  const status = statusConfig[agendamento.status] || { bg: 'bg-gray-100 dark:bg-gray-700', text: 'text-gray-800 dark:text-gray-300', label: agendamento.status };

  const handleDelete = () => {
    if (confirm(`Tem certeza que deseja excluir o agendamento de ${agendamento.cliente_nome}?`)) {
      onDelete?.(agendamento.id);
    }
  };

  const handleStatusChange = (novoStatus: string) => {
    onStatusChange?.(agendamento.id, novoStatus);
    setShowStatusMenu(false);
  };

    return (
    <div 
      className="flex flex-col sm:flex-row sm:items-center justify-between p-3 sm:p-4 bg-gray-50 dark:bg-gray-700/50 rounded-xl 
                    hover:bg-gray-100 dark:hover:bg-gray-700 transition-all duration-200 
                    group card-hover gap-3 sm:gap-4 relative"
    >
      <div className="flex items-center space-x-3 sm:space-x-4 flex-1 min-w-0">
        <div 
          className="w-10 h-10 sm:w-12 sm:h-12 rounded-lg sm:rounded-xl flex items-center justify-center text-white font-bold text-base sm:text-lg flex-shrink-0
                     transform group-hover:scale-105 transition-transform duration-200 shadow-md"
          style={{ backgroundColor: cor }}
        >
          {agendamento.cliente_nome.charAt(0)}
                    </div>
        <div className="min-w-0 flex-1">
          <p className="font-semibold text-gray-900 dark:text-white text-sm sm:text-base truncate">{agendamento.cliente_nome}</p>
          <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400 truncate">{agendamento.procedimento_nome}</p>
          <p className="text-[10px] sm:text-xs text-gray-500 dark:text-gray-400 truncate">Prof: {agendamento.profissional_nome}</p>
                    </div>
                  </div>
      
      <div className="flex items-center gap-2 sm:gap-3 flex-wrap">
        <div className="sm:text-right">
          <p className="font-bold text-base sm:text-lg" style={{ color: cor }}>
            {agendamento.horario}
          </p>
          <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">{agendamento.data}</p>
        </div>
        
        {/* Status com menu dropdown - SEMPRE VISÍVEL */}
        <div className="relative">
              <button
            onClick={() => setShowStatusMenu(!showStatusMenu)}
            className={`text-[10px] sm:text-xs px-2 sm:px-3 py-1 rounded-full font-medium whitespace-nowrap ${status.bg} ${status.text} hover:opacity-80 transition-opacity`}
            title="Clique para alterar status"
          >
            {status.label}
              </button>
          
          {showStatusMenu && (
            <div className="absolute right-0 top-full mt-1 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-10 min-w-[140px]">
              {Object.entries(statusConfig).map(([key, config]) => (
            <button
                  key={key}
                  onClick={() => handleStatusChange(key)}
                  className={`w-full text-left px-3 py-2 text-xs hover:bg-gray-100 dark:hover:bg-gray-700 first:rounded-t-lg last:rounded-b-lg ${
                    key === agendamento.status ? 'font-bold' : ''
                  }`}
                >
                  {config.label}
            </button>
            ))}
          </div>
        )}
        </div>

        {/* Botão Excluir - SEMPRE VISÍVEL */}
              <button
          onClick={handleDelete}
          className="p-2 bg-red-500 hover:bg-red-600 text-white rounded-lg transition-colors active:scale-95 flex-shrink-0"
          title="Excluir agendamento"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
              </button>
        </div>
      </div>
    );
  }

// Componente de estado vazio - Responsivo
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
      <p className="text-xs sm:text-sm mb-4 text-gray-500 dark:text-gray-400">{subMessage}</p>
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
