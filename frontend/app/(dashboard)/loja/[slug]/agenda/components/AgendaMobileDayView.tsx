"use client";

import { useMemo } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import type { AgendaEventData } from "@/lib/clinica-beleza-agenda-types";
import { parseEventDate } from "@/lib/clinica-beleza-datetime";
import { CLINICA_AGENDA_SLOT_VISUAL_MIN } from "@/lib/clinica-beleza-constants";

function toInputDate(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

function parseHm(t: string): { h: number; m: number } {
  const [h, m] = (t || "07:00:00").slice(0, 5).split(":").map(Number);
  return { h: h || 0, m: m || 0 };
}

function addDaysIso(iso: string, delta: number): string {
  const [y, mo, d] = iso.split("-").map(Number);
  const dt = new Date(y, (mo || 1) - 1, d || 1);
  dt.setDate(dt.getDate() + delta);
  return toInputDate(dt);
}

function formatLabel(iso: string): string {
  const [y, mo, d] = iso.split("-").map(Number);
  return new Date(y, (mo || 1) - 1, d || 1).toLocaleDateString("pt-BR", {
    weekday: "long",
    day: "2-digit",
    month: "long",
  });
}

function slotDate(iso: string, minutesFromMidnight: number): Date {
  const [y, mo, d] = iso.split("-").map(Number);
  const dt = new Date(y, (mo || 1) - 1, d || 1, 0, 0, 0, 0);
  dt.setMinutes(minutesFromMidnight);
  return dt;
}

function formatHm(minutes: number): string {
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`;
}

type SlotItem =
  | { kind: "empty"; minutes: number; label: string }
  | { kind: "event"; minutes: number; label: string; event: AgendaEventData; spanSlots: number };

export function AgendaMobileDayView({
  dateIso,
  onDateChange,
  eventos,
  slotMinTime,
  slotMaxTime,
  onOpenEvent,
  onSlotClick,
}: {
  dateIso: string;
  onDateChange: (iso: string) => void;
  eventos: AgendaEventData[];
  slotMinTime: string;
  slotMaxTime: string;
  onOpenEvent: (evt: AgendaEventData) => void;
  onSlotClick: (date: Date) => void;
}) {
  const step = CLINICA_AGENDA_SLOT_VISUAL_MIN || 15;

  const dayEvents = useMemo(() => {
    return eventos
      .map((e) => {
        const start = parseEventDate(e.start);
        const end = parseEventDate(e.end) || start;
        return { event: e, start, end };
      })
      .filter(({ start }) => start && toInputDate(start) === dateIso)
      .sort((a, b) => (a.start?.getTime() || 0) - (b.start?.getTime() || 0));
  }, [eventos, dateIso]);

  const slots = useMemo(() => {
    const min = parseHm(slotMinTime);
    const max = parseHm(slotMaxTime);
    const startMin = min.h * 60 + min.m;
    let endMin = max.h * 60 + max.m;
    if (endMin <= startMin) endMin = startMin + 60;

    const eventStarts = new Map<number, SlotItem>();
    const occupied = new Set<number>();

    for (const { event, start, end } of dayEvents) {
      if (!start) continue;
      const startM = start.getHours() * 60 + start.getMinutes();
      const aligned = Math.floor(startM / step) * step;
      const endM = end ? end.getHours() * 60 + end.getMinutes() : aligned + step;
      const span = Math.max(1, Math.ceil((Math.max(endM, aligned + step) - aligned) / step));
      for (let i = 0; i < span; i++) occupied.add(aligned + i * step);
      if (!eventStarts.has(aligned)) {
        eventStarts.set(aligned, {
          kind: "event",
          minutes: aligned,
          label: formatHm(aligned),
          event,
          spanSlots: span,
        });
      }
    }

    const items: SlotItem[] = [];
    for (let m = startMin; m < endMin; m += step) {
      const ev = eventStarts.get(m);
      if (ev) {
        items.push(ev);
        continue;
      }
      if (occupied.has(m)) continue;
      items.push({ kind: "empty", minutes: m, label: formatHm(m) });
    }
    return items;
  }, [dayEvents, slotMinTime, slotMaxTime, step]);

  return (
    <div className="flex flex-col flex-1 min-h-0">
      <div className="shrink-0 sticky top-0 z-20 space-y-2 bg-white dark:bg-gray-800 pb-2 border-b border-gray-100 dark:border-neutral-700">
        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={() => onDateChange(addDaysIso(dateIso, -1))}
            className="p-2.5 rounded-lg border border-gray-200 dark:border-neutral-600 text-gray-700 dark:text-gray-200 touch-manipulation"
            aria-label="Dia anterior"
          >
            <ChevronLeft size={18} />
          </button>
          <div className="flex-1 min-w-0 text-center px-1">
            <p className="text-sm font-semibold text-gray-900 dark:text-gray-100 capitalize truncate">
              {formatLabel(dateIso)}
            </p>
          </div>
          <button
            type="button"
            onClick={() => onDateChange(addDaysIso(dateIso, 1))}
            className="p-2.5 rounded-lg border border-gray-200 dark:border-neutral-600 text-gray-700 dark:text-gray-200 touch-manipulation"
            aria-label="Próximo dia"
          >
            <ChevronRight size={18} />
          </button>
        </div>
        <input
          type="date"
          value={dateIso}
          onChange={(e) => e.target.value && onDateChange(e.target.value)}
          className="w-full rounded-lg border border-gray-200 dark:border-neutral-600 bg-white dark:bg-neutral-800 px-3 py-2.5 text-sm font-medium text-gray-900 dark:text-gray-100 touch-manipulation [color-scheme:light] dark:[color-scheme:dark]"
          aria-label="Escolher qualquer data"
        />
      </div>

      <div
        className="flex-1 min-h-0 overflow-y-auto overscroll-contain pb-28"
        style={{ WebkitOverflowScrolling: "touch", touchAction: "pan-y" }}
      >
        {slots.length === 0 ? (
          <p className="text-sm text-gray-500 py-8 text-center">Sem horários neste dia.</p>
        ) : (
          <ul className="divide-y divide-gray-100 dark:divide-neutral-700">
            {slots.map((slot) => {
              if (slot.kind === "event") {
                const ev = slot.event;
                return (
                  <li key={`e-${ev.id}-${slot.minutes}`}>
                    <button
                      type="button"
                      onClick={() => onOpenEvent(ev)}
                      className="w-full flex gap-3 px-2 py-2.5 text-left touch-manipulation active:opacity-80"
                      style={{
                        minHeight: Math.max(48, slot.spanSlots * 40),
                        backgroundColor: ev.backgroundColor || "#fce7f3",
                      }}
                    >
                      <span className="w-12 shrink-0 text-xs font-semibold text-gray-800 pt-0.5">
                        {slot.label}
                      </span>
                      <span className="min-w-0 flex-1">
                        <span className="block text-sm font-medium text-gray-900 truncate">
                          {ev.title}
                        </span>
                        {ev.extendedProps?.professional_name ? (
                          <span className="block text-xs text-gray-700/80 truncate">
                            {ev.extendedProps.professional_name}
                          </span>
                        ) : null}
                      </span>
                    </button>
                  </li>
                );
              }
              return (
                <li key={`s-${slot.minutes}`}>
                  <button
                    type="button"
                    onClick={() => onSlotClick(slotDate(dateIso, slot.minutes))}
                    className="w-full flex gap-3 px-2 py-3.5 text-left touch-manipulation active:bg-pink-50 dark:active:bg-neutral-700 min-h-[48px]"
                  >
                    <span className="w-12 shrink-0 text-xs font-medium text-gray-500">
                      {slot.label}
                    </span>
                    <span className="text-xs text-gray-400 self-center">Toque para agendar</span>
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </div>
  );
}
