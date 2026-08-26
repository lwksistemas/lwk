"use client";

import { useMemo, useRef } from "react";
import { Calendar } from "lucide-react";
import type { AgendaEventData } from "@/lib/clinica-beleza-agenda-types";
import type { ClinicaProfessional } from "@/lib/clinica-beleza-entities";
import { formatClinicaHora } from "@/lib/clinica-beleza-datetime";
import {
  addDaysIso,
  celulasCalendarioMes,
  colunasProfissionaisDia,
  corProfissionalAgenda,
  eventProfessionalId,
  eventosDoDia,
  eventosDoDiaNaColuna,
  minutesToHm,
  parseHmToMinutes,
  sameDayIso,
  slotDateFromMinutes,
  snapMinutos,
  tituloMesCalendario,
  toAgendaDiaIso,
} from "@/hooks/clinica-beleza/agenda-data/agenda-dia-colunas-utils";

const PX_PER_HOUR = 72;
const COL_MIN_WIDTH = 280;
const TIME_COL_W = 44;
const WEEKDAYS = ["D", "S", "T", "Q", "Q", "S", "S"] as const;
const DIA_ACCENT = "#7c3aed";

function capitalizar(s: string): string {
  return s ? s.charAt(0).toUpperCase() + s.slice(1) : s;
}

function fundoPastel(hex: string): string {
  return `color-mix(in srgb, ${hex} 18%, white)`;
}

function tituloCard(evt: AgendaEventData): string {
  const p = evt.extendedProps || {};
  if (p.isBloqueio) return (p.motivo || evt.title).replace(/^🚫\s*/, "");
  if (p.isIntervalo) return evt.title.replace(/^🍽️\s*/, "") || "Intervalo / Almoço";
  return (p.patient_name || evt.title).toUpperCase();
}

function subtituloCard(evt: AgendaEventData): string {
  const p = evt.extendedProps || {};
  if (p.isBloqueio) return "Bloqueio";
  if (p.isIntervalo) return "Intervalo";
  return p.procedure_name || "";
}

export function AgendaDiaColunas({
  dateIso,
  onDateChange,
  eventos,
  professionals,
  selectedProfessional,
  slotMinTime,
  slotMaxTime,
  onOpenEvent,
  onSlotClick,
  onMudarVisao,
  onVerLista,
}: {
  dateIso: string;
  onDateChange: (iso: string) => void;
  eventos: AgendaEventData[];
  professionals: ClinicaProfessional[];
  selectedProfessional: string;
  slotMinTime: string;
  slotMaxTime: string;
  onOpenEvent: (evt: AgendaEventData) => void;
  onSlotClick: (date: Date, professionalId: number) => void;
  onMudarVisao: (view: "week" | "month") => void;
  onVerLista?: () => void;
}) {
  const dateInputRef = useRef<HTMLInputElement>(null);
  const minMin = parseHmToMinutes(slotMinTime);
  const maxMin = Math.max(minMin + 60, parseHmToMinutes(slotMaxTime));
  const totalMin = maxMin - minMin;
  const pxPerMin = PX_PER_HOUR / 60;
  const gridH = totalMin * pxPerMin;
  const colunas = useMemo(
    () => colunasProfissionaisDia(professionals, selectedProfessional),
    [professionals, selectedProfessional],
  );

  const horas = useMemo(() => {
    const out: number[] = [];
    const startHour = Math.floor(minMin / 60) * 60;
    for (let m = startHour; m < maxMin; m += 60) {
      if (m >= minMin) out.push(m);
    }
    return out;
  }, [minMin, maxMin]);

  const agora = new Date();
  const mostrarAgora = sameDayIso(agora, dateIso);
  const agoraMin = agora.getHours() * 60 + agora.getMinutes();
  const agoraTop = (agoraMin - minMin) * pxPerMin;
  const agoraVisivel = mostrarAgora && agoraMin >= minMin && agoraMin <= maxMin;

  const { tituloData, weekday } = useMemo(() => {
    const [y, mo, d] = dateIso.split("-").map(Number);
    const ref = new Date(y, (mo || 1) - 1, d || 1);
    return {
      tituloData: ref.toLocaleDateString("pt-BR", {
        day: "numeric",
        month: "long",
        year: "numeric",
      }),
      weekday: capitalizar(ref.toLocaleDateString("pt-BR", { weekday: "long" })),
    };
  }, [dateIso]);

  const listaDia = useMemo(() => eventosDoDia(eventos, dateIso), [eventos, dateIso]);
  const celulasMes = useMemo(() => celulasCalendarioMes(dateIso), [dateIso]);
  const mesTitulo = useMemo(() => capitalizar(tituloMesCalendario(dateIso)), [dateIso]);
  const hojeIso = toAgendaDiaIso(new Date());

  return (
    <div className="flex flex-col min-h-0 flex-1 bg-white dark:bg-gray-800">
      <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-2 px-3 sm:px-4 py-3 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-1.5">
          <button
            type="button"
            className="w-8 h-8 rounded-lg border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-50"
            onClick={() => onDateChange(addDaysIso(dateIso, -1))}
            aria-label="Dia anterior"
          >
            ‹
          </button>
          <button
            type="button"
            className="w-8 h-8 rounded-lg border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-50"
            onClick={() => onDateChange(addDaysIso(dateIso, 1))}
            aria-label="Próximo dia"
          >
            ›
          </button>
          <button
            type="button"
            className="ml-1 px-3 h-8 text-sm rounded-lg border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-100 hover:bg-gray-50"
            onClick={() => onDateChange(hojeIso)}
          >
            Hoje
          </button>
          <button
            type="button"
            className="w-8 h-8 rounded-lg border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-600 dark:text-gray-200 hover:bg-gray-50 inline-flex items-center justify-center"
            onClick={() => {
              const el = dateInputRef.current;
              if (!el) return;
              if (typeof el.showPicker === "function") el.showPicker();
              else el.click();
            }}
            aria-label="Escolher data"
          >
            <Calendar size={16} />
          </button>
          <input
            ref={dateInputRef}
            type="date"
            value={dateIso}
            onChange={(e) => {
              if (e.target.value) onDateChange(e.target.value);
            }}
            className="sr-only"
            tabIndex={-1}
            aria-hidden
          />
        </div>
        <div className="text-center min-w-[12rem]">
          <h2 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-gray-50 capitalize leading-tight">
            {tituloData}
          </h2>
          <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">{weekday}</p>
        </div>
        <div className="flex justify-end">
          <div className="inline-flex items-center rounded-lg overflow-hidden border border-gray-200 dark:border-gray-600 text-sm">
            <span
              className="px-3 py-1.5 font-medium text-white"
              style={{ backgroundColor: DIA_ACCENT }}
            >
              Dia
            </span>
            <button
              type="button"
              className="px-3 py-1.5 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-50"
              onClick={() => onMudarVisao("week")}
            >
              Semana
            </button>
            <button
              type="button"
              className="px-3 py-1.5 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-50 border-l border-gray-200 dark:border-gray-600"
              onClick={() => onMudarVisao("month")}
            >
              Mês
            </button>
          </div>
        </div>
      </div>

      {colunas.length === 0 ? (
        <p className="text-center text-sm text-gray-500 py-12">Nenhum profissional na agenda.</p>
      ) : (
        <div className="flex flex-1 min-h-0">
          <div className="flex-1 min-h-0 overflow-auto agenda-scroll-root">
            <div
              className="grid min-w-max h-full"
              style={{
                gridTemplateColumns: `repeat(${colunas.length}, minmax(${COL_MIN_WIDTH}px, 1fr))`,
              }}
            >
              {colunas.map((col) => {
                const items = eventosDoDiaNaColuna(eventos, dateIso, col.id);
                return (
                  <div
                    key={col.id}
                    className="flex flex-col border-r border-gray-200 dark:border-gray-700 min-w-0"
                  >
                    <div className="sticky top-0 z-20 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-3 py-2.5">
                      <div className="flex items-center gap-2.5 min-w-0">
                        <span
                          className="shrink-0 w-9 h-9 rounded-full text-white text-xs font-bold flex items-center justify-center"
                          style={{ backgroundColor: col.cor }}
                        >
                          {col.iniciais}
                        </span>
                        <div className="min-w-0 flex-1">
                          <p className="text-[11px] sm:text-xs font-semibold text-gray-900 dark:text-gray-100 truncate uppercase tracking-wide">
                            {col.nome}
                          </p>
                          {col.especialidade ? (
                            <p className="text-[11px] text-gray-500 dark:text-gray-400 truncate flex items-center gap-1.5">
                              <span
                                className="inline-block w-1.5 h-1.5 rounded-full shrink-0"
                                style={{ backgroundColor: col.cor }}
                              />
                              {col.especialidade}
                            </p>
                          ) : null}
                        </div>
                      </div>
                    </div>
                    <div
                      className="relative bg-white dark:bg-gray-800 cursor-pointer"
                      style={{ height: gridH }}
                      onClick={(e) => {
                        if ((e.target as HTMLElement).closest("[data-agenda-card]")) return;
                        const rect = (e.currentTarget as HTMLDivElement).getBoundingClientRect();
                        const y = e.clientY - rect.top;
                        const mins = snapMinutos(minMin + y / pxPerMin);
                        onSlotClick(slotDateFromMinutes(dateIso, mins), col.id);
                      }}
                    >
                      {horas.map((m) => (
                        <div
                          key={m}
                          className="absolute left-0 right-0 pointer-events-none"
                          style={{ top: (m - minMin) * pxPerMin }}
                        >
                          <span className="absolute left-1.5 text-[10px] tabular-nums text-gray-400 dark:text-gray-500 leading-none pt-0.5">
                            {minutesToHm(m)}
                          </span>
                          <div
                            className="border-t border-gray-100 dark:border-gray-700/80"
                            style={{ marginLeft: TIME_COL_W }}
                          />
                        </div>
                      ))}
                      {agoraVisivel ? (
                        <div
                          className="absolute z-10 h-px bg-red-500 pointer-events-none"
                          style={{ top: agoraTop, left: TIME_COL_W, right: 0 }}
                        />
                      ) : null}
                      {items.map(({ evt, start, end }) => {
                        const startMin = start.getHours() * 60 + start.getMinutes();
                        const endMin = Math.max(startMin + 15, end.getHours() * 60 + end.getMinutes());
                        const top = (startMin - minMin) * pxPerMin;
                        const height = Math.max(36, (endMin - startMin) * pxPerMin - 4);
                        const intervalo = Boolean(evt.extendedProps?.isIntervalo);
                        const bloqueio = Boolean(evt.extendedProps?.isBloqueio);
                        const cor = intervalo ? "#d97706" : bloqueio ? "#4f46e5" : col.cor;
                        return (
                          <button
                            key={evt.id}
                            type="button"
                            data-agenda-card
                            onClick={(e) => {
                              e.stopPropagation();
                              if (!intervalo) onOpenEvent(evt);
                            }}
                            className="absolute z-[1] rounded-lg text-left overflow-hidden px-2.5 py-1.5"
                            style={{
                              top,
                              height,
                              left: TIME_COL_W,
                              right: 6,
                              backgroundColor: intervalo
                                ? "color-mix(in srgb, #d97706 16%, white)"
                                : fundoPastel(cor),
                            }}
                          >
                            <div className="flex items-start justify-between gap-1">
                              <p className="text-[11px] tabular-nums text-gray-600 dark:text-gray-700">
                                {formatClinicaHora(start)} - {formatClinicaHora(end)}
                              </p>
                              <span
                                className="mt-0.5 w-2 h-2 rounded-full shrink-0"
                                style={{ backgroundColor: cor }}
                              />
                            </div>
                            <p className="text-xs font-semibold text-gray-900 truncate leading-tight">
                              {tituloCard(evt)}
                            </p>
                            {height > 48 ? (
                              <p className="text-[11px] text-gray-500 truncate">
                                {subtituloCard(evt)}
                              </p>
                            ) : null}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <aside className="hidden lg:flex w-72 shrink-0 flex-col border-l border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
            <div className="p-4 border-b border-gray-100 dark:border-gray-700">
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
                      onClick={() => onDateChange(cel.iso)}
                      className={`h-8 text-xs rounded-full ${
                        selected
                          ? "text-white font-semibold"
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
            <div className="flex-1 min-h-0 overflow-auto p-4">
              <p className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">
                Agendamentos do dia
              </p>
              {listaDia.length === 0 ? (
                <p className="text-xs text-gray-500">Nenhum agendamento neste dia.</p>
              ) : (
                <ul className="space-y-2.5">
                  {listaDia.map(({ evt, start }) => {
                    const pid = eventProfessionalId(evt);
                    const cor = pid != null ? corProfissionalAgenda(pid) : "#94a3b8";
                    return (
                      <li key={evt.id}>
                        <button
                          type="button"
                          onClick={() => onOpenEvent(evt)}
                          className="w-full flex items-start gap-2 text-left rounded-md hover:bg-gray-50 dark:hover:bg-gray-700/60 px-1 py-0.5"
                        >
                          <span
                            className="mt-1.5 w-2 h-2 rounded-full shrink-0"
                            style={{ backgroundColor: cor }}
                          />
                          <span className="min-w-0">
                            <span className="block text-xs text-gray-900 dark:text-gray-100">
                              <span className="tabular-nums text-gray-500 mr-1.5">
                                {formatClinicaHora(start)}
                              </span>
                              <span className="font-semibold">
                                {evt.extendedProps?.patient_name || evt.title}
                              </span>
                            </span>
                            {evt.extendedProps?.professional_name ? (
                              <span className="block text-[11px] text-gray-400 truncate">
                                {evt.extendedProps.professional_name}
                              </span>
                            ) : null}
                          </span>
                        </button>
                      </li>
                    );
                  })}
                </ul>
              )}
            </div>
            {onVerLista ? (
              <div className="p-3 border-t border-gray-100 dark:border-gray-700">
                <button
                  type="button"
                  onClick={onVerLista}
                  className="text-sm font-medium"
                  style={{ color: DIA_ACCENT }}
                >
                  Ver todos
                </button>
              </div>
            ) : null}
          </aside>
        </div>
      )}
    </div>
  );
}
