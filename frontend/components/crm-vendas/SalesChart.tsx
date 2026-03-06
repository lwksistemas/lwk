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

interface SalesChartProps {
  data: { name: string; valor: number; quantidade?: number }[];
  title?: string;
}

export default function SalesChart({ data, title = 'Pipeline por etapa' }: SalesChartProps) {
  if (!data?.length) return null;

  const chartData = data.map((d) => ({
    name: d.name.replace(/_/g, ' '),
    Valor: d.valor,
    Oportunidades: d.quantidade ?? 0,
  }));

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow border border-gray-100 dark:border-gray-700 p-4">
      {title && (
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-200 mb-4">
          {title}
        </h3>
      )}
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-600" />
            <XAxis
              dataKey="name"
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
            <Bar dataKey="Valor" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} name="Valor (R$)" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
