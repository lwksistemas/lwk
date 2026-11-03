/** Tipos mínimos dos handlers do FullCalendar (clínica + CRM), sem depender do pacote v6. */

export type FullCalendarEventLike = {
  id: string;
  title: string;
  start: Date | null;
  end: Date | null;
  backgroundColor?: string;
  borderColor?: string;
  textColor?: string;
  extendedProps: Record<string, unknown>;
  setExtendedProp?: (name: string, value: unknown) => void;
};

export type EventClickArg = {
  event: FullCalendarEventLike;
  jsEvent?: MouseEvent;
  el?: HTMLElement;
};

export type DateClickArg = {
  date: Date;
  dateStr?: string;
  allDay: boolean;
  jsEvent?: MouseEvent;
  dayEl?: HTMLElement;
};

export type EventDropArg = {
  event: FullCalendarEventLike;
  oldEvent: FullCalendarEventLike;
  delta?: unknown;
  revert: () => void;
  jsEvent?: MouseEvent;
};

export type EventResizeDoneArg = {
  event: FullCalendarEventLike;
  oldEvent: FullCalendarEventLike;
  startDelta?: unknown;
  endDelta?: unknown;
  revert: () => void;
  jsEvent?: MouseEvent;
};
