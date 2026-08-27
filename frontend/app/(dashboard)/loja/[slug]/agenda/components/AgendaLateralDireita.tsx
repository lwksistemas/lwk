"use client";

import { useEffect, useMemo, useState } from "react";
import type { AgendaEventData } from "@/lib/clinica-beleza-agenda-types";
import { formatClinicaHora } from "@/lib/clinica-beleza-datetime";
import {
  agendamentoEmAndamento,
  celulasCalendarioMes,
  corProfissionalAgenda,
  eventProfessionalId,
  estiloCardStatusAgenda,
  primeiroNomeProfissional,
  proximosAgendamentosAgenda,
  rotuloStatusCardAgenda,
  capitalizarAgenda,
  tituloCardAgenda,
  tituloMesCalendario,
  toAgendaDiaIso,
} from "@/hooks/clinica-beleza/agenda-data/agenda-dia-colunas-utils";

const WEEKDAYS = ["D", "S", "T", "Q", "Q", "S", "S"] as const;
const DIA_ACCENT = "#7c3aed";

export function AgendaLateralDireita({
  dateIso,
  onDateChange,
  eventos,
  selectedProfessional,
  hoverDiaIso,
  deveIgnorarClick,
  onOpenEvent,
  expandToFill = false,
}: {
  dateIso: string;
  onDateChange: (iso: string) => void;
  eventos: AgendaEventData[];
  selectedProfessional: string;
  hoverDiaIso?: string | null;
  deveIgnorarClick: () => boolean;
  onOpenEvent: (evt: AgendaEventData) => void;
  expandToFill?: boolean;
}) {
  const [agora, setAgora] = useState(() => new Date());
  useEffect(() => {
    const id = window.setInterval(() => setAgora(new Date()), 30_000);
    return () => window.clearInterval(id);
  }, []);

  const celulasMes = useMemo(() => celulasCalendarioMes(dateIso), [dateIso]);
  const mesTitulo = useMemo(() => capitalizarAgenda(tituloMesCalendario(dateIso)), [dateIso]);
  const hojeIso = toAgendaDiaIso(agora);
  const proximos = useMemo(
    () => proximosAgendamentosAgenda(eventos, dateIso, agora, selectedProfessional),
    [eventos, dateIso, agora, selectedProfessional],
  );
  const tituloFila = dateIso === hojeIso ? "Próximos" : "Neste dia";

  return (
    <aside
      className={`hidden lg:flex min-h-0 flex-col border-l border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 ${
        expandToFill ? "flex-1 min-w-64" : "w-64 shrink-0"
      }`}
    >
      <div className="p-4 pb-3 shrink-0">
        <p className="text-sm font-semibold text-gray-900 dark:text-gray-100 capitalize mb-3">
          {mesTitulo}
        </p>
        <div className="grid grid-cols-7 gap-y-1 text-center">
          {WEEKDAYS.map((d, i) => (
            <span key={`${d}-${i}`} className="text-[10px] font-medium text-gray-400 py-1">
              {d}
            </span>
          ))}
          {celulasMes.map((cel) => {
            const selected = cel.iso === dateIso;
            const today = cel.iso === hojeIso;
            return (
              <button
                key={cel.iso}
                type="button"
                data-agenda-dia-iso={cel.iso}
                onClick={() => {
                  if (deveIgnorarClick()) return;
                  onDateChange(cel.iso);
                }}
                className={`h-8 text-xs rounded-full ${
                  selected
                    ? "text-white font-semibold"
                    : hoverDiaIso === cel.iso
                      ? "ring-2 ring-violet-500 font-semibold text-gray-900"
                      : today
                        ? "font-semibold text-gray-900 dark:text-gray-100"
                        : cel.inMonth
                          ? "text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700"
                          : "text-gray-300 dark:text-gray-600"
                }`}
                style={selected ? { backgroundColor: DIA_ACCENT } : undefined}
              >
                {Number(cel.iso.slice(-2))}
              </button>
            );
          })}
        </div>
      </div>

      <div className="flex-1 min-h-0 flex flex-col border-t border-gray-100 dark:border-gray-700">
        <div className="flex items-baseline justify-between gap-2 px-4 pt-3 pb-1.5 shrink-0">
          <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">{tituloFila}</h3>
          <span className="text-[11px] tabular-nums text-gray-400">{proximos.length}</span>
        </div>
        {proximos.length === 0 ? (
          <p className="px-4 py-3 text-xs text-gray-500 dark:text-gray-400 leading-relaxed">
            {dateIso === hojeIso
              ? "Nenhum agendamento restante hoje."
              : "Nenhum agendamento neste dia."}
          </p>
        ) : (
          <ul className="flex-1 min-h-0 overflow-y-auto px-2 pb-3 space-y-1">
            {proximos.map((row) => {
              const estilo = estiloCardStatusAgenda(row.evt);
              const pid = eventProfessionalId(row.evt);
              const corProf = pid != null ? corProfissionalAgenda(pid) : "#94a3b8";
              const agoraItem = agendamentoEmAndamento(row, agora);
              const procedimento = row.evt.extendedProps?.procedure_name || "";
              const profNome = primeiroNomeProfissional(row.evt.extendedProps?.professional_name);
              return (
                <li key={row.evt.id}>
                  <button
                    type="button"
                    onClick={() => onOpenEvent(row.evt)}
                    className="w-full text-left rounded-lg px-2 py-1.5 hover:bg-gray-50 dark:hover:bg-gray-700/60"
                    style={{ borderLeft: estilo.borderLeft }}
                  >
                    <div className="flex items-start justify-between gap-1.5">
                      <p className="text-[11px] tabular-nums font-semibold text-gray-700 dark:text-gray-200">
                        {formatClinicaHora(row.start)}
                        {agoraItem ? (
                          <span
                            className="ml-1.5 text-[10px] font-semibold uppercase tracking-wide"
                            style={{ color: "var(--cb-primary, #8B3D52)" }}
                          >
                            Agora
                          </span>
                        ) : null}
                      </p>
                      <span
                        className="text-[10px] font-semibold leading-none px-1.5 py-0.5 rounded-full text-white shrink-0 max-w-[5.5rem] truncate"
                        style={{ backgroundColor: estilo.cor }}
                      >
                        {rotuloStatusCardAgenda(row.evt)}
                      </span>
                    </div>
                    <p className="text-xs font-semibold text-gray-900 dark:text-gray-50 truncate leading-tight mt-0.5">
                      {tituloCardAgenda(row.evt)}
                    </p>
                    <p className="text-[11px] text-gray-500 dark:text-gray-400 truncate flex items-center gap-1.5 mt-0.5">
                      {profNome ? (
                        <span
                          className="inline-block w-1.5 h-1.5 rounded-full shrink-0"
                          style={{ backgroundColor: corProf }}
                          aria-hidden
                        />
                      ) : null}
                      <span className="truncate">
                        {[procedimento, profNome].filter(Boolean).join(" · ")}
                      </span>
                    </p>
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </aside>
  );
}
