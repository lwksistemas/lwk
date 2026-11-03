"use client";

import { useAgendaStatusColors } from "@/components/clinica-beleza/ClinicaBelezaThemeContext";
import {
  CLINICA_AGENDA_BLOQUEIO_COLORS,
  CLINICA_AGENDA_STATUS_LABEL_CURTO,
} from "@/lib/clinica-beleza-constants";

const LEGENDA_KEYS = [
  "SCHEDULED",
  "CLIENT_CONFIRMED",
  "CONFIRMED",
  "IN_PROGRESS",
  "COMPLETED",
  "CANCELLED",
] as const;

/** Faixa compacta de status — acessível sob a grade (Semana/Mês/Dia). */
export function AgendaStatusLegenda() {
  const colors = useAgendaStatusColors();
  return (
    <div
      className="shrink-0 flex flex-wrap items-center gap-x-3 gap-y-1 px-2 sm:px-3 py-1.5 border-t border-gray-100 dark:border-gray-700 bg-white/90 dark:bg-gray-800/90 text-[10px] sm:text-[11px] text-gray-600 dark:text-gray-300"
      role="list"
      aria-label="Legenda de status da agenda"
    >
      {LEGENDA_KEYS.map((key) => {
        const cor = colors[key]?.bg || "#a855f7";
        return (
          <span key={key} role="listitem" className="inline-flex items-center gap-1.5">
            <span
              className="w-2 h-2 rounded-full shrink-0 ring-1 ring-black/5"
              style={{ backgroundColor: cor }}
              aria-hidden
            />
            {CLINICA_AGENDA_STATUS_LABEL_CURTO[key] || key}
          </span>
        );
      })}
      <span role="listitem" className="inline-flex items-center gap-1.5">
        <span
          className="w-2.5 h-2 rounded-sm shrink-0 border border-dashed"
          style={{
            backgroundColor: "color-mix(in srgb, #57534e 12%, white)",
            borderColor: CLINICA_AGENDA_BLOQUEIO_COLORS.border,
          }}
          aria-hidden
        />
        Bloqueado
      </span>
    </div>
  );
}
