import { useEffect, useRef, useState } from "react";
import type { ReadonlyURLSearchParams } from "next/navigation";
import type { AgendaEventData } from "@/lib/clinica-beleza-agenda-types";

export function useAgendaPageEffects({
  searchParams,
  selectedProfessional,
  carregarDados,
  recarregarEventos,
  showModal,
  selectedEvent,
  eventos,
  setSelectedEvent,
  setSelectedDate,
  setShowCreateModal,
  isMutatingRef,
  isDraggingRef,
}: {
  searchParams: ReadonlyURLSearchParams;
  selectedProfessional: string;
  carregarDados: () => Promise<void>;
  recarregarEventos?: () => Promise<void>;
  showModal: boolean;
  selectedEvent: AgendaEventData | null;
  eventos: AgendaEventData[];
  setSelectedEvent: (event: AgendaEventData | null) => void;
  setSelectedDate: (date: Date | null) => void;
  setShowCreateModal: (open: boolean) => void;
  isMutatingRef?: React.MutableRefObject<boolean>;
  isDraggingRef?: React.MutableRefObject<boolean>;
}) {
  const [calendarPlugins, setCalendarPlugins] = useState<unknown[]>([]);
  const [ptBrLocale, setPtBrLocale] = useState<unknown>(null);
  const [isMobile, setIsMobile] = useState(false);
  const carregarDadosRef = useRef(carregarDados);
  const recarregarEventosRef = useRef(recarregarEventos);
  const userScrollingRef = useRef(false);
  const scrollPauseTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const desktopPluginsReadyRef = useRef(false);

  carregarDadosRef.current = carregarDados;
  recarregarEventosRef.current = recarregarEventos;

  useEffect(() => {
    if (searchParams.get("novo") === "1") {
      setSelectedDate(new Date());
      setShowCreateModal(true);
    }
  }, [searchParams, setSelectedDate, setShowCreateModal]);

  useEffect(() => {
    // Celular usa AgendaMobileDayView — não carrega FullCalendar (economiza memória/Android).
    if (typeof window !== "undefined" && window.innerWidth < 640) {
      void carregarDadosRef.current();
      return;
    }
    const loadPlugins = async () => {
      // Visão Mês usa dayGrid + interaction. Dia/Semana são views próprias (sem timeGrid).
      const [dayGrid, interaction, ptBr] = await Promise.all([
        import("@fullcalendar/daygrid"),
        import("@fullcalendar/interaction"),
        import("@fullcalendar/core/locales/pt-br"),
      ]);
      setCalendarPlugins([dayGrid.default, interaction.default]);
      setPtBrLocale(ptBr.default);
    };
    void loadPlugins();
  }, []);

  useEffect(() => {
    if (!desktopPluginsReadyRef.current) {
      desktopPluginsReadyRef.current = true;
      return;
    }
    void carregarDadosRef.current();
  }, [selectedProfessional]);

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
      if (el?.closest?.(".fc-scroller") || el?.closest?.(".agenda-scroll-root")) markScrolling();
    };
    document.addEventListener("scroll", onScroll, true);
    return () => {
      document.removeEventListener("scroll", onScroll, true);
      if (scrollPauseTimerRef.current) clearTimeout(scrollPauseTimerRef.current);
    };
  }, []);

  useEffect(() => {
    const handler = () => setTimeout(() => {
      if (isMutatingRef?.current || isDraggingRef?.current) return;
      void carregarDadosRef.current();
    }, 1200);
    window.addEventListener("offline-sync-done", handler);
    return () => window.removeEventListener("offline-sync-done", handler);
  }, [isDraggingRef, isMutatingRef]);

  useEffect(() => {
    if (typeof navigator !== "undefined" && !navigator.onLine) return;
    // Polling de eventos (8s; 4s com modal em aguardando). Pausa em arrasto, mutação e scroll.

    const aguardando =
      showModal &&
      (selectedEvent?.extendedProps.status === "SCHEDULED" ||
        selectedEvent?.extendedProps.status === "PENDING");
    const intervalMs = aguardando ? 4000 : 8000;

    const poll = () => {
      if (document.visibilityState !== "visible") return;
      if (isMutatingRef?.current || isDraggingRef?.current) return;
      if (userScrollingRef.current) return;
      void (recarregarEventosRef.current ?? carregarDadosRef.current)();
    };

    if (aguardando) poll();
    const timer = window.setInterval(poll, intervalMs);
    const onVisibility = () => {
      if (document.visibilityState !== "visible") return;
      if (isMutatingRef?.current || isDraggingRef?.current) return;
      void (recarregarEventosRef.current ?? carregarDadosRef.current)();
    };
    document.addEventListener("visibilitychange", onVisibility);
    return () => {
      window.clearInterval(timer);
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, [
    selectedProfessional,
    showModal,
    selectedEvent?.extendedProps.status,
    isDraggingRef,
    isMutatingRef,
  ]);

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

  return { calendarPlugins, ptBrLocale, isMobile };
}
