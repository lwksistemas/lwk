"use client";

import { CLINICA_AGENDA_LEGEND_ITEMS } from "@/lib/clinica-beleza-constants";

export function AgendaLegenda() {
  return (
    <div className="flex flex-wrap items-center gap-3 sm:gap-4 text-xs sm:text-sm text-gray-600 dark:text-gray-400">
      {CLINICA_AGENDA_LEGEND_ITEMS.map(({ key, label, bg }) => (
        <span key={key} className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 sm:w-3 sm:h-3 rounded-full" style={{ backgroundColor: bg }} aria-hidden />
          {label}
        </span>
      ))}
      <span className="hidden sm:inline text-gray-500 dark:text-gray-400">
        · Bloqueios 🚫: arraste ou puxe a borda inferior para ajustar
      </span>
    </div>
  );
}
