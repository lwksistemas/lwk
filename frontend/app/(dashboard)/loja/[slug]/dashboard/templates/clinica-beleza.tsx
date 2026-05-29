'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { CalendarDays, Users, TrendingUp, Activity } from 'lucide-react';
import { ClinicaBelezaShell } from '@/components/clinica-beleza/ClinicaBelezaShell';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell,
} from 'recharts';
import { LojaInfo } from '@/types/dashboard';
import { useClinicaBelezaDark } from '@/hooks/useClinicaBelezaDark';
import {
  getClinicaBelezaBaseUrl,
  getClinicaBelezaHeaders,
} from '@/lib/clinica-beleza-api';

// ─── Types ───────────────────────────────────────────────────────────────────

interface DashboardStats {
  appointments_today: number;
  appointments_yesterday?: number;
  patients_total: number;
  procedures_total: number;
  revenue_month: number;
  revenue_today?: number;
  sessions_month?: number;
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
  statistics: DashboardStats;
  next_appointments: Appointment[];
  revenue_last_7_days?: RevenueDay[];
  top_procedures?: TopProcedure[];
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

const STATUS_COLORS: Record<string, string> = {
  SCHEDULED: 'bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300',
  CONFIRMED: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300',
  PENDING: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300',
  COMPLETED: 'bg-teal-100 text-teal-700 dark:bg-teal-900/40 dark:text-teal-300',
  CANCELLED: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300',
};

const STATUS_LABELS: Record<string, string> = {
  SCHEDULED: 'Agendado',
  CONFIRMED: 'Confirmado',
  PENDING: 'Pendente',
  COMPLETED: 'Concluído',
  CANCELLED: 'Cancelado',
};

const CHART_COLORS = ['#a855f7', '#ec4899', '#f59e0b', '#10b981', '#3b82f6'];

function formatCurrency(value: number): string {
  return value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

function formatDate(): string {
  return new Date().toLocaleDateString('pt-BR', {
    weekday: 'long', day: 'numeric', month: 'long', year: 'numeric',
  });
}

// ─── Sub-components ──────────────────────────────────────────────────────────

function StatCard({ title, value, icon: Icon, subtitle, color }: {
  title: string; value: string | number; icon: React.ElementType;
  subtitle?: string; color: string;
}) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm text-gray-500 dark:text-gray-400 font-medium">{title}</span>
        <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${color}`}>
          <Icon className="w-5 h-5 text-white" />
        </div>
      </div>
      <p className="text-2xl font-bold text-gray-900 dark:text-white">{value}</p>
      {subtitle && <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">{subtitle}</p>}
    </div>
  );
}

function ChartCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden relative z-0">
      <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4">{title}</h3>
      <div className="relative overflow-hidden">{children}</div>
    </div>
  );
}

function AppointmentItem({ appt, slug }: { appt: Appointment; slug: string }) {
  const statusClass = STATUS_COLORS[appt.status] || STATUS_COLORS.PENDING;
  const statusLabel = STATUS_LABELS[appt.status] || appt.status;
  return (
    <div className="flex items-center justify-between py-3 border-b border-gray-50 dark:border-gray-700 last:border-0">
      <div className="flex items-center gap-3">
        <span className="text-xs font-mono text-gray-400 dark:text-gray-500 w-12">
          {appt.time || appt.date?.slice(11, 16) || '--:--'}
        </span>
        <div>
          <p className="text-sm font-medium text-gray-800 dark:text-gray-200">{appt.patient_name}</p>
          <p className="text-xs text-gray-400 dark:text-gray-500">{appt.procedure_name}</p>
        </div>
      </div>
      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${statusClass}`}>
        {statusLabel}
      </span>
    </div>
  );
}

// ─── Main Component ──────────────────────────────────────────────────────────

export default function DashboardClinicaBeleza({ loja, onLogout }: { loja: LojaInfo; onLogout?: () => void }) {
  const params = useParams();
  const slug = (params?.slug as string) || loja?.slug || '';
  const [data, setData] = useState<DashboardData | null>(null);
  const [financial, setFinancial] = useState<FinancialSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [darkMode] = useClinicaBelezaDark();

  useEffect(() => {
    if (!loja?.id && !loja?.slug) return;
    fetchData();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loja?.id, loja?.slug]);

  async function fetchData() {
    setLoading(true);
    try {
      const base = getClinicaBelezaBaseUrl();
      const headers = getClinicaBelezaHeaders() as Record<string, string>;
      const [dashRes, finRes] = await Promise.all([
        fetch(`${base}/dashboard/`, { headers }),
        fetch(`${base}/financeiro/resumo/`, { headers }).catch(() => null),
      ]);
      if (dashRes.ok) {
        const json = await dashRes.json();
        setData(json);
      }
      if (finRes && finRes.ok) {
        const finJson = await finRes.json();
        setFinancial(finJson);
      }
    } catch (err) {
      console.error('Dashboard fetch error:', err);
    } finally {
      setLoading(false);
    }
  }

  const stats = data?.statistics;
  const appointments = data?.next_appointments || [];
  const revenueData = data?.revenue_last_7_days || [];
  const topProcedures = data?.top_procedures || [];

  const appointmentsChange = stats?.appointments_yesterday
    ? Math.round(((stats.appointments_today - stats.appointments_yesterday) / (stats.appointments_yesterday || 1)) * 100)
    : null;

  return (
    <ClinicaBelezaShell loja={loja} onLogout={onLogout}>
        <header className="sticky top-0 z-20 bg-white/80 dark:bg-gray-800/80 backdrop-blur-md border-b border-gray-100 dark:border-gray-700 px-4 sm:px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Bem-vinda, {loja?.nome?.split(' ')[0] || 'Usuária'}! 👋
              </p>
            </div>
            <p className="hidden sm:block text-xs text-gray-400 dark:text-gray-500 capitalize">{formatDate()}</p>
          </div>
          <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
            Aqui está o resumo da sua clínica hoje.
          </p>
        </header>

        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="w-8 h-8 border-4 border-purple-200 border-t-purple-600 rounded-full animate-spin" />
          </div>
        ) : (
          <div className="p-4 sm:p-6 space-y-6 max-w-7xl mx-auto">
            {/* Stat Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <StatCard
                title="Atendimentos hoje"
                value={stats?.appointments_today ?? 0}
                icon={CalendarDays}
                color="bg-purple-500"
                subtitle={appointmentsChange !== null ? `${appointmentsChange >= 0 ? '+' : ''}${appointmentsChange}% vs ontem` : undefined}
              />
              <StatCard
                title="Faturamento hoje"
                value={formatCurrency(stats?.revenue_today ?? 0)}
                icon={TrendingUp}
                color="bg-pink-500"
              />
              <StatCard
                title="Pacientes ativos"
                value={stats?.patients_total ?? 0}
                icon={Users}
                color="bg-blue-500"
              />
              <StatCard
                title="Sessões realizadas"
                value={stats?.sessions_month ?? stats?.procedures_total ?? 0}
                icon={Activity}
                color="bg-teal-500"
                subtitle="Este mês"
              />
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <ChartCard title="Faturamento (últimos 7 dias)">
                <div className="h-56">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={revenueData}>
                      <CartesianGrid strokeDasharray="3 3" stroke={darkMode ? '#374151' : '#f3f4f6'} />
                      <XAxis dataKey="day" tick={{ fontSize: 11 }} stroke={darkMode ? '#6b7280' : '#9ca3af'} />
                      <YAxis tick={{ fontSize: 11 }} stroke={darkMode ? '#6b7280' : '#9ca3af'} tickFormatter={(v) => `R$${(v / 1000).toFixed(0)}k`} />
                      <Tooltip formatter={(v) => formatCurrency(Number(v))} labelStyle={{ color: '#6b7280' }} />
                      <Line type="monotone" dataKey="value" stroke="#a855f7" strokeWidth={2.5} dot={{ r: 4, fill: '#a855f7' }} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </ChartCard>

              <ChartCard title="Top 5 Procedimentos">
                <div className="h-56 flex items-center justify-center">
                  {topProcedures.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={topProcedures.slice(0, 5)}
                          dataKey="count"
                          nameKey="name"
                          cx="50%"
                          cy="50%"
                          innerRadius={50}
                          outerRadius={80}
                          paddingAngle={3}
                        >
                          {topProcedures.slice(0, 5).map((_, i) => (
                            <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                  ) : (
                    <p className="text-sm text-gray-400 dark:text-gray-500">Sem dados disponíveis</p>
                  )}
                </div>
                {topProcedures.length > 0 && (
                  <div className="mt-2 space-y-1">
                    {topProcedures.slice(0, 5).map((proc, i) => (
                      <div key={i} className="flex items-center gap-2 text-xs">
                        <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: CHART_COLORS[i] }} />
                        <span className="text-gray-600 dark:text-gray-400 truncate flex-1">{proc.name}</span>
                        <span className="text-gray-500 dark:text-gray-400 font-medium">{proc.count}</span>
                      </div>
                    ))}
                  </div>
                )}
              </ChartCard>
            </div>

            {/* Bottom Row */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              {/* Próximos agendamentos */}
              <div className="bg-white dark:bg-gray-800 rounded-2xl p-5 shadow-sm border border-gray-100 dark:border-gray-700">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">Próximos agendamentos</h3>
                  <Link
                    href={`/loja/${slug}/agenda`}
                    className="text-xs text-purple-600 dark:text-purple-400 hover:underline font-medium"
                  >
                    Ver agenda →
                  </Link>
                </div>
                {appointments.length > 0 ? (
                  <div className="divide-y divide-gray-50 dark:divide-gray-700">
                    {appointments.slice(0, 5).map((appt) => (
                      <AppointmentItem key={appt.id} appt={appt} slug={slug} />
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-gray-400 dark:text-gray-500 text-center py-6">
                    Nenhum agendamento próximo
                  </p>
                )}
              </div>

              {/* Procedimentos mais realizados */}
              <div className="bg-white dark:bg-gray-800 rounded-2xl p-5 shadow-sm border border-gray-100 dark:border-gray-700">
                <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4">
                  Procedimentos mais realizados (mês)
                </h3>
                {topProcedures.length > 0 ? (
                  <div className="space-y-3">
                    {topProcedures.slice(0, 5).map((proc, i) => {
                      const max = topProcedures[0]?.count || 1;
                      const pct = Math.round((proc.count / max) * 100);
                      return (
                        <div key={i}>
                          <div className="flex justify-between text-xs mb-1">
                            <span className="text-gray-600 dark:text-gray-400 truncate">{proc.name}</span>
                            <span className="text-gray-500 dark:text-gray-400 font-medium">{proc.count}</span>
                          </div>
                          <div className="h-2 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
                            <div
                              className="h-full rounded-full transition-all"
                              style={{ width: `${pct}%`, backgroundColor: CHART_COLORS[i % CHART_COLORS.length] }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <p className="text-sm text-gray-400 dark:text-gray-500 text-center py-6">Sem dados</p>
                )}
              </div>

              {/* Resumo financeiro */}
              <div className="bg-white dark:bg-gray-800 rounded-2xl p-5 shadow-sm border border-gray-100 dark:border-gray-700">
                <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4">
                  Resumo financeiro (mês)
                </h3>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500 dark:text-gray-400">Faturamento</span>
                    <span className="text-sm font-semibold text-gray-800 dark:text-gray-200">
                      {formatCurrency(financial?.faturamento ?? stats?.revenue_month ?? 0)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500 dark:text-gray-400">Despesas</span>
                    <span className="text-sm font-semibold text-red-500">
                      {formatCurrency(financial?.despesas ?? 0)}
                    </span>
                  </div>
                  <hr className="border-gray-100 dark:border-gray-700" />
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Lucro líquido</span>
                    <span className="text-base font-bold text-green-600 dark:text-green-400">
                      {formatCurrency(financial?.lucro ?? (financial?.faturamento ?? stats?.revenue_month ?? 0) - (financial?.despesas ?? 0))}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
    </ClinicaBelezaShell>
  );
}
