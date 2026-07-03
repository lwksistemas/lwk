import { X } from "lucide-react";
import type { PacienteFotoItem } from "@/lib/clinica-beleza-api";
import { MAX_FOTOS_COMPARAR, MIN_FOTOS_COMPARAR } from "./fotos-constants";

export function ConsultaFotosCompararModal({
  fotos,
  onClose,
}: {
  fotos: PacienteFotoItem[];
  onClose: () => void;
}) {
  if (fotos.length < MIN_FOTOS_COMPARAR) return null;

  const colsComparacao =
    fotos.length >= MAX_FOTOS_COMPARAR
      ? "md:grid-cols-3"
      : fotos.length === MIN_FOTOS_COMPARAR
        ? "md:grid-cols-2"
        : "md:grid-cols-1";

  return (
    <div className="fixed inset-0 z-[60] bg-black flex flex-col" role="dialog" aria-modal>
      <div className="flex items-center justify-between px-4 py-3 bg-black/80 text-white shrink-0">
        <span className="text-sm font-medium">
          Comparação de {fotos.length} foto{fotos.length !== 1 ? "s" : ""} — tela cheia
        </span>
        <button type="button" onClick={onClose} className="p-2 rounded-lg hover:bg-white/10">
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
              <img src={f.cloudinary_url} alt={`Comparação ${i + 1}`} className="w-full h-full object-cover" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
