"use client";

import { X } from "lucide-react";
import type { PacienteFotoItem } from "@/lib/clinica-beleza-api";

interface ConsultaFotosComparacaoModalProps {
  fotos: PacienteFotoItem[];
  onClose: () => void;
}

const MAX_COMPARAR = 3;
const MIN_COMPARAR = 2;

export function ConsultaFotosComparacaoModal({ fotos, onClose }: ConsultaFotosComparacaoModalProps) {
  const colsComparacao =
    fotos.length >= MAX_COMPARAR
      ? "md:grid-cols-3"
      : fotos.length === MIN_COMPARAR
        ? "md:grid-cols-2"
        : "md:grid-cols-1";

  return (
    <div
      className="fixed inset-0 z-[60] bg-black flex flex-col"
      role="dialog"
      aria-modal
    >
      <div className="flex items-center justify-between px-4 py-3 bg-black/80 text-white shrink-0">
        <span className="text-sm font-medium">
          Comparação de {fotos.length} foto{fotos.length !== 1 ? "s" : ""} — tela cheia
        </span>
        <button
          type="button"
          onClick={onClose}
          className="p-2 rounded-lg hover:bg-white/10"
        >
          <X size={22} />
        </button>
      </div>
      <div className={`flex-1 grid grid-cols-1 ${colsComparacao} gap-0 min-h-0`}>
        {fotos.map((f, i) => (
          <div key={f.id} className="relative flex flex-col min-h-0">
            <p className="text-xs text-white/70 px-3 py-1 shrink-0 bg-black/60 text-center">
              Foto {i + 1} — {f.consulta_data} ({f.origem_display})
            </p>
            <div className="flex-1 min-h-0 overflow-hidden bg-neutral-900">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={f.url}
                alt={`Comparação ${i + 1}`}
                className="w-full h-full object-cover"
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
