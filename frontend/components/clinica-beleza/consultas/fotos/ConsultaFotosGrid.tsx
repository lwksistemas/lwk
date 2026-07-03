import { Check, Trash2 } from "lucide-react";
import type { PacienteFotoItem } from "@/lib/clinica-beleza-api";

export function ConsultaFotosGrid({
  fotos,
  permiteEnviar,
  selecionadas,
  onZoom,
  onToggleSelecao,
  onExcluir,
}: {
  fotos: PacienteFotoItem[];
  permiteEnviar?: boolean;
  selecionadas: number[];
  onZoom: (foto: PacienteFotoItem) => void;
  onToggleSelecao: (id: number) => void;
  onExcluir: (id: number) => void;
}) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
      {fotos.map((f) => {
        const sel = selecionadas.includes(f.id);
        return (
          <div
            key={f.id}
            className={`relative group rounded-xl overflow-hidden border-2 transition-colors ${
              sel ? "border-purple-600 ring-2 ring-purple-300" : "border-gray-200 dark:border-neutral-700"
            }`}
          >
            <button
              type="button"
              onClick={() => onZoom(f)}
              className="block w-full aspect-square cursor-zoom-in"
              title="Ampliar foto"
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={f.cloudinary_url} alt={`Foto ${f.consulta_data}`} className="w-full h-full object-cover" />
            </button>
            <button
              type="button"
              onClick={() => onToggleSelecao(f.id)}
              className={`absolute top-2 left-2 rounded-full p-1.5 shadow transition-colors ${
                sel ? "bg-purple-600 text-white" : "bg-black/50 text-white hover:bg-black/70"
              }`}
              title={sel ? "Desmarcar comparação" : "Selecionar para comparar"}
            >
              <Check size={14} />
            </button>
            <div className="absolute bottom-0 inset-x-0 bg-black/60 text-white text-[10px] px-2 py-1">
              {f.consulta_data || "—"} · {f.origem_display}
            </div>
            {permiteEnviar && (
              <button
                type="button"
                onClick={() => onExcluir(f.id)}
                className="absolute top-2 right-2 p-1.5 rounded-full bg-red-600/90 text-white opacity-0 group-hover:opacity-100 transition-opacity"
                title="Remover"
              >
                <Trash2 size={14} />
              </button>
            )}
          </div>
        );
      })}
    </div>
  );
}
