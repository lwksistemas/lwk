"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import {
  CLINICA_AGENDA_SLOT_DURATION,
  CLINICA_AGENDA_SLOT_LABEL_INTERVAL,
  CLINICA_AGENDA_SNAP_DURATION,
} from "@/lib/clinica-beleza-constants";
import type { AgendaEventData } from "@/lib/clinica-beleza-agenda-types";
import type { EventClickArg, EventDropArg } from "@fullcalendar/core";
import type { DateClickArg, EventResizeDoneArg } from "@fullcalendar/interaction";
import { AgendaListaColunas } from "./AgendaListaColunas";
import { AgendaMobileDayView } from "./AgendaMobileDayView";

const FullCalendar = dynamic(() => import("@fullcalendar/react"), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-40 text-sm text-gray-500">
      Carregando calendário...
    </div>
  ),
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
  const [mobileDateIso, setMobileDateIso] = useState(() => toInputDate(new Date()));
  /** null = viewport ainda não medido — não monta FullCalendar no celular. */
  const [isMobileUi, setIsMobileUi] = useState<boolean | null>(null);

  useEffect(() => {
    const check = () => setIsMobileUi(window.innerWidth < 640);
    check();
    window.addEventListener("resize", check);
    return () => window.removeEventListener("resize", check);
  }, []);

  if (isMobileUi === null) {
    return (
      <div className="flex flex-1 items-center justify-center min-h-[200px] text-sm text-gray-500">
        Carregando agenda...
      </div>
    );
  }

  if (isMobileUi && modoAgenda === "grade") {
    return (
      <div className="flex flex-col min-h-[60vh] p-2">
        <AgendaMobileDayView
          dateIso={mobileDateIso}
          onDateChange={setMobileDateIso}
          eventos={eventos}
          slotMinTime={slotMinTime}
          slotMaxTime={slotMaxTime}
          onOpenEvent={onAbrirLista}
          onSlotClick={(date) => {
            onDateClick({ date, allDay: false } as DateClickArg);
          }}
        />
      </div>
    );
  }

  if (modoAgenda === "lista") {
    return (
      <div className="flex-1 min-h-0 p-2 sm:p-3 overflow-y-auto overscroll-contain">
        <AgendaListaColunas eventos={eventos} onAbrir={onAbrirLista} />
      </div>
    );
  }

  return (
    <div className="flex-1 min-h-0 p-2 sm:p-3 overflow-y-auto overscroll-contain fc-agenda-calendar-root">
      {calendarPlugins.length > 0 && ptBrLocale ? (
        <FullCalendar
          key={`desktop-${selectedProfessional}`}
          plugins={calendarPlugins as never[]}
          initialView="timeGridWeek"
          locale={ptBrLocale as never}
          editable
          eventStartEditable
          eventDurationEditable
          selectable
          selectMirror
          selectConstraint={temHorarioExpediente ? "businessHours" : undefined}
          dayMaxEvents
          weekends
          events={eventos}
          eventDrop={onEventDrop}
          eventResize={onEventResize}
          eventClick={onEventClick}
          dateClick={onDateClick}
          height="auto"
          headerToolbar={{
            left: "prev,next today",
            center: "title",
            right: "timeGridDay,timeGridWeek,dayGridMonth",
          }}
          slotMinTime={slotMinTime}
          slotMaxTime={slotMaxTime}
          allDaySlot={false}
          slotDuration={CLINICA_AGENDA_SLOT_DURATION}
          slotLabelInterval={CLINICA_AGENDA_SLOT_LABEL_INTERVAL}
          snapDuration={CLINICA_AGENDA_SNAP_DURATION}
          businessHours={businessHours as never}
          hiddenDays={hiddenDays}
        />
      ) : (
        <div className="flex items-center justify-center h-40 text-sm text-gray-500">
          Carregando calendário...
        </div>
      )}
    </div>
  );
}
