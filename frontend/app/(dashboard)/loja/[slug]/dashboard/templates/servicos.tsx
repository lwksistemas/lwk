'use client';

import { useEffect, lazy, Suspense } from 'react';
import { useRouter } from 'next/navigation';
import { useDashboardData } from '@/hooks/useDashboardData';
import { useModals } from '@/hooks/useModals';
import { ThemeToggle } from '@/components/ui/ThemeProvider';
import { DashboardSkeleton, AgendamentosListSkeleton } from '@/components/ui/Skeleton';
import { ModalLoadingFallback, ActionButton, StatCard, EmptyState } from '@/components/dashboard';
import { LojaInfo, EstatisticasServicos, Agendamento } from '@/types/dashboard';
import { formatCurrency } from '@/lib/financeiro-helpers';
import { STATUS_AGENDAMENTO } from '@/constants/status';
import BackupButton from '@/components/loja/BackupButton';

// Lazy loading dos modais - carrega apenas quando necessário
const ModalAgendamentos = lazy(() => import('@/components/servicos/modals/ModalAgendamentos').then(m => ({ default: m.ModalAgendamentos })));
const ModalClientes = lazy(() => import('@/components/servicos/modals/ModalClientes').then(m => ({ default: m.ModalClientes })));
const ModalServicos = lazy(() => import('@/components/servicos/modals/ModalServicos').then(m => ({ default: m.ModalServicos })));
const ModalProfissionais = lazy(() => import('@/components/servicos/modals/ModalProfissionais').then(m => ({ default: m.ModalProfissionais })));
const ModalOrdensServico = lazy(() => import('@/components/servicos/modals/ModalOrdensServico').then(m => ({ default: m.ModalOrdensServico })));
const ModalOrcamentos = lazy(() => import('@/components/servicos/modals/ModalOrcamentos').then(m => ({ default: m.ModalOrcamentos })));
const ModalFuncionarios = lazy(() => import('@/components/servicos/modals/ModalFuncionarios').then(m => ({ default: m.ModalFuncionarios })));

export default function DashboardServicos({ loja }: { loja: LojaInfo }) {
  const router = useRouter();
  
  // Hook para gerenciar modais
  const { modals, openModal, closeModal } = useModals([
    'agendamento', 'cliente', 'servico', 'profissional', 
    'os', 'orcamento', 'funcionarios'
  ] as const);

  // Hook para carregar dados do dashboard
  const { loading, loadingData, stats, data, reload } = useDashboardData<EstatisticasServicos, Agendamento>({
    endpoint: `/servicos/agendamentos/?data=${new Date().toISOString().split('T')[0]}`,
    initialStats: {
      agendamentos_hoje: 0,
      ordens_abertas: 0,
      orcamentos_pendentes: 0,
      receita_mensal: 0
    },
    initialData: [],
    transformResponse: (responseData) => {
      const agendamentos = Array.isArray(responseData) 
        ? responseData 
        : responseData?.results ?? [];
      
      return {
        stats: {
          agendamentos_hoje: agendamentos.length,
          ordens_abertas: 0,
          orcamentos_pendentes: 0,
          receita_mensal: 0
        },
        data: agendamentos
      };
    }
  });

  useEffect(() => {
    if (typeof window !== 'undefined' && loja?.id) {
      sessionStorage.setItem('current_loja_id', String(loja.id));
      if (loja.slug) sessionStorage.setItem('loja_slug', loja.slug);
    }
  }, [loja?.id, loja?.slug]);

  if (loading) {
    return <DashboardSkeleton />;
  }

  return (
    <div className="space-y-6 sm:space-y-8 px-2 sm:px-4 lg:px-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
        <h1 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">
          Dashboard - {loja.nome}
        </h1>
        <div className="flex items-center gap-2">
          <BackupButton lojaId={loja.id} lojaNome={loja.nome} />
          <ThemeToggle />
        </div>
      </div>

      {/* Ações Rápidas */}
      <div className="bg-white dark:bg-gray-800 p-4 sm:p-6 rounded-xl shadow-lg card-hover">
        <h3 className="text-base sm:text-lg font-semibold mb-3 sm:mb-4 text-gray-900 dark:text-white" style={{ color: loja.cor_primaria }}>
          🚀 Ações Rápidas
        </h3>
        <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-7 gap-2 sm:gap-3 md:gap-4">
          <ActionButton onClick={() => openModal('agendamento')} color="#3B82F6" icon="📅" label="Agendamento" />
          <ActionButton onClick={() => openModal('os')} color="#F59E0B" icon="🔧" label="Ordem Serviço" />
          <ActionButton onClick={() => openModal('orcamento')} color="#8B5CF6" icon="💰" label="Orçamento" />
          <ActionButton onClick={() => openModal('cliente')} color="#EC4899" icon="👤" label="Clientes" />
          <ActionButton onClick={() => openModal('servico')} color="#06B6D4" icon="⚙️" label="Serviços" />
          <ActionButton onClick={() => openModal('profissional')} color="#10B981" icon="👨‍🔧" label="Profissionais" />
          <ActionButton onClick={() => openModal('funcionarios')} color="#6366F1" icon="👥" label="Funcionários" />
        </div>
        <div className="mt-3 sm:mt-4 p-2 sm:p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
          <p className="text-[10px] sm:text-xs text-gray-600 dark:text-gray-400 text-center">
            💡 <strong>Dashboard Serviços</strong> - Gerencie agendamentos, ordens de serviço e orçamentos
          </p>
        </div>
      </div>

      {/* Estatísticas */}
      <div className="grid grid-cols-2 sm:grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4 md:gap-6">
        <StatCard title="Agendamentos Hoje" value={stats.agendamentos_hoje} icon="📅" cor={loja.cor_primaria} />
        <StatCard title="Ordens Abertas" value={stats.ordens_abertas} icon="🔧" cor={loja.cor_primaria} />
        <StatCard title="Orçamentos Pendentes" value={stats.orcamentos_pendentes} icon="💰" cor={loja.cor_primaria} />
        <StatCard title="Receita Mensal" value={formatCurrency(stats.receita_mensal)} icon="💵" cor={loja.cor_primaria} />
      </div>

      {/* Agendamentos de Hoje */}
      <div className="bg-white dark:bg-gray-800 p-4 sm:p-6 rounded-xl shadow-lg">
        <div className="flex items-center justify-between mb-3 sm:mb-4">
          <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white">Agendamentos de Hoje</h3>
          <button
            onClick={() => openModal('agendamento')}
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
            message="Nenhum agendamento para hoje"
            subMessage="Comece criando um novo agendamento"
            actionLabel="+ Novo Agendamento"
            onAction={() => openModal('agendamento')}
            cor={loja.cor_primaria}
            icon="📅"
          />
        ) : (
          <div className="space-y-4">
            {data.map((agendamento) => (
              <AgendamentoCard key={agendamento.id} agendamento={agendamento} cor={loja.cor_primaria} />
            ))}
          </div>
        )}
      </div>

      {/* Modais - lazy loaded */}
      <Suspense fallback={<ModalLoadingFallback />}>
        {modals.agendamento && <ModalAgendamentos loja={loja} onClose={() => closeModal('agendamento')} onSuccess={reload} />}
        {modals.cliente && <ModalClientes loja={loja} onClose={() => closeModal('cliente')} />}
        {modals.servico && <ModalServicos loja={loja} onClose={() => closeModal('servico')} />}
        {modals.profissional && <ModalProfissionais loja={loja} onClose={() => closeModal('profissional')} />}
        {modals.os && <ModalOrdensServico loja={loja} onClose={() => closeModal('os')} />}
        {modals.orcamento && <ModalOrcamentos loja={loja} onClose={() => closeModal('orcamento')} />}
        {modals.funcionarios && <ModalFuncionarios loja={loja} onClose={() => closeModal('funcionarios')} />}
      </Suspense>
    </div>
  );
}

// Card de agendamento específico para Serviços (layout com valor e status)
function AgendamentoCard({ agendamento, cor }: { agendamento: Agendamento; cor: string }) {
  const statusInfo = STATUS_AGENDAMENTO.find(s => s.value === agendamento.status);
  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between p-3 sm:p-4 bg-gray-50 dark:bg-gray-700/50 rounded-xl hover:bg-gray-100 dark:hover:bg-gray-700 transition-all gap-3 sm:gap-4 card-hover">
      <div className="flex items-center space-x-3 sm:space-x-4">
        <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-lg sm:rounded-xl flex items-center justify-center text-white font-bold flex-shrink-0 shadow-md" style={{ backgroundColor: cor }}>
          {agendamento.cliente_nome.charAt(0)}
        </div>
        <div className="min-w-0 flex-1">
          <p className="font-semibold text-gray-900 dark:text-white text-sm sm:text-base truncate">{agendamento.cliente_nome}</p>
          <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400 truncate">{agendamento.servico_nome || agendamento.procedimento_nome}</p>
          <p className="text-xs text-gray-500 dark:text-gray-400">{agendamento.horario} • {agendamento.profissional_nome}</p>
        </div>
      </div>
      <div className="flex sm:flex-col items-center sm:items-end gap-2">
        <p className="font-bold text-base sm:text-lg" style={{ color: cor }}>
          {formatCurrency(agendamento.valor ?? 0)}
        </p>
        <span className="text-xs px-2 py-1 rounded-full" style={{ backgroundColor: `${statusInfo?.color}20`, color: statusInfo?.color }}>
          {statusInfo?.label}
        </span>
      </div>
    </div>
  );
}

function EmptyState({ message, subMessage, actionLabel, onAction, cor, icon = '📋' }: {
  message: string;
  subMessage: string;
  actionLabel: string;
  onAction: () => void;
  cor: string;
  icon?: string;
}) {
  return (
    <div className="text-center py-8 sm:py-12 px-4">
      <div className="w-12 h-12 sm:w-16 sm:h-16 mx-auto mb-3 sm:mb-4 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
        <span className="text-2xl sm:text-3xl">{icon}</span>
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
