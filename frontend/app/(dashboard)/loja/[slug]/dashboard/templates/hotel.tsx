/* eslint-disable react-hooks/exhaustive-deps */
'use client';

import dynamic from 'next/dynamic';
import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import {
  ArrowRight,
  BedDouble,
  ClipboardList,
  DoorOpen,
  LogIn,
  LogOut,
  TrendingUp,
} from 'lucide-react';
import apiClient from '@/lib/api-client';
import type { HotelRelatorios } from './hotel-reports-charts';

const HotelReportsCharts = dynamic(() => import('./hotel-reports-charts'), {
  ssr: false,
  loading: () => (
    <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800">
      <div className="h-[320px] animate-pulse rounded-xl bg-gray-100 dark:bg-gray-900" />
    </div>
  ),
});

type LojaInfo = {
  id: number;
  nome: string;
  slug: string;
  tipo_loja_nome: string;
  cor_primaria: string;
  cor_secundaria: string;
  logo?: string;
  senha_foi_alterada: boolean;
};

function StatCard({
  title,
  value,
  sub,
  accent,
  icon: Icon,
}: {
  title: string;
  value: string;
  sub?: string;
  accent: string;
  icon: React.ComponentType<{ className?: string; style?: React.CSSProperties }>;
}) {
  return (
    <div className="group relative overflow-hidden rounded-2xl border border-gray-200/80 bg-white p-5 shadow-sm transition hover:shadow-md dark:border-gray-700 dark:bg-gray-800">
      <div
        className="pointer-events-none absolute inset-x-0 top-0 h-1 opacity-90"
        style={{ background: `linear-gradient(90deg, ${accent}, ${accent}99)` }}
      />
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">{title}</p>
          <p className="mt-2 truncate text-3xl font-bold tabular-nums tracking-tight" style={{ color: accent }}>
            {value}
          </p>
          {sub ? <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">{sub}</p> : null}
        </div>
        <div
          className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-gray-100 bg-gray-50 dark:border-gray-600 dark:bg-gray-900/40"
          style={{ color: accent }}
        >
          <Icon className="h-5 w-5" />
        </div>
      </div>
    </div>
  );
}

function QuickLink({
  title,
  description,
  href,
  accent,
}: {
  title: string;
  description: string;
  href: string;
  accent: string;
}) {
  return (
    <Link
      href={href}
      className="group flex min-w-0 flex-col rounded-xl border border-gray-200 bg-white p-4 shadow-sm transition hover:border-gray-300 hover:shadow-md dark:border-gray-700 dark:bg-gray-800/80 dark:hover:border-gray-600"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="font-semibold text-gray-900 dark:text-gray-100">{title}</p>
          <p className="mt-1 text-sm leading-snug text-gray-600 dark:text-gray-400">{description}</p>
        </div>
        <span
          className="inline-flex shrink-0 items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium text-white"
          style={{ backgroundColor: accent }}
        >
          Ir
          <ArrowRight className="h-3.5 w-3.5" aria-hidden />
        </span>
      </div>
    </Link>
  );
}

function statusLabel(status: string): string {
  const map: Record<string, string> = {
    pendente: 'Pendente',
    confirmada: 'Confirmada',
    checkin: 'Hospedado',
    checkout: 'Encerrada',
    cancelada: 'Cancelada',
    no_show: 'No-show',
  };
  return map[status] || status;
}

export default function DashboardHotel({ loja }: { loja: LojaInfo }) {
  const accent = loja.cor_primaria || '#0EA5E9';

  const [dashboard, setDashboard] = useState<{
    kpis: {
      ocupacao_hoje_percent: number;
      quartos_total: number;
      quartos_ocupados: number;
      checkins_hoje: number;
      checkouts_hoje: number;
      adr_mes: number;
      pendencias_governanca: number;
    };
    chegadas_hoje: Array<{
      id: number;
      status: string;
      hospede_nome: string;
      quarto_numero: string;
      quarto_nome: string;
      data_checkin: string;
      data_checkout: string;
    }>;
    saidas_hoje: Array<{
      id: number;
      status: string;
      hospede_nome: string;
      quarto_numero: string;
      quarto_nome: string;
      data_checkin: string;
      data_checkout: string;
    }>;
    pendencias_governanca: Array<{
      id: number;
      tipo: string;
      status: string;
      prioridade: number;
      descricao: string;
      quarto_numero: string;
    }>;
    relatorios?: HotelRelatorios;
  } | null>(null);
  const [statsLoading, setStatsLoading] = useState(false);

  const occupancyLabel = useMemo(() => {
    if (!dashboard?.kpis) return '—';
    return `${dashboard.kpis.ocupacao_hoje_percent}%`;
  }, [dashboard]);

  const adrLabel = useMemo(() => {
    if (!dashboard?.kpis) return '—';
    const v = Number(dashboard.kpis.adr_mes || 0);
    return v ? `R$ ${v.toFixed(2)}` : 'R$ 0,00';
  }, [dashboard]);

  useEffect(() => {
    let mounted = true;
    const load = async () => {
      setStatsLoading(true);
      try {
        const r = await apiClient.get('/hotel/dashboard/');
        if (!mounted) return;
        setDashboard(r.data);
      } catch {
        if (!mounted) return;
        setDashboard(null);
      } finally {
        if (!mounted) return;
        setStatsLoading(false);
      }
    };
    load();
    return () => {
      mounted = false;
    };
  }, [loja?.slug]);

  const kpis = dashboard?.kpis || null;

  return (
    <div className="space-y-6">
      {/* KPIs */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Ocupação hoje"
          value={statsLoading ? '…' : occupancyLabel}
          sub={kpis ? `${kpis.quartos_ocupados} de ${kpis.quartos_total} quartos` : 'Quartos ocupados / total'}
          accent={accent}
          icon={BedDouble}
        />
        <StatCard
          title="Check-ins hoje"
          value={statsLoading ? '…' : String(kpis?.checkins_hoje ?? '—')}
          sub="Chegadas previstas"
          accent={accent}
          icon={LogIn}
        />
        <StatCard
          title="Check-outs hoje"
          value={statsLoading ? '…' : String(kpis?.checkouts_hoje ?? '—')}
          sub="Saídas previstas"
          accent={accent}
          icon={LogOut}
        />
        <StatCard
          title="Diária média (ADR)"
          value={statsLoading ? '…' : adrLabel}
          sub="Mês corrente"
          accent={accent}
          icon={TrendingUp}
        />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3 lg:items-start">
        {/* Operação + listas (sem duplicar os mesmos números em blocos gigantes) */}
        <div className="space-y-4 lg:col-span-2">
          <div className="rounded-2xl border border-gray-200/80 bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-gray-800">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <DoorOpen className="h-5 w-5 text-gray-500 dark:text-gray-400" aria-hidden />
                <p className="text-lg font-semibold text-gray-900 dark:text-white">Operação do dia</p>
              </div>
              <Link
                href={`/loja/${loja.slug}/hotel/reservas`}
                className="inline-flex items-center gap-1.5 rounded-lg border border-gray-200 bg-gray-50 px-3 py-1.5 text-xs font-medium text-gray-800 transition hover:bg-gray-100 dark:border-gray-600 dark:bg-gray-900/50 dark:text-gray-200 dark:hover:bg-gray-700"
              >
                Ver todas as reservas
                <ArrowRight className="h-3.5 w-3.5" aria-hidden />
              </Link>
            </div>

            <div className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-3">
              <ListPanel
                title="Chegadas de hoje"
                empty="Nenhuma chegada prevista para hoje."
                loading={statsLoading}
                accent={accent}
                actionHref={`/loja/${loja.slug}/hotel/reservas?data_checkin=hoje`}
                actionLabel="Lista"
              >
                {dashboard?.chegadas_hoje?.map((r) => (
                  <li
                    key={r.id}
                    className="flex items-center justify-between gap-2 rounded-lg border border-transparent bg-gray-50/80 px-2.5 py-2 dark:bg-gray-900/40"
                  >
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium text-gray-900 dark:text-gray-100">
                        {r.hospede_nome || 'Hóspede'}
                      </p>
                      <p className="truncate text-xs text-gray-500 dark:text-gray-400">
                        Quarto {r.quarto_numero || '—'}
                        {r.quarto_nome ? ` · ${r.quarto_nome}` : ''}
                      </p>
                    </div>
                    <span className="shrink-0 rounded-full bg-white px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-gray-600 ring-1 ring-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:ring-gray-600">
                      {statusLabel(r.status)}
                    </span>
                  </li>
                ))}
              </ListPanel>

              <ListPanel
                title="Saídas de hoje"
                empty="Nenhuma saída prevista para hoje."
                loading={statsLoading}
                accent={accent}
                actionHref={`/loja/${loja.slug}/hotel/reservas?data_checkout=hoje`}
                actionLabel="Lista"
              >
                {dashboard?.saidas_hoje?.map((r) => (
                  <li
                    key={r.id}
                    className="flex items-center justify-between gap-2 rounded-lg border border-transparent bg-gray-50/80 px-2.5 py-2 dark:bg-gray-900/40"
                  >
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium text-gray-900 dark:text-gray-100">
                        {r.hospede_nome || 'Hóspede'}
                      </p>
                      <p className="truncate text-xs text-gray-500 dark:text-gray-400">Quarto {r.quarto_numero || '—'}</p>
                    </div>
                    <span className="shrink-0 rounded-full bg-white px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-gray-600 ring-1 ring-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:ring-gray-600">
                      {statusLabel(r.status)}
                    </span>
                  </li>
                ))}
              </ListPanel>

              <ListPanel
                title="Pendências (governança)"
                empty="Sem pendências abertas."
                loading={statsLoading}
                accent={accent}
                actionHref={`/loja/${loja.slug}/hotel/governanca`}
                actionLabel="Abrir"
              >
                {dashboard?.pendencias_governanca?.map((t) => (
                  <li
                    key={t.id}
                    className="flex items-center justify-between gap-2 rounded-lg border border-transparent bg-gray-50/80 px-2.5 py-2 dark:bg-gray-900/40"
                  >
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium text-gray-900 dark:text-gray-100">
                        {t.descricao || t.tipo || 'Tarefa'}
                      </p>
                      <p className="truncate text-xs text-gray-500 dark:text-gray-400">Quarto {t.quarto_numero || '—'}</p>
                    </div>
                    <span className="shrink-0 rounded-full bg-amber-50 px-2 py-0.5 text-[10px] font-semibold text-amber-800 ring-1 ring-amber-200 dark:bg-amber-950/40 dark:text-amber-200 dark:ring-amber-800">
                      P{t.prioridade}
                    </span>
                  </li>
                ))}
              </ListPanel>
            </div>

            <p className="mt-4 text-xs text-gray-500 dark:text-gray-400">
              {dashboard
                ? 'Dados atualizados pelo módulo Hotel ao carregar esta página.'
                : 'Cadastre quartos e reservas para ver o resumo do dia.'}
            </p>
          </div>

          <div className="rounded-2xl border border-gray-200/80 bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-gray-800">
            <HotelReportsCharts loading={statsLoading} accent={accent} relatorios={dashboard?.relatorios} />
          </div>
        </div>

        {/* Atalhos: sem border-l que “quebra” no layout estreito */}
        <div className="rounded-2xl border border-gray-200/80 bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-gray-800">
          <div className="flex items-center gap-2">
            <ClipboardList className="h-5 w-5 text-gray-500 dark:text-gray-400" aria-hidden />
            <p className="text-lg font-semibold text-gray-900 dark:text-white">Atalhos rápidos</p>
          </div>
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">Acesso direto às telas mais usadas na operação.</p>
          <div className="mt-4 space-y-3">
            <QuickLink
              title="Nova reserva"
              description="Período, hóspede, quarto, tarifa e canal."
              href={`/loja/${loja.slug}/hotel/reservas?novo=1`}
              accent={accent}
            />
            <QuickLink
              title="Reservas e check-in/out"
              description="Lista completa e ações de hospedagem."
              href={`/loja/${loja.slug}/hotel/reservas`}
              accent={accent}
            />
            <QuickLink
              title="Quartos e status"
              description="Disponível, ocupado, limpeza ou manutenção."
              href={`/loja/${loja.slug}/hotel/quartos`}
              accent={accent}
            />
            <QuickLink
              title="Governança"
              description="Tarefas de limpeza e manutenção por quarto."
              href={`/loja/${loja.slug}/hotel/governanca`}
              accent={accent}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

function ListPanel({
  title,
  empty,
  loading,
  children,
  accent,
  actionHref,
  actionLabel,
}: {
  title: string;
  empty: string;
  loading: boolean;
  children?: React.ReactNode;
  accent: string;
  actionHref: string;
  actionLabel: string;
}) {
  const items = Array.isArray(children) ? children : null;
  const hasItems = Boolean(items && items.length);

  return (
    <div className="flex min-h-[220px] flex-col rounded-xl border border-gray-200/90 bg-gray-50/50 dark:border-gray-700 dark:bg-gray-900/20">
      <div className="flex items-center justify-between gap-2 border-b border-gray-200/80 px-3 py-2.5 dark:border-gray-700">
        <p className="text-sm font-semibold text-gray-900 dark:text-white">{title}</p>
        <Link
          href={actionHref}
          className="shrink-0 rounded-md px-2 py-1 text-xs font-semibold text-white shadow-sm"
          style={{ backgroundColor: accent }}
        >
          {actionLabel}
        </Link>
      </div>
      <ul className="flex flex-1 flex-col gap-1.5 p-2">
        {loading ? (
          <li className="px-2 py-6 text-center text-xs text-gray-500 dark:text-gray-400">Carregando…</li>
        ) : hasItems ? (
          items!.slice(0, 6)
        ) : (
          <li className="px-2 py-6 text-center text-xs text-gray-500 dark:text-gray-400">{empty}</li>
        )}
      </ul>
    </div>
  );
}
