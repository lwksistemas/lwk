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
  const limparArrasto = useRef<(() => void) | null>(null);

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
      limparArrasto.current?.();
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
      const cursorAnterior = document.body.style.cursor;
      const selecaoAnterior = document.body.style.userSelect;
      document.body.style.cursor = "col-resize";
      document.body.style.userSelect = "none";
      const aoMover = (evento: PointerEvent) => {
        const arrasto = dragRef.current;
        if (!arrasto) return;
        const proxima = clampLarguraColuna(arrasto.startW + (evento.clientX - arrasto.startX));
        setWidths((prev) => (prev[arrasto.id] === proxima ? prev : { ...prev, [arrasto.id]: proxima }));
      };
      const aoSoltar = () => {
        limparArrasto.current?.();
        dragRef.current = null;
        setArrastando(false);
        ignorarClickRef.current = true;
        window.setTimeout(() => {
          ignorarClickRef.current = false;
        }, 200);
      };
      const limpar = () => {
        document.body.style.cursor = cursorAnterior;
        document.body.style.userSelect = selecaoAnterior;
        window.removeEventListener("pointermove", aoMover);
        window.removeEventListener("pointerup", aoSoltar);
        window.removeEventListener("pointercancel", aoSoltar);
        limparArrasto.current = null;
      };
      limparArrasto.current = limpar;
      window.addEventListener("pointermove", aoMover);
      window.addEventListener("pointerup", aoSoltar);
      window.addEventListener("pointercancel", aoSoltar);
    },
    [defaultWidth],
  );

  useEffect(() => () => limparArrasto.current?.(), []);

  const deveIgnorarClick = useCallback(
    () => ignorarClickRef.current || Boolean(dragRef.current),
    [],
  );

  return { template, iniciar, arrastando, deveIgnorarClick, hasCustomWidths };
}

export function AlcaLarguraColuna({
  onPointerDown,
  className = "",
}: {
  onPointerDown: (e: React.PointerEvent) => void;
  className?: string;
}) {
  return (
    <span
      role="separator"
      aria-orientation="vertical"
      aria-label="Redimensionar coluna"
      title="Arraste para mudar a largura"
      className={`absolute top-0 right-0 z-30 h-full w-3 cursor-col-resize hover:bg-violet-400/40 active:bg-violet-500/50 ${className}`}
      onPointerDown={onPointerDown}
    />
  );
}
