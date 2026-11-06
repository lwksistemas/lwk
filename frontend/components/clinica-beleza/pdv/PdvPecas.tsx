import type { ReactNode } from "react";
import { Trash2 } from "lucide-react";
import { formatCurrency } from "@/lib/financeiro-helpers";

export function Indicador({ icone, cor, titulo, valor }: { icone: ReactNode; cor: string; titulo: string; valor: string }) {
  return (
    <div className="flex items-center gap-3 rounded-2xl border border-gray-200 bg-white px-3 py-3">
      <span className={`flex h-9 w-9 items-center justify-center rounded-full ${cor}`}>{icone}</span>
      <span>
        <span className="block text-xs text-gray-500">{titulo}</span>
        <span className="block text-lg font-semibold text-gray-900">{valor}</span>
      </span>
    </div>
  );
}

export function Bloco({ titulo, children }: { titulo: string; children: ReactNode }) {
  return (
    <div>
      <p className="mb-2 text-sm font-medium text-gray-700">{titulo}</p>
      <div className="space-y-2">{children}</div>
    </div>
  );
}

export function LinhaCarrinho({ tipo, nome, detalhe, valor, onRemove }: { tipo: string; nome: string; detalhe: string; valor: number; onRemove?: () => void }) {
  return (
    <div className="flex items-center gap-3 rounded-xl border px-3 py-2">
      <span className="rounded-full bg-pink-50 px-2 py-0.5 text-[11px] font-medium text-pink-700">{tipo}</span>
      <span className="min-w-0 flex-1">
        <span className="block truncate text-sm font-medium">{nome}</span>
        {detalhe && <span className="block text-xs text-gray-500">{detalhe}</span>}
      </span>
      <span className="text-sm font-semibold">{formatCurrency(valor)}</span>
      {onRemove && <button type="button" onClick={onRemove} aria-label={`Remover ${nome}`}><Trash2 size={14} className="text-gray-400" /></button>}
    </div>
  );
}
