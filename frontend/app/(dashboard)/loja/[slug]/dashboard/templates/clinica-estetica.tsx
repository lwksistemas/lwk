'use client';

import { useState, useEffect, lazy, Suspense } from 'react';
import { useRouter } from 'next/navigation';
import { useToast } from '@/components/ui/Toast';
import { DashboardSkeleton, AgendamentosListSkeleton } from '@/components/ui/Skeleton';
import CalendarioAgendamentos from '@/components/calendario/CalendarioAgendamentos';
import GerenciadorConsultas from '@/components/clinica/GerenciadorConsultas';
import { ModalLoadingFallback, EmptyState, ActionButton, StatCard, AgendamentoCard } from '@/components/dashboard';
import { useDashboardData } from '@/hooks/useDashboardData';
import { useModals } from '@/hooks/useModals';
import { LojaInfo, EstatisticasClinica, Agendamento } from '@/types/dashboard';
import { ensureArray } from '@/lib/array-helpers';
import { formatCurrency } from '@/lib/financeiro-helpers';
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

export default function DashboardClinicaEstetica({ loja, onLogout }: { loja: LojaInfo; onLogout?: () => void }) {
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
              onClick={() => (onLogout ? onLogout() : (sessionStorage.clear(), (window.location.href = `/loja/${loja.slug}/login`)))}
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

  // Calendário - tela cheia, layout tipo app para mobile (Clínica de Estética)
  if (showCalendario) {
    return (
      <div className="fixed inset-0 bg-gray-50 dark:bg-gray-900 flex flex-col min-h-[100dvh] safe-area-inset pt-[env(safe-area-inset-top)] pb-[env(safe-area-inset-bottom)]">
        {/* Barra superior: título à esquerda, ações à direita; no mobile botões compactos (ícone) */}
        <nav
          className="text-white shadow-lg flex-shrink-0 px-[max(0.75rem,env(safe-area-inset-left))]"
          style={{ backgroundColor: loja.cor_primaria }}
        >
          <div className="flex items-center justify-between min-h-[56px] sm:h-14 gap-2">
            <div className="min-w-0 flex-1">
              <h1 className="text-base sm:text-xl font-bold truncate">{loja.nome}</h1>
              <p className="text-xs opacity-90 truncate hidden sm:block">{loja.tipo_loja_nome}</p>
            </div>
            <div className="flex items-center gap-1 sm:gap-2 flex-shrink-0">
              <button
                onClick={() => router.push(`/loja/${loja.slug}/suporte`)}
                className="min-w-[44px] min-h-[44px] flex items-center justify-center rounded-lg bg-white/20 hover:bg-white/30 active:scale-95"
                title="Chamados"
                aria-label="Chamados"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
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
                className="min-w-[44px] min-h-[44px] flex items-center justify-center rounded-lg bg-white/20 hover:bg-white/30 active:scale-95"
                title="Tema"
                aria-label="Alternar tema"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                </svg>
              </button>
              <button
                onClick={() => setShowCalendario(false)}
                className="min-w-[44px] min-h-[44px] flex items-center justify-center rounded-lg bg-white/20 hover:bg-white/30 active:scale-95"
                title="Voltar"
                aria-label="Voltar ao dashboard"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
              </button>
              <button
                onClick={() => (onLogout ? onLogout() : (sessionStorage.clear(), router.push(`/loja/${loja.slug}/login`)))}
                className="min-w-[44px] min-h-[44px] sm:min-w-0 sm:px-3 flex items-center justify-center rounded-lg bg-red-600 hover:bg-red-700 active:scale-95 text-sm font-medium"
              >
                <span className="hidden sm:inline">Sair</span>
                <svg className="w-5 h-5 sm:hidden" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
              </button>
            </div>
          </div>
        </nav>

        {/* Área do calendário: flex-1, scroll suave no mobile */}
        <div className="flex-1 min-h-0 flex flex-col overflow-hidden px-2 sm:px-4 lg:px-8 py-2 sm:py-4">
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
        <StatCard title="Receita Mensal" value={formatCurrency(stats.receita_mensal)} icon="💰" cor={loja.cor_primaria} trend="+8%" />
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
            icon="📅"
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

