"use client";

import { useMemo, useRef, useCallback } from "react";
import { ChevronLeft, ChevronRight, Calendar } from "lucide-react";
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
    weekday: "short",
    day: "2-digit",
    month: "short",
  });
}

function isToday(iso: string): boolean {
  return iso === toInputDate(new Date());
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
  const dateInputRef = useRef<HTMLInputElement>(null);

  // ─── Swipe horizontal para navegar entre dias ───
  const touchStartX = useRef<number | null>(null);
  const touchStartY = useRef<number | null>(null);
  const swiped = useRef(false);

  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    touchStartX.current = e.touches[0].clientX;
    touchStartY.current = e.touches[0].clientY;
    swiped.current = false;
  }, []);

  const handleTouchEnd = useCallback((e: React.TouchEvent) => {
    if (touchStartX.current === null || touchStartY.current === null) return;
    const dx = e.changedTouches[0].clientX - touchStartX.current;
    const dy = e.changedTouches[0].clientY - touchStartY.current;
    touchStartX.current = null;
    touchStartY.current = null;
    // Swipe horizontal > 60px e predominantemente horizontal
    if (Math.abs(dx) > 60 && Math.abs(dx) > Math.abs(dy) * 1.5) {
      swiped.current = true;
      onDateChange(addDaysIso(dateIso, dx < 0 ? 1 : -1));
    }
  }, [dateIso, onDateChange]);

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

  const totalEventos = dayEvents.length;

  return (
    <div className="flex flex-col flex-1 min-h-0">
      {/* Header compacto com navegação e date picker inline */}
      <div className="shrink-0 sticky top-0 z-20 bg-white dark:bg-gray-800 pb-1.5 pt-1 border-b border-gray-100 dark:border-neutral-700">
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => onDateChange(addDaysIso(dateIso, -1))}
            className="p-3 rounded-xl border border-gray-200 dark:border-neutral-600 text-gray-700 dark:text-gray-200 touch-manipulation active:bg-gray-100 dark:active:bg-neutral-700 min-w-[44px] min-h-[44px] flex items-center justify-center"
            aria-label="Dia anterior"
          >
            <ChevronLeft size={20} />
          </button>
          <div className="flex-1 min-w-0 text-center">
            <p className="text-sm font-bold text-gray-900 dark:text-gray-100 capitalize truncate">
              {formatLabel(dateIso)}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {isToday(dateIso) ? "Hoje" : ""} · {totalEventos} {totalEventos === 1 ? "agendamento" : "agendamentos"}
            </p>
          </div>
          <button
            type="button"
            onClick={() => onDateChange(addDaysIso(dateIso, 1))}
            className="p-3 rounded-xl border border-gray-200 dark:border-neutral-600 text-gray-700 dark:text-gray-200 touch-manipulation active:bg-gray-100 dark:active:bg-neutral-700 min-w-[44px] min-h-[44px] flex items-center justify-center"
            aria-label="Próximo dia"
          >
            <ChevronRight size={20} />
          </button>
          <button
            type="button"
            onClick={() => dateInputRef.current?.showPicker()}
            className="p-3 rounded-xl border border-gray-200 dark:border-neutral-600 text-gray-700 dark:text-gray-200 touch-manipulation active:bg-gray-100 dark:active:bg-neutral-700 min-w-[44px] min-h-[44px] flex items-center justify-center"
            aria-label="Escolher data"
          >
            <Calendar size={18} />
          </button>
        </div>
        {/* Input date hidden — ativado via botão calendário */}
        <input
          ref={dateInputRef}
          type="date"
          value={dateIso}
          onChange={(e) => e.target.value && onDateChange(e.target.value)}
          className="sr-only"
          tabIndex={-1}
          aria-hidden="true"
        />
      </div>

      {/* Grade de horários com swipe */}
      <div
        className="flex-1 min-h-0 overflow-y-auto overscroll-contain pb-24"
        style={{ WebkitOverflowScrolling: "touch" }}
        onTouchStart={handleTouchStart}
        onTouchEnd={handleTouchEnd}
      >
        {slots.length === 0 ? (
          <p className="text-sm text-gray-500 py-8 text-center">Sem horários neste dia.</p>
        ) : (
          <ul className="divide-y divide-gray-100 dark:divide-neutral-700">
            {slots.map((slot) => {
              if (slot.kind === "event") {
                const ev = slot.event;
                const statusColor = ev.extendedProps?.status === "COMPLETED"
                  ? "border-l-emerald-500"
                  : ev.extendedProps?.status === "CANCELLED"
                    ? "border-l-red-400"
                    : "border-l-transparent";
                return (
                  <li key={`e-${ev.id}-${slot.minutes}`}>
                    <button
                      type="button"
                      onClick={() => { if (!swiped.current) onOpenEvent(ev); }}
                      className={`w-full flex gap-3 px-3 py-3 text-left touch-manipulation active:opacity-80 border-l-4 ${statusColor} rounded-r-lg`}
                      style={{
                        minHeight: Math.max(56, slot.spanSlots * 44),
                        backgroundColor: ev.backgroundColor || "#fce7f3",
                      }}
                    >
                      <span className="w-11 shrink-0 text-xs font-bold text-gray-800 dark:text-gray-200 pt-0.5">
                        {slot.label}
                      </span>
                      <span className="min-w-0 flex-1">
                        <span className="block text-sm font-semibold text-gray-900 dark:text-gray-100 truncate">
                          {ev.title}
                        </span>
                        {ev.extendedProps?.professional_name && (
                          <span className="block text-xs text-gray-600 dark:text-gray-400 truncate mt-0.5">
                            {ev.extendedProps.professional_name}
                          </span>
                        )}
                        {ev.extendedProps?.procedure_name && (
                          <span className="block text-xs text-gray-500 dark:text-gray-500 truncate">
                            {ev.extendedProps.procedure_name}
                          </span>
                        )}
                      </span>
                    </button>
                  </li>
                );
              }
              return (
                <li key={`s-${slot.minutes}`}>
                  <button
                    type="button"
                    onClick={() => { if (!swiped.current) onSlotClick(slotDate(dateIso, slot.minutes)); }}
                    className="w-full flex gap-3 px-3 py-4 text-left touch-manipulation active:bg-pink-50 dark:active:bg-neutral-700 min-h-[52px]"
                  >
                    <span className="w-11 shrink-0 text-xs font-medium text-gray-400 dark:text-gray-500">
                      {slot.label}
                    </span>
                    <span className="text-xs text-gray-300 dark:text-gray-600 self-center">—</span>
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
