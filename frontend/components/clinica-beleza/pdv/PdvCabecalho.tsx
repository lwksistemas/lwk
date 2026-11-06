import { ChevronDown, DollarSign, History, Lock, ShoppingCart } from "lucide-react";
import { rosa } from "./pdv-tipos";

export function PdvCabecalho({
  onHistorico,
  caixaAberto,
  onFechamento,
  onAlternarMenu,
  caixaResponsavel,
  onAbrirCaixa,
  menuCaixa,
}: {
  onHistorico: () => void;
  caixaAberto: boolean;
  onFechamento: () => void;
  onAlternarMenu: () => void;
  caixaResponsavel: string;
  onAbrirCaixa: () => void;
  menuCaixa: boolean;
}) {
  return (
    <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
      <div className="flex items-center gap-3">
        <span className="flex h-11 w-11 items-center justify-center rounded-xl text-white" style={{ backgroundColor: rosa }}>
          <ShoppingCart size={20} />
        </span>
        <div>
          <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">PDV / Caixa</h1>
          <p className="text-sm text-gray-500">Recepção • Atendimentos • Vendas</p>
        </div>
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <button type="button" onClick={onHistorico} className="inline-flex items-center gap-1.5 rounded-full border border-gray-200 bg-white px-3 py-2 text-sm text-gray-700">
          <History size={15} /> Caixa fechado
        </button>
        {caixaAberto && (
          <button type="button" onClick={onFechamento} className="inline-flex items-center gap-1.5 rounded-full border border-gray-200 bg-white px-3 py-2 text-sm text-gray-700">
            <Lock size={15} /> Fechamento do caixa
          </button>
        )}
        <div className="relative">
          {caixaAberto ? (
            <button type="button" onClick={onAlternarMenu} className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-3 py-2 text-sm font-medium text-emerald-700">
              <DollarSign size={15} />
              <span>Caixa Aberto</span>
              {caixaResponsavel && <span>{caixaResponsavel}</span>}
              <ChevronDown size={14} />
            </button>
          ) : (
            <button type="button" onClick={onAbrirCaixa} className="inline-flex items-center gap-1.5 rounded-full px-3 py-2 text-sm font-medium text-white" style={{ backgroundColor: rosa }}>
              <DollarSign size={15} /> Abrir caixa
            </button>
          )}
          {menuCaixa && caixaAberto && (
            <div className="absolute right-0 z-20 mt-1 w-64 rounded-xl border bg-white p-2 shadow-lg">
              <p className="px-2 py-1 text-xs text-gray-500">Responsável pelo recebimento</p>
              <p className="px-2 pb-1 text-sm font-medium text-gray-800">{caixaResponsavel || "—"}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
