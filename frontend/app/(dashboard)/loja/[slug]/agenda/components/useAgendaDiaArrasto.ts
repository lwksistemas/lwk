"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { AgendaEventData } from "@/lib/clinica-beleza-agenda-types";
import {
  clampMinutosInicio,
  combinarDiaEHorario,
  duracaoEventoMinutos,
  duracaoResizeNaGrade,
  eventProfessionalId,
  minutosArrastoNaGrade,
  movimentoGradeAlterou,
  slotDateFromMinutes,
} from "@/hooks/clinica-beleza/agenda-data/agenda-dia-colunas-utils";

const LIMIAR_PX = 6;

export type AgendaDiaArrasto =
  | {
      modo: "mover";
      evt: AgendaEventData;
      start: Date;
      end: Date;
      professionalId: number;
      durationMin: number;
      offsetY: number;
      x: number;
      y: number;
      moved: boolean;
      hoverDiaIso?: string;
      hoverProfessionalId?: number;
    }
  | {
      modo: "resize";
      evt: AgendaEventData;
      start: Date;
      professionalId: number;
      startMin: number;
      durationMin: number;
      originalDurationMin: number;
      x: number;
      y: number;
      moved: boolean;
    };

function alvoArrasto(x: number, y: number): HTMLElement | null {
  const stack = document.elementsFromPoint(x, y);
  for (const node of stack) {
    if (!(node instanceof Element)) continue;
    if (node.closest("[data-agenda-ghost]")) continue;
    if (node.closest("[data-agenda-card]")) continue;
    const hit = node.closest(
      "[data-agenda-dia-iso], [data-agenda-coluna], [data-agenda-semana-dia]",
    ) as HTMLElement | null;
    if (hit) return hit;
  }
  return null;
}

export function useAgendaDiaArrasto({
  dateIso,
  minMin,
  maxMin,
  pxPerMin,
  onMover,
  onRedimensionar,
  onDateChange,
}: {
  dateIso: string;
  minMin: number;
  maxMin: number;
  pxPerMin: number;
  onMover?: (evt: AgendaEventData, start: Date, professionalId: number) => void;
  onRedimensionar?: (evt: AgendaEventData, duracaoMinutos: number) => void;
  onDateChange: (iso: string) => void;
}) {
  const [arrasto, setArrasto] = useState<AgendaDiaArrasto | null>(null);
  const arrastoRef = useRef<AgendaDiaArrasto | null>(null);
  const ignorarClickRef = useRef(false);
  arrastoRef.current = arrasto;

  const iniciarMover = useCallback((
    evt: AgendaEventData,
    start: Date,
    end: Date,
    e: React.PointerEvent,
  ) => {
    if (evt.extendedProps?.isIntervalo || evt.extendedProps?.isBloqueio) return;
    const professionalId = eventProfessionalId(evt);
    if (professionalId == null) return;
    const card = (e.currentTarget as HTMLElement).closest("[data-agenda-card]") as HTMLElement | null;
    const top = card?.getBoundingClientRect().top ?? e.clientY;
    const next: AgendaDiaArrasto = {
      modo: "mover",
      evt,
      start,
      end,
      professionalId,
      durationMin: duracaoEventoMinutos(evt, start, end),
      offsetY: e.clientY - top,
      x: e.clientX,
      y: e.clientY,
      moved: false,
    };
    arrastoRef.current = next;
    setArrasto(next);
  }, []);

  const iniciarResize = useCallback((
    evt: AgendaEventData,
    start: Date,
    end: Date,
    e: React.PointerEvent,
  ) => {
    e.stopPropagation();
    if (evt.extendedProps?.isIntervalo || evt.extendedProps?.isBloqueio) return;
    const professionalId = eventProfessionalId(evt);
    if (professionalId == null) return;
    const startMin = start.getHours() * 60 + start.getMinutes();
    const durationMin = duracaoEventoMinutos(evt, start, end);
    const next: AgendaDiaArrasto = {
      modo: "resize",
      evt,
      start,
      professionalId,
      startMin,
      durationMin,
      originalDurationMin: durationMin,
      x: e.clientX,
      y: e.clientY,
      moved: false,
    };
    arrastoRef.current = next;
    setArrasto(next);
  }, []);

  useEffect(() => {
    if (arrasto == null) return;

    const onMove = (e: PointerEvent) => {
      const atual = arrastoRef.current;
      if (!atual) return;
      const dx = e.clientX - atual.x;
      const dy = e.clientY - atual.y;
      const moved = atual.moved || Math.hypot(dx, dy) > LIMIAR_PX;
      if (atual.modo === "resize") {
        const grade =
          document.querySelector(`[data-agenda-card-id="${atual.evt.id}"]`)?.closest("[data-agenda-grade]") as
            | HTMLElement
            | null;
        const gridTop = grade?.getBoundingClientRect().top ?? 0;
        const durationMin = duracaoResizeNaGrade(
          atual.startMin,
          e.clientY,
          gridTop,
          minMin,
          maxMin,
          pxPerMin,
        );
        const next = { ...atual, x: e.clientX, y: e.clientY, moved, durationMin };
        arrastoRef.current = next;
        setArrasto(next);
        return;
      }
      const hit = alvoArrasto(e.clientX, e.clientY);
      const hoverDiaIso =
        hit?.getAttribute("data-agenda-semana-dia") ||
        hit?.getAttribute("data-agenda-dia-iso") ||
        undefined;
      const hoverProfessionalId = hit?.hasAttribute("data-agenda-coluna")
        ? Number(hit.getAttribute("data-agenda-coluna"))
        : undefined;
      const next = {
        ...atual,
        x: e.clientX,
        y: e.clientY,
        moved,
        hoverDiaIso,
        hoverProfessionalId: Number.isFinite(hoverProfessionalId) ? hoverProfessionalId : undefined,
      };
      arrastoRef.current = next;
      setArrasto(next);
    };

    const onUp = (e: PointerEvent) => {
      const atual = arrastoRef.current;
      arrastoRef.current = null;
      setArrasto(null);
      if (!atual?.moved) return;
      ignorarClickRef.current = true;
      window.setTimeout(() => {
        ignorarClickRef.current = false;
      }, 200);
      if (atual.modo === "resize") {
        if (atual.durationMin !== atual.originalDurationMin) {
          onRedimensionar?.(atual.evt, atual.durationMin);
        }
        return;
      }
      const hit = alvoArrasto(e.clientX, e.clientY);
      if (!hit) return;
      const semanaIso = hit.getAttribute("data-agenda-semana-dia");
      if (semanaIso) {
        const gridTop = hit.getBoundingClientRect().top;
        const minutes = clampMinutosInicio(
          minutosArrastoNaGrade(e.clientY, gridTop, minMin, pxPerMin, atual.offsetY),
          minMin,
          maxMin,
          atual.durationMin,
        );
        const start = slotDateFromMinutes(semanaIso, minutes);
        if (movimentoGradeAlterou(atual.evt, start, atual.professionalId)) {
          onMover?.(atual.evt, start, atual.professionalId);
          if (semanaIso !== dateIso) onDateChange(semanaIso);
        }
        return;
      }
      const diaIso = hit.getAttribute("data-agenda-dia-iso");
      if (diaIso) {
        const start = combinarDiaEHorario(diaIso, atual.start);
        if (movimentoGradeAlterou(atual.evt, start, atual.professionalId)) {
          onMover?.(atual.evt, start, atual.professionalId);
          if (diaIso !== dateIso) onDateChange(diaIso);
        }
        return;
      }
      const pid = Number(hit.getAttribute("data-agenda-coluna"));
      if (!Number.isFinite(pid)) return;
      const gridTop = hit.getBoundingClientRect().top;
      const minutes = clampMinutosInicio(
        minutosArrastoNaGrade(e.clientY, gridTop, minMin, pxPerMin, atual.offsetY),
        minMin,
        maxMin,
        atual.durationMin,
      );
      const start = slotDateFromMinutes(dateIso, minutes);
      if (movimentoGradeAlterou(atual.evt, start, pid)) {
        onMover?.(atual.evt, start, pid);
      }
    };

    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp);
    window.addEventListener("pointercancel", onUp);
    return () => {
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerup", onUp);
      window.removeEventListener("pointercancel", onUp);
    };
  }, [arrasto != null, dateIso, maxMin, minMin, onDateChange, onMover, onRedimensionar, pxPerMin]);

  const deveIgnorarClick = useCallback(() => ignorarClickRef.current || Boolean(arrastoRef.current?.moved), []);

  return { arrasto, iniciarMover, iniciarResize, deveIgnorarClick };
}
