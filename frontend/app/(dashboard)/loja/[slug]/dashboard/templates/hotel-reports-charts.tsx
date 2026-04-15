'use client';

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

export type HotelRelatorios = {
  receita_diaria: Array<{ data: string; valor: number }>;
  receita_total_30d: number;
  ocupacao_por_tipo: Array<{ tipo: string; total: number; ocupados: number; ocupacao_percent: number }>;
  indicadores: {
    reservas_mes: number;
    no_show_mes: number;
    cancelamentos_mes: number;
    tarefas_concluidas_mes: number;
    indice_operacional: number;
  };
};

function formatMoney(v: number): string {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }).format(v);
}

function formatDayLabel(iso: string): string {
  try {
    const [y, m, d] = iso.split('-').map(Number);
    const dt = new Date(y, m - 1, d);
    return dt.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' });
  } catch {
    return iso;
  }
}

export default function HotelReportsCharts({
  loading,
  accent,
  relatorios,
}: {
  loading: boolean;
  accent: string;
  relatorios?: HotelRelatorios | null;
}) {
  if (loading) {
    return (
      <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800">
        <div className="h-[280px] animate-pulse rounded-xl bg-gray-100 dark:bg-gray-900" />
      </div>
    );
  }

  const receita = relatorios?.receita_diaria?.length
    ? relatorios.receita_diaria.map((r) => ({
        ...r,
        label: formatDayLabel(r.data),
      }))
    : [];

  const tipos = relatorios?.ocupacao_por_tipo?.length
    ? relatorios.ocupacao_por_tipo.map((t) => ({
        name:
          t.tipo.length > 18 ? `${t.tipo.slice(0, 16)}…` : t.tipo,
        fullName: t.tipo,
        pct: t.ocupacao_percent,
        ocupados: t.ocupados,
        total: t.total,
      }))
    : [];

  const ind = relatorios?.indicadores;

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Relatórios e gráficos</h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Receita por dia (últimos 30 dias), ocupação por categoria de quarto e indicadores operacionais — alinhado ao padrão dos outros módulos.
          </p>
        </div>
        {relatorios != null ? (
          <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Receita 30 dias:{' '}
            <span style={{ color: accent }}>{formatMoney(relatorios.receita_total_30d)}</span>
          </p>
        ) : null}
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <IndicadorCard
          label="Reservas (mês)"
          value={ind?.reservas_mes ?? '—'}
          hint="Check-in no mês"
        />
        <IndicadorCard
          label="No-show"
          value={ind?.no_show_mes ?? '—'}
          hint="No mês corrente"
        />
        <IndicadorCard
          label="Cancelamentos"
          value={ind?.cancelamentos_mes ?? '—'}
          hint="No mês corrente"
        />
        <IndicadorCard
          label="Índice operacional"
          value={ind != null ? `${ind.indice_operacional}/10` : '—'}
          hint="Penaliza no-show e cancelamentos"
          accent={accent}
        />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="rounded-2xl border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
          <p className="mb-1 text-sm font-semibold text-gray-900 dark:text-white">Receita por período</p>
          <p className="mb-3 text-xs text-gray-500 dark:text-gray-400">Soma de valor total das reservas por dia de check-in (exc. canceladas/no-show).</p>
          {receita.length === 0 ? (
            <p className="py-12 text-center text-sm text-gray-500 dark:text-gray-400">Sem reservas no período para exibir.</p>
          ) : (
            <div className="h-[240px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={receita} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />
                  <XAxis
                    dataKey="label"
                    tick={{ fontSize: 10 }}
                    interval="preserveStartEnd"
                    minTickGap={24}
                    className="text-gray-500"
                  />
                  <YAxis
                    tick={{ fontSize: 10 }}
                    tickFormatter={(v) =>
                      Number(v) >= 1000
                        ? `R$ ${(Number(v) / 1000).toFixed(1)}k`
                        : `R$ ${Math.round(Number(v))}`
                    }
                    className="text-gray-500"
                  />
                  <Tooltip
                    formatter={(value: number) => [formatMoney(value), 'Receita']}
                    labelFormatter={(_, payload) => {
                      const p = payload?.[0]?.payload as { data?: string } | undefined;
                      return p?.data ? formatDayLabel(p.data) : '';
                    }}
                    contentStyle={{ borderRadius: '12px', border: '1px solid #e5e7eb' }}
                  />
                  <Line type="monotone" dataKey="valor" stroke={accent} strokeWidth={2} dot={false} activeDot={{ r: 4 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        <div className="rounded-2xl border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
          <p className="mb-1 text-sm font-semibold text-gray-900 dark:text-white">Ocupação por categoria</p>
          <p className="mb-3 text-xs text-gray-500 dark:text-gray-400">Percentual de quartos ocupados por tipo (campo &quot;tipo&quot; do quarto).</p>
          {tipos.length === 0 ? (
            <p className="py-12 text-center text-sm text-gray-500 dark:text-gray-400">Cadastre quartos com tipo para ver o gráfico.</p>
          ) : (
            <div className="h-[240px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={tipos} layout="vertical" margin={{ top: 8, right: 16, left: 8, bottom: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal className="stroke-gray-200 dark:stroke-gray-700" />
                  <XAxis type="number" domain={[0, 100]} tickFormatter={(v) => `${v}%`} tick={{ fontSize: 10 }} />
                  <YAxis type="category" dataKey="name" width={100} tick={{ fontSize: 10 }} />
                  <Tooltip
                    formatter={(value: number, _name, item) => [
                      `${value}% (${(item?.payload as { ocupados: number; total: number }).ocupados}/${
                        (item?.payload as { ocupados: number; total: number }).total
                      } quartos)`,
                      'Ocupação',
                    ]}
                    contentStyle={{ borderRadius: '12px', border: '1px solid #e5e7eb' }}
                  />
                  <Bar dataKey="pct" radius={[0, 6, 6, 0]} name="Ocupação %">
                    {tipos.map((_, i) => (
                      <Cell key={i} fill={i % 2 === 0 ? accent : `${accent}cc`} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      </div>

      <div className="rounded-xl border border-gray-100 bg-gray-50/80 px-4 py-3 text-xs text-gray-600 dark:border-gray-700 dark:bg-gray-900/30 dark:text-gray-400">
        <strong className="text-gray-800 dark:text-gray-200">Satisfação / qualidade:</strong> ainda não há pesquisa de NPS no sistema; usamos o{' '}
        <span className="font-medium">índice operacional</span> (0–10) com base em no-show e cancelamentos no mês, e exibimos{' '}
        <span className="font-medium">tarefas de governança concluídas</span> no mês:{' '}
        <span style={{ color: accent }}>{ind?.tarefas_concluidas_mes ?? 0}</span>.
      </div>
    </div>
  );
}

function IndicadorCard({
  label,
  value,
  hint,
  accent,
}: {
  label: string;
  value: string | number;
  hint: string;
  accent?: string;
}) {
  return (
    <div className="rounded-xl border border-gray-200 bg-white px-3 py-2.5 shadow-sm dark:border-gray-700 dark:bg-gray-800">
      <p className="text-[10px] font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">{label}</p>
      <p className="mt-0.5 text-xl font-bold tabular-nums" style={accent ? { color: accent } : undefined}>
        {value}
      </p>
      <p className="text-[10px] text-gray-500 dark:text-gray-500">{hint}</p>
    </div>
  );
}
