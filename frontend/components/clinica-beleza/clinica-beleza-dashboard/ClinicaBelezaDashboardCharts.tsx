"use client";

import type { ReactNode } from "react";
import {
  Bar,
  BarChart,
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
import { percentualDashboard } from "./clinica-beleza-dashboard-utils";
import type { RevenueDay, TopProcedure } from "./clinica-beleza-dashboard-types";

function ChartCard({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl p-4 sm:p-5 shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden min-w-0">
      <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-100 mb-4">{title}</h3>
      <div className="relative overflow-hidden">{children}</div>
    </div>
  );
}

function eixoMoeda(valor: number): string {
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
    maximumFractionDigits: 0,
  }).format(valor);
}

function TooltipFaturamento({
  active,
  payload,
  label,
  primary,
}: {
  active?: boolean;
  payload?: { value?: number }[];
  label?: string;
  primary: string;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-xl bg-white dark:bg-gray-900 shadow-lg border border-gray-100 dark:border-gray-700 px-3 py-2 text-center">
      <p className="text-xs text-gray-500 dark:text-gray-400">{label}</p>
      <p className="text-sm font-semibold" style={{ color: primary }}>
        {formatCurrency(Number(payload[0]?.value ?? 0))}
      </p>
    </div>
  );
}

export type ClinicaBelezaDashboardChartsProps = {
  faturamentoChartTitle: string;
  filterLabel: string;
  revenueData: RevenueDay[];
  revenueComValor: boolean;
  topProcedures: TopProcedure[];
  chartColors: string[];
  primary: string;
  darkMode: boolean;
};

export function ClinicaBelezaDashboardCharts({
  faturamentoChartTitle,
  filterLabel,
  revenueData,
  revenueComValor,
  topProcedures,
  chartColors,
  primary,
  darkMode,
}: ClinicaBelezaDashboardChartsProps) {
  const topCinco = topProcedures.filter((p) => p.count > 0).slice(0, 5);
  const totalProcedimentos = topProcedures.reduce((soma, p) => soma + p.count, 0);
  const maiorFaturamento = revenueData.reduce((maior, dia) => Math.max(maior, dia.value), 0);
  const grade = darkMode ? "#374151" : "#f3f4f6";
  const tick = darkMode ? "#9ca3af" : "#6b7280";

  return (
    <div className="grid grid-cols-1 @min-[980px]:grid-cols-5 gap-3">
      <div className="@min-[980px]:col-span-3 min-w-0">
        <ChartCard title={faturamentoChartTitle}>
          <div className="h-56">
            {revenueComValor ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={revenueData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke={grade} vertical={false} />
                  <XAxis
                    dataKey="day"
                    tick={{ fontSize: 11, fill: tick }}
                    stroke="transparent"
                    minTickGap={18}
                  />
                  <YAxis
                    tick={{ fontSize: 11, fill: tick }}
                    stroke="transparent"
                    tickFormatter={eixoMoeda}
                    width={72}
                  />
                  <Tooltip
                    cursor={{ fill: "color-mix(in srgb, var(--cb-primary, #8B3D52) 8%, transparent)" }}
                    content={<TooltipFaturamento primary={primary} />}
                  />
                  <Bar dataKey="value" radius={[6, 6, 0, 0]} maxBarSize={22}>
                    {revenueData.map((dia, i) => (
                      <Cell
                        key={dia.day || i}
                        fill={
                          dia.value <= 0
                            ? "color-mix(in srgb, var(--cb-primary, #8B3D52) 16%, white)"
                            : dia.value === maiorFaturamento
                              ? primary
                              : "color-mix(in srgb, var(--cb-primary, #8B3D52) 55%, white)"
                        }
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-sm text-gray-400 dark:text-gray-500 text-center py-16">Sem faturamento no período</p>
            )}
          </div>
        </ChartCard>
      </div>

      <div className="@min-[980px]:col-span-2 min-w-0">
        <ChartCard title={`Top 5 procedimentos — ${filterLabel}`}>
          {topCinco.length > 0 ? (
            <div className="flex flex-col sm:flex-row sm:items-center gap-2 min-w-0">
              <div className="h-52 w-full sm:w-[46%] sm:shrink-0">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={topCinco}
                      dataKey="count"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      innerRadius={52}
                      outerRadius={78}
                      paddingAngle={2}
                      stroke="none"
                    >
                      {topCinco.map((_, i) => (
                        <Cell key={i} fill={chartColors[i % chartColors.length]} />
                      ))}
                    </Pie>
                    <Tooltip
                      formatter={(v, nome) => [
                        `${v} (${percentualDashboard(Number(v), totalProcedimentos)}%)`,
                        String(nome),
                      ]}
                      contentStyle={
                        darkMode
                          ? { backgroundColor: "#1f2937", border: "1px solid #374151", borderRadius: 12, color: "#f3f4f6" }
                          : { borderRadius: 12 }
                      }
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <ul className="min-w-0 flex-1 space-y-2">
                {topCinco.map((proc, i) => (
                  <li key={`${proc.name}-${i}`} className="grid grid-cols-[0.65rem_minmax(0,1fr)_auto] items-center gap-2 text-xs text-gray-600 dark:text-gray-300 min-w-0">
                    <span
                      className="w-2.5 h-2.5 rounded-full"
                      style={{ backgroundColor: chartColors[i % chartColors.length] }}
                    />
                    <span className="min-w-0 leading-tight">{proc.name}</span>
                    <span className="shrink-0 tabular-nums font-medium text-gray-800 dark:text-gray-100 text-right">
                      {proc.count} ({percentualDashboard(proc.count, totalProcedimentos)}%)
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <p className="text-sm text-gray-400 dark:text-gray-500 text-center py-16">
              Sem procedimentos realizados em {filterLabel}.
            </p>
          )}
        </ChartCard>
      </div>
    </div>
  );
}
