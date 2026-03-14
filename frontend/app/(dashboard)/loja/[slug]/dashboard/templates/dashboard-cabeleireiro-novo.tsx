"use client";

// v576 - DASHBOARD COM CONTROLE DE ACESSO + MOBILE OTIMIZADO (Simplificado)

import { lazy, Suspense } from 'react';
import { CalendarDays, Scissors, Users, Wallet } from "lucide-react";
import { useRouter } from 'next/navigation';
import { useModals } from '@/hooks/useModals';
import { LojaInfo } from '@/types/dashboard';
import { DashboardHeader, StatCard, AppointmentsTable, ShortcutCard } from '@/components/cabeleireiro/dashboard';
import { ModalLoadingFallback } from '@/components/dashboard';

// Lazy loading dos modais - carrega apenas quando necessário
const ModalAgendamentos = lazy(() => import('@/components/cabeleireiro/modals/ModalAgendamentos').then(m => ({ default: m.ModalAgendamentos })));
const ModalClientes = lazy(() => import('@/components/cabeleireiro/modals/ModalClientes').then(m => ({ default: m.ModalClientes })));
const ModalServicos = lazy(() => import('@/components/cabeleireiro/modals/ModalServicos').then(m => ({ default: m.ModalServicos })));
const ModalFuncionarios = lazy(() => import('@/components/cabeleireiro/modals/ModalFuncionarios').then(m => ({ default: m.ModalFuncionarios })));
import { formatCurrency } from '@/lib/financeiro-helpers';
import { getRolePermissions, canView, UserRole } from '@/lib/roles-cabeleireiro';

interface AgendamentoCabeleireiro {
  id: number;
  cliente_nome: string;
  profissional_nome: string;
  servico_nome: string;
  horario: string;
  status: string;
}

// Dados mockados (serão substituídos quando o backend implementar o endpoint)
const MOCK_STATS = { 
  agendamentos_hoje: 32, 
  agendamentos_mes: 0, 
  clientes_ativos: 245, 
  servicos_ativos: 12, 
  receita_mensal: 3200 
};

const MOCK_APPOINTMENTS = [
  { id: 1, horario: "09:00", cliente_nome: "Mariana Souza", servico_nome: "Corte & Escova", profissional_nome: "Julia", status: "Confirmado" },
  { id: 2, horario: "10:30", cliente_nome: "Carlos Lima", servico_nome: "Coloração", profissional_nome: "Pedro", status: "A Confirmar" },
  { id: 3, horario: "11:15", cliente_nome: "Laura Mendes", servico_nome: "Manicure", profissional_nome: "Fernanda", status: "Agendado" },
  { id: 4, horario: "12:00", cliente_nome: "João Pereira", servico_nome: "Barba", profissional_nome: "Ricardo", status: "Confirmado" },
];

export default function DashboardCabeleireiro({ loja }: { loja: LojaInfo }) {
  const router = useRouter();
  const { modals, openModal, closeModal } = useModals(['agendamento', 'cliente', 'servico', 'funcionarios'] as const);

  // Por enquanto, usar role padrão de administrador e dados mockados
  // TODO: Implementar busca de role do usuário logado via API
  const userRole: UserRole = 'administrador';
  const userInfo = { nome: loja.nome, foto: undefined };
  const permissions = getRolePermissions(userRole);

  // Usar dados mockados até backend implementar endpoint de dashboard
  const loading = false;
  const stats = MOCK_STATS;
  const data = MOCK_APPOINTMENTS;
  const reload = () => {};

  const statsConfig = [
    { 
      title: "Agendamentos", 
      value: stats.agendamentos_hoje.toString(), 
      subtitle: "Hoje", 
      icon: CalendarDays, 
      color: "bg-purple-100 text-purple-600",
      show: permissions.verEstatisticas
    },
    { 
      title: "Clientes", 
      value: stats.clientes_ativos.toString(), 
      subtitle: "Total", 
      icon: Users, 
      color: "bg-indigo-100 text-indigo-600",
      show: canView(userRole, 'clientes')
    },
    { 
      title: "Serviços", 
      value: stats.servicos_ativos.toString(), 
      subtitle: "Ativos", 
      icon: Scissors, 
      color: "bg-pink-100 text-pink-600",
      show: canView(userRole, 'servicos')
    },
    { 
      title: "Faturamento", 
      value: formatCurrency(stats.receita_mensal), 
      subtitle: "Este mês", 
      icon: Wallet, 
      color: "bg-blue-100 text-blue-600",
      show: permissions.verFaturamento
    },
  ].filter(stat => stat.show);

  const shortcuts = [
    { title: "Agenda", icon: CalendarDays, onClick: () => router.push(`/loja/${loja.slug}/cabeleireiro/agenda`), show: canView(userRole, 'agendamentos') },
    { title: "Clientes", icon: Users, onClick: () => openModal('cliente'), show: canView(userRole, 'clientes') },
    { title: "Serviços", icon: Scissors, onClick: () => openModal('servico'), show: canView(userRole, 'servicos') },
    { title: "Profissionais", icon: Users, onClick: () => openModal('funcionarios'), show: canView(userRole, 'funcionarios') },
    { title: "Financeiro", icon: Wallet, onClick: () => router.push(`/loja/${loja.slug}/financeiro`), show: permissions.verFinanceiro },
  ].filter(shortcut => shortcut.show);

  // Filtrar agendamentos se for profissional (apenas seus próprios)
  const filteredAppointments = permissions.verApenasPropriosAgendamentos
    ? data.filter(a => a.profissional_nome === userInfo.nome)
    : data;

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-purple-50 dark:from-gray-900 dark:to-gray-800 p-4 sm:p-6 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-purple-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Carregando dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-purple-50 dark:from-gray-900 dark:to-gray-800 p-4 sm:p-6">
      {/* Header */}
      <DashboardHeader 
        userName={userInfo.nome} 
        userAvatar={userInfo.foto}
        lojaId={loja.id}
        lojaNome={loja.nome}
      />

      {/* Stats Cards - Grid responsivo */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 mb-4 sm:mb-6">
        {statsConfig.map((stat) => (
          <StatCard key={stat.title} {...stat} />
        ))}
      </div>

      {/* Appointments Table - Apenas se tiver permissão */}
      {canView(userRole, 'agendamentos') && (
        <AppointmentsTable 
          appointments={filteredAppointments} 
          onFilterChange={(filter) => console.log('Filter changed:', filter)}
        />
      )}

      {/* Shortcuts - Grid responsivo */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        {shortcuts.map((shortcut) => (
          <ShortcutCard key={shortcut.title} {...shortcut} />
        ))}
      </div>

      {/* Bottom Navigation Mobile */}
      <div className="fixed bottom-0 left-0 right-0 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 p-4 lg:hidden z-50">
        <div className="grid grid-cols-4 gap-2">
          {shortcuts.slice(0, 4).map((shortcut) => (
            <button
              key={shortcut.title}
              onClick={shortcut.onClick}
              className="flex flex-col items-center gap-1 p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            >
              <shortcut.icon className="w-5 h-5 text-purple-600 dark:text-purple-400" />
              <span className="text-xs text-gray-600 dark:text-gray-400">{shortcut.title}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Padding bottom para não sobrepor bottom nav em mobile */}
      <div className="h-20 lg:hidden"></div>

      {/* Modais - lazy loaded */}
      <Suspense fallback={<ModalLoadingFallback />}>
        {modals.agendamento && <ModalAgendamentos loja={loja} onClose={() => { closeModal('agendamento'); reload(); }} />}
        {modals.cliente && <ModalClientes loja={loja} onClose={() => { closeModal('cliente'); reload(); }} />}
        {modals.servico && <ModalServicos loja={loja} onClose={() => { closeModal('servico'); reload(); }} />}
        {modals.funcionarios && <ModalFuncionarios loja={loja} onClose={() => { closeModal('funcionarios'); reload(); }} />}
      </Suspense>
    </div>
  );
}
