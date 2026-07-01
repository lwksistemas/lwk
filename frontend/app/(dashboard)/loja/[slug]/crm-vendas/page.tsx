'use client';

import { useEffect, useState, useRef, useMemo, useCallback } from 'react';
import dynamic from 'next/dynamic';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import apiClient from '@/lib/api-client';
import StatCard from '@/components/crm-vendas/StatCard';
import SkeletonDashboard from '@/components/crm-vendas/SkeletonDashboard';
import FunilVendas from '@/components/crm-vendas/FunilVendas';

const SalesChart = dynamic(() => import('@/components/crm-vendas/SalesChart'), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center min-h-[320px] bg-blue-50/40 dark:bg-blue-900/10 rounded-2xl border-2 border-blue-200 dark:border-blue-800 animate-pulse">
      <span className="text-sm text-gray-500">Carregando gráfico...</span>
    </div>
  ),
});
import {
  Wallet,
  Users,
  Percent,
  Calendar,
  Phone,
  FileText,
  Flag,
  ChevronRight,
  DollarSign,
  TrendingDown,
} from 'lucide-react';
import { useCRMConfig } from '@/contexts/CRMConfigContext';
import { authService } from '@/lib/auth';
import { normalizeListResponse } from '@/lib/crm-utils';

function toISO(date: Date): string {
  return date.toISOString().slice(0, 19) + 'Z';
}

interface DashboardData {
  leads: number;
  oportunidades: number;
  receita: number;
  pipeline_aberto: number;
  oportunidades_em_andamento: number;
  valor_perdido?: number;
  taxa_conversao: number;
  pipeline_por_etapa: { etapa: string; valor: number; quantidade: number }[];
  atividades_hoje: unknown[];
  performance_vendedores: { id: number | null; nome: string; receita_mes: number; comissao_mes: number }[];
  comissao_total_mes: number;
}

const PERIODO_CARD_LABELS: Record<string, { receita: string; comissao: string; leads: string; comissaoSub: string }> = {
  mes_atual: {
    receita: 'Receita do mês',
    comissao: 'Comissão do mês',
    leads: 'Novos leads',
    comissaoSub: 'Vendas ganhas neste mês',
  },
  mes_passado: {
    receita: 'Receita do mês passado',
    comissao: 'Comissão do mês passado',
    leads: 'Novos leads',
    comissaoSub: 'Vendas ganhas no mês passado',
  },
  trimestre_atual: {
    receita: 'Receita do trimestre',
    comissao: 'Comissão do trimestre',
    leads: 'Novos leads no trimestre',
    comissaoSub: 'Vendas ganhas no trimestre (últimos 3 meses)',
  },
  ano_atual: {
    receita: 'Receita do ano',
    comissao: 'Comissão do ano',
    leads: 'Novos leads no ano',
    comissaoSub: 'Vendas ganhas neste ano',
  },
};

const PERIODO_NOME: Record<string, string> = {
  mes_atual: 'Este mês',
  mes_passado: 'Mês passado',
  trimestre_atual: 'Este trimestre',
  ano_atual: 'Este ano',
};

function labelsPeriodo(periodo: string) {
  return PERIODO_CARD_LABELS[periodo] ?? PERIODO_CARD_LABELS.mes_atual;
}

function formatMoney(value: number): string {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

const ETAPAS_LABEL: Record<string, string> = {
  prospecting: 'Prospecção',
  qualification: 'Qualificação',
  proposal: 'Proposta',
  negotiation: 'Negociação',
  closed_won: 'Fechado (ganho)',
  closed_lost: 'Fechado (perdido)',
};

const TIPO_LABEL_DASHBOARD: Record<string, string> = {
  call: 'Ligação',
  meeting: 'Reunião',
  email: 'E-mail',
  task: 'Tarefa',
};

function iconPorTipo(tipo: string) {
  const t = (tipo || '').toLowerCase();
  if (t.includes('reunião') || t.includes('reuniao')) return Calendar;
  if (t.includes('ligar') || t.includes('call')) return Phone;
  if (t.includes('proposta') || t.includes('enviar')) return FileText;
  return Flag;
}

export default function CrmVendasDashboardPage() {
  const params = useParams();
  const slug = (params?.slug as string) ?? '';
  const { etapasAtivas } = useCRMConfig();
  const isVendedor = authService.isVendedor();
  const [data, setData] = useState<DashboardData | null>(null);
  const [proximasAtividades, setProximasAtividades] = useState<
    { id: number; titulo: string; tipo: string; data: string; lead_nome?: string; concluido?: boolean }[]
  >([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showFiltro, setShowFiltro] = useState(false);
  const [periodoFiltro, setPeriodoFiltro] = useState('mes_atual');
  const filtroRef = useRef<HTMLDivElement>(null);

  const pipelineMap = useMemo(() => 
    new Map(
      (data?.pipeline_por_etapa || []).map((p) => [p.etapa, { valor: p.valor, quantidade: p.quantidade }])
    )
  , [data?.pipeline_por_etapa]);

  // Apenas etapas ativas na configuração (respeita desmarcar em Personalizar)
  const etapasComValor = useMemo(() => 
    etapasAtivas().map((e) => ({
      key: e.key,
      label: e.label,
      ...(pipelineMap.get(e.key) || { valor: 0, quantidade: 0 }),
    }))
  , [etapasAtivas, pipelineMap]);

  const chartData = useMemo(() => 
    etapasComValor.map((p) => ({
      name: p.label,
      valor: p.valor,
      quantidade: p.quantidade,
    }))
  , [etapasComValor]);

  // useCallback para event handlers
  const handleClickOutside = useCallback((e: MouseEvent) => {
    if (filtroRef.current && !filtroRef.current.contains(e.target as Node)) {
      setShowFiltro(false);
    }
  }, []);

  const toggleFiltro = useCallback(() => {
    setShowFiltro((v) => !v);
  }, []);

  const selecionarPeriodo = useCallback((periodo: string) => {
    setPeriodoFiltro(periodo);
    setShowFiltro(false);
  }, []);

  useEffect(() => {
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [handleClickOutside]);

  useEffect(() => {
    setLoading(true);
    const inicio = new Date();
    inicio.setHours(0, 0, 0, 0);
    const fim = new Date(inicio);
    fim.setDate(fim.getDate() + 60);

    Promise.allSettled([
      apiClient.get<DashboardData>(`/crm-vendas/dashboard/?periodo=${periodoFiltro}`),
      apiClient.get('/crm-vendas/atividades/', {
        params: {
          data_inicio: toISO(inicio),
          data_fim: toISO(fim),
          concluido: 'false',
          page_size: 10,
        },
      }),
    ])
      .then(([dashResult, ativResult]) => {
        if (dashResult.status === 'rejected') {
          const err = dashResult.reason as { response?: { data?: { detail?: string } } };
          throw new Error(err.response?.data?.detail || 'Erro ao carregar dashboard.');
        }
        setData(dashResult.value.data);
        if (ativResult.status === 'fulfilled') {
          const list = normalizeListResponse<{
            id: number;
            titulo: string;
            tipo: string;
            data: string;
            concluido?: boolean;
          }>(ativResult.value.data);
          list.sort((a, b) => new Date(a.data).getTime() - new Date(b.data).getTime());
          setProximasAtividades(list.slice(0, 5));
        } else {
          setProximasAtividades([]);
        }
      })
      .catch((err: Error) => {
        setError(err.message || 'Erro ao carregar dashboard.');
        setProximasAtividades([]);
      })
      .finally(() => setLoading(false));
  }, [periodoFiltro]);

  if (loading) {
    return <SkeletonDashboard />;
  }

  if (error) {
    return (
      <div className="rounded-xl bg-red-50 dark:bg-red-900/20 p-4 text-red-700 dark:text-red-300">
        {error}
      </div>
    );
  }

  if (!data) return null;

  const periodoLabels = labelsPeriodo(periodoFiltro);

  return (
    <div className="space-y-5">
      {/* Page Header - Estilo Salesforce */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <Link
            href={`/loja/${slug}/crm-vendas`}
            className="text-2xl font-bold text-gray-900 dark:text-white hover:text-[#0176d3] dark:hover:text-[#0d9dda] transition-colors"
          >
            Home
          </Link>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Visão geral do seu pipeline de vendas
            <span className="ml-2 text-xs font-medium text-[#0176d3]">
              · {PERIODO_NOME[periodoFiltro] ?? 'Este mês'}
            </span>
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="relative" ref={filtroRef}>
            <button
              type="button"
              onClick={toggleFiltro}
              className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-[#16325c] border border-gray-300 dark:border-[#0d1f3c] rounded hover:bg-gray-50 dark:hover:bg-[#0d1f3c] transition-colors"
            >
              {PERIODO_NOME[periodoFiltro] ?? 'Filtrar'} ▾
            </button>
            {showFiltro && (
              <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-[#16325c] rounded-lg shadow-lg border border-gray-200 dark:border-[#0d1f3c] py-1 z-20">
                <div className="px-4 py-2 text-xs text-gray-500 dark:text-gray-400 border-b border-gray-100 dark:border-[#0d1f3c]">
                  Período
                </div>
                {[
                  { key: 'mes_atual', label: 'Este mês' },
                  { key: 'mes_passado', label: 'Mês passado' },
                  { key: 'trimestre_atual', label: 'Este trimestre' },
                  { key: 'ano_atual', label: 'Este ano' },
                ].map((p) => (
                  <button
                    key={p.key}
                    type="button"
                    className={`w-full text-left px-4 py-2 text-sm hover:bg-gray-50 dark:hover:bg-[#0d1f3c] ${periodoFiltro === p.key ? 'text-[#0176d3] font-semibold' : 'text-gray-700 dark:text-gray-200'}`}
                    onClick={() => selecionarPeriodo(p.key)}
                  >
                    {p.label} {periodoFiltro === p.key ? '✓' : ''}
                  </button>
                ))}
              </div>
            )}
          </div>
          
          <a
            href={`/loja/${slug}/crm-vendas/leads/novo`}
            className="px-4 py-2 text-sm font-medium text-white bg-[#0176d3] hover:bg-[#0159a8] rounded transition-colors"
          >
            + Novo Lead
          </a>
        </div>
      </div>

      {/* Cards de métricas – estilo Salesforce Lightning */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title={periodoLabels.receita}
          value={formatMoney(data.receita)}
          icon={Wallet}
          iconColor="text-[#0176d3]"
          iconBgColor="bg-[#e3f3ff]"
          trend={data.receita > 0 ? 'up' : undefined}
          trendValue={data.receita > 0 ? '+12%' : undefined}
        />
        <StatCard
          title={periodoLabels.leads}
          value={String(data.leads)}
          subtitle={`${data.oportunidades_em_andamento} em negociação`}
          icon={Users}
          iconColor="text-[#06a59a]"
          iconBgColor="bg-[#d9f5f3]"
        />
        <StatCard
          title="Taxa de conversão"
          value={`${data.taxa_conversao}%`}
          icon={Percent}
          iconColor="text-[#ffb75d]"
          iconBgColor="bg-[#fff4e6]"
          trend={data.taxa_conversao > 20 ? 'up' : 'down'}
          trendValue={data.taxa_conversao > 20 ? '+5%' : '-2%'}
        />
        <StatCard
          title="Valor das vendas (perdido)"
          value={formatMoney(data.valor_perdido ?? 0)}
          icon={TrendingDown}
          iconColor="text-[#e287b2]"
          iconBgColor="bg-[#fef0f7]"
        />
      </div>

      {/* Pipeline aberto + Comissão Total + resumo por etapa - Estilo Salesforce */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        {/* Card de Pipeline Aberto */}
        <div className="bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] shadow-sm p-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 rounded-lg bg-[#d9f5f3] dark:bg-opacity-20">
              <DollarSign size={20} className="text-[#06a59a]" />
            </div>
            <h2 className="text-xs font-medium text-gray-600 dark:text-gray-400 uppercase tracking-wide">
              Pipeline em andamento
            </h2>
          </div>
          <p className="text-3xl font-bold text-[#06a59a] dark:text-[#06a59a]">
            {formatMoney(data.pipeline_aberto)}
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
            {data.oportunidades_em_andamento} oportunidade(s) em negociação
          </p>
        </div>

        {/* Card de Comissão Total do Mês */}
        <div className="bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] shadow-sm p-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 rounded-lg bg-[#fef0f7] dark:bg-opacity-20">
              <DollarSign size={20} className="text-[#e287b2]" />
            </div>
            <h2 className="text-xs font-medium text-gray-600 dark:text-gray-400 uppercase tracking-wide">
              {periodoLabels.comissao}
            </h2>
          </div>
          <p className="text-3xl font-bold text-[#e287b2] dark:text-[#e287b2]">
            {formatMoney(data.comissao_total_mes || 0)}
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
            {periodoLabels.comissaoSub}
          </p>
        </div>

        {/* Pipeline por Etapa */}
        <div className="lg:col-span-2 bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] shadow-sm p-5 overflow-hidden">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-gray-900 dark:text-white">
              Pipeline de vendas
            </h2>
            <Link
              href={`/loja/${slug}/crm-vendas/pipeline`}
              className="text-sm font-medium text-[#0176d3] hover:text-[#0159a8] inline-flex items-center gap-1 transition-colors"
            >
              Ver pipeline
              <ChevronRight size={16} />
            </Link>
          </div>
          <div className="flex gap-3 overflow-x-auto pb-2 -mx-2 px-2">
            {etapasComValor.map((e, i) => (
              <div
                key={e.key}
                className={`flex-shrink-0 w-32 rounded-lg border p-4 text-center transition-all hover:shadow-md ${
                  i === etapasComValor.length - 1
                    ? 'bg-[#d9f5f3] dark:bg-[#06a59a]/20 border-[#06a59a]/30'
                    : 'bg-gray-50 dark:bg-[#0d1f3c] border-gray-200 dark:border-[#0d1f3c]'
                }`}
              >
                <p className="text-xs font-medium text-gray-600 dark:text-gray-400 truncate mb-2">
                  {e.label}
                </p>
                <p className="text-lg font-bold text-gray-900 dark:text-white">
                  {formatMoney(e.valor)}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  {e.quantidade} {e.quantidade === 1 ? 'negócio' : 'negócios'}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Gráfico Pipeline por etapa + Funil de Vendas */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <SalesChart data={chartData.length > 0 ? chartData : undefined} title={`Pipeline por etapa — ${periodoFiltro === 'mes_atual' ? 'Mês Atual' : periodoFiltro === 'mes_passado' ? 'Mês Passado' : periodoFiltro === 'trimestre_atual' ? 'Trimestre' : 'Ano'}`} />
        <FunilVendas dados={data?.pipeline_por_etapa || []} etapasConfig={etapasAtivas()} />
      </div>

      {/* Atividades de hoje + Top Vendedores – duas colunas - Estilo Salesforce */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Atividades de hoje */}
        <div className="bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] shadow-sm p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <div className="p-1.5 rounded bg-[#e3f3ff] dark:bg-opacity-20">
                <Calendar size={18} className="text-[#0176d3]" />
              </div>
              Próximas atividades
            </h2>
            <Link
              href={`/loja/${slug}/crm-vendas/calendario`}
              className="text-sm text-[#0176d3] hover:text-[#0159a8] font-medium"
            >
              Ver todas
            </Link>
          </div>
          {proximasAtividades.length === 0 ? (
            <div className="text-center py-8">
              <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-gray-100 dark:bg-[#0d1f3c] flex items-center justify-center">
                <Calendar size={24} className="text-gray-400" />
              </div>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Nenhuma tarefa pendente no calendário
              </p>
              <Link
                href={`/loja/${slug}/crm-vendas/calendario`}
                className="text-sm text-[#0176d3] hover:text-[#0159a8] font-medium mt-2 inline-block"
              >
                Criar atividade
              </Link>
            </div>
          ) : (
            <ul className="space-y-3">
              {proximasAtividades.map((a) => {
                const Icon = iconPorTipo(a.tipo);
                let dataFormatada = '';
                let atrasada = false;
                if (a.data) {
                  try {
                    const date = new Date(a.data);
                    const agora = new Date();
                    const hoje = new Date();
                    const amanha = new Date(hoje);
                    amanha.setDate(amanha.getDate() + 1);
                    atrasada = date.getTime() < agora.getTime();
                    const isHoje = date.toDateString() === hoje.toDateString();
                    const isAmanha = date.toDateString() === amanha.toDateString();
                    const hora = date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
                    if (atrasada) {
                      const dia = date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' });
                      dataFormatada = `Atrasada — ${dia} às ${hora}`;
                    } else if (isHoje) {
                      dataFormatada = `Hoje às ${hora}`;
                    } else if (isAmanha) {
                      dataFormatada = `Amanhã às ${hora}`;
                    } else {
                      const dia = date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' });
                      dataFormatada = `${dia} às ${hora}`;
                    }
                  } catch {
                    dataFormatada = a.data;
                  }
                }

                return (
                  <li key={a.id}>
                    <Link
                      href={`/loja/${slug}/crm-vendas/calendario`}
                      className="flex items-center gap-3 py-2.5 border-b border-gray-100 dark:border-[#0d1f3c] last:border-0 hover:bg-gray-50 dark:hover:bg-[#0d1f3c] -mx-2 px-2 rounded transition-colors"
                    >
                      <div className="p-2 rounded bg-[#e3f3ff] dark:bg-opacity-20 text-[#0176d3]">
                        <Icon size={16} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                          {a.titulo}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                          {TIPO_LABEL_DASHBOARD[a.tipo] || a.tipo}
                          {a.lead_nome ? ` • ${a.lead_nome}` : ''}
                          {dataFormatada ? ` • ${dataFormatada}` : ''}
                        </p>
                      </div>
                      <ChevronRight size={16} className="text-gray-400 shrink-0" />
                    </Link>
                  </li>
                );
              })}
            </ul>
          )}
        </div>

        {/* Top Vendedores – oculto para vendedores (informação já disponível em relatórios) */}
        {!isVendedor && data.performance_vendedores && data.performance_vendedores.length > 0 && (
          <div className="bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] shadow-sm p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                <div className="p-1.5 rounded bg-[#d9f5f3] dark:bg-opacity-20">
                  <DollarSign size={18} className="text-[#06a59a]" />
                </div>
                Top vendedores (mês)
              </h2>
            </div>
            <ul className="space-y-3">
              {data.performance_vendedores.map((v, i) => (
                <li
                  key={v.id != null ? `v-${v.id}` : `outros-${i}`}
                  className="flex items-center gap-3 py-2.5 border-b border-gray-100 dark:border-[#0d1f3c] last:border-0 hover:bg-gray-50 dark:hover:bg-[#0d1f3c] -mx-2 px-2 rounded transition-colors"
                >
                  <div className="relative">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#0176d3] to-[#0d9dda] flex items-center justify-center text-white font-semibold text-sm shrink-0">
                      {(v.nome.charAt(0) || '?').toUpperCase()}
                    </div>
                    {i < 3 && (
                      <div className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-[#ffb75d] text-white text-xs font-bold flex items-center justify-center">
                        {i + 1}
                      </div>
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                      {v.nome}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {v.id == null ? 'Sem vendedor no cadastro' : 'Vendedor'}
                    </p>
                  </div>
                  <div className="text-right shrink-0">
                    <p className="font-semibold text-[#06a59a] text-sm">
                      {formatMoney(v.receita_mes)}
                    </p>
                    {v.comissao_mes > 0 && (
                      <p className="text-xs text-purple-600 dark:text-purple-400 mt-0.5">
                        Comissão: {formatMoney(v.comissao_mes)}
                      </p>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
