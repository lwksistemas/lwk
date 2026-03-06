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
          stage: d.name.replace(/_/g, ' '),
          value: d.valor,
          Valor: d.valor,
          Oportunidades: d.quantidade ?? 0,
        }))
      : ETAPAS_PADRAO;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
      {title && (
        <h2 className="text-lg font-semibold text-gray-800 dark:text-white mb-4">
          {title}
        </h2>
      )}
      <div style={{ width: '100%', height: 300 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-600" />
            <XAxis
              dataKey="stage"
              tick={{ fontSize: 11 }}
              className="text-gray-600 dark:text-gray-400"
            />
            <YAxis
              tick={{ fontSize: 11 }}
              tickFormatter={(v) => (v >= 1000 ? `R$${v / 1000}k` : `R$${v}`)}
              className="text-gray-600 dark:text-gray-400"
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
                '',
              ]}
              contentStyle={{
                backgroundColor: 'hsl(var(--card))',
                border: '1px solid hsl(var(--border))',
                borderRadius: '8px',
              }}
            />
            <Legend />
            <Bar dataKey="value" fill="hsl(var(--primary))" radius={[6, 6, 0, 0]} name="Valor (R$)" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
