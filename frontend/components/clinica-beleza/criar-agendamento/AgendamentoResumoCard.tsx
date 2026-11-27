"use client";

import { Calculator, CalendarClock, Clock3 } from "lucide-react";
import { AgendamentoSectionCard } from "./AgendamentoSectionCard";
import { formatCurrency } from "@/lib/financeiro-helpers";
import { useClinicaBelezaTheme } from "@/components/clinica-beleza/ClinicaBelezaThemeContext";
import { cbPrimaryTitle } from "@/lib/clinica-beleza-theme-utils";

export function formatDuracaoPrevista(minutos: number): string {
  if (!minutos || minutos <= 0) return "Não definida";
  const h = Math.floor(minutos / 60);
  const m = minutos % 60;
  if (h > 0 && m > 0) return `${h}h ${m}min`;
  if (h > 0) return `${h}h`;
  return `${m}min`;
}

export function AgendamentoResumoCard({
  taxaConsultaBase,
  taxaZerada,
  procedimentosValor,
  procedimentosCount,
  totalEstimado,
  duracaoMinutos,
  retornoTexto,
  children,
}: {
  taxaConsultaBase: number;
  taxaZerada: boolean;
  procedimentosValor: number;
  procedimentosCount: number;
  totalEstimado: number;
  duracaoMinutos: number;
  retornoTexto: string;
  children?: React.ReactNode;
}) {
  const theme = useClinicaBelezaTheme();
  const wine = cbPrimaryTitle();

  return (
    <AgendamentoSectionCard icon={Calculator} title="Resumo do Agendamento">
      <div className="space-y-1.5 text-sm">
        <div className="flex justify-between gap-3 text-slate-500 dark:text-gray-300">
          <span>Taxa de avaliação</span>
          <span className="font-semibold text-gray-900 dark:text-gray-100 tabular-nums">
            {taxaZerada ? (
              <>
                {taxaConsultaBase > 0 ? (
                  <span className="line-through opacity-50 mr-1.5">{formatCurrency(taxaConsultaBase)}</span>
                ) : null}
                <span className="text-[#22C55E]">R$ 0,00</span>
              </>
            ) : (
              formatCurrency(taxaConsultaBase)
            )}
          </span>
        </div>
        <div className="flex justify-between gap-3 text-slate-500 dark:text-gray-300">
          <span>
            Procedimentos{procedimentosCount > 0 ? ` (${procedimentosCount})` : ""}
          </span>
          <span className="font-semibold text-gray-900 dark:text-gray-100 tabular-nums">
            {formatCurrency(procedimentosValor)}
          </span>
        </div>
        <div
          className="mt-1 flex items-center justify-between gap-3 rounded-xl px-3 py-2"
          style={{ backgroundColor: theme.primaryLight }}
        >
          <span className="text-sm font-bold" style={{ color: wine }}>
            Total estimado
          </span>
          <span className="text-base font-extrabold tabular-nums" style={{ color: wine }}>
            {formatCurrency(totalEstimado)}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-1.5">
        <div className="flex items-center gap-1.5 rounded-lg border border-[#E9D5E3] dark:border-neutral-700 bg-[#FAF8FA] dark:bg-neutral-800/50 px-2 py-1 min-h-[36px]">
          <Clock3 className="h-3.5 w-3.5 shrink-0 text-slate-400" />
          <div className="min-w-0">
            <p className="text-[10px] text-slate-500 leading-none">Duração prevista</p>
            <p className="text-[12px] font-semibold text-gray-900 dark:text-gray-100 mt-0.5 truncate">
              {formatDuracaoPrevista(duracaoMinutos)}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-1.5 rounded-lg border border-[#E9D5E3] dark:border-neutral-700 bg-[#FAF8FA] dark:bg-neutral-800/50 px-2 py-1 min-h-[36px]">
          <CalendarClock className="h-3.5 w-3.5 shrink-0 text-slate-400" />
          <div className="min-w-0">
            <p className="text-[10px] text-slate-500 leading-none">Retorno</p>
            <p className="text-[12px] font-semibold text-gray-900 dark:text-gray-100 mt-0.5 truncate">
              {retornoTexto}
            </p>
          </div>
        </div>
      </div>

      {children}
    </AgendamentoSectionCard>
  );
}
