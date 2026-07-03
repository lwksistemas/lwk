import { AlertTriangle } from "lucide-react";

export function ProcedimentosConsultaAlerts({ erro, avisoTermo }: { erro: string; avisoTermo: string }) {
  return (
    <>
      {erro && (
        <div className="p-2.5 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-xs">
          {erro}
        </div>
      )}
      {avisoTermo && (
        <div className="p-2.5 rounded-lg bg-amber-50 dark:bg-amber-900/20 text-amber-800 dark:text-amber-200 text-xs flex gap-2">
          <AlertTriangle size={14} className="shrink-0 mt-0.5" />
          <span>{avisoTermo}</span>
        </div>
      )}
    </>
  );
}
