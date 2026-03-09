'use client';

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';

const ETAPAS_PADRAO = [
  { stage: 'Prospecção', value: 0 },
  { stage: 'Qualificação', value: 0 },
  { stage: 'Proposta', value: 0 },
  { stage: 'Negociação', value: 0 },
  { stage: 'Fechado (ganho)', value: 0 },
];

interface SalesChartProps {
  data?: { name: string; valor: number; quantidade?: number }[];
  title?: string;
}

export default function SalesChart({ data, title = 'Pipeline por etapa' }: SalesChartProps) {
  const hasData = data && data.length > 0;
  const chartData = hasData
    ? data.map((d) => ({
          stage: d.name,
          value: d.valor,
          Valor: d.valor,
          Oportunidades: d.quantidade ?? 0,
        }))
      : ETAPAS_PADRAO;

  return (
    <div className="bg-blue-50/40 dark:bg-blue-900/10 rounded-2xl border-2 border-blue-200 dark:border-blue-800 border-l-4 border-l-blue-500 shadow-md p-6">
      {title && (
        <h2 className="text-lg font-semibold text-blue-800 dark:text-blue-200 mb-5">
          {title}
        </h2>
      )}
      <div style={{ width: '100%', height: 320 }} className="bg-white/60 dark:bg-slate-800/60 rounded-xl p-3">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 12, right: 12, left: 0, bottom: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#94a3b8" strokeOpacity={0.4} vertical={false} />
            <XAxis
              dataKey="stage"
              tick={{ fontSize: 12, fill: '#1e40af' }}
              axisLine={{ stroke: '#3b82f6', strokeWidth: 1 }}
              tickLine={false}
              className="text-blue-800 dark:text-blue-300"
            />
            <YAxis
              tick={{ fontSize: 11, fill: '#1e40af' }}
              tickFormatter={(v) => (v >= 1000 ? `R$${v / 1000}k` : `R$${v}`)}
              axisLine={false}
              tickLine={false}
              className="text-blue-800 dark:text-blue-300"
            />
            <Tooltip
              formatter={(value: number | undefined) => [
                value != null
                  ? new Intl.NumberFormat('pt-BR', {
                      style: 'currency',
                      currency: 'BRL',
                      minimumFractionDigits: 0,
                    }).format(value)
                  : '',
                'Valor',
              ]}
              contentStyle={{
                backgroundColor: 'white',
                border: '1px solid rgba(0,0,0,0.08)',
                borderRadius: '12px',
                boxShadow: '0 10px 25px -5px rgba(0,0,0,0.1), 0 8px 10px -6px rgba(0,0,0,0.06)',
                padding: '12px 16px',
              }}
              labelStyle={{ fontWeight: 600, marginBottom: 4 }}
            />
            <Legend wrapperStyle={{ paddingTop: 8 }} />
            <Bar
              dataKey="value"
              fill="#2563eb"
              radius={[8, 8, 0, 0]}
              name="Valor (R$)"
              maxBarSize={56}
              minPointSize={3}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
