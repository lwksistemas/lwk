"use client";

import { Calculator, CalendarClock, Clock3 } from "lucide-react";
import { AgendamentoSectionCard } from "./AgendamentoSectionCard";
import {
  formatDuracaoPrevista,
  formatTerminoPrevisto,
} from "./agendamento-resumo-format";
import { formatCurrency } from "@/lib/financeiro-helpers";
import { useClinicaBelezaTheme } from "@/components/clinica-beleza/ClinicaBelezaThemeContext";
import { cbPrimaryTitle } from "@/lib/clinica-beleza-theme-utils";

export {
  formatDuracaoPrevista,
  formatRetornoResumoCompact,
  formatTerminoPrevisto,
} from "./agendamento-resumo-format";

export function AgendamentoResumoCard({
  taxaConsultaBase,
  taxaZerada,
  procedimentosValor,
  procedimentosCount,
  totalEstimado,
  duracaoMinutos,
  horarioInicio,
  retornoTexto,
  children,
}: {
  taxaConsultaBase: number;
  taxaZerada: boolean;
  procedimentosValor: number;
  procedimentosCount: number;
  totalEstimado: number;
  duracaoMinutos: number;
  horarioInicio?: string;
  retornoTexto: string;
  children?: React.ReactNode;
}) {
  const theme = useClinicaBelezaTheme();
  const wine = cbPrimaryTitle();
  const termino = formatTerminoPrevisto(horarioInicio || "", duracaoMinutos);

  return (
    <AgendamentoSectionCard icon={Calculator} title="Resumo do Agendamento">
      <div className="space-y-1.5 text-sm">
        <div className="flex justify-between gap-3 text-slate-600 dark:text-gray-300">
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
        <div className="flex justify-between gap-3 text-slate-600 dark:text-gray-300">
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
        <div className="flex items-start gap-1.5 rounded-lg border border-[#E9D5E3] dark:border-neutral-700 bg-[#FAF8FA] dark:bg-neutral-800/50 px-2 py-1.5 min-h-[40px]">
          <Clock3 className="h-3.5 w-3.5 shrink-0 text-slate-400 mt-0.5" />
          <div className="min-w-0">
            <p className="text-[12px] text-slate-600 dark:text-gray-300 leading-snug">
              Duração prevista{" "}
              <span className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                {formatDuracaoPrevista(duracaoMinutos)}
              </span>
            </p>
            {termino ? (
              <p className="text-[12px] text-slate-500 mt-0.5 leading-snug">
                Término previsto:{" "}
                <span className="font-semibold text-gray-800 dark:text-gray-200">{termino}</span>
              </p>
            ) : null}
          </div>
        </div>
        <div className="flex items-start gap-1.5 rounded-lg border border-[#E9D5E3] dark:border-neutral-700 bg-[#FAF8FA] dark:bg-neutral-800/50 px-2 py-1.5 min-h-[40px]">
          <CalendarClock className="h-3.5 w-3.5 shrink-0 text-slate-400 mt-0.5" />
          <p className="min-w-0 text-[12px] font-semibold text-gray-900 dark:text-gray-100 leading-snug break-words">
            {retornoTexto}
          </p>
        </div>
      </div>

      {children}
    </AgendamentoSectionCard>
  );
}
