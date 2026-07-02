'use client';

import dynamic from 'next/dynamic';
import Link from 'next/link';
import StatCard from '@/components/crm-vendas/StatCard';
import SkeletonDashboard from '@/components/crm-vendas/SkeletonDashboard';
import FunilVendas from '@/components/crm-vendas/FunilVendas';
import {
  Wallet,
  Users,
  Percent,
  Calendar,
  ChevronRight,
  DollarSign,
  TrendingDown,
} from 'lucide-react';
import { formatCrmBrl } from '@/lib/crm-utils';
import { CRM_PERIODO_DASHBOARD_FILTRO, CRM_PERIODO_NOME } from '@/lib/crm-periodos';
import {
  formatarDataAtividade,
  iconPorTipoAtividade,
  labelTipoAtividade,
  useCrmDashboardPage,
} from '@/hooks/crm-vendas/useCrmDashboardPage';

const SalesChart = dynamic(() => import('@/components/crm-vendas/SalesChart'), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center min-h-[320px] bg-blue-50/40 dark:bg-blue-900/10 rounded-2xl border-2 border-blue-200 dark:border-blue-800 animate-pulse">
      <span className="text-sm text-gray-500">Carregando gráfico...</span>
    </div>
  ),
});

export default function CrmVendasDashboardPage() {
  const {
    slug,
    isVendedor,
    etapasAtivas,
    data,
    proximasAtividades,
    loading,
    error,
    showFiltro,
    periodoFiltro,
    filtroRef,
    etapasComValor,
    chartData,
    periodoLabels,
    chartTitle,
    toggleFiltro,
    selecionarPeriodo,
  } = useCrmDashboardPage();

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

  return (
    <div className="space-y-5">
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
              · {CRM_PERIODO_NOME[periodoFiltro] ?? 'Este mês'}
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
              {CRM_PERIODO_NOME[periodoFiltro] ?? 'Filtrar'} ▾
            </button>
            {showFiltro && (
              <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-[#16325c] rounded-lg shadow-lg border border-gray-200 dark:border-[#0d1f3c] py-1 z-20">
                <div className="px-4 py-2 text-xs text-gray-500 dark:text-gray-400 border-b border-gray-100 dark:border-[#0d1f3c]">
                  Período
                </div>
                {CRM_PERIODO_DASHBOARD_FILTRO.map((p) => (
                  <button
                    key={p.value}
                    type="button"
                    className={`w-full text-left px-4 py-2 text-sm hover:bg-gray-50 dark:hover:bg-[#0d1f3c] ${periodoFiltro === p.value ? 'text-[#0176d3] font-semibold' : 'text-gray-700 dark:text-gray-200'}`}
                    onClick={() => selecionarPeriodo(p.value)}
                  >
                    {p.label} {periodoFiltro === p.value ? '✓' : ''}
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

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title={periodoLabels.receita}
          value={formatCrmBrl(data.receita)}
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
          value={formatCrmBrl(data.valor_perdido ?? 0)}
          icon={TrendingDown}
          iconColor="text-[#e287b2]"
          iconBgColor="bg-[#fef0f7]"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
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
            {formatCrmBrl(data.pipeline_aberto)}
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
            {data.oportunidades_em_andamento} oportunidade(s) em negociação
          </p>
        </div>

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
            {formatCrmBrl(data.comissao_total_mes || 0)}
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
            {periodoLabels.comissaoSub}
          </p>
        </div>

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
                  {formatCrmBrl(e.valor)}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  {e.quantidade} {e.quantidade === 1 ? 'negócio' : 'negócios'}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <SalesChart
          data={chartData.length > 0 ? chartData : undefined}
          title={`Pipeline por etapa — ${chartTitle}`}
        />
        <FunilVendas dados={data?.pipeline_por_etapa || []} etapasConfig={etapasAtivas()} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
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
                const Icon = iconPorTipoAtividade(a.tipo);
                const { texto: dataFormatada } = a.data ? formatarDataAtividade(a.data) : { texto: '' };

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
                          {labelTipoAtividade(a.tipo)}
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
                      {formatCrmBrl(v.receita_mes)}
                    </p>
                    {v.comissao_mes > 0 && (
                      <p className="text-xs text-purple-600 dark:text-purple-400 mt-0.5">
                        Comissão: {formatCrmBrl(v.comissao_mes)}
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
