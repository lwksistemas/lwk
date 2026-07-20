"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { CalendarDays } from "lucide-react";
import {
  CLINICA_AGENDA_SLOT_DURATION,
  CLINICA_AGENDA_SLOT_LABEL_INTERVAL,
  CLINICA_AGENDA_SNAP_DURATION,
} from "@/lib/clinica-beleza-constants";
import type { AgendaEventData } from "@/lib/clinica-beleza-agenda-types";
import type { EventClickArg, EventDropArg } from "@fullcalendar/core";
import type { DateClickArg, EventResizeDoneArg } from "@fullcalendar/interaction";
import { AgendaListaColunas } from "./AgendaListaColunas";

const FullCalendar = dynamic(() => import("@fullcalendar/react"), {
  ssr: false,
  loading: () => <div className="flex items-center justify-center h-40 text-sm text-gray-500">Carregando calendário...</div>,
});

function toInputDate(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

export function AgendaCalendarSection({
  modoAgenda,
  eventos,
  calendarPlugins,
  ptBrLocale,
  isMobile,
  selectedProfessional,
  temHorarioExpediente,
  businessHours,
  hiddenDays,
  slotMinTime,
  slotMaxTime,
  onAbrirLista,
  onEventClick,
  onDateClick,
  onEventDrop,
  onEventResize,
}: {
  modoAgenda: "grade" | "lista";
  eventos: AgendaEventData[];
  calendarPlugins: unknown[];
  ptBrLocale: unknown;
  isMobile: boolean;
  selectedProfessional: string;
  temHorarioExpediente: boolean;
  businessHours: unknown;
  hiddenDays: number[];
  slotMinTime: string;
  slotMaxTime: string;
  onAbrirLista: (evt: AgendaEventData) => void;
  onEventClick: (info: EventClickArg) => void;
  onDateClick: (info: DateClickArg) => void;
  onEventDrop: (info: EventDropArg) => void;
  onEventResize: (info: EventResizeDoneArg) => void;
}) {
  const [currentDateIso, setCurrentDateIso] = useState(() => toInputDate(new Date()));
  /** Incrementa só ao escolher data no input — remonta o FC sem usar ref no dynamic(). */
  const [jumpKey, setJumpKey] = useState(0);

  const gradeMobile = modoAgenda === "grade" && isMobile;

  const irParaData = (iso: string) => {
    if (!iso) return;
    setCurrentDateIso(iso);
    setJumpKey((k) => k + 1);
  };

  return (
    <div
      className={`flex-1 min-h-0 flex flex-col p-2 sm:p-3 overflow-y-auto overscroll-contain fc-agenda-scroll-host ${
        modoAgenda === "grade" ? "fc-agenda-calendar-root" : ""
      }`}
      style={{ WebkitOverflowScrolling: "touch", touchAction: "pan-y" }}
    >
      {gradeMobile && (
        <div className="shrink-0 sticky top-0 z-20 mb-2 bg-white/95 dark:bg-gray-800/95 backdrop-blur-sm pb-1">
          <label className="flex items-center gap-2 rounded-lg border border-gray-200 dark:border-neutral-600 bg-white dark:bg-neutral-800 px-2.5 py-2 text-sm text-gray-800 dark:text-gray-100">
            <CalendarDays size={16} className="text-[#8B3D52] shrink-0" aria-hidden />
            <span className="text-xs text-gray-500 dark:text-gray-400 shrink-0">Dia</span>
            <input
              type="date"
              value={currentDateIso}
              onChange={(e) => irParaData(e.target.value)}
              className="flex-1 min-w-0 bg-transparent text-sm font-medium text-gray-900 dark:text-gray-100 outline-none [color-scheme:light] dark:[color-scheme:dark]"
              aria-label="Escolher data da agenda"
            />
          </label>
        </div>
      )}

      {modoAgenda === "lista" ? (
        <div className="pb-4">
          <AgendaListaColunas eventos={eventos} onAbrir={onAbrirLista} />
        </div>
      ) : calendarPlugins.length > 0 && ptBrLocale ? (
        <div className={gradeMobile ? "pb-28 min-w-0" : "min-w-0"}>
          <FullCalendar
            key={`${isMobile ? "m" : "d"}-${selectedProfessional}-${jumpKey}`}
            plugins={calendarPlugins as never[]}
            initialView={isMobile ? "timeGridDay" : "timeGridWeek"}
            initialDate={currentDateIso}
            locale={ptBrLocale as never}
            editable={!isMobile}
            eventStartEditable={!isMobile}
            eventDurationEditable={!isMobile}
            selectable={!isMobile}
            selectMirror={!isMobile}
            selectConstraint={
              !isMobile && temHorarioExpediente ? "businessHours" : undefined
            }
            dayMaxEvents={isMobile ? 6 : true}
            weekends
            events={eventos}
            eventDrop={onEventDrop}
            eventResize={onEventResize}
            eventClick={onEventClick}
            dateClick={onDateClick}
            datesSet={(arg) => {
              try {
                const d = arg.view?.currentStart ?? arg.start;
                if (d instanceof Date && !Number.isNaN(d.getTime())) {
                  setCurrentDateIso(toInputDate(d));
                }
              } catch {
                // não derruba a página se o calendário emitir datesSet incompleto
              }
            }}
            height="auto"
            headerToolbar={
              isMobile
                ? { left: "prev,next", center: "title", right: "today" }
                : {
                    left: "prev,next today",
                    center: "title",
                    right: "timeGridDay,timeGridWeek,dayGridMonth",
                  }
            }
            buttonText={isMobile ? { today: "Hoje" } : undefined}
            slotMinTime={slotMinTime}
            slotMaxTime={slotMaxTime}
            allDaySlot={false}
            slotDuration={CLINICA_AGENDA_SLOT_DURATION}
            slotLabelInterval={CLINICA_AGENDA_SLOT_LABEL_INTERVAL}
            snapDuration={CLINICA_AGENDA_SNAP_DURATION}
            businessHours={businessHours as never}
            hiddenDays={hiddenDays}
          />
        </div>
      ) : null}
    </div>
  );
}
