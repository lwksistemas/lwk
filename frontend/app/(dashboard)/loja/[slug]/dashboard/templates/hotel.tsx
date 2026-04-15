/* eslint-disable react-hooks/exhaustive-deps */
'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import apiClient from '@/lib/api-client';

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
}: {
  title: string;
  value: string;
  sub?: string;
  accent: string;
}) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-5">
      <p className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">{title}</p>
      <div className="mt-2 flex items-end justify-between gap-3">
        <p className="text-3xl font-bold" style={{ color: accent }}>
          {value}
        </p>
        {sub ? <p className="text-xs text-gray-500 dark:text-gray-400 text-right">{sub}</p> : null}
      </div>
    </div>
  );
}

function ActionCard({
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
      className="bg-white dark:bg-gray-800 rounded-lg shadow p-5 hover:shadow-md transition-shadow border-l-4"
      style={{ borderLeftColor: accent }}
    >
      <p className="font-semibold text-gray-900 dark:text-gray-100">{title}</p>
      <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{description}</p>
      <div className="mt-3 text-sm font-medium" style={{ color: accent }}>
        Abrir →
      </div>
    </Link>
  );
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
      <div className="flex flex-col gap-2">
        <h2 className="text-2xl font-bold" style={{ color: accent }}>
          Dashboard — Hotelaria
        </h2>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Visão operacional do dia: ocupação, check-ins/outs, reservas e pendências de governança.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Ocupação hoje"
          value={statsLoading ? '…' : occupancyLabel}
          sub={kpis ? `${kpis.quartos_ocupados} / ${kpis.quartos_total} aptos` : 'Aptos ocupados / total'}
          accent={accent}
        />
        <StatCard title="Check-ins" value={statsLoading ? '…' : String(kpis?.checkins_hoje ?? '—')} sub="Previstos para hoje" accent={accent} />
        <StatCard title="Check-outs" value={statsLoading ? '…' : String(kpis?.checkouts_hoje ?? '—')} sub="Saídas previstas" accent={accent} />
        <StatCard title="Diária média" value={statsLoading ? '…' : adrLabel} sub="ADR (mês)" accent={accent} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-5 lg:col-span-2">
          <div className="flex items-center justify-between gap-3">
            <p className="font-semibold text-gray-900 dark:text-gray-100">Operação do dia</p>
            <Link
              href={`/loja/${loja.slug}/hotel/reservas`}
              className="text-xs px-2 py-1 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
            >
              Ver reservas →
            </Link>
          </div>
          <div className="mt-4 grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-4">
              <p className="text-sm font-medium text-gray-900 dark:text-gray-100">Chegadas</p>
              <p className="mt-2 text-2xl font-bold" style={{ color: accent }}>
                {statsLoading ? '…' : String(kpis?.checkins_hoje ?? '—')}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Reservas com check-in hoje</p>
            </div>
            <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-4">
              <p className="text-sm font-medium text-gray-900 dark:text-gray-100">Saídas</p>
              <p className="mt-2 text-2xl font-bold" style={{ color: accent }}>
                {statsLoading ? '…' : String(kpis?.checkouts_hoje ?? '—')}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Hóspedes com check-out hoje</p>
            </div>
            <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-4">
              <p className="text-sm font-medium text-gray-900 dark:text-gray-100">Pendências</p>
              <p className="mt-2 text-2xl font-bold" style={{ color: accent }}>
                {statsLoading ? '…' : String(kpis?.pendencias_governanca ?? '—')}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Governança / manutenção</p>
            </div>
          </div>

          <div className="mt-5 grid grid-cols-1 lg:grid-cols-3 gap-4">
            <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-4">
              <div className="flex items-center justify-between gap-2">
                <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">Chegadas de hoje</p>
                <Link href={`/loja/${loja.slug}/hotel/reservas?data_checkin=hoje`} className="text-xs text-gray-600 dark:text-gray-300 hover:underline">
                  Abrir
                </Link>
              </div>
              <div className="mt-3 space-y-2">
                {statsLoading ? (
                  <p className="text-xs text-gray-500 dark:text-gray-400">Carregando…</p>
                ) : dashboard?.chegadas_hoje?.length ? (
                  dashboard.chegadas_hoje.slice(0, 6).map((r) => (
                    <div key={r.id} className="flex items-center justify-between gap-3">
                      <p className="text-xs text-gray-900 dark:text-gray-100 truncate">
                        <span className="font-medium">{r.quarto_numero || '—'}</span>
                        <span className="text-gray-500 dark:text-gray-400"> · </span>
                        {r.hospede_nome || 'Hóspede'}
                      </p>
                      <span className="text-[11px] px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300">
                        {r.status}
                      </span>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-gray-500 dark:text-gray-400">Nenhuma chegada prevista.</p>
                )}
              </div>
            </div>

            <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-4">
              <div className="flex items-center justify-between gap-2">
                <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">Saídas de hoje</p>
                <Link href={`/loja/${loja.slug}/hotel/reservas?data_checkout=hoje`} className="text-xs text-gray-600 dark:text-gray-300 hover:underline">
                  Abrir
                </Link>
              </div>
              <div className="mt-3 space-y-2">
                {statsLoading ? (
                  <p className="text-xs text-gray-500 dark:text-gray-400">Carregando…</p>
                ) : dashboard?.saidas_hoje?.length ? (
                  dashboard.saidas_hoje.slice(0, 6).map((r) => (
                    <div key={r.id} className="flex items-center justify-between gap-3">
                      <p className="text-xs text-gray-900 dark:text-gray-100 truncate">
                        <span className="font-medium">{r.quarto_numero || '—'}</span>
                        <span className="text-gray-500 dark:text-gray-400"> · </span>
                        {r.hospede_nome || 'Hóspede'}
                      </p>
                      <span className="text-[11px] px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300">
                        {r.status}
                      </span>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-gray-500 dark:text-gray-400">Nenhuma saída prevista.</p>
                )}
              </div>
            </div>

            <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-4">
              <div className="flex items-center justify-between gap-2">
                <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">Pendências</p>
                <Link href={`/loja/${loja.slug}/hotel/governanca`} className="text-xs text-gray-600 dark:text-gray-300 hover:underline">
                  Abrir
                </Link>
              </div>
              <div className="mt-3 space-y-2">
                {statsLoading ? (
                  <p className="text-xs text-gray-500 dark:text-gray-400">Carregando…</p>
                ) : dashboard?.pendencias_governanca?.length ? (
                  dashboard.pendencias_governanca.slice(0, 6).map((t) => (
                    <div key={t.id} className="flex items-center justify-between gap-3">
                      <p className="text-xs text-gray-900 dark:text-gray-100 truncate">
                        <span className="font-medium">{t.quarto_numero || '—'}</span>
                        <span className="text-gray-500 dark:text-gray-400"> · </span>
                        {t.descricao || t.tipo}
                      </p>
                      <span className="text-[11px] px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300">
                        P{t.prioridade}
                      </span>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-gray-500 dark:text-gray-400">Sem pendências abertas.</p>
                )}
              </div>
            </div>
          </div>

          <div className="mt-4 text-sm text-gray-600 dark:text-gray-400">
            {dashboard ? 'Dashboard carregado em tempo real via API do módulo Hotel.' : 'Cadastre quartos, reservas e tarefas para ver o resumo do dia aqui.'}
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-5">
          <p className="font-semibold text-gray-900 dark:text-gray-100">Atalhos rápidos</p>
          <div className="mt-4 space-y-3">
            <ActionCard
              title="Nova reserva"
              description="Cadastrar reserva, período, tarifa e canal."
              href={`/loja/${loja.slug}/hotel/reservas?novo=1`}
              accent={accent}
            />
            <ActionCard
              title="Check-in / Check-out"
              description="Atualizar status da hospedagem e pagamentos."
              href={`/loja/${loja.slug}/hotel/reservas`}
              accent={accent}
            />
            <ActionCard
              title="Quartos"
              description="Atualizar status: disponível/ocupado/limpeza/manutenção."
              href={`/loja/${loja.slug}/hotel/quartos`}
              accent={accent}
            />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-5">
          <p className="font-semibold text-gray-900 dark:text-gray-100">Receitas</p>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">Faturamento do período e parcelas pendentes.</p>
          <div className="mt-4 h-24 rounded-lg bg-gray-50 dark:bg-gray-900 border border-dashed border-gray-200 dark:border-gray-700 flex items-center justify-center text-sm text-gray-500 dark:text-gray-400">
            Gráfico (em breve)
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-5">
          <p className="font-semibold text-gray-900 dark:text-gray-100">Distribuição de ocupação</p>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">Por tipo de quarto e categoria.</p>
          <div className="mt-4 h-24 rounded-lg bg-gray-50 dark:bg-gray-900 border border-dashed border-gray-200 dark:border-gray-700 flex items-center justify-center text-sm text-gray-500 dark:text-gray-400">
            Gráfico (em breve)
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-5">
          <p className="font-semibold text-gray-900 dark:text-gray-100">Satisfação</p>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">Avaliações e ocorrências recentes.</p>
          <div className="mt-4 h-24 rounded-lg bg-gray-50 dark:bg-gray-900 border border-dashed border-gray-200 dark:border-gray-700 flex items-center justify-center text-sm text-gray-500 dark:text-gray-400">
            Widget (em breve)
          </div>
        </div>
      </div>
    </div>
  );
}

