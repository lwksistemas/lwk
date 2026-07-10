import { Loader2, Plus, Trash2 } from "lucide-react";
import type { AgendaRetornoConfigItem, RetornoProcedimentoRegraItem } from "@/lib/clinica-beleza-api";
import { entityName } from "@/lib/clinica-beleza-entities";
import { RETORNO_INPUT_CLASS } from "./retorno-agenda-utils";

export function RetornoProcedimentoSection({
  config,
  regras,
  proceduresDisponiveis,
  salvando,
  novaRegraProc,
  novaRegraDias,
  onToggleAtivo,
  onNovaRegraProcChange,
  onNovaRegraDiasChange,
  onAdicionarRegra,
  onExcluirRegra,
}: {
  config: AgendaRetornoConfigItem;
  regras: RetornoProcedimentoRegraItem[];
  proceduresDisponiveis: { id: number; nome?: string; name?: string }[];
  salvando: boolean;
  novaRegraProc: number | "";
  novaRegraDias: string;
  onToggleAtivo: (ativo: boolean) => void;
  onNovaRegraProcChange: (id: number | "") => void;
  onNovaRegraDiasChange: (dias: string) => void;
  onAdicionarRegra: () => void;
  onExcluirRegra: (id: number) => void;
}) {
  return (
    <section className="space-y-3 md:pt-0 pt-2 border-t md:border-t-0 border-gray-100 dark:border-neutral-800">
      <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">Retorno por procedimento</h3>
      <p className="text-xs text-gray-500 dark:text-gray-400">
        Após procedimento concluído, acompanhamento dentro do prazo → taxa de consulta isenta
        (procedimentos cobram normalmente).
      </p>
      <label className="flex items-center gap-2 text-sm text-gray-800 dark:text-gray-200">
        <input
          type="checkbox"
          checked={config.retorno_procedimento_ativo}
          disabled={salvando}
          onChange={(e) => onToggleAtivo(e.target.checked)}
          className="rounded border-gray-300"
        />
        Ativar retorno por procedimento
      </label>

      {config.retorno_procedimento_ativo && (
        <div className="space-y-3">
          <ul className="space-y-2">
            {regras.length === 0 ? (
              <li className="text-xs text-gray-500 py-2">Nenhuma regra cadastrada.</li>
            ) : (
              regras.map((r) => (
                <li
                  key={r.id}
                  className="flex items-center justify-between gap-2 p-3 rounded-lg bg-gray-50 dark:bg-neutral-800"
                >
                  <div className="min-w-0">
                    <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                      {r.procedure_name}
                    </span>
                    <span className="block text-xs text-gray-500">{r.dias_retorno} dias</span>
                  </div>
                  <button
                    type="button"
                    onClick={() => onExcluirRegra(r.id)}
                    disabled={salvando}
                    className="p-1.5 rounded hover:bg-red-50 dark:hover:bg-red-900/20 shrink-0"
                    title="Remover"
                  >
                    <Trash2 size={14} className="text-red-500" />
                  </button>
                </li>
              ))
            )}
          </ul>

          {proceduresDisponiveis.length > 0 && (
            <div className="p-3 rounded-lg border border-purple-200 dark:border-purple-800 bg-purple-50/40 dark:bg-purple-900/10 space-y-2">
              <p className="text-xs font-medium text-gray-700 dark:text-gray-300">Nova regra</p>
              <select
                value={novaRegraProc}
                onChange={(e) => onNovaRegraProcChange(e.target.value ? Number(e.target.value) : "")}
                className={RETORNO_INPUT_CLASS}
                disabled={salvando}
              >
                <option value="">Procedimento</option>
                {proceduresDisponiveis.map((p) => (
                  <option key={p.id} value={p.id}>
                    {entityName(p)}
                  </option>
                ))}
              </select>
              <div className="flex gap-2 items-end">
                <div className="flex-1">
                  <label className="block text-xs text-gray-500 mb-1">Prazo (dias)</label>
                  <input
                    type="number"
                    min={1}
                    max={3650}
                    value={novaRegraDias}
                    onChange={(e) => onNovaRegraDiasChange(e.target.value)}
                    className={RETORNO_INPUT_CLASS}
                    disabled={salvando}
                  />
                </div>
                <button
                  type="button"
                  onClick={onAdicionarRegra}
                  disabled={salvando}
                  className="flex items-center gap-1 px-3 py-2 text-white rounded-lg text-sm font-medium disabled:opacity-50 shrink-0"
                  style={{ backgroundColor: 'var(--cb-primary, #8B3D52)' }}
                >
                  {salvando ? <Loader2 size={14} className="animate-spin" /> : <Plus size={14} />}
                  Adicionar
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </section>
  );
}
