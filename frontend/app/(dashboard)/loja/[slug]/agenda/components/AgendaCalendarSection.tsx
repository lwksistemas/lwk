"use client";

import { lazy, Suspense, useCallback, useEffect, useRef, useState } from "react";
import {
  CLINICA_AGENDA_SLOT_DURATION,
  CLINICA_AGENDA_SLOT_LABEL_INTERVAL,
  CLINICA_AGENDA_SNAP_DURATION,
} from "@/lib/clinica-beleza-constants";
import { aplicarHorarioAgendaEvento } from "@/hooks/clinica-beleza/agenda-data/agenda-event-mappers";
import type { AgendaEventData } from "@/lib/clinica-beleza-agenda-types";
import type { EventClickArg, EventDropArg } from "@fullcalendar/core";
import type { DateClickArg, EventResizeDoneArg } from "@fullcalendar/interaction";
import { AgendaListaColunas } from "./AgendaListaColunas";
import { AgendaMobileDayView } from "./AgendaMobileDayView";
import { AgendaDiaColunas } from "./AgendaDiaColunas";
import { toAgendaDiaIso } from "@/hooks/clinica-beleza/agenda-data/agenda-dia-colunas-utils";
import type { ClinicaProfessional } from "@/lib/clinica-beleza-entities";

const FullCalendar = lazy(() => import("@fullcalendar/react"));

function toInputDate(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

function findVerticalScroller(start: HTMLElement): HTMLElement {
  let node: HTMLElement | null = start;
  while (node) {
    const overflowY = window.getComputedStyle(node).overflowY;
    if (
      (overflowY === "auto" || overflowY === "scroll") &&
      node.scrollHeight > node.clientHeight + 1
    ) {
      return node;
    }
    node = node.parentElement;
  }
  return (document.scrollingElement || document.documentElement) as HTMLElement;
}

function wheelDeltaY(e: WheelEvent, scroller: HTMLElement): number {
  if (e.deltaMode === 1) return e.deltaY * 16;
  if (e.deltaMode === 2) return e.deltaY * scroller.clientHeight;
  return e.deltaY;
}

const AGENDA_SCROLL_ROOT = ".agenda-scroll-root";

/** Roda no calendário/lista move a barra da página (FullCalendar e overflow-x da tabela engolem o wheel). */
function useAgendaPageWheel(active: boolean) {
  useEffect(() => {
    if (!active) return;

    const onWheel = (e: WheelEvent) => {
      if (e.ctrlKey || e.deltaY === 0) return;
      const target = e.target;
      if (!(target instanceof Element)) return;
      const root = target.closest(AGENDA_SCROLL_ROOT);
      if (!root) return;

      const scroller = findVerticalScroller(root as HTMLElement);
      const max = scroller.scrollHeight - scroller.clientHeight;
      if (max <= 1) return;
      const next = Math.min(max, Math.max(0, scroller.scrollTop + wheelDeltaY(e, scroller)));
      if (next === scroller.scrollTop) return;
      scroller.scrollTop = next;
      e.preventDefault();
    };

    document.addEventListener("wheel", onWheel, { capture: true, passive: false });
    return () => document.removeEventListener("wheel", onWheel, true);
  }, [active]);
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
  isDraggingRef: parentDraggingRef,
  professionals = [],
  onNovoHorario,
  onVerLista,
  onMoverGrade,
  onRedimensionarGrade,
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
  onEventDrop: (info: EventDropArg) => void | Promise<void>;
  onEventResize: (info: EventResizeDoneArg) => void | Promise<void>;
  isDraggingRef?: React.MutableRefObject<boolean>;
  professionals?: ClinicaProfessional[];
  onNovoHorario?: (date: Date, professionalId: number) => void;
  onVerLista?: () => void;
  onMoverGrade?: (evt: AgendaEventData, start: Date, professionalId: number) => void;
  onRedimensionarGrade?: (evt: AgendaEventData, duracaoMinutos: number) => void;
}) {
  const [mobileDateIso, setMobileDateIso] = useState(() => toInputDate(new Date()));
  const [gradeView, setGradeView] = useState<"day" | "week" | "month">("day");
  const [diaIso, setDiaIso] = useState(() => toAgendaDiaIso(new Date()));
  const [, setFreezeTick] = useState(0);
  const isDraggingRef = useRef(false);
  const dropHandlingRef = useRef(false);
  const frozenEventsRef = useRef(eventos);
  if (!isDraggingRef.current) {
    frozenEventsRef.current = eventos;
  }
  const stableEventos = isDraggingRef.current ? frozenEventsRef.current : eventos;

  const marcarArrasto = useCallback((dragging: boolean) => {
    isDraggingRef.current = dragging;
    if (parentDraggingRef) parentDraggingRef.current = dragging;
  }, [parentDraggingRef]);

  const handleEventDrop = useCallback((info: EventDropArg) => {
    dropHandlingRef.current = true;
    const start = info.event.start?.toISOString();
    const end = info.event.end?.toISOString();
    if (start) {
      frozenEventsRef.current = aplicarHorarioAgendaEvento(
        frozenEventsRef.current,
        String(info.event.id),
        start,
        end,
      );
    }
    void Promise.resolve(onEventDrop(info)).finally(() => {
      dropHandlingRef.current = false;
      marcarArrasto(false);
      setFreezeTick((n) => n + 1);
    });
  }, [marcarArrasto, onEventDrop]);

  const handleEventResize = useCallback((info: EventResizeDoneArg) => {
    dropHandlingRef.current = true;
    const start = info.event.start?.toISOString();
    const end = info.event.end?.toISOString();
    if (start) {
      frozenEventsRef.current = aplicarHorarioAgendaEvento(
        frozenEventsRef.current,
        String(info.event.id),
        start,
        end,
      );
    }
    void Promise.resolve(onEventResize(info)).finally(() => {
      dropHandlingRef.current = false;
      marcarArrasto(false);
      setFreezeTick((n) => n + 1);
    });
  }, [marcarArrasto, onEventResize]);
  /** null = viewport ainda não medido — não monta FullCalendar no celular. */
  const [isMobileUi, setIsMobileUi] = useState<boolean | null>(null);
  useAgendaPageWheel(
    isMobileUi === false || (isMobileUi === true && modoAgenda === "lista"),
  );

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
      <div className="flex-1 min-h-0 p-2 sm:p-3 overflow-auto overscroll-contain agenda-scroll-root">
        <AgendaListaColunas eventos={eventos} onAbrir={onAbrirLista} />
      </div>
    );
  }

  if (gradeView === "day") {
    return (
      <div className="flex-1 min-h-0 flex flex-col overflow-hidden">
        <AgendaDiaColunas
          dateIso={diaIso}
          onDateChange={setDiaIso}
          eventos={eventos}
          professionals={professionals}
          selectedProfessional={selectedProfessional}
          slotMinTime={slotMinTime}
          slotMaxTime={slotMaxTime}
          onOpenEvent={onAbrirLista}
          onSlotClick={(date, professionalId) => {
            onNovoHorario?.(date, professionalId);
            onDateClick({ date, allDay: false } as DateClickArg);
          }}
          onMudarVisao={(view) => setGradeView(view)}
          onVerLista={onVerLista}
          onMover={onMoverGrade}
          onRedimensionar={onRedimensionarGrade}
        />
      </div>
    );
  }

  return (
    <div className="flex-1 min-h-0 p-2 sm:p-3 overflow-y-auto overscroll-contain agenda-scroll-root fc-agenda-calendar-root">
      {calendarPlugins.length > 0 && ptBrLocale ? (
        <Suspense fallback={<div className="flex items-center justify-center h-40 text-sm text-gray-500">Carregando calendário...</div>}>
        <FullCalendar
          key={`desktop-${selectedProfessional}-${gradeView}`}
          plugins={calendarPlugins as never[]}
          initialView={gradeView === "month" ? "dayGridMonth" : "timeGridWeek"}
          initialDate={diaIso}
          locale={ptBrLocale as never}
          editable
          eventStartEditable
          eventDurationEditable
          selectable
          selectMirror
          selectConstraint={temHorarioExpediente ? "businessHours" : undefined}
          dayMaxEvents
          weekends
          events={stableEventos}
          eventDragStart={() => {
            frozenEventsRef.current = eventos;
            marcarArrasto(true);
          }}
          eventDragStop={() => {
            // setTimeout (não microtask): o FullCalendar às vezes dispara
            // eventDrop no frame seguinte. Soltar o freeze antes disso
            // cancela o drop e o PATCH nem sai.
            window.setTimeout(() => {
              if (!dropHandlingRef.current) {
                marcarArrasto(false);
                setFreezeTick((n) => n + 1);
              }
            }, 250);
          }}
          eventResizeStart={() => {
            frozenEventsRef.current = eventos;
            marcarArrasto(true);
          }}
          eventDrop={handleEventDrop}
          eventResize={handleEventResize}
          eventClick={onEventClick}
          dateClick={onDateClick}
          datesSet={(arg) => {
            setDiaIso(toAgendaDiaIso(arg.view.calendar.getDate()));
          }}
          height="auto"
          customButtons={{
            visaoDia: {
              text: "Dia",
              click: () => setGradeView("day"),
            },
          }}
          headerToolbar={{
            left: "prev,next today",
            center: "title",
            right: "visaoDia,timeGridWeek,dayGridMonth",
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
        </Suspense>
      ) : (
        <div className="flex items-center justify-center h-40 text-sm text-gray-500">
          Carregando calendário...
        </div>
      )}
    </div>
  );
}
