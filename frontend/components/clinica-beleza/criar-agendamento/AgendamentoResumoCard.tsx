"use client";

import { Calculator, CalendarClock, Clock3 } from "lucide-react";
import { AgendamentoSectionCard } from "./AgendamentoSectionCard";
import { formatCurrency } from "@/lib/financeiro-helpers";
import { useClinicaBelezaTheme } from "@/components/clinica-beleza/ClinicaBelezaThemeContext";

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
}: {
  taxaConsultaBase: number;
  taxaZerada: boolean;
  procedimentosValor: number;
  procedimentosCount: number;
  totalEstimado: number;
  duracaoMinutos: number;
  retornoTexto: string;
}) {
  const theme = useClinicaBelezaTheme();

  return (
    <AgendamentoSectionCard icon={Calculator} title="Resumo do agendamento">
      <div className="space-y-2 text-sm">
        <div className="flex justify-between gap-3 text-gray-600 dark:text-gray-300">
          <span>Taxa de avaliação</span>
          <span className="font-medium text-gray-900 dark:text-gray-100">
            {taxaZerada ? (
              <>
                {taxaConsultaBase > 0 ? (
                  <span className="line-through opacity-50 mr-1.5">{formatCurrency(taxaConsultaBase)}</span>
                ) : null}
                <span className="text-emerald-600 dark:text-emerald-400">R$ 0,00</span>
              </>
            ) : (
              formatCurrency(taxaConsultaBase)
            )}
          </span>
        </div>
        <div className="flex justify-between gap-3 text-gray-600 dark:text-gray-300">
          <span>
            Procedimentos{procedimentosCount > 0 ? ` (${procedimentosCount})` : ""}
          </span>
          <span className="font-medium text-gray-900 dark:text-gray-100">
            {formatCurrency(procedimentosValor)}
          </span>
        </div>
        <div
          className="mt-2 flex items-center justify-between gap-3 rounded-xl px-3.5 py-3"
          style={{ backgroundColor: theme.primaryLight }}
        >
          <span className="text-sm font-semibold text-gray-900 dark:text-gray-100">Total estimado</span>
          <span className="text-base font-bold" style={{ color: theme.primary }}>
            {formatCurrency(totalEstimado)}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
        <div className="flex items-start gap-2 rounded-xl border border-gray-100 dark:border-neutral-700 bg-gray-50/80 dark:bg-neutral-800/50 px-3 py-2.5">
          <Clock3 className="h-4 w-4 mt-0.5 shrink-0 text-gray-500" />
          <div className="min-w-0">
            <p className="text-[11px] text-gray-500 dark:text-gray-400">Duração prevista</p>
            <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">
              {formatDuracaoPrevista(duracaoMinutos)}
            </p>
          </div>
        </div>
        <div className="flex items-start gap-2 rounded-xl border border-gray-100 dark:border-neutral-700 bg-gray-50/80 dark:bg-neutral-800/50 px-3 py-2.5">
          <CalendarClock className="h-4 w-4 mt-0.5 shrink-0 text-gray-500" />
          <div className="min-w-0">
            <p className="text-[11px] text-gray-500 dark:text-gray-400">Retorno</p>
            <p className="text-sm font-semibold text-gray-900 dark:text-gray-100 line-clamp-2">
              {retornoTexto}
            </p>
          </div>
        </div>
      </div>
    </AgendamentoSectionCard>
  );
}
