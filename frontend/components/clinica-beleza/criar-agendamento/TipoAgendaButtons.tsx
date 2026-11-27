"use client";

import {
  CalendarCheck2,
  ClipboardList,
  Layers,
  RefreshCw,
  Stethoscope,
} from "lucide-react";
import type { NomeAgendaItem } from "@/lib/clinica-beleza-api";
import { normalizarTipoAgendaNome, sortTiposAgenda } from "@/lib/clinica-beleza-tipo-agenda";
import { useClinicaBelezaTheme } from "@/components/clinica-beleza/ClinicaBelezaThemeContext";
import { cbPrimaryGradient } from "@/lib/clinica-beleza-theme-utils";

const ICONES: Record<string, typeof Stethoscope> = {
  CONSULTA: Stethoscope,
  RETORNO: RefreshCw,
  ATENDIMENTO: ClipboardList,
  PROTOCOLO: Layers,
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
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-1.5">
      {itens.map((item) => {
        const selected = value === item.id;
        const Icon = iconeTipoAgenda(item.nome);
        return (
          <button
            key={item.id}
            type="button"
            disabled={Boolean(locked)}
            onClick={() => onChange(item.id)}
            className={`relative flex flex-col items-center justify-center gap-0.5 rounded-lg border px-1 text-center transition-colors h-[46px] min-h-[44px] max-h-[50px] ${
              selected
                ? "text-white border-transparent shadow-sm"
                : "border-[#E9D5E3] dark:border-neutral-600 text-gray-700 dark:text-gray-200 bg-white dark:bg-neutral-800 hover:bg-gray-50 dark:hover:bg-neutral-700"
            }`}
            style={selected ? { backgroundImage: cbPrimaryGradient(145) } : undefined}
          >
            {selected ? (
              <span className="absolute top-0.5 right-1 flex h-3.5 w-3.5 items-center justify-center rounded-full bg-white/30 text-[9px] leading-none">
                ✓
              </span>
            ) : null}
            <Icon className="h-3.5 w-3.5 shrink-0" style={selected ? undefined : { color: theme.primary }} />
            <span className="text-xs font-semibold leading-tight line-clamp-1">{item.nome}</span>
          </button>
        );
      })}
    </div>
  );
}
