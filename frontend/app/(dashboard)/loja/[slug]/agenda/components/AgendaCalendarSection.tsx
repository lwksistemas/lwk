"use client";

import dynamic from "next/dynamic";
import {
  CLINICA_AGENDA_SLOT_DURATION,
  CLINICA_AGENDA_SLOT_LABEL_INTERVAL,
  CLINICA_AGENDA_SNAP_DURATION,
} from "@/lib/clinica-beleza-constants";
import type { AgendaEventData } from "@/lib/clinica-beleza-agenda-types";
import type { EventClickArg, EventDropArg } from "@fullcalendar/core";
import { AgendaListaColunas } from "./AgendaListaColunas";

const FullCalendar = dynamic(() => import("@fullcalendar/react"), {
  ssr: false,
  loading: () => <div className="flex items-center justify-center h-full">Carregando calendário...</div>,
});

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
  onDateClick: (info: { date: Date }) => void;
  onEventDrop: (info: EventDropArg) => void;
  onEventResize: (info: any) => void;
}) {
  return (
    <div
      className={`flex-1 min-h-0 p-2 sm:p-3 overflow-y-auto overscroll-contain ${
        modoAgenda === "grade" ? "fc-agenda-calendar-root" : ""
      }`}
      style={{ WebkitOverflowScrolling: "touch" }}
    >
      {modoAgenda === "lista" ? (
        <AgendaListaColunas eventos={eventos} onAbrir={onAbrirLista} />
      ) : calendarPlugins.length > 0 && ptBrLocale ? (
        <FullCalendar
          key={`${isMobile ? "mobile" : "desktop"}-${selectedProfessional}`}
          plugins={calendarPlugins as never[]}
          initialView={isMobile ? "timeGridDay" : "timeGridWeek"}
          locale={ptBrLocale as never}
          editable
          eventStartEditable
          eventDurationEditable
          selectable
          selectMirror
          selectConstraint={temHorarioExpediente ? "businessHours" : undefined}
          dayMaxEvents={isMobile ? 6 : true}
          weekends
          events={eventos}
          eventDrop={onEventDrop}
          eventResize={onEventResize}
          eventClick={onEventClick}
          dateClick={onDateClick}
          height="auto"
          headerToolbar={
            isMobile
              ? { left: "prev,next", center: "title", right: "today" }
              : { left: "prev,next today", center: "title", right: "timeGridDay,timeGridWeek,dayGridMonth" }
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
      ) : null}
    </div>
  );
}
