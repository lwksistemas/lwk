"use client";

import type { ElementType, ReactNode } from "react";
import Link from "next/link";
import { CalendarDays, ChevronRight, Flower2, RefreshCw } from "lucide-react";
import { formatCurrency } from "@/lib/financeiro-helpers";
import { CLINICA_AGENDA_STATUS_LABEL } from "@/lib/clinica-beleza-constants";
import type { DashboardAppointment, TopProcedure } from "./clinica-beleza-dashboard-types";
import { DASHBOARD_STATUS_COLORS } from "./clinica-beleza-dashboard-utils";

const CARD =
  "bg-white dark:bg-gray-800 rounded-2xl p-4 shadow-sm border border-gray-100 dark:border-gray-700 min-w-0";

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
    <Link href={href} className="inline-flex items-center gap-0.5 text-xs font-medium hover:underline shrink-0 whitespace-nowrap" style={{ color: COR_PRIMARIA }}>
      {children}
      <ChevronRight className="w-3.5 h-3.5" aria-hidden />
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
    <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2 w-full min-w-0">
      <div className="flex items-center gap-3 min-w-0">
        <div
          className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
          style={{ backgroundColor: ICONE_FUNDO }}
        >
          <Flower2 className="w-5 h-5" style={{ color: COR_PRIMARIA }} aria-hidden />
        </div>
        <div className="min-w-0">
          <h1 className="text-base sm:text-lg font-bold text-gray-900 dark:text-white truncate leading-tight">{cumprimento}</h1>
          <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">Visão geral da clínica</p>
        </div>
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <label className="relative inline-flex items-center gap-2 px-3 py-2 text-sm border border-gray-200 dark:border-neutral-600 rounded-xl bg-white dark:bg-neutral-800 text-gray-700 dark:text-gray-200 cursor-pointer">
          <CalendarDays className="w-4 h-4 shrink-0" style={{ color: COR_PRIMARIA }} aria-hidden />
          <span className="text-gray-400">Período:</span>
          <span className="font-medium">{rotuloPeriodo}</span>
          <input
            type="month"
            value={mesAno}
            max={mesAnoMax}
            onChange={(e) => e.target.value && onMesAno(e.target.value)}
            onMouseDown={(e) => e.preventDefault()}
            onClick={(e) => {
              const input = e.currentTarget;
              if (typeof input.showPicker !== "function") return;
              try {
                input.showPicker();
              } catch {
                input.focus();
              }
            }}
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
      <div className="flex items-center gap-2.5 mb-2">
        <div
          className="w-9 h-9 rounded-lg flex items-center justify-center shrink-0"
          style={{ backgroundColor: ICONE_FUNDO }}
        >
          <Icon className="w-[18px] h-[18px]" style={{ color: COR_PRIMARIA }} aria-hidden />
        </div>
        <span className="text-[13px] text-gray-500 dark:text-gray-400 leading-tight flex-1 min-w-0">{title}</span>
        {href && <ChevronRight className="w-4 h-4 text-gray-300 shrink-0" aria-hidden />}
      </div>
      <p className={`text-xl sm:text-[1.65rem] font-bold tabular-nums leading-none break-words ${valueClass}`}>{value}</p>
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
      title={`${appt.patient_name} — ${appt.procedure_name} — ${statusLabel}`}
      className="grid grid-cols-[3rem_minmax(0,1fr)_auto] items-center gap-x-2 py-1.5 px-1 -mx-1 rounded-lg border-b border-gray-50 dark:border-gray-700 last:border-0 hover:bg-gray-50 dark:hover:bg-gray-700/40"
      aria-label={`Abrir agendamento de ${appt.patient_name}`}
    >
      <span
        className="inline-flex items-center justify-center h-7 rounded-md text-xs font-semibold"
        style={{ backgroundColor: ICONE_FUNDO, color: COR_PRIMARIA }}
      >
        {hora}
      </span>
      <span className="min-w-0">
        <span className="block text-[13px] font-semibold text-gray-800 dark:text-gray-100 leading-tight">
          {appt.patient_name}
        </span>
        <span className="block text-[11px] text-gray-400 dark:text-gray-500 leading-tight">{appt.procedure_name}</span>
      </span>
      <span className={`text-[11px] px-2 py-0.5 rounded-full font-medium whitespace-nowrap ${statusClass}`}>
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
    <div className="flex flex-col gap-2.5">
      {procedures.map((proc, i) => {
        const pct = Math.max(8, Math.round((proc.count / max) * 100));
        return (
          <div key={`${proc.name}-${i}`} className="min-w-0">
            <div className="flex justify-between gap-3 text-xs mb-1">
              <span className="text-gray-600 dark:text-gray-300 min-w-0 break-words">{proc.name}</span>
              <span className="text-gray-800 dark:text-gray-100 font-semibold shrink-0 tabular-nums">{proc.count}</span>
            </div>
            <div className="h-2 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
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
    <div>
      <div>
      {resultado.map((linha) => (
        <div
          key={linha.label}
          className={`flex justify-between items-center gap-3 py-1 text-sm ${
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
      </div>
      <div>
      <div className="border-t border-gray-100 dark:border-gray-700 my-2" />
      {pendencias.map((linha) => (
        <div key={linha.label} className="flex justify-between items-center gap-3 py-1 text-sm">
          <span className="text-gray-500 dark:text-gray-400">{linha.label}</span>
          <span className="font-semibold shrink-0 tabular-nums text-gray-800 dark:text-gray-100">
            {formatCurrency(linha.valor)}
          </span>
        </div>
      ))}
      </div>
    </div>
  );
}
