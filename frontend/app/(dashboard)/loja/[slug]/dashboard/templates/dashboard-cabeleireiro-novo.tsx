'use client';

// v567 - DASHBOARD MODERNO - Design Limpo e Profissional

import { useState, useEffect, lazy, Suspense } from 'react';
import { useRouter } from 'next/navigation';
import { useToast } from '@/components/ui/Toast';
import { DashboardSkeleton } from '@/components/ui/Skeleton';
import CalendarioCabeleireiro from '@/components/cabeleireiro/CalendarioCabeleireiro';
import { useDashboardData } from '@/hooks/useDashboardData';
import { useModals } from '@/hooks/useModals';
import { LojaInfo } from '@/types/dashboard';
import apiClient from '@/lib/api-client';
import { ModalClientes, ModalServicos, ModalAgendamentos, ModalFuncionarios } from '@/components/cabeleireiro/modals';
import { UserRole, getRolePermissions, canView, canCreate } from '@/lib/roles-cabeleireiro';

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

const STATUS_CONFIG: Record<string, { bg: string; text: string; label: string }> = {
  confirmado: { bg: 'bg-green-100 dark:bg-green-900/30', text: 'text-green-800 dark:text-green-300', label: 'Confirmado' },
  agendado: { bg: 'bg-blue-100 dark:bg-blue-900/30', text: 'text-blue-800 dark:text-blue-300', label: 'Agendado' },
  cancelado: { bg: 'bg-red-100 dark:bg-red-900/30', text: 'text-red-800 dark:text-red-300', label: 'Cancelado' },
  em_atendimento: { bg: 'bg-yellow-100 dark:bg-yellow-900/30', text: 'text-yellow-800 dark:text-yellow-300', label: 'Em Atendimento' },
  concluido: { bg: 'bg-gray-100 dark:bg-gray-700', text: 'text-gray-800 dark:text-gray-300', label: 'Concluído' },
};

export default function DashboardCabeleireiro({ loja }: { loja: LojaInfo }) {
  const router = useRouter();
  const toast = useToast();

  useEffect(() => {
    console.log('🎨 DASHBOARD MODERNO v567');
  }, []);

  const [agendamentoIdEditando, setAgendamentoIdEditando] = useState<number | null>(null);
  const [userRole] = useState<UserRole>('administrador');

  const { modals, openModal, closeModal } = useModals(['agendamento', 'cliente', 'servico', 'funcionarios', 'configuracoes'] as const);

  const { loading, loadingData, stats, data, reload } = useDashboardData<EstatisticasCabeleireiro, AgendamentoCabeleireiro>({
    endpoint: '/cabeleireiro/agendamentos/dashboard/',
    initialStats: { agendamentos_hoje: 0, agendamentos_mes: 0, clientes_ativos: 0, servicos_ativos: 0, receita_mensal: 0 },
    initialData: [],
    transformResponse: (responseData) => {
      const stats = responseData?.estatisticas || { agendamentos_hoje: 0, agendamentos_mes: 0, clientes_ativos: 0, servicos_ativos: 0, receita_mensal: 0 };
      let proximos = responseData?.proximos;
      if (!Array.isArray(proximos)) proximos = [];
      return { stats, data: proximos };
    }
  });

  useEffect(() => {
    if (typeof window !== 'undefined' && loja?.id) {
      sessionStorage.setItem('current_loja_id', String(loja.id));
      if (loja.slug) sessionStorage.setItem('loja_slug', loja.slug);
    }
  }, [loja?.id, loja?.slug]);

  const permissions = getRolePermissions(userRole);

  const handleNovoAgendamento = () => openModal('agendamento');
  const handleEditarAgendamento = (agendamento: AgendamentoCabeleireiro) => {
    setAgendamentoIdEditando(agendamento.id);
    openModal('agendamento');
  };

  const statsCards = [
    { title: 'Agendamentos Hoje', value: stats.agendamentos_hoje, icon: '📅', color: 'from-blue-500 to-blue-600' },
    { title: 'Clientes Atendidos', value: stats.clientes_ativos, icon: '👥', color: 'from-purple-500 to-purple-600' },
    { title: 'Serviços', value: stats.servicos_ativos, icon: '✂️', color: 'from-pink-500 to-pink-600' },
    { title: 'Faturamento do Mês', value: `R$ ${stats.receita_mensal.toLocaleString('pt-BR')}`, icon: '💰', color: 'from-green-500 to-green-600' },
  ];

  if (loading) return <DashboardSkeleton />;

  return (
    <div className="p-4 sm:p-6 space-y-6 bg-gray-50 dark:bg-gray-900 min-h-screen">
      {/* Header */}
      <div className="animate-fade-in">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white">
          Dashboard • Salão de Cabeleireiro
        </h1>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
          Bem-vindo, {loja.nome}
        </p>
      </div>

      {/* Cards de Estatísticas */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {statsCards.map((stat, i) => (
          <div
            key={i}
            className="animate-slide-up"
            style={{ animationDelay: `${i * 100}ms` }}
          >
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm hover:shadow-md transition-shadow p-4">
              <div className="flex items-center gap-4">
                <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${stat.color} flex items-center justify-center text-2xl`}>
                  {stat.icon}
                </div>
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">{stat.title}</p>
                  <p className="text-2xl font-semibold text-gray-900 dark:text-white">{stat.value}</p>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Próximos Agendamentos */}
      {canView(userRole, 'agendamentos') && (
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            Próximos Agendamentos
          </h2>
          
          {loadingData ? (
            <div className="space-y-3">
              {[1, 2, 3].map(i => (
                <div key={i} className="animate-pulse flex items-center justify-between border rounded-xl p-3">
                  <div className="flex-1">
                    <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/3 mb-2"></div>
                    <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
                  </div>
                  <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-16"></div>
                </div>
              ))}
            </div>
          ) : !Array.isArray(data) || data.length === 0 ? (
            <div className="text-center py-12">
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center text-3xl">
                📅
              </div>
              <p className="text-gray-600 dark:text-gray-400 mb-4">Nenhum agendamento cadastrado</p>
              {canCreate(userRole, 'agendamentos') && (
                <button
                  onClick={handleNovoAgendamento}
                  className="px-6 py-3 bg-gradient-to-r from-purple-600 to-purple-700 text-white rounded-xl hover:from-purple-700 hover:to-purple-800 transition-all shadow-md"
                >
                  + Novo Agendamento
                </button>
              )}
            </div>
          ) : (
            <>
              <div className="space-y-3 mb-4">
                {data.slice(0, 5).map((item) => {
                  const status = STATUS_CONFIG[item.status] || { bg: 'bg-gray-100', text: 'text-gray-800', label: 'Desconhecido' };
                  return (
                    <div
                      key={item.id}
                      onClick={() => handleEditarAgendamento(item)}
                      className="flex items-center justify-between border border-gray-200 dark:border-gray-700 rounded-xl p-3 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors cursor-pointer"
                    >
                      <div className="flex items-center gap-3 flex-1">
                        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center text-white font-bold">
                          {item.cliente_nome.charAt(0)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-gray-900 dark:text-white truncate">{item.cliente_nome}</p>
                          <p className="text-sm text-gray-600 dark:text-gray-400 truncate">{item.servico_nome}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className={`text-xs px-3 py-1 rounded-full font-medium ${status.bg} ${status.text}`}>
                          {status.label}
                        </span>
                        <span className="font-semibold text-gray-900 dark:text-white">{item.horario}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
              {canCreate(userRole, 'agendamentos') && (
                <button
                  onClick={handleNovoAgendamento}
                  className="w-full py-3 bg-gradient-to-r from-purple-600 to-purple-700 text-white rounded-xl hover:from-purple-700 hover:to-purple-800 transition-all shadow-md font-medium"
                >
                  + Novo Agendamento
                </button>
              )}
            </>
          )}
        </div>
      )}

      {/* Botões de Ação */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <button
          onClick={() => openModal('cliente')}
          className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm hover:shadow-md transition-all p-6 text-center group"
        >
          <div className="w-12 h-12 mx-auto mb-3 rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center text-2xl group-hover:scale-110 transition-transform">
            👥
          </div>
          <p className="font-semibold text-gray-900 dark:text-white">Clientes</p>
        </button>
        
        <button
          onClick={() => openModal('servico')}
          className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm hover:shadow-md transition-all p-6 text-center group"
        >
          <div className="w-12 h-12 mx-auto mb-3 rounded-xl bg-gradient-to-br from-pink-500 to-pink-600 flex items-center justify-center text-2xl group-hover:scale-110 transition-transform">
            ✂️
          </div>
          <p className="font-semibold text-gray-900 dark:text-white">Serviços</p>
        </button>
        
        <button
          onClick={() => openModal('funcionarios')}
          className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm hover:shadow-md transition-all p-6 text-center group"
        >
          <div className="w-12 h-12 mx-auto mb-3 rounded-xl bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center text-2xl group-hover:scale-110 transition-transform">
            👨‍💼
          </div>
          <p className="font-semibold text-gray-900 dark:text-white">Profissionais</p>
        </button>
        
        {permissions.verFaturamento && (
          <button
            onClick={() => router.push(`/loja/${loja.slug}/relatorios`)}
            className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm hover:shadow-md transition-all p-6 text-center group"
          >
            <div className="w-12 h-12 mx-auto mb-3 rounded-xl bg-gradient-to-br from-green-500 to-green-600 flex items-center justify-center text-2xl group-hover:scale-110 transition-transform">
              💰
            </div>
            <p className="font-semibold text-gray-900 dark:text-white">Financeiro</p>
          </button>
        )}
      </div>

      {/* Modais */}
      {modals.agendamento && (
        <ModalAgendamentos 
          loja={loja} 
          agendamentoId={agendamentoIdEditando || undefined}
          onClose={() => {
            closeModal('agendamento');
            setAgendamentoIdEditando(null);
            reload();
          }} 
        />
      )}
      {modals.cliente && <ModalClientes loja={loja} onClose={() => { closeModal('cliente'); reload(); }} />}
      {modals.servico && <ModalServicos loja={loja} onClose={() => { closeModal('servico'); reload(); }} />}
      {modals.funcionarios && <ModalFuncionarios loja={loja} onClose={() => { closeModal('funcionarios'); reload(); }} />}
      {modals.configuracoes && (
        <Suspense fallback={<div className="fixed inset-0 bg-black/50 flex items-center justify-center"><div className="bg-white dark:bg-gray-800 rounded-xl p-8"><div className="w-6 h-6 border-2 border-purple-500 border-t-transparent rounded-full animate-spin"></div></div></div>}>
          <ConfiguracoesModal loja={loja} onClose={() => closeModal('configuracoes')} />
        </Suspense>
      )}
    </div>
  );
}
