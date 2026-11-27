"use client";

import {
  CalendarCheck2,
  ClipboardList,
  Package,
  RefreshCw,
  Stethoscope,
} from "lucide-react";
import type { NomeAgendaItem } from "@/lib/clinica-beleza-api";
import { normalizarTipoAgendaNome, sortTiposAgenda } from "@/lib/clinica-beleza-tipo-agenda";
import { useClinicaBelezaTheme } from "@/components/clinica-beleza/ClinicaBelezaThemeContext";

const ICONES: Record<string, typeof Stethoscope> = {
  CONSULTA: Stethoscope,
  RETORNO: RefreshCw,
  ATENDIMENTO: ClipboardList,
  PROTOCOLO: Package,
};

export function iconeTipoAgenda(nome: string) {
  const n = normalizarTipoAgendaNome(nome);
  return ICONES[n] || CalendarCheck2;
}

export function TipoAgendaButtons({
  nomesAgenda,
  value,
  onChange,
  locked,
}: {
  nomesAgenda: NomeAgendaItem[];
  value: number | "";
  onChange: (id: number | "") => void;
  locked?: NomeAgendaItem | null;
}) {
  const theme = useClinicaBelezaTheme();
  const itens = locked ? [locked] : sortTiposAgenda(nomesAgenda);

  if (itens.length === 0) {
    return (
      <p className="text-xs text-amber-600 dark:text-amber-400">
        Cadastre tipos de agenda em Atendimentos → ícone de calendário.
      </p>
    );
  }

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
      {itens.map((item) => {
        const selected = value === item.id;
        const Icon = iconeTipoAgenda(item.nome);
        return (
          <button
            key={item.id}
            type="button"
            disabled={Boolean(locked)}
            onClick={() => onChange(item.id)}
            className={`relative flex flex-col items-center justify-center gap-1.5 rounded-xl border px-2 py-3 text-center transition-colors min-h-[72px] ${
              selected
                ? "text-white border-transparent shadow-sm"
                : "border-gray-200 dark:border-neutral-600 text-gray-700 dark:text-gray-200 bg-white dark:bg-neutral-800 hover:bg-gray-50 dark:hover:bg-neutral-700"
            }`}
            style={selected ? { backgroundColor: theme.primary } : undefined}
          >
            {selected ? (
              <span className="absolute top-1.5 right-1.5 flex h-4 w-4 items-center justify-center rounded-full bg-white/25 text-[10px]">
                ✓
              </span>
            ) : null}
            <Icon className="h-4 w-4 shrink-0" />
            <span className="text-[11px] font-semibold leading-tight line-clamp-2">{item.nome}</span>
          </button>
        );
      })}
    </div>
  );
}
