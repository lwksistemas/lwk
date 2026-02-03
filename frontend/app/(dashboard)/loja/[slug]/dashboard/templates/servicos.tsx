'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { clinicaApiClient } from '@/lib/api-client';
import { useToast } from '@/components/ui/Toast';
import { ThemeToggle } from '@/components/ui/ThemeProvider';
import { DashboardSkeleton, AgendamentosListSkeleton } from '@/components/ui/Skeleton';
import { 
  ModalAgendamentos, 
  ModalClientes,
  ModalServicos,
  ModalProfissionais,
  ModalOrdensServico,
  ModalOrcamentos,
  ModalFuncionarios
} from './servicos-modals-all';

interface LojaInfo {
  id: number;
  nome: string;
  slug: string;
  tipo_loja_nome: string;
  cor_primaria: string;
  cor_secundaria: string;
  logo?: string;
}

interface EstatisticasServicos {
  agendamentos_hoje: number;
  ordens_abertas: number;
  orcamentos_pendentes: number;
  receita_mensal: number;
}

interface Agendamento {
  id: number;
  cliente_nome: string;
  servico_nome: string;
  profissional_nome: string;
  data: string;
  horario: string;
  status: string;
  valor: number;
}

const STATUS_AGENDAMENTO = [
  { value: 'agendado', label: 'Agendado', color: '#3B82F6' },
  { value: 'confirmado', label: 'Confirmado', color: '#10B981' },
  { value: 'em_andamento', label: 'Em Andamento', color: '#F59E0B' },
  { value: 'concluido', label: 'Concluído', color: '#059669' },
  { value: 'cancelado', label: 'Cancelado', color: '#EF4444' }
];

const STATUS_OS = [
  { value: 'aberta', label: 'Aberta', color: '#3B82F6' },
  { value: 'em_andamento', label: 'Em Andamento', color: '#F59E0B' },
  { value: 'aguardando_peca', label: 'Aguardando Peça', color: '#8B5CF6' },
  { value: 'concluida', label: 'Concluída', color: '#059669' },
  { value: 'cancelada', label: 'Cancelada', color: '#EF4444' }
];

export default function DashboardServicos({ loja }: { loja: LojaInfo }) {
  const router = useRouter();
  const toast = useToast();
  
  // Estados dos modais
  const [showModalAgendamento, setShowModalAgendamento] = useState(false);
  const [showModalCliente, setShowModalCliente] = useState(false);
  const [showModalServico, setShowModalServico] = useState(false);
  const [showModalProfissional, setShowModalProfissional] = useState(false);
  const [showModalOS, setShowModalOS] = useState(false);
  const [showModalOrcamento, setShowModalOrcamento] = useState(false);
  const [showModalFuncionarios, setShowModalFuncionarios] = useState(false);

  // Estados dos dados
  const [estatisticas, setEstatisticas] = useState<EstatisticasServicos>({
    agendamentos_hoje: 0,
    ordens_abertas: 0,
    orcamentos_pendentes: 0,
    receita_mensal: 0
  });
  const [agendamentosHoje, setAgendamentosHoje] = useState<Agendamento[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingAgendamentos, setLoadingAgendamentos] = useState(false);

  const loadDashboard = useCallback(async () => {
    try {
      setLoading(true);
      setLoadingAgendamentos(true);
      
      // Carregar estatísticas e agendamentos de hoje
      const hoje = new Date().toISOString().split('T')[0];
      const [agendamentosRes] = await Promise.all([
        clinicaApiClient.get(`/servicos/agendamentos/?data=${hoje}`)
      ]);

      const agendamentos = Array.isArray(agendamentosRes.data) 
        ? agendamentosRes.data 
        : agendamentosRes.data?.results ?? [];
      
      setAgendamentosHoje(agendamentos);
      
      // Calcular estatísticas básicas
      setEstatisticas({
        agendamentos_hoje: agendamentos.length,
        ordens_abertas: 0, // TODO: implementar endpoint
        orcamentos_pendentes: 0, // TODO: implementar endpoint
        receita_mensal: 0 // TODO: implementar endpoint
      });
    } catch (error) {
      console.error('Erro ao carregar dashboard:', error);
      toast.error('Erro ao carregar dashboard');
      setAgendamentosHoje([]);
    } finally {
      setLoading(false);
      setLoadingAgendamentos(false);
    }
  }, []); // Removido toast das dependências para evitar loop

  useEffect(() => {
    if (typeof window !== 'undefined' && loja?.id) {
      sessionStorage.setItem('current_loja_id', String(loja.id));
      if (loja.slug) sessionStorage.setItem('loja_slug', loja.slug);
      loadDashboard();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Executar apenas uma vez no mount

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
        <ThemeToggle />
      </div>

      {/* Ações Rápidas */}
      <div className="bg-white dark:bg-gray-800 p-4 sm:p-6 rounded-xl shadow-lg card-hover">
        <h3 className="text-base sm:text-lg font-semibold mb-3 sm:mb-4 text-gray-900 dark:text-white" style={{ color: loja.cor_primaria }}>
          🚀 Ações Rápidas
        </h3>
        <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-7 gap-2 sm:gap-3 md:gap-4">
          <ActionButton onClick={() => setShowModalAgendamento(true)} color="#3B82F6" icon="📅" label="Agendamento" />
          <ActionButton onClick={() => setShowModalOS(true)} color="#F59E0B" icon="🔧" label="Ordem Serviço" />
          <ActionButton onClick={() => setShowModalOrcamento(true)} color="#8B5CF6" icon="💰" label="Orçamento" />
          <ActionButton onClick={() => setShowModalCliente(true)} color="#EC4899" icon="👤" label="Clientes" />
          <ActionButton onClick={() => setShowModalServico(true)} color="#06B6D4" icon="⚙️" label="Serviços" />
          <ActionButton onClick={() => setShowModalProfissional(true)} color="#10B981" icon="👨‍🔧" label="Profissionais" />
          <ActionButton onClick={() => setShowModalFuncionarios(true)} color="#6366F1" icon="👥" label="Funcionários" />
        </div>
        <div className="mt-3 sm:mt-4 p-2 sm:p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
          <p className="text-[10px] sm:text-xs text-gray-600 dark:text-gray-400 text-center">
            💡 <strong>Dashboard Serviços</strong> - Gerencie agendamentos, ordens de serviço e orçamentos
          </p>
        </div>
      </div>

      {/* Estatísticas */}
      <div className="grid grid-cols-2 sm:grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4 md:gap-6">
        <StatCard title="Agendamentos Hoje" value={estatisticas.agendamentos_hoje} icon="📅" cor={loja.cor_primaria} />
        <StatCard title="Ordens Abertas" value={estatisticas.ordens_abertas} icon="🔧" cor={loja.cor_primaria} />
        <StatCard title="Orçamentos Pendentes" value={estatisticas.orcamentos_pendentes} icon="💰" cor={loja.cor_primaria} />
        <StatCard title="Receita Mensal" value={`R$ ${Number(estatisticas.receita_mensal).toLocaleString('pt-BR')}`} icon="💵" cor={loja.cor_primaria} />
      </div>

      {/* Agendamentos de Hoje */}
      <div className="bg-white dark:bg-gray-800 p-4 sm:p-6 rounded-xl shadow-lg">
        <div className="flex items-center justify-between mb-3 sm:mb-4">
          <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white">Agendamentos de Hoje</h3>
          <button
            onClick={() => setShowModalAgendamento(true)}
            className="text-xs sm:text-sm px-3 sm:px-4 py-2 min-h-[40px] rounded-lg text-white hover:opacity-90 transition-all btn-press shadow-md"
            style={{ backgroundColor: loja.cor_primaria }}
          >
            + Novo
          </button>
        </div>

        {loadingAgendamentos ? (
          <AgendamentosListSkeleton count={3} />
        ) : agendamentosHoje.length === 0 ? (
          <EmptyState
            message="Nenhum agendamento para hoje"
            subMessage="Comece criando um novo agendamento"
            actionLabel="+ Novo Agendamento"
            onAction={() => setShowModalAgendamento(true)}
            cor={loja.cor_primaria}
            icon="📅"
          />
        ) : (
          <div className="space-y-4">
            {agendamentosHoje.map((agendamento) => (
              <AgendamentoCard key={agendamento.id} agendamento={agendamento} cor={loja.cor_primaria} />
            ))}
          </div>
        )}
      </div>

      {/* Modais */}
      {showModalAgendamento && <ModalAgendamentos loja={loja} onClose={() => setShowModalAgendamento(false)} onSuccess={loadDashboard} />}
      {showModalCliente && <ModalClientes loja={loja} onClose={() => setShowModalCliente(false)} />}
      {showModalServico && <ModalServicos loja={loja} onClose={() => setShowModalServico(false)} />}
      {showModalProfissional && <ModalProfissionais loja={loja} onClose={() => setShowModalProfissional(false)} />}
      {showModalOS && <ModalOrdensServico loja={loja} onClose={() => setShowModalOS(false)} />}
      {showModalOrcamento && <ModalOrcamentos loja={loja} onClose={() => setShowModalOrcamento(false)} />}
      {showModalFuncionarios && <ModalFuncionarios loja={loja} onClose={() => setShowModalFuncionarios(false)} />}
    </div>
  );
}

// Componentes auxiliares
function ActionButton({ onClick, color, icon, label }: { onClick: () => void; color: string; icon: string; label: string }) {
  return (
    <button
      onClick={onClick}
      className="group p-2 sm:p-3 md:p-4 rounded-lg sm:rounded-xl text-white font-semibold transition-all duration-200 transform hover:scale-105 active:scale-95 shadow-md sm:shadow-lg hover:shadow-xl btn-press relative overflow-hidden min-h-[70px] sm:min-h-[80px] md:min-h-[100px]"
      style={{ backgroundColor: color }}
    >
      <div className="absolute inset-0 bg-white/0 group-hover:bg-white/10 transition-colors duration-200" />
      <div className="relative flex flex-col items-center justify-center h-full">
        <div className="text-xl sm:text-2xl md:text-3xl mb-1 sm:mb-2">{icon}</div>
        <div className="text-[10px] sm:text-xs md:text-sm leading-tight text-center">{label}</div>
      </div>
    </button>
  );
}

function StatCard({ title, value, icon, cor }: { title: string; value: string | number; icon: string; cor: string }) {
  return (
    <div className="bg-white dark:bg-gray-800 p-3 sm:p-4 md:p-6 rounded-xl shadow-lg hover:shadow-xl transition-all duration-200 card-hover group">
      <div className="flex items-center justify-between gap-2">
        <div className="min-w-0 flex-1">
          <h3 className="text-gray-500 dark:text-gray-400 text-xs sm:text-sm font-medium truncate">{title}</h3>
          <p className="text-xl sm:text-2xl md:text-3xl font-bold mt-1 sm:mt-2 text-gray-900 dark:text-white truncate" style={{ color: cor }}>
            {value}
          </p>
        </div>
        <div className="w-10 h-10 sm:w-12 sm:h-12 md:w-14 md:h-14 rounded-lg sm:rounded-xl flex items-center justify-center flex-shrink-0" style={{ backgroundColor: `${cor}20` }}>
          <span className="text-xl sm:text-2xl md:text-3xl">{icon}</span>
        </div>
      </div>
    </div>
  );
}

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
          <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400 truncate">{agendamento.servico_nome}</p>
          <p className="text-xs text-gray-500 dark:text-gray-500">{agendamento.horario} • {agendamento.profissional_nome}</p>
        </div>
      </div>
      <div className="flex sm:flex-col items-center sm:items-end gap-2">
        <p className="font-bold text-base sm:text-lg" style={{ color: cor }}>
          R$ {Number(agendamento.valor).toLocaleString('pt-BR')}
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
