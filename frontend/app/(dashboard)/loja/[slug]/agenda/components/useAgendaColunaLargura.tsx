"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  clampLarguraColuna,
  snapshotLargurasColunas,
  templateLarguraColuna,
} from "@/hooks/clinica-beleza/agenda-data/agenda-dia-colunas-utils";

export function useAgendaColunaLargura(storageKey: string, defaultWidth: number) {
  const [widths, setWidths] = useState<Record<string, number>>({});
  const [ready, setReady] = useState(false);
  const [arrastando, setArrastando] = useState(false);
  const dragRef = useRef<{ id: string; startX: number; startW: number } | null>(null);
  const ignorarClickRef = useRef(false);

  useEffect(() => {
    try {
      const raw = window.localStorage.getItem(storageKey);
      if (raw) {
        const parsed = JSON.parse(raw) as Record<string, number>;
        if (parsed && typeof parsed === "object") setWidths(parsed);
      }
    } catch {
      /* ignore */
    }
    setReady(true);
  }, [storageKey]);

  useEffect(() => {
    if (!ready) return;
    try {
      window.localStorage.setItem(storageKey, JSON.stringify(widths));
    } catch {
      /* ignore */
    }
  }, [ready, storageKey, widths]);

  const hasCustomWidths = Object.keys(widths).length > 0;

  const template = useCallback(
    (id: string) => templateLarguraColuna(widths[id], defaultWidth, hasCustomWidths),
    [defaultWidth, hasCustomWidths, widths],
  );

  const iniciar = useCallback(
    (id: string, e: React.PointerEvent) => {
      if (e.button !== 0) return;
      e.preventDefault();
      e.stopPropagation();
      const wrap = (e.currentTarget as HTMLElement).closest("[data-agenda-col-wrap]");
      const grid = wrap?.parentElement instanceof HTMLElement ? wrap.parentElement : null;
      const measured =
        wrap instanceof HTMLElement ? wrap.getBoundingClientRect().width : defaultWidth;
      dragRef.current = { id, startX: e.clientX, startW: measured };
      setWidths((prev) => ({
        ...prev,
        ...snapshotLargurasColunas(grid),
        [id]: clampLarguraColuna(measured),
      }));
      setArrastando(true);
    },
    [defaultWidth],
  );

  useEffect(() => {
    if (!arrastando) return;
    const prevCursor = document.body.style.cursor;
    const prevSelect = document.body.style.userSelect;
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
    const onMove = (e: PointerEvent) => {
      const drag = dragRef.current;
      if (!drag) return;
      const next = clampLarguraColuna(drag.startW + (e.clientX - drag.startX));
      setWidths((prev) => (prev[drag.id] === next ? prev : { ...prev, [drag.id]: next }));
    };
    const onUp = () => {
      dragRef.current = null;
      setArrastando(false);
      ignorarClickRef.current = true;
      window.setTimeout(() => {
        ignorarClickRef.current = false;
      }, 200);
    };
    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp);
    window.addEventListener("pointercancel", onUp);
    return () => {
      document.body.style.cursor = prevCursor;
      document.body.style.userSelect = prevSelect;
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerup", onUp);
      window.removeEventListener("pointercancel", onUp);
    };
  }, [arrastando]);

  const deveIgnorarClick = useCallback(
    () => ignorarClickRef.current || Boolean(dragRef.current),
    [],
  );

  return { template, iniciar, arrastando, deveIgnorarClick, hasCustomWidths };
}

export function AlcaLarguraColuna({
  onPointerDown,
}: {
  onPointerDown: (e: React.PointerEvent) => void;
}) {
  return (
    <span
      role="separator"
      aria-orientation="vertical"
      aria-label="Redimensionar coluna"
      title="Arraste para mudar a largura"
      className="absolute top-0 right-0 z-30 w-3 h-full cursor-col-resize hover:bg-violet-400/40 active:bg-violet-500/50"
      onPointerDown={onPointerDown}
    />
  );
}
