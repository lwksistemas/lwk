"use client";

import { ChevronRight } from "lucide-react";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import {
  CLINICA_AGENDA_STATUS_LABEL,
} from "@/lib/clinica-beleza-constants";
import { formatClinicaDia, formatClinicaHora, parseEventDate } from "@/lib/clinica-beleza-datetime";
import type { AgendaEventData } from "./ModalDetalheAgendamento";

function labelStatusLista(evt: AgendaEventData): string {
  const props = evt.extendedProps || {};
  const isBloqueio = (props as { isBloqueio?: boolean }).isBloqueio;
  const isIntervalo = (props as { isIntervalo?: boolean }).isIntervalo;
  const status = props.status as string | undefined;
  if (isBloqueio) return "Bloqueio";
  if (isIntervalo) return "Intervalo";
  return CLINICA_AGENDA_STATUS_LABEL[status || ""] || "Agendamento";
}

function tituloLista(evt: AgendaEventData): string {
  const props = evt.extendedProps || {};
  const isBloqueio = (props as { isBloqueio?: boolean }).isBloqueio;
  const isIntervalo = (props as { isIntervalo?: boolean }).isIntervalo;
  if (isBloqueio || isIntervalo) {
    return evt.title.replace(/^🚫\s*/, "").replace(/^🍽️\s*/, "");
  }
  const parts = [props.patient_name, props.procedure_name].filter(Boolean);
  return parts.length ? parts.join(" · ") : evt.title;
}

export function AgendaListaColunas({
  eventos,
  onAbrir,
}: {
  eventos: AgendaEventData[];
  onAbrir: (evt: AgendaEventData) => void;
}) {
  const ordenados = eventos
    .map((evt) => {
      const start = parseEventDate(evt.start);
      if (!start) return null;
      const end = parseEventDate(evt.end) || start;
      return { evt, start, end };
    })
    .filter((x): x is { evt: AgendaEventData; start: Date; end: Date } => x != null)
    .sort((a, b) => a.start.getTime() - b.start.getTime());

  const grupos: { chave: string; label: string; items: typeof ordenados }[] = [];
  const mapa = new Map<string, typeof ordenados>();
  for (const item of ordenados) {
    const chave = item.start.toISOString().slice(0, 10);
    if (!mapa.has(chave)) mapa.set(chave, []);
    mapa.get(chave)!.push(item);
  }
  for (const [chave, items] of [...mapa.entries()].sort(([a], [b]) => a.localeCompare(b))) {
    grupos.push({ chave, label: formatClinicaDia(items[0].start), items });
  }

  if (ordenados.length === 0) {
    return (
      <p className="text-center text-sm text-gray-500 dark:text-gray-400 py-12">
        Nenhum agendamento ou bloqueio carregado.
      </p>
    );
  }

  const thClass =
    "text-left px-3 sm:px-4 py-3 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400 whitespace-nowrap";
  const tdClass = "px-3 sm:px-4 py-3 align-middle text-sm";

  return (
    <div className="space-y-6 pb-4">
      {grupos.map((grupo) => (
        <section key={grupo.chave}>
          <h3 className="sticky top-0 z-10 bg-white dark:bg-gray-800 py-2 mb-1 text-sm font-semibold text-gray-800 dark:text-gray-100 capitalize border-b border-gray-200 dark:border-gray-700">
            {grupo.label}
          </h3>
          <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
            <table className="w-full min-w-[640px] text-sm border-collapse">
              <thead className="bg-gray-50 dark:bg-neutral-900/80 border-b border-gray-200 dark:border-gray-700">
                <tr>
                  <th className={thClass}>Horário</th>
                  <th className={thClass}>Cliente / Descrição</th>
                  <th className={`${thClass} hidden sm:table-cell`}>Profissional</th>
                  <th className={`${thClass} hidden md:table-cell`}>Duração</th>
                  <th className={thClass}>Status</th>
                  <th className="w-10" aria-hidden />
                </tr>
              </thead>
              <tbody>
                {grupo.items.map(({ evt, start, end }) => {
                  const props = evt.extendedProps || {};
                  const isIntervalo = (props as { isIntervalo?: boolean }).isIntervalo;
                  const duracaoMin = Math.max(1, Math.round((end.getTime() - start.getTime()) / 60000));
                  const cor = evt.backgroundColor || CLINICA_BELEZA_PRIMARY;
                  return (
                    <tr
                      key={String(evt.id)}
                      onClick={() => !isIntervalo && onAbrir(evt)}
                      className={`border-t border-gray-100 dark:border-gray-700/80 transition-colors ${
                        isIntervalo
                          ? "bg-amber-50/40 dark:bg-amber-950/20 cursor-default"
                          : "hover:bg-[#F5E6EA]/40 dark:hover:bg-neutral-700/30 cursor-pointer"
                      }`}
                    >
                      <td className={`${tdClass} tabular-nums whitespace-nowrap`}>
                        <span className="inline-flex items-center gap-2">
                          <span className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: cor }} aria-hidden />
                          <span>
                            <span className="font-medium text-gray-900 dark:text-gray-100">{formatClinicaHora(start)}</span>
                            <span className="text-gray-400 dark:text-gray-500 mx-1">–</span>
                            <span className="text-gray-600 dark:text-gray-300">{formatClinicaHora(end)}</span>
                          </span>
                        </span>
                      </td>
                      <td className={tdClass}>
                        <p className="font-medium text-gray-900 dark:text-gray-100 truncate max-w-[220px] sm:max-w-none">
                          {tituloLista(evt)}
                        </p>
                        {!isIntervalo && props.professional_name && (
                          <p className="sm:hidden text-xs text-gray-500 dark:text-gray-400 mt-0.5 truncate">
                            {props.professional_name}
                          </p>
                        )}
                      </td>
                      <td className={`${tdClass} hidden sm:table-cell text-gray-600 dark:text-gray-400`}>
                        {!isIntervalo ? (props.professional_name || "—") : "—"}
                      </td>
                      <td className={`${tdClass} hidden md:table-cell text-gray-600 dark:text-gray-400 tabular-nums`}>
                        {duracaoMin} min
                      </td>
                      <td className={tdClass}>
                        <span
                          className="inline-block text-xs font-medium px-2 py-0.5 rounded-full whitespace-nowrap"
                          style={{ backgroundColor: `${cor}22`, color: cor }}
                        >
                          {labelStatusLista(evt)}
                        </span>
                      </td>
                      <td className="px-2 py-3 text-gray-400">
                        {!isIntervalo && <ChevronRight size={18} className="mx-auto" />}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>
      ))}
    </div>
  );
}
