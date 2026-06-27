"use client";

import { useEffect, useRef, useState } from "react";
import { ChevronLeft, ChevronRight, X, ZoomIn, ZoomOut } from "lucide-react";
import type { PacienteFotoItem } from "@/lib/clinica-beleza-api";

const ZOOM_MIN = 1;
const ZOOM_MAX = 4;
const ZOOM_STEP = 0.05;

export function PacienteFotoZoomModal({
  foto,
  fotos,
  onClose,
  onChangeFoto,
}: {
  foto: PacienteFotoItem;
  fotos: PacienteFotoItem[];
  onClose: () => void;
  onChangeFoto: (foto: PacienteFotoItem) => void;
}) {
  const [zoomScale, setZoomScale] = useState(1);
  const [zoomPan, setZoomPan] = useState({ x: 0, y: 0 });
  const arrastandoRef = useRef(false);
  const ultimoPontoRef = useRef({ x: 0, y: 0 });

  useEffect(() => {
    setZoomScale(1);
    setZoomPan({ x: 0, y: 0 });
  }, [foto.id]);

  const ajustarZoom = (delta: number) => {
    setZoomScale((s) => {
      const next = Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, +(s + delta).toFixed(2)));
      if (next <= 1) setZoomPan({ x: 0, y: 0 });
      return next;
    });
  };

  const navegar = (dir: -1 | 1) => {
    const idx = fotos.findIndex((f) => f.id === foto.id);
    if (idx < 0) return;
    const next = fotos[idx + dir];
    if (next) onChangeFoto(next);
  };

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
        return;
      }
      const idx = fotos.findIndex((f) => f.id === foto.id);
      if (e.key === "ArrowLeft" && idx > 0) onChangeFoto(fotos[idx - 1]);
      if (e.key === "ArrowRight" && idx >= 0 && idx < fotos.length - 1) onChangeFoto(fotos[idx + 1]);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [foto, fotos, onClose, onChangeFoto]);

  const onWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    ajustarZoom(e.deltaY < 0 ? ZOOM_STEP : -ZOOM_STEP);
  };

  const iniciarArraste = (clientX: number, clientY: number) => {
    if (zoomScale <= 1) return;
    arrastandoRef.current = true;
    ultimoPontoRef.current = { x: clientX, y: clientY };
  };

  const moverArraste = (clientX: number, clientY: number) => {
    if (!arrastandoRef.current || zoomScale <= 1) return;
    const dx = clientX - ultimoPontoRef.current.x;
    const dy = clientY - ultimoPontoRef.current.y;
    ultimoPontoRef.current = { x: clientX, y: clientY };
    setZoomPan((p) => ({ x: p.x + dx, y: p.y + dy }));
  };

  const pararArraste = () => {
    arrastandoRef.current = false;
  };

  const idxAtual = fotos.findIndex((f) => f.id === foto.id);

  return (
    <div
      className="fixed inset-0 z-[55] bg-black/95 flex flex-col"
      role="dialog"
      aria-modal
      aria-label="Visualização ampliada da foto"
    >
      <div className="flex items-center justify-between px-3 py-2 bg-black/80 text-white shrink-0 gap-2">
        <div className="min-w-0 text-xs sm:text-sm truncate">
          {foto.consulta_data || "—"} · {foto.origem_display}
        </div>
        <div className="flex items-center gap-1 shrink-0">
          <button
            type="button"
            onClick={() => navegar(-1)}
            disabled={idxAtual <= 0}
            className="p-2 rounded-lg hover:bg-white/10 disabled:opacity-30"
            title="Foto anterior"
          >
            <ChevronLeft size={20} />
          </button>
          <button
            type="button"
            onClick={() => ajustarZoom(-ZOOM_STEP)}
            disabled={zoomScale <= ZOOM_MIN}
            className="p-2 rounded-lg hover:bg-white/10 disabled:opacity-30"
            title="Diminuir zoom"
          >
            <ZoomOut size={20} />
          </button>
          <span className="text-xs w-12 text-center tabular-nums">{Math.round(zoomScale * 100)}%</span>
          <button
            type="button"
            onClick={() => ajustarZoom(ZOOM_STEP)}
            disabled={zoomScale >= ZOOM_MAX}
            className="p-2 rounded-lg hover:bg-white/10 disabled:opacity-30"
            title="Aumentar zoom"
          >
            <ZoomIn size={20} />
          </button>
          <button
            type="button"
            onClick={() => navegar(1)}
            disabled={idxAtual >= fotos.length - 1}
            className="p-2 rounded-lg hover:bg-white/10 disabled:opacity-30"
            title="Próxima foto"
          >
            <ChevronRight size={20} />
          </button>
          <button
            type="button"
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-white/10 ml-1"
            title="Fechar"
          >
            <X size={22} />
          </button>
        </div>
      </div>
      <div
        className="flex-1 overflow-hidden flex items-center justify-center touch-none select-none"
        onWheel={onWheel}
        onMouseDown={(e) => iniciarArraste(e.clientX, e.clientY)}
        onMouseMove={(e) => moverArraste(e.clientX, e.clientY)}
        onMouseUp={pararArraste}
        onMouseLeave={pararArraste}
        onTouchStart={(e) => {
          const t = e.touches[0];
          if (t) iniciarArraste(t.clientX, t.clientY);
        }}
        onTouchMove={(e) => {
          const t = e.touches[0];
          if (t) moverArraste(t.clientX, t.clientY);
        }}
        onTouchEnd={pararArraste}
      >
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={foto.cloudinary_url}
          alt={`Foto ampliada ${foto.consulta_data}`}
          className="max-w-none transition-transform duration-100"
          style={{
            transform: `translate(${zoomPan.x}px, ${zoomPan.y}px) scale(${zoomScale})`,
            maxHeight: zoomScale === 1 ? "90vh" : "none",
            maxWidth: zoomScale === 1 ? "100%" : "none",
            cursor: zoomScale > 1 ? "grab" : "zoom-in",
          }}
          draggable={false}
          onDoubleClick={() => {
            if (zoomScale < ZOOM_MAX) ajustarZoom(ZOOM_STEP);
          }}
        />
      </div>
      <p className="text-[10px] text-white/50 text-center py-2 shrink-0">
        Botões ou scroll: zoom de 5 em 5% · arraste para mover · duplo clique amplia · Esc fecha
      </p>
    </div>
  );
}
