'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { CalendarDays, Users, TrendingUp, Activity, CalendarRange } from 'lucide-react';
import { ClinicaBelezaShell } from '@/components/clinica-beleza/ClinicaBelezaShell';
import { CLINICA_BELEZA_PRIMARY } from '@/components/clinica-beleza/clinica-beleza-nav';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell,
} from 'recharts';
import { LojaInfo } from '@/types/dashboard';
import { useClinicaBelezaDark } from '@/hooks/useClinicaBelezaDark';
import { formatCurrency } from '@/lib/financeiro-helpers';
import { CLINICA_AGENDA_STATUS_LABEL } from '@/lib/clinica-beleza-constants';
import { clinicaBelezaFetch } from '@/lib/clinica-beleza-api';

interface DashboardStats {
  appointments_today: number;
  appointments_yesterday?: number;
  patients_total: number;
  procedures_total: number;
  revenue_month: number;
  revenue_today?: number;
  sessions_month?: number;
}

interface DashboardFilter {
  mes: number;
  ano: number;
  label: string;
  is_current_month: boolean;
}

interface Appointment {
  id: number;
  date: string;
  time?: string;
  patient_name: string;
  procedure_name: string;
  professional_name: string;
  status: string;
}

interface RevenueDay {
  day: string;
  value: number;
}

interface TopProcedure {
  name: string;
  count: number;
}

interface FinancialSummary {
  faturamento: number;
  despesas: number;
  lucro: number;
}

interface DashboardData {
  filter?: DashboardFilter;
  statistics: DashboardStats;
  next_appointments: Appointment[];
  revenue_last_7_days?: RevenueDay[];
  top_procedures?: TopProcedure[];
  top_procedures_volume?: TopProcedure[];
}

const STATUS_COLORS: Record<string, string> = {
  SCHEDULED: 'bg-gray-100 text-gray-700',
  CONFIRMED: 'bg-green-100 text-green-700',
  PENDING: 'bg-amber-100 text-amber-800',
  COMPLETED: 'bg-teal-100 text-teal-700',
  CANCELLED: 'bg-red-100 text-red-700',
};

const CHART_COLORS = [CLINICA_BELEZA_PRIMARY, '#A64D63', '#C4727E', '#E8A0B0', '#D4A574'];

function currentMesAnoValue(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
}

function parseMesAno(value: string): { mes: number; ano: number } {
  const [anoStr, mesStr] = value.split('-');
  return { ano: Number(anoStr), mes: Number(mesStr) };
}

function pctChange(current: number, previous: number): string | null {
  if (!previous) return null;
  const pct = Math.round(((current - previous) / previous) * 100);
  return `${pct >= 0 ? '+' : ''}${pct}%`;
}

function StatCard({
  title,
  value,
  icon: Icon,
  changeLabel,
  positive,
}: {
  title: string;
  value: string | number;
  icon: React.ElementType;
  changeLabel?: string | null;
  positive?: boolean;
}) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700">
      <div className="flex items-start justify-between gap-2 mb-2">
        <span className="text-sm text-gray-500 dark:text-gray-400">{title}</span>
        <div
          className="w-9 h-9 rounded-lg flex items-center justify-center shrink-0"
          style={{ backgroundColor: `${CLINICA_BELEZA_PRIMARY}18` }}
        >
          <Icon className="w-4 h-4" style={{ color: CLINICA_BELEZA_PRIMARY }} />
        </div>
      </div>
      <p className="text-2xl font-bold text-gray-900 dark:text-white">{value}</p>
      {changeLabel && (
        <p
          className={`text-xs mt-1 font-medium ${
            positive === false ? 'text-red-500' : 'text-emerald-600'
          }`}
        >
          {changeLabel}
        </p>
      )}
    </div>
  );
}

function ChartCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
      <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-200 mb-4">{title}</h3>
      <div className="relative overflow-hidden">{children}</div>
    </div>
  );
}

function AppointmentItem({ appt }: { appt: Appointment }) {
  const statusClass = STATUS_COLORS[appt.status] || STATUS_COLORS.PENDING;
  const statusLabel = CLINICA_AGENDA_STATUS_LABEL[appt.status] || appt.status;
  return (
    <div className="flex items-center justify-between py-3 border-b border-gray-50 dark:border-gray-700 last:border-0">
      <div className="flex items-center gap-3 min-w-0">
        <span className="text-xs font-semibold text-gray-500 w-11 shrink-0">
          {appt.time || appt.date?.slice(11, 16) || '--:--'}
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

export default function DashboardClinicaBeleza({ loja, onLogout }: { loja: LojaInfo; onLogout?: () => void }) {
  const params = useParams();
  const slug = (params?.slug as string) || loja?.slug || '';
  const [data, setData] = useState<DashboardData | null>(null);
  const [financial, setFinancial] = useState<FinancialSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [mesAno, setMesAno] = useState(currentMesAnoValue);
  const [darkMode] = useClinicaBelezaDark();

  const mesAnoMax = useMemo(() => currentMesAnoValue(), []);

  const fetchData = useCallback(async () => {
    if (!loja?.id && !loja?.slug) return;
    setLoading(true);
    try {
      const { mes, ano } = parseMesAno(mesAno);
      const lojaCtx = loja?.id || loja?.slug ? { id: loja.id, slug: loja.slug || slug } : undefined;
      const qs = `period=proximos&mes=${mes}&ano=${ano}`;
      const [dashRes, finRes] = await Promise.all([
        clinicaBelezaFetch(`/dashboard/?${qs}`, {}, lojaCtx),
        clinicaBelezaFetch(`/financeiro/resumo/?mes=${mes}&ano=${ano}`, {}, lojaCtx).catch(() => null),
      ]);
      if (dashRes.ok) setData(await dashRes.json());
      else setData(null);
      if (finRes?.ok) setFinancial(await finRes.json());
    } catch (err) {
      console.error('Dashboard fetch error:', err);
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [loja?.id, loja?.slug, loja.slug, slug, mesAno]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const stats = data?.statistics;
  const filterLabel = data?.filter?.label ?? 'Este mês';
  const isCurrentMonth = data?.filter?.is_current_month ?? true;
  const appointments = data?.next_appointments || [];
  const revenueData = data?.revenue_last_7_days || [];
  const topProcedures = data?.top_procedures || [];
  const topProceduresVolume = data?.top_procedures_volume || [];
  const soroterapiaComMovimento = topProceduresVolume.filter((p) => p.count > 0);

  const apptChange = stats?.appointments_yesterday != null
    ? pctChange(stats.appointments_today, stats.appointments_yesterday)
    : null;

  const displayName = loja?.nome?.split(' ')[0] || 'Usuária';
  const faturamentoChartTitle = isCurrentMonth
    ? `Faturamento (${filterLabel})`
    : `Faturamento — ${filterLabel}`;

  return (
    <ClinicaBelezaShell loja={loja} onLogout={onLogout}>
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div
            className="w-8 h-8 border-4 rounded-full animate-spin"
            style={{ borderColor: `${CLINICA_BELEZA_PRIMARY}33`, borderTopColor: CLINICA_BELEZA_PRIMARY }}
          />
        </div>
      ) : (
        <div className="p-4 md:p-6 lg:p-8 space-y-6 w-full">
          {/* Header com título + filtro de mês */}
          <div className="flex items-center justify-between">
            <h1 className="text-xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
            <div className="flex items-center gap-2 shrink-0">
              <CalendarRange className="w-4 h-4 text-gray-400 hidden sm:block" aria-hidden />
              <label htmlFor="dashboard-mes-ano" className="sr-only">
                Filtrar mês do dashboard
              </label>
              <input
                id="dashboard-mes-ano"
                type="month"
                value={mesAno}
                max={mesAnoMax}
                onChange={(e) => e.target.value && setMesAno(e.target.value)}
                className="px-3 py-2 text-sm border border-gray-200 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-800 text-gray-900 dark:text-gray-100"
              />
            </div>
          </div>

          {/* Cards de indicadores */}
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
            <StatCard
              title="Atendimentos hoje"
              value={stats?.appointments_today ?? 0}
              icon={CalendarDays}
              changeLabel={apptChange ? `${apptChange} vs ontem` : undefined}
              positive={apptChange ? !apptChange.startsWith('-') : true}
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

          {/* Próximos agendamentos + Procedimentos + Financeiro */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-200">Próximos agendamentos</h3>
                <Link
                  href={`/loja/${slug}/agenda`}
                  className="text-xs font-medium hover:underline"
                  style={{ color: CLINICA_BELEZA_PRIMARY }}
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
                            style={{ width: `${pct}%`, backgroundColor: CHART_COLORS[i % CHART_COLORS.length] }}
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
                  <span className="font-semibold text-red-500">
                    {formatCurrency(financial?.despesas ?? 0)}
                  </span>
                </div>
                <hr className="border-gray-100 dark:border-gray-700" />
                <div className="flex justify-between text-sm">
                  <span className="font-medium text-gray-700 dark:text-gray-300">Lucro líquido</span>
                  <span className="font-bold text-emerald-600">
                    {formatCurrency(
                      financial?.lucro ??
                        (financial?.faturamento ?? stats?.revenue_month ?? 0) - (financial?.despesas ?? 0)
                    )}
                  </span>
                </div>
              </div>
              <Link
                href={`/loja/${slug}/clinica-beleza/financeiro`}
                className="mt-5 block w-full text-center py-3 rounded-lg text-sm font-semibold text-white transition-opacity hover:opacity-90"
                style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
              >
                Ver relatório financeiro
              </Link>
            </div>
          </div>

          {/* Gráficos no final */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <ChartCard title={faturamentoChartTitle}>
              <div className="h-56">
                {revenueData.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={revenueData}>
                      <CartesianGrid strokeDasharray="3 3" stroke={darkMode ? '#374151' : '#f0f0f0'} />
                      <XAxis dataKey="day" tick={{ fontSize: 11 }} stroke="#9ca3af" />
                      <YAxis tick={{ fontSize: 11 }} stroke="#9ca3af" tickFormatter={(v) => `R$${(v / 1000).toFixed(0)}k`} />
                      <Tooltip formatter={(v) => formatCurrency(Number(v))} />
                      <Line
                        type="monotone"
                        dataKey="value"
                        stroke={CLINICA_BELEZA_PRIMARY}
                        strokeWidth={2.5}
                        dot={{ r: 3, fill: CLINICA_BELEZA_PRIMARY }}
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
                          <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
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
                      <span className="w-2 h-2 rounded-full" style={{ backgroundColor: CHART_COLORS[i % CHART_COLORS.length] }} />
                      {proc.name}
                      {proc.count > 0 ? ` (${proc.count})` : ' — 0 no período'}
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
