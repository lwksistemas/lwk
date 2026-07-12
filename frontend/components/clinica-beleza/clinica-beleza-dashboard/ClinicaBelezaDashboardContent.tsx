"use client";

import type { ElementType, ReactNode } from "react";
import Link from "next/link";
import { Activity, CalendarDays, RefreshCw, TrendingUp, Users } from "lucide-react";
import {
  Line,
  LineChart,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import { ClinicaBelezaShell } from "@/components/clinica-beleza/clinica-beleza-shell/ClinicaBelezaShell";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import {
  ClinicaBelezaThemeProvider,
  useClinicaBelezaTheme,
} from "@/components/clinica-beleza/ClinicaBelezaThemeContext";
import { useClinicaBelezaDark } from "@/hooks/useClinicaBelezaDark";
import { formatCurrency } from "@/lib/financeiro-helpers";
import { CLINICA_AGENDA_STATUS_LABEL } from "@/lib/clinica-beleza-constants";
import type { LojaInfo } from "@/types/dashboard";
import type { DashboardAppointment } from "./clinica-beleza-dashboard-types";
import {
  DASHBOARD_STATUS_COLORS,
  getDashboardChartColors,
  pctChangeDashboard,
} from "./clinica-beleza-dashboard-utils";
import { useClinicaBelezaDashboard } from "./useClinicaBelezaDashboard";

function StatCard({
  title,
  value,
  icon: Icon,
  changeLabel,
  positive,
}: {
  title: string;
  value: string | number;
  icon: ElementType;
  changeLabel?: string | null;
  positive?: boolean;
}) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700">
      <div className="flex items-start justify-between gap-2 mb-2">
        <span className="text-sm text-gray-500 dark:text-gray-400">{title}</span>
        <div
          className="w-9 h-9 rounded-lg flex items-center justify-center shrink-0"
          style={{ backgroundColor: 'color-mix(in srgb, var(--cb-primary, #8B3D52) 9%, transparent)' }}
        >
          <Icon className="w-4 h-4" style={{ color: 'var(--cb-primary, #8B3D52)' }} />
        </div>
      </div>
      <p className="text-2xl font-bold text-gray-900 dark:text-white">{value}</p>
      {changeLabel && (
        <p
          className={`text-xs mt-1 font-medium ${positive === false ? "text-red-500" : "text-emerald-600"}`}
        >
          {changeLabel}
        </p>
      )}
    </div>
  );
}

function ChartCard({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
      <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-200 mb-4">{title}</h3>
      <div className="relative overflow-hidden">{children}</div>
    </div>
  );
}

function AppointmentItem({ appt }: { appt: DashboardAppointment }) {
  const statusClass = DASHBOARD_STATUS_COLORS[appt.status] || DASHBOARD_STATUS_COLORS.PENDING;
  const statusLabel = CLINICA_AGENDA_STATUS_LABEL[appt.status] || appt.status;
  return (
    <div className="flex items-center justify-between py-3 border-b border-gray-50 dark:border-gray-700 last:border-0">
      <div className="flex items-center gap-3 min-w-0">
        <span className="text-xs font-semibold text-gray-500 w-11 shrink-0">
          {appt.time || appt.date?.slice(11, 16) || "--:--"}
        </span>
        <div className="min-w-0">
          <p className="text-sm font-medium text-gray-800 dark:text-gray-200 truncate">{appt.patient_name}</p>
          <p className="text-xs text-gray-400 truncate">{appt.procedure_name}</p>
        </div>
      </div>
      <span className={`text-xs px-2.5 py-0.5 rounded-full font-medium shrink-0 ml-2 ${statusClass}`}>
        {statusLabel}
      </span>
    </div>
  );
}

export function ClinicaBelezaDashboardContent({ loja, onLogout }: { loja: LojaInfo; onLogout?: () => void }) {
  return (
    <ClinicaBelezaThemeProvider
      corPrimaria={loja.cor_primaria}
      corSecundaria={loja.cor_secundaria}
      corFundoPagina={loja.cor_fundo_pagina}
      agendaStatusColors={loja.agenda_status_colors}
    >
      <ClinicaBelezaDashboardInner loja={loja} onLogout={onLogout} />
    </ClinicaBelezaThemeProvider>
  );
}

function ClinicaBelezaDashboardInner({ loja, onLogout }: { loja: LojaInfo; onLogout?: () => void }) {
  const { primary } = useClinicaBelezaTheme();
  const chartColors = getDashboardChartColors(primary);
  const { slug, data, financial, loading, mesAno, setMesAno, mesAnoMax, fetchData } =
    useClinicaBelezaDashboard(loja);
  const [darkMode] = useClinicaBelezaDark();

  const stats = data?.statistics;
  const filterLabel = data?.filter?.label ?? "Este mês";
  const isCurrentMonth = data?.filter?.is_current_month ?? true;
  const appointments = data?.next_appointments || [];
  const revenueData = data?.revenue_last_7_days || [];
  const revenueComValor = revenueData.some((d) => d.value > 0);
  const topProcedures = data?.top_procedures || [];
  const topProceduresVolume = data?.top_procedures_volume || [];
  const soroterapiaComMovimento = topProceduresVolume.filter((p) => p.count > 0);

  const apptChange =
    stats?.appointments_yesterday != null
      ? pctChangeDashboard(stats.appointments_today, stats.appointments_yesterday)
      : null;

  const faturamentoChartTitle = isCurrentMonth
    ? `Faturamento (${filterLabel})`
    : `Faturamento — ${filterLabel}`;

  return (
    <ClinicaBelezaShell loja={loja} onLogout={onLogout}>
      <ClinicaBelezaStandardPageHeader
        title=""
        actionsOnly
        extraActions={
          <div className="flex items-center gap-2">
            <input
              type="month"
              value={mesAno}
              max={mesAnoMax}
              onChange={(e) => e.target.value && setMesAno(e.target.value)}
              className="px-3 py-1.5 text-sm border border-gray-200 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-800 text-gray-900 dark:text-gray-100"
              aria-label="Filtrar mês do dashboard"
            />
            <button
              type="button"
              onClick={() => void fetchData(true)}
              disabled={loading}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm border border-gray-200 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-800 text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-neutral-700 disabled:opacity-50"
              title="Atualizar gráficos"
            >
              <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
              Atualizar
            </button>
          </div>
        }
      />
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div
            className="w-8 h-8 border-4 rounded-full animate-spin"
            style={{ borderColor: 'color-mix(in srgb, var(--cb-primary, #8B3D52) 20%, transparent)', borderTopColor: 'var(--cb-primary, #8B3D52)' }}
          />
        </div>
      ) : (
        <div className="p-4 md:p-6 lg:p-8 space-y-6 w-full">
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
            <StatCard
              title="Atendimentos hoje"
              value={stats?.appointments_today ?? 0}
              icon={CalendarDays}
              changeLabel={apptChange ? `${apptChange} vs ontem` : undefined}
              positive={apptChange ? !apptChange.startsWith("-") : true}
            />
            <StatCard
              title="Faturamento hoje"
              value={formatCurrency(stats?.revenue_today ?? 0)}
              icon={TrendingUp}
              changeLabel="Hoje"
            />
            <StatCard
              title="Clientes ativos"
              value={stats?.patients_total ?? 0}
              icon={Users}
              changeLabel="Cadastrados"
            />
            <StatCard
              title="Sessões realizadas"
              value={stats?.sessions_month ?? 0}
              icon={Activity}
              changeLabel={filterLabel}
            />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-200">Próximos agendamentos</h3>
                <Link
                  href={`/loja/${slug}/agenda`}
                  className="text-xs font-medium hover:underline"
                  style={{ color: 'var(--cb-primary, #8B3D52)' }}
                >
                  Ver agenda completa
                </Link>
              </div>
              {appointments.length > 0 ? (
                appointments.slice(0, 5).map((appt) => <AppointmentItem key={appt.id} appt={appt} />)
              ) : (
                <p className="text-sm text-gray-400 text-center py-6">Nenhum agendamento próximo</p>
              )}
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700">
              <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-200 mb-4">
                Procedimentos realizados — {filterLabel}
              </h3>
              {topProcedures.length > 0 ? (
                <div className="space-y-3">
                  {topProcedures.slice(0, 5).map((proc, i) => {
                    const max = topProcedures[0]?.count || 1;
                    const pct = Math.round((proc.count / max) * 100);
                    return (
                      <div key={i}>
                        <div className="flex justify-between text-xs mb-1">
                          <span className="text-gray-600 dark:text-gray-400 truncate pr-2">{proc.name}</span>
                          <span className="text-gray-500 font-medium shrink-0">{proc.count}</span>
                        </div>
                        <div className="h-2 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
                          <div
                            className="h-full rounded-full"
                            style={{
                              width: `${pct}%`,
                              backgroundColor: chartColors[i % chartColors.length],
                            }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p className="text-sm text-gray-400 text-center py-6">Sem consultas concluídas no período</p>
              )}
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 flex flex-col">
              <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-200 mb-4">
                Resumo financeiro — {filterLabel}
              </h3>
              <div className="space-y-3 flex-1">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Faturamento</span>
                  <span className="font-semibold text-emerald-600">
                    {formatCurrency(financial?.faturamento ?? stats?.revenue_month ?? 0)}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Despesas</span>
                  <span className="font-semibold text-red-500">{formatCurrency(financial?.despesas ?? 0)}</span>
                </div>
                <hr className="border-gray-100 dark:border-gray-700" />
                <div className="flex justify-between text-sm">
                  <span className="font-medium text-gray-700 dark:text-gray-300">Lucro líquido</span>
                  <span className="font-bold text-emerald-600">
                    {formatCurrency(
                      financial?.lucro ??
                        (financial?.faturamento ?? stats?.revenue_month ?? 0) - (financial?.despesas ?? 0),
                    )}
                  </span>
                </div>
              </div>
              <Link
                href={`/loja/${slug}/clinica-beleza/financeiro`}
                className="mt-5 block w-full text-center py-3 rounded-lg text-sm font-semibold text-white transition-opacity hover:opacity-90"
                style={{ backgroundColor: 'var(--cb-primary, #8B3D52)' }}
              >
                Ver relatório financeiro
              </Link>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <ChartCard title={faturamentoChartTitle}>
              <div className="h-56">
                {revenueComValor ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={revenueData}>
                      <CartesianGrid strokeDasharray="3 3" stroke={darkMode ? "#374151" : "#f0f0f0"} />
                      <XAxis dataKey="day" tick={{ fontSize: 11 }} stroke="#9ca3af" />
                      <YAxis
                        tick={{ fontSize: 11 }}
                        stroke="#9ca3af"
                        tickFormatter={(v) => `R$${(v / 1000).toFixed(0)}k`}
                      />
                      <Tooltip formatter={(v) => formatCurrency(Number(v))} />
                      <Line
                        type="monotone"
                        dataKey="value"
                        stroke={primary}
                        strokeWidth={2.5}
                        dot={{ r: 3, fill: primary }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <p className="text-sm text-gray-400 text-center py-16">Sem faturamento no período</p>
                )}
              </div>
            </ChartCard>

            <ChartCard title={`Top 5 Soroterapias — ${filterLabel}`}>
              <div className="h-56 flex items-center justify-center">
                {soroterapiaComMovimento.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={soroterapiaComMovimento.slice(0, 5)}
                        dataKey="count"
                        nameKey="name"
                        cx="50%"
                        cy="50%"
                        innerRadius={55}
                        outerRadius={85}
                        paddingAngle={2}
                      >
                        {soroterapiaComMovimento.slice(0, 5).map((_, i) => (
                          <Cell key={i} fill={chartColors[i % chartColors.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                ) : topProceduresVolume.length > 0 ? (
                  <p className="text-sm text-gray-400 text-center px-4">
                    Soroterapias cadastradas, sem movimento em {filterLabel}.
                  </p>
                ) : (
                  <p className="text-sm text-gray-400">Nenhuma soroterapia cadastrada</p>
                )}
              </div>
              {topProceduresVolume.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 justify-center">
                  {topProceduresVolume.slice(0, 5).map((proc, i) => (
                    <div key={i} className="flex items-center gap-1.5 text-xs text-gray-600 dark:text-gray-400">
                      <span
                        className="w-2 h-2 rounded-full"
                        style={{ backgroundColor: chartColors[i % chartColors.length] }}
                      />
                      {proc.name}
                      {proc.count > 0 ? ` (${proc.count})` : " — 0 no período"}
                    </div>
                  ))}
                </div>
              )}
            </ChartCard>
          </div>
        </div>
      )}
    </ClinicaBelezaShell>
  );
}
