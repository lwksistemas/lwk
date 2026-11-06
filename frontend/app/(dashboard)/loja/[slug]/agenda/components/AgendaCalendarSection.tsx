"use client";

import { lazy, Suspense, useCallback, useEffect, useMemo, useRef, useState, type CSSProperties } from "react";
import { CLINICA_AGENDA_SNAP_DURATION } from "@/lib/clinica-beleza-constants";
import { duracaoSlotAgenda, intervaloAgendaMinutos } from "@/lib/intervalo-agenda";
import {
  aplicarHorarioAgendaEvento,
  eventosParaFullCalendar,
} from "@/hooks/clinica-beleza/agenda-data/agenda-event-mappers";
import {
  idsEventosSimultaneosOutrosProf,
  idsEventosSobrepostosMesmoProf,
  makeAgendaFcEventContent,
} from "@/hooks/clinica-beleza/agenda-data/agenda-fc-event-content";
import type { AgendaEventData } from "@/lib/clinica-beleza-agenda-types";
import type {
  DateClickArg,
  EventClickArg,
  EventDropArg,
  EventResizeDoneArg,
} from "@/types/fullcalendar-handlers";
import { AgendaListaColunas } from "./AgendaListaColunas";
import { AgendaMobileDayView } from "./AgendaMobileDayView";
import { AgendaDiaColunas } from "./AgendaDiaColunas";
import { AgendaStatusLegenda } from "./AgendaStatusLegenda";
import { marcarIgnorarClickGradeAgenda, toAgendaDiaIso } from "@/hooks/clinica-beleza/agenda-data/agenda-dia-colunas-utils";
import type { ClinicaProfessional } from "@/lib/clinica-beleza-entities";
import {
  AGENDA_VISUAL_DEFAULT,
  agendaVisualStyleVars,
  type AgendaVisualId,
} from "@/lib/clinica-agenda-visual";
import { syncAgendaFetchRangeToVisible } from "@/lib/clinica-beleza-cadastros-api";

const FullCalendar = lazy(() => import("@fullcalendar-v7/react"));

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

function fcViewFromGrade(view: "day" | "week" | "month"): string {
  if (view === "week") return "timeGridWeek";
  if (view === "month") return "dayGridMonth";
  return "timeGridDay";
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
  onMoverGrade,
  onRedimensionarGrade,
  visual = AGENDA_VISUAL_DEFAULT,
  onVisibleRangeChange,
}: {
  modoAgenda: "grade" | "lista";
  eventos: AgendaEventData[];
  calendarPlugins: unknown[];
  ptBrLocale: unknown;
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
  onMoverGrade?: (evt: AgendaEventData, start: Date, professionalId: number | null) => void;
  onRedimensionarGrade?: (evt: AgendaEventData, duracaoMinutos: number) => void;
  visual?: AgendaVisualId;
  /** Chamado quando a janela da API precisa expandir ao navegar no calendário. */
  onVisibleRangeChange?: () => void;
}) {
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
  const eventosFc = useMemo(
    () => eventosParaFullCalendar(stableEventos, selectedProfessional),
    [stableEventos, selectedProfessional],
  );
  const idsConflito = useMemo(() => idsEventosSobrepostosMesmoProf(eventosFc), [eventosFc]);
  const idsSimultaneos = useMemo(
    () =>
      selectedProfessional ? new Set<string>() : idsEventosSimultaneosOutrosProf(eventosFc),
    [eventosFc, selectedProfessional],
  );
  const eventContent = useMemo(
    () => makeAgendaFcEventContent({ showProfessional: !selectedProfessional }),
    [selectedProfessional],
  );
  const eventClassNames = useCallback(
    (arg: { event: { id: string; extendedProps?: Record<string, unknown> } }) => {
      const classes = ["agenda-fc-event"];
      const p = arg.event.extendedProps || {};
      if (p.isBloqueio) classes.push("agenda-fc-event-bloqueio");
      if (p.isIntervalo) classes.push("agenda-fc-event-intervalo");
      if (idsConflito.has(String(arg.event.id))) classes.push("agenda-fc-event-conflito");
      else if (idsSimultaneos.has(String(arg.event.id))) classes.push("agenda-fc-event-simultaneo");
      return classes;
    },
    [idsConflito, idsSimultaneos],
  );
  const rangeSyncTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const handleDatesSet = useCallback(
    (arg: {
      startStr?: string;
      endStr?: string;
      view: { type: string; calendar: { getDate: () => Date }; activeStart?: Date; activeEnd?: Date };
    }) => {
      setDiaIso(toAgendaDiaIso(arg.view.calendar.getDate()));
      if (arg.view.type === "timeGridDay") setGradeView("day");
      else if (arg.view.type === "timeGridWeek") setGradeView("week");
      else if (arg.view.type === "dayGridMonth") setGradeView("month");

      const start =
        (arg.startStr || arg.view.activeStart?.toISOString() || "").slice(0, 10);
      const end = (arg.endStr || arg.view.activeEnd?.toISOString() || "").slice(0, 10);
      if (!start || !end || !onVisibleRangeChange) return;
      if (rangeSyncTimer.current) clearTimeout(rangeSyncTimer.current);
      rangeSyncTimer.current = setTimeout(() => {
        if (syncAgendaFetchRangeToVisible(start, end)) onVisibleRangeChange();
      }, 280);
    },
    [onVisibleRangeChange],
  );

  const marcarArrasto = useCallback((dragging: boolean) => {
    isDraggingRef.current = dragging;
    if (parentDraggingRef) parentDraggingRef.current = dragging;
  }, [parentDraggingRef]);

  const handleEventDrop = useCallback((info: EventDropArg) => {
    marcarIgnorarClickGradeAgenda();
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
    marcarIgnorarClickGradeAgenda();
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

  /** Dia com vários profissionais e sem filtro: grade por coluna. Senão = FullCalendar do tema. */
  const usarColunasDia =
    gradeView === "day" && !selectedProfessional && professionals.length > 1;
  const passoAgenda = intervaloAgendaMinutos(
    professionals.find((p) => String(p.id) === String(selectedProfessional)),
  );
  const slotAgenda = duracaoSlotAgenda(passoAgenda);

  if (isMobileUi === null) {
    return (
      <div className="flex flex-1 items-center justify-center min-h-[200px] text-sm text-gray-500">
        Carregando agenda...
      </div>
    );
  }

  if (isMobileUi && modoAgenda === "grade") {
    return (
      <div className="flex flex-col min-h-0 flex-1 overflow-y-auto p-2">
        <AgendaMobileDayView
          dateIso={diaIso}
          onDateChange={(iso) => {
            setDiaIso(iso);
            if (syncAgendaFetchRangeToVisible(iso, iso)) onVisibleRangeChange?.();
          }}
          eventos={eventos}
          slotMinTime={slotMinTime}
          slotMaxTime={slotMaxTime}
          stepMinutes={passoAgenda}
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

  if (usarColunasDia) {
    return (
      <div className="flex-1 min-h-0 flex flex-col overflow-hidden">
        <AgendaDiaColunas
          dateIso={diaIso}
          onDateChange={(iso) => {
            setDiaIso(iso);
            if (syncAgendaFetchRangeToVisible(iso, iso)) onVisibleRangeChange?.();
          }}
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
          onMover={onMoverGrade}
          onRedimensionar={onRedimensionarGrade}
          onArrastoAtivo={marcarArrasto}
          visual={visual}
        />
        <AgendaStatusLegenda />
      </div>
    );
  }

  const fcView = fcViewFromGrade(gradeView);

  return (
    <div className="flex flex-col min-h-0 flex-1 overflow-hidden">
      <div
        className="flex-1 min-h-0 p-2 sm:p-3 overflow-y-auto overscroll-contain agenda-scroll-root fc-agenda-calendar-root agenda-v7-root"
        data-agenda-visual={visual}
        style={agendaVisualStyleVars(visual) as CSSProperties}
      >
        {calendarPlugins.length > 0 && ptBrLocale ? (
          <Suspense fallback={<div className="flex items-center justify-center h-40 text-sm text-gray-500">Carregando calendário...</div>}>
          <FullCalendar
            key={`desktop-${selectedProfessional}-${fcView}-${visual}-${slotAgenda}`}
            plugins={calendarPlugins as never[]}
            initialView={fcView}
            initialDate={diaIso}
            locale={ptBrLocale as never}
            editable
            eventStartEditable
            eventDurationEditable
            eventAllow={(_info: unknown, dragged: { extendedProps?: Record<string, unknown>; start?: Date | null } | null) => {
              const props = dragged?.extendedProps || {};
              if (props.isBloqueio || props.isIntervalo) return true;
              const inicio = dragged?.start;
              if (!inicio) return true;
              return inicio.getTime() >= Date.now();
            }}
            selectable
            selectMirror
            selectConstraint={temHorarioExpediente ? "businessHours" : undefined}
            dayMaxEvents={3}
            moreLinkClick="popover"
            eventMinHeight={28}
            eventShortHeight={28}
            eventMaxStack={3}
            eventContent={eventContent as never}
            eventClassNames={eventClassNames as never}
            weekends
            nowIndicator
            events={eventosFc}
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
            eventDrop={handleEventDrop as never}
            eventResize={handleEventResize as never}
            eventClick={onEventClick as never}
            dateClick={onDateClick as never}
            datesSet={handleDatesSet as never}
            height="auto"
            headerToolbar={{
              left: "prev,next today",
              center: "title",
              right: "timeGridDay,timeGridWeek,dayGridMonth",
            }}
            buttonText={{
              today: "Hoje",
              month: "Mês",
              week: "Semana",
              day: "Dia",
            }}
            slotMinTime={slotMinTime}
            slotMaxTime={slotMaxTime}
            allDaySlot={false}
            slotDuration={slotAgenda}
            slotLabelInterval={slotAgenda}
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
      <AgendaStatusLegenda />
    </div>
  );
}
