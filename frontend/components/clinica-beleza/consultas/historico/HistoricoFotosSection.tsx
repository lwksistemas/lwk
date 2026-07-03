import type { PacienteFotoItem } from "@/lib/clinica-beleza-api";

export function HistoricoFotosSection({
  fotos,
  loading,
  onZoom,
}: {
  fotos: PacienteFotoItem[];
  loading: boolean;
  onZoom: (foto: PacienteFotoItem) => void;
}) {
  if (loading) return <p className="text-gray-500 text-sm">Carregando fotos…</p>;
  if (fotos.length === 0) {
    return <p className="text-gray-500 text-sm">Nenhuma foto de acompanhamento registrada.</p>;
  }

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
      {fotos.map((foto) => (
        <button
          key={foto.id}
          type="button"
          onClick={() => onZoom(foto)}
          className="text-left rounded-lg border border-gray-200 dark:border-neutral-600 overflow-hidden hover:border-[#8B3D52] transition-colors"
        >
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={foto.cloudinary_url}
            alt={`Foto ${foto.consulta_data}`}
            className="w-full aspect-square object-cover cursor-zoom-in"
          />
          <p className="text-[10px] text-gray-500 dark:text-gray-400 px-2 py-1.5 truncate">
            {foto.consulta_data || "—"} · {foto.origem_display}
          </p>
        </button>
      ))}
    </div>
  );
}
