import { useEffect, useRef, useState } from "react";
import type { ReadonlyURLSearchParams } from "next/navigation";
import type { AgendaEventData } from "@/lib/clinica-beleza-agenda-types";

export function useAgendaPageEffects({
  searchParams,
  selectedProfessional,
  carregarDados,
  showModal,
  selectedEvent,
  eventos,
  setSelectedEvent,
  setSelectedDate,
  setShowCreateModal,
}: {
  searchParams: ReadonlyURLSearchParams;
  selectedProfessional: string;
  carregarDados: () => Promise<void>;
  showModal: boolean;
  selectedEvent: AgendaEventData | null;
  eventos: AgendaEventData[];
  setSelectedEvent: (event: AgendaEventData | null) => void;
  setSelectedDate: (date: Date | null) => void;
  setShowCreateModal: (open: boolean) => void;
}) {
  const [calendarPlugins, setCalendarPlugins] = useState<unknown[]>([]);
  const [ptBrLocale, setPtBrLocale] = useState<unknown>(null);
  const [isMobile, setIsMobile] = useState(false);
  const carregarDadosRef = useRef(carregarDados);
  const userScrollingRef = useRef(false);
  const scrollPauseTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  carregarDadosRef.current = carregarDados;

  useEffect(() => {
    if (searchParams.get("novo") === "1") {
      setSelectedDate(new Date());
      setShowCreateModal(true);
    }
  }, [searchParams, setSelectedDate, setShowCreateModal]);

  useEffect(() => {
    const loadPlugins = async () => {
      const [dayGrid, timeGrid, interaction, ptBr] = await Promise.all([
        import("@fullcalendar/daygrid"),
        import("@fullcalendar/timegrid"),
        import("@fullcalendar/interaction"),
        import("@fullcalendar/core/locales/pt-br"),
      ]);
      setCalendarPlugins([dayGrid.default, timeGrid.default, interaction.default]);
      setPtBrLocale(ptBr.default);
    };
    void loadPlugins();
  }, []);

  useEffect(() => {
    if (calendarPlugins.length > 0) void carregarDadosRef.current();
  }, [selectedProfessional, calendarPlugins]);

  useEffect(() => {
    const check = () => setIsMobile(typeof window !== "undefined" && window.innerWidth < 640);
    check();
    window.addEventListener("resize", check);
    return () => window.removeEventListener("resize", check);
  }, []);

  useEffect(() => {
    const markScrolling = () => {
      userScrollingRef.current = true;
      if (scrollPauseTimerRef.current) clearTimeout(scrollPauseTimerRef.current);
      scrollPauseTimerRef.current = setTimeout(() => {
        userScrollingRef.current = false;
      }, 4000);
    };
    const onScroll = (e: Event) => {
      const el = e.target as HTMLElement | null;
      if (el?.closest?.(".fc-scroller") || el?.closest?.(".fc-agenda-calendar-root")) markScrolling();
    };
    document.addEventListener("scroll", onScroll, true);
    return () => {
      document.removeEventListener("scroll", onScroll, true);
      if (scrollPauseTimerRef.current) clearTimeout(scrollPauseTimerRef.current);
    };
  }, []);

  useEffect(() => {
    const handler = () => setTimeout(() => void carregarDadosRef.current(), 1200);
    window.addEventListener("offline-sync-done", handler);
    return () => window.removeEventListener("offline-sync-done", handler);
  }, []);

  useEffect(() => {
    if (!calendarPlugins.length) return;
    if (typeof navigator !== "undefined" && !navigator.onLine) return;
    const aguardando =
      showModal &&
      (selectedEvent?.extendedProps.status === "SCHEDULED" ||
        selectedEvent?.extendedProps.status === "PENDING");
    const intervalMs = aguardando ? 5000 : 15000;
    const timer = window.setInterval(() => {
      if (userScrollingRef.current) return;
      void carregarDadosRef.current();
    }, intervalMs);
    return () => window.clearInterval(timer);
  }, [calendarPlugins.length, selectedProfessional, showModal, selectedEvent?.extendedProps.status]);

  useEffect(() => {
    if (!showModal || !selectedEvent?.extendedProps?.dbId) return;
    const dbId = String(selectedEvent.extendedProps.dbId);
    const atualizado = eventos.find((e) => String(e.extendedProps.dbId) === dbId);
    if (!atualizado) return;
    if (
      atualizado.extendedProps.status !== selectedEvent.extendedProps.status ||
      atualizado.backgroundColor !== selectedEvent.backgroundColor
    ) {
      setSelectedEvent(atualizado);
    }
  }, [
    eventos,
    showModal,
    selectedEvent?.extendedProps?.dbId,
    selectedEvent?.extendedProps.status,
    selectedEvent?.backgroundColor,
    setSelectedEvent,
  ]);

  return { calendarPlugins, ptBrLocale, isMobile, calendarReady: calendarPlugins.length > 0 && ptBrLocale != null };
}
