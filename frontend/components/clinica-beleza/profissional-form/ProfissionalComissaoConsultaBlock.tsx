import { Plus, Trash2 } from "lucide-react";
import type { LocalAtendimentoItem } from "@/lib/clinica-beleza-api";
import { INPUT_CLASS, type ProfissionalCommission } from "./profissional-form-types";

interface ProfissionalComissaoConsultaBlockProps {
  comissoesConsultaLocal: ProfissionalCommission[];
  locais: LocalAtendimentoItem[];
  locaisDisponiveisConsulta: (idx: number) => LocalAtendimentoItem[];
  onAdd: () => void;
  onRemove: (idx: number) => void;
  onUpdate: (idx: number, field: string, value: string | number | null) => void;
}

export function ProfissionalComissaoConsultaBlock({
  comissoesConsultaLocal,
  locais,
  locaisDisponiveisConsulta,
  onAdd,
  onRemove,
  onUpdate,
}: ProfissionalComissaoConsultaBlockProps) {
  return (
    <div className="bg-purple-50 dark:bg-purple-900/10 border border-purple-200 dark:border-purple-800/40 rounded-lg p-4 space-y-3">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <p className="text-xs font-semibold text-purple-800 dark:text-purple-300">
            Comissão da consulta por local de atendimento
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            Adicione cada local e defina percentual ou valor fixo. A regra vale só no local escolhido.
          </p>
        </div>
        <button
          type="button"
          onClick={onAdd}
          disabled={comissoesConsultaLocal.length >= locais.length}
          className="inline-flex items-center gap-1 text-xs font-medium text-purple-600 dark:text-purple-400 hover:underline disabled:opacity-40 disabled:no-underline"
        >
          <Plus size={14} /> Adicionar local
        </button>
      </div>
      {comissoesConsultaLocal.length === 0 ? (
        <p className="text-xs text-gray-400 italic">
          Ex.: Unidade Moema 35%, Spa Clínico R$ 140 fixo, Teleconsulta 20%.
        </p>
      ) : (
        comissoesConsultaLocal.map((c, idx) => (
          <div
            key={idx}
            className="flex flex-wrap items-center gap-2 bg-white/60 dark:bg-neutral-800/40 rounded-lg px-3 py-2.5"
          >
            <div className="flex-1 min-w-[180px]">
              <label className="sr-only">Local de atendimento</label>
              <select
                value={c.local_atendimento ?? ""}
                onChange={(e) =>
                  onUpdate(idx, "local_atendimento", e.target.value ? Number(e.target.value) : null)
                }
                className={INPUT_CLASS}
              >
                <option value="">Selecione o local...</option>
                {locaisDisponiveisConsulta(idx).map((l) => (
                  <option key={l.id} value={l.id}>{l.nome}</option>
                ))}
              </select>
            </div>
            <div className="w-36">
              <select
                value={c.modo}
                onChange={(e) => onUpdate(idx, "modo", e.target.value)}
                className={INPUT_CLASS}
              >
                <option value="percentual">% do valor</option>
                <option value="fixo">R$ fixo</option>
              </select>
            </div>
            <div className="w-28">
              <input
                type="number"
                step="0.01"
                min="0"
                value={c.valor}
                onChange={(e) => onUpdate(idx, "valor", e.target.value)}
                className={INPUT_CLASS}
                placeholder={c.modo === "percentual" ? "35" : "140.00"}
              />
            </div>
            <button
              type="button"
              onClick={() => onRemove(idx)}
              className="p-1.5 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded"
              aria-label="Remover"
            >
              <Trash2 size={16} />
            </button>
          </div>
        ))
      )}
    </div>
  );
}
