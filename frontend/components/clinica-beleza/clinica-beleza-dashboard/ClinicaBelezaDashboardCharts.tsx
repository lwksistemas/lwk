"use client";

import type { ReactNode } from "react";
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
import { formatCurrency } from "@/lib/financeiro-helpers";
import type { RevenueDay, TopProcedure } from "./clinica-beleza-dashboard-types";

function ChartCard({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
      <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-200 mb-4">{title}</h3>
      <div className="relative overflow-hidden">{children}</div>
    </div>
  );
}

export type ClinicaBelezaDashboardChartsProps = {
  faturamentoChartTitle: string;
  filterLabel: string;
  revenueData: RevenueDay[];
  revenueComValor: boolean;
  topProceduresVolume: TopProcedure[];
  soroterapiaComMovimento: TopProcedure[];
  chartColors: string[];
  primary: string;
  darkMode: boolean;
};

export function ClinicaBelezaDashboardCharts({
  faturamentoChartTitle,
  filterLabel,
  revenueData,
  revenueComValor,
  topProceduresVolume,
  soroterapiaComMovimento,
  chartColors,
  primary,
  darkMode,
}: ClinicaBelezaDashboardChartsProps) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <ChartCard title={faturamentoChartTitle}>
        <div className="h-56">
          {revenueComValor ? (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={revenueData}>
                <CartesianGrid strokeDasharray="3 3" stroke={darkMode ? "#374151" : "#f0f0f0"} />
                <XAxis dataKey="day" tick={{ fontSize: 11, fill: darkMode ? "#9ca3af" : "#666" }} stroke="#9ca3af" />
                <YAxis
                  tick={{ fontSize: 11, fill: darkMode ? "#9ca3af" : "#666" }}
                  stroke="#9ca3af"
                  tickFormatter={(v) => `R$${(v / 1000).toFixed(0)}k`}
                />
                <Tooltip
                  formatter={(v) => formatCurrency(Number(v))}
                  contentStyle={
                    darkMode
                      ? { backgroundColor: "#1f2937", border: "1px solid #374151", borderRadius: 8, color: "#f3f4f6" }
                      : undefined
                  }
                  labelStyle={darkMode ? { color: "#f3f4f6" } : undefined}
                  itemStyle={darkMode ? { color: "#f3f4f6" } : undefined}
                />
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
            <p className="text-sm text-gray-400 dark:text-gray-500 text-center py-16">Sem faturamento no período</p>
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
                <Tooltip
                  contentStyle={
                    darkMode
                      ? { backgroundColor: "#1f2937", border: "1px solid #374151", borderRadius: 8, color: "#f3f4f6" }
                      : undefined
                  }
                  labelStyle={darkMode ? { color: "#f3f4f6" } : undefined}
                  itemStyle={darkMode ? { color: "#f3f4f6" } : undefined}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : topProceduresVolume.length > 0 ? (
            <p className="text-sm text-gray-400 dark:text-gray-500 text-center px-4">
              Soroterapias cadastradas, sem movimento em {filterLabel}.
            </p>
          ) : (
            <p className="text-sm text-gray-400 dark:text-gray-500">Nenhuma soroterapia cadastrada</p>
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
  );
}
