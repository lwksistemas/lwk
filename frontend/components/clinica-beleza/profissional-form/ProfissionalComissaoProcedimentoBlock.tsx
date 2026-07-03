import { Plus, Trash2 } from "lucide-react";
import type { ConvenioItem } from "@/lib/clinica-beleza-api";
import { formatConvenioLabel } from "./profissional-form-utils";
import { INPUT_CLASS, type ProfissionalCommission, type ProfissionalProcedure } from "./profissional-form-types";

interface ProfissionalComissaoProcedimentoBlockProps {
  comissoes: ProfissionalCommission[];
  procedures: ProfissionalProcedure[];
  convenios: ConvenioItem[];
  onAdd: () => void;
  onRemove: (idx: number) => void;
  onUpdate: (idx: number, field: string, value: string | number | null) => void;
}

export function ProfissionalComissaoProcedimentoBlock({
  comissoes,
  procedures,
  convenios,
  onAdd,
  onRemove,
  onUpdate,
}: ProfissionalComissaoProcedimentoBlockProps) {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-semibold text-gray-700 dark:text-gray-300">Comissão por Procedimento</p>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            Defina por procedimento e convênio. Ex.: Botox na Unimed R$ fixo; na Santa Casa percentual.
          </p>
        </div>
        <button
          type="button"
          onClick={onAdd}
          className="inline-flex items-center gap-1 text-xs font-medium text-purple-600 dark:text-purple-400 hover:underline"
        >
          <Plus size={14} /> Adicionar
        </button>
      </div>
      {comissoes.length === 0 ? (
        <p className="text-xs text-gray-400 italic">Nenhuma comissão por procedimento configurada.</p>
      ) : (
        <div className="space-y-2">
          {comissoes.map((c, idx) => (
            <div
              key={idx}
              className="flex flex-wrap items-center gap-2 bg-gray-50 dark:bg-neutral-700/30 rounded-lg px-3 py-2.5"
            >
              <div className="flex-1 min-w-[160px]">
                <label className="sr-only">Procedimento</label>
                <select
                  value={c.procedure ?? ""}
                  onChange={(e) =>
                    onUpdate(idx, "procedure", e.target.value ? Number(e.target.value) : null)
                  }
                  className={INPUT_CLASS}
                >
                  <option value="">Procedimento...</option>
                  {procedures.map((p) => (
                    <option key={p.id} value={p.id}>{p.nome}</option>
                  ))}
                </select>
              </div>
              <div className="flex-1 min-w-[140px]">
                <label className="sr-only">Convênio</label>
                <select
                  value={c.convenio ?? ""}
                  onChange={(e) =>
                    onUpdate(idx, "convenio", e.target.value ? Number(e.target.value) : null)
                  }
                  className={INPUT_CLASS}
                >
                  <option value="">Convênio...</option>
                  {convenios.map((cv) => (
                    <option key={cv.id} value={cv.id}>
                      {formatConvenioLabel(cv)}
                    </option>
                  ))}
                </select>
              </div>
              <div className="w-28">
                <select
                  value={c.modo}
                  onChange={(e) => onUpdate(idx, "modo", e.target.value)}
                  className={INPUT_CLASS}
                >
                  <option value="percentual">%</option>
                  <option value="fixo">R$</option>
                </select>
              </div>
              <div className="w-24">
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={c.valor}
                  onChange={(e) => onUpdate(idx, "valor", e.target.value)}
                  className={INPUT_CLASS}
                  placeholder={c.modo === "percentual" ? "30" : "200.00"}
                />
              </div>
              <button
                type="button"
                onClick={() => onRemove(idx)}
                className="p-1.5 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded"
              >
                <Trash2 size={14} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
