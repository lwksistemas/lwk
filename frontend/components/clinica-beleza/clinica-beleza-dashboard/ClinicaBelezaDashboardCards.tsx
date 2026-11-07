"use client";

import type { ElementType, ReactNode } from "react";
import Link from "next/link";
import { ChevronRight, Flower2, RefreshCw } from "lucide-react";
import { formatCurrency } from "@/lib/financeiro-helpers";
import { CLINICA_AGENDA_STATUS_LABEL } from "@/lib/clinica-beleza-constants";
import type { DashboardAppointment, TopProcedure } from "./clinica-beleza-dashboard-types";
import { DASHBOARD_STATUS_COLORS } from "./clinica-beleza-dashboard-utils";

const CARD =
  "bg-white dark:bg-gray-800 rounded-2xl p-4 sm:p-5 shadow-sm border border-gray-100 dark:border-gray-700 min-w-0";

const ICONE_FUNDO = "color-mix(in srgb, var(--cb-primary, #8B3D52) 12%, transparent)";
const COR_PRIMARIA = "var(--cb-primary, #8B3D52)";

export function PainelCard({
  title,
  action,
  children,
}: {
  title: string;
  action?: ReactNode;
  children: ReactNode;
}) {
  return (
    <section className={`${CARD} h-full flex flex-col`}>
      <div className="flex items-start justify-between gap-3 mb-4">
        <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-100 leading-snug">{title}</h3>
        {action}
      </div>
      <div className="min-w-0 flex-1">{children}</div>
    </section>
  );
}

export function LinkPainel({ href, children }: { href: string; children: ReactNode }) {
  return (
    <Link href={href} className="text-xs font-medium hover:underline shrink-0 whitespace-nowrap" style={{ color: COR_PRIMARIA }}>
      {children}
    </Link>
  );
}

export function DashboardGreeting({
  saudacao,
  primeiroNome,
  mesAno,
  mesAnoMax,
  rotuloPeriodo,
  loading,
  onMesAno,
  onAtualizar,
}: {
  saudacao: string;
  primeiroNome: string;
  mesAno: string;
  mesAnoMax: string;
  rotuloPeriodo: string;
  loading: boolean;
  onMesAno: (value: string) => void;
  onAtualizar: () => void;
}) {
  const cumprimento = primeiroNome ? `${saudacao}, ${primeiroNome}!` : `${saudacao}!`;
  return (
    <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
      <div className="flex items-center gap-3 min-w-0">
        <div
          className="w-12 h-12 rounded-2xl flex items-center justify-center shrink-0"
          style={{ backgroundColor: ICONE_FUNDO }}
        >
          <Flower2 className="w-6 h-6" style={{ color: COR_PRIMARIA }} aria-hidden />
        </div>
        <div className="min-w-0">
          <h1 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white truncate">{cumprimento}</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">Visão geral da clínica</p>
        </div>
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <label className="relative inline-flex items-center gap-2 px-3 py-2 text-sm border border-gray-200 dark:border-neutral-600 rounded-xl bg-white dark:bg-neutral-800 text-gray-700 dark:text-gray-200 cursor-pointer">
          <span className="text-gray-400">Período:</span>
          <span className="font-medium">{rotuloPeriodo}</span>
          <input
            type="month"
            value={mesAno}
            max={mesAnoMax}
            onChange={(e) => e.target.value && onMesAno(e.target.value)}
            className="absolute inset-0 opacity-0 cursor-pointer"
            aria-label="Filtrar mês do dashboard"
          />
        </label>
        <button
          type="button"
          onClick={onAtualizar}
          disabled={loading}
          className="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium text-white rounded-xl disabled:opacity-50"
          style={{ backgroundColor: COR_PRIMARIA }}
          title="Atualizar"
        >
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
          Atualizar
        </button>
      </div>
    </div>
  );
}

export function StatCard({
  title,
  value,
  icon: Icon,
  changeLabel,
  hintTone = "muted",
  valueTone = "default",
  href,
}: {
  title: string;
  value: string | number;
  icon: ElementType;
  changeLabel?: string | null;
  hintTone?: "positive" | "alert" | "muted";
  valueTone?: "default" | "positive" | "alert";
  href?: string;
}) {
  const valueClass =
    valueTone === "positive"
      ? "text-emerald-600 dark:text-emerald-400"
      : valueTone === "alert"
        ? "text-red-600 dark:text-red-400"
        : "text-gray-900 dark:text-white";
  const hintClass =
    hintTone === "alert"
      ? "text-red-500"
      : hintTone === "positive"
        ? "text-emerald-600 dark:text-emerald-400"
        : "text-gray-400 dark:text-gray-500";

  const corpo = (
    <div className={`${CARD} h-full ${href ? "hover:shadow-md transition-shadow" : ""}`}>
      <div className="flex items-center gap-3 mb-3">
        <div
          className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
          style={{ backgroundColor: ICONE_FUNDO }}
        >
          <Icon className="w-5 h-5" style={{ color: COR_PRIMARIA }} aria-hidden />
        </div>
        <span className="text-sm text-gray-500 dark:text-gray-400 leading-snug flex-1 min-w-0">{title}</span>
        {href && <ChevronRight className="w-4 h-4 text-gray-300 shrink-0" aria-hidden />}
      </div>
      <p className={`text-xl sm:text-2xl font-bold tabular-nums break-words ${valueClass}`}>{value}</p>
      {changeLabel && <p className={`text-xs mt-1 font-medium ${hintClass}`}>{changeLabel}</p>}
    </div>
  );

  if (!href) return corpo;
  return (
    <Link href={href} className="block h-full min-w-0">
      {corpo}
    </Link>
  );
}

export function AppointmentItem({ appt, href }: { appt: DashboardAppointment; href: string }) {
  const statusClass = DASHBOARD_STATUS_COLORS[appt.status] || DASHBOARD_STATUS_COLORS.PENDING;
  const statusLabel = CLINICA_AGENDA_STATUS_LABEL[appt.status] || appt.status;
  const hora = appt.time || appt.date?.slice(11, 16) || "--:--";

  return (
    <Link
      href={href}
      className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between py-2.5 px-2 -mx-2 rounded-xl border-b border-gray-50 dark:border-gray-700 last:border-0 hover:bg-gray-50 dark:hover:bg-gray-700/40"
      aria-label={`Abrir agendamento de ${appt.patient_name}`}
    >
      <div className="flex items-center gap-3 min-w-0">
        <span
          className="inline-flex items-center justify-center min-w-[3.4rem] px-2 py-1 rounded-lg text-xs font-semibold shrink-0"
          style={{ backgroundColor: ICONE_FUNDO, color: COR_PRIMARIA }}
        >
          {hora}
        </span>
        <div className="min-w-0">
          <p className="text-sm font-semibold text-gray-800 dark:text-gray-100 truncate uppercase tracking-wide">
            {appt.patient_name}
          </p>
          <p className="text-xs text-gray-400 dark:text-gray-500 truncate">{appt.procedure_name}</p>
        </div>
      </div>
      <span className={`text-xs px-2.5 py-1 rounded-full font-medium shrink-0 self-start sm:self-center ${statusClass}`}>
        {statusLabel}
      </span>
    </Link>
  );
}

export function ProcedureBars({
  procedures,
  colors,
}: {
  procedures: TopProcedure[];
  colors: string[];
}) {
  const max = procedures[0]?.count || 1;
  return (
    <div className="space-y-3">
      {procedures.map((proc, i) => {
        const pct = Math.max(4, Math.round((proc.count / max) * 100));
        return (
          <div key={`${proc.name}-${i}`} className="min-w-0">
            <div className="flex justify-between gap-3 text-xs mb-1">
              <span className="text-gray-600 dark:text-gray-300 truncate">{proc.name}</span>
              <span className="text-gray-700 dark:text-gray-200 font-semibold shrink-0 tabular-nums">{proc.count}</span>
            </div>
            <div className="h-2.5 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
              <div
                className="h-full rounded-full"
                style={{ width: `${pct}%`, backgroundColor: colors[i % colors.length] }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}

function textoValor(valor: number, deducao: boolean) {
  if (deducao && valor > 0) return `− ${formatCurrency(valor)}`;
  return formatCurrency(valor);
}

export function ResumoFinanceiroLista({
  faturamento,
  desconto,
  despesas,
  lucro,
  aReceber,
  aPrazo,
}: {
  faturamento: number;
  desconto: number;
  despesas: number;
  lucro: number;
  aReceber: number;
  aPrazo: number;
}) {
  const resultado = [
    { label: "Faturamento", valor: faturamento, deducao: false, destaque: false },
    { label: "Descontos", valor: desconto, deducao: true, destaque: false },
    { label: "Despesas", valor: despesas, deducao: true, destaque: false },
    { label: "Lucro líquido", valor: lucro, deducao: false, destaque: true },
  ];
  const pendencias = [
    { label: "A receber", valor: aReceber },
    { label: "A prazo", valor: aPrazo },
  ];

  return (
    <div className="space-y-1">
      {resultado.map((linha) => (
        <div
          key={linha.label}
          className={`flex justify-between items-center gap-3 py-1.5 text-sm ${
            linha.destaque
              ? "mt-1 px-3 py-2 rounded-xl bg-emerald-50 dark:bg-emerald-950/30"
              : ""
          }`}
        >
          <span
            className={
              linha.destaque
                ? "font-semibold text-emerald-800 dark:text-emerald-200"
                : "text-gray-500 dark:text-gray-400"
            }
          >
            {linha.label}
          </span>
          <span
            className={`font-semibold shrink-0 tabular-nums text-right ${
              linha.destaque
                ? "text-base text-emerald-700 dark:text-emerald-300"
                : linha.deducao && linha.valor > 0
                  ? "text-red-500 dark:text-red-400"
                  : "text-gray-800 dark:text-gray-100"
            }`}
          >
            {textoValor(linha.valor, linha.deducao)}
          </span>
        </div>
      ))}
      <div className="border-t border-gray-100 dark:border-gray-700 my-2" />
      {pendencias.map((linha) => (
        <div key={linha.label} className="flex justify-between items-center gap-3 py-1.5 text-sm">
          <span className="text-gray-500 dark:text-gray-400">{linha.label}</span>
          <span className="font-semibold shrink-0 tabular-nums text-gray-800 dark:text-gray-100">
            {formatCurrency(linha.valor)}
          </span>
        </div>
      ))}
    </div>
  );
}
