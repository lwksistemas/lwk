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
  }, [toast]);

  useEffect(() => {
    if (typeof window !== 'undefined' && loja?.id) {
      sessionStorage.setItem('current_loja_id', String(loja.id));
      if (loja.slug) sessionStorage.setItem('loja_slug', loja.slug);
    }
    loadDashboard();
  }, [loadDashboard, loja?.id, loja?.slug]);

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
