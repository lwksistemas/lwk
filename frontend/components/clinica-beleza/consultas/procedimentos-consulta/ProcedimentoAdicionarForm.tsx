"use client";

import { Loader2 } from "lucide-react";
import { toUpperCase } from "@/lib/format-br";
import {
  procedureCategoriaLabel,
  procedureItemCategoriaSlug,
  procedureSelectLabel,
} from "@/lib/clinica-beleza-categories";
import { ProcedimentoCategoriaChips, useProcedimentoCategoriaFiltro } from "./procedimento-categoria-filtro";
import type { ProcedureOption } from "./procedimentos-consulta-types";
import { PROCEDIMENTOS_SELECT_CLASS } from "./procedimentos-consulta-types";

export function ProcedimentoAdicionarForm({
  opcoesDisponiveis,
  procedureId,
  saving,
  onProcedureChange,
  onAdicionar,
  onCancel,
}: {
  opcoesDisponiveis: ProcedureOption[];
  procedureId: number | "";
  saving: boolean;
  onProcedureChange: (id: number | "") => void;
  onAdicionar: () => void;
  onCancel: () => void;
}) {
  const { categoriaAtiva, setCategoriaAtiva, categoriasDisponiveis, filtrados } =
    useProcedimentoCategoriaFiltro(opcoesDisponiveis);

  return (
    <div className="p-3 rounded-lg border border-gray-200 dark:border-neutral-700 bg-gray-50/80 dark:bg-neutral-800/40 space-y-2">
      <label className="block text-xs font-medium text-gray-700 dark:text-gray-300">
        Incluir procedimento
      </label>

      <ProcedimentoCategoriaChips
        categoriasDisponiveis={categoriasDisponiveis}
        categoriaAtiva={categoriaAtiva}
        onChange={(slug) => {
          setCategoriaAtiva(slug);
          onProcedureChange("");
        }}
      />

      <select
        value={procedureId}
        onChange={(e) => onProcedureChange(e.target.value ? Number(e.target.value) : "")}
        className={PROCEDIMENTOS_SELECT_CLASS}
        autoFocus
      >
        <option value="">
          {categoriaAtiva
            ? `Selecione de ${procedureCategoriaLabel(categoriaAtiva)}...`
            : "Selecione..."}
        </option>
        {filtrados.map((p) => (
          <option key={p.id} value={p.id}>
            {procedureSelectLabel(toUpperCase(p.nome), procedureItemCategoriaSlug(p), {
              includeCategorySuffix: !categoriaAtiva,
            })}
          </option>
        ))}
      </select>
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={onAdicionar}
          disabled={saving || !procedureId}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-white disabled:opacity-50"
          style={{ backgroundColor: "var(--cb-primary, #8B3D52)" }}
        >
          {saving ? <Loader2 size={14} className="animate-spin" /> : null}
          Incluir
        </button>
        <button
          type="button"
          onClick={onCancel}
          disabled={saving}
          className="px-3 py-1.5 text-xs text-gray-600 dark:text-gray-400"
        >
          Cancelar
        </button>
      </div>
    </div>
  );
}
