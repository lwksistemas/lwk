import { CheckCircle2, Trash2 } from "lucide-react";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";

export function ConsultaDetailHeaderActions({
  consultaAtiva,
  podeExcluir,
  onFinalizar,
  onExcluir,
}: {
  consultaAtiva: boolean;
  podeExcluir: boolean;
  onFinalizar: () => void;
  onExcluir: () => void;
}) {
  if (!consultaAtiva) return null;

  return (
    <>
      <button
        type="button"
        onClick={onFinalizar}
        className="inline-flex items-center gap-1 px-2.5 sm:px-3 py-1.5 rounded-lg text-white text-xs sm:text-sm font-medium"
        style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
      >
        <CheckCircle2 size={15} />
        <span className="hidden sm:inline">Finalizar consulta</span>
        <span className="sm:hidden">Finalizar</span>
      </button>
      {podeExcluir && (
        <button
          type="button"
          onClick={onExcluir}
          className="inline-flex items-center gap-1 px-2.5 sm:px-3 py-1.5 rounded-lg text-xs sm:text-sm font-medium border border-red-300 dark:border-red-700 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20"
        >
          <Trash2 size={15} />
          <span className="hidden sm:inline">Excluir</span>
        </button>
      )}
    </>
  );
}
