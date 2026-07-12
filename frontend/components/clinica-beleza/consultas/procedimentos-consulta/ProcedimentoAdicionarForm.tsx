"use client";

import { useMemo, useState } from "react";
import { Loader2 } from "lucide-react";
import { toUpperCase } from "@/lib/format-br";
import {
  PROCEDURE_CATEGORIA_OPTIONS,
  procedureCategoriaLabel,
  resolveProcedureCategoriaSlug,
} from "@/lib/clinica-beleza-categories";
import type { ProcedureOption } from "./procedimentos-consulta-types";
import { PROCEDIMENTOS_SELECT_CLASS } from "./procedimentos-consulta-types";

function procedureCat(p: ProcedureOption): string {
  return resolveProcedureCategoriaSlug(p.categoria || "") || "outro";
}

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
  const [categoriaAtiva, setCategoriaAtiva] = useState("");

  const categoriasDisponiveis = useMemo(() => {
    const counts = new Map<string, number>();
    for (const p of opcoesDisponiveis) {
      const slug = procedureCat(p);
      counts.set(slug, (counts.get(slug) || 0) + 1);
    }
    const cards: { value: string; label: string; count: number }[] = PROCEDURE_CATEGORIA_OPTIONS.filter((o) => (counts.get(o.value) || 0) > 0).map(
      (o) => ({ value: o.value, label: o.label, count: counts.get(o.value) || 0 }),
    );
    for (const [slug, count] of counts) {
      if (!cards.some((c) => c.value === slug)) {
        cards.push({
          value: slug,
          label: procedureCategoriaLabel(slug) || slug,
          count,
        });
      }
    }
    return cards.sort((a, b) => b.count - a.count || a.label.localeCompare(b.label));
  }, [opcoesDisponiveis]);

  const filtrados = useMemo(() => {
    if (!categoriaAtiva) return opcoesDisponiveis;
    return opcoesDisponiveis.filter((p) => procedureCat(p) === categoriaAtiva);
  }, [opcoesDisponiveis, categoriaAtiva]);

  return (
    <div className="p-3 rounded-lg border border-gray-200 dark:border-neutral-700 bg-gray-50/80 dark:bg-neutral-800/40 space-y-2">
      <label className="block text-xs font-medium text-gray-700 dark:text-gray-300">
        Incluir procedimento
      </label>

      {categoriasDisponiveis.length > 1 && (
        <div className="flex flex-wrap gap-1.5">
          <button
            type="button"
            onClick={() => {
              setCategoriaAtiva("");
              onProcedureChange("");
            }}
            className={`px-2.5 py-1 rounded-full text-xs font-medium border transition-colors ${
              !categoriaAtiva
                ? "text-white border-transparent"
                : "border-gray-300 dark:border-neutral-600 text-gray-600 dark:text-gray-300"
            }`}
            style={!categoriaAtiva ? { backgroundColor: "var(--cb-primary, #8B3D52)" } : undefined}
          >
            Todas
          </button>
          {categoriasDisponiveis.map((cat) => (
            <button
              key={cat.value}
              type="button"
              onClick={() => {
                setCategoriaAtiva(cat.value);
                onProcedureChange("");
              }}
              className={`px-2.5 py-1 rounded-full text-xs font-medium border transition-colors ${
                categoriaAtiva === cat.value
                  ? "text-white border-transparent"
                  : "border-gray-300 dark:border-neutral-600 text-gray-600 dark:text-gray-300"
              }`}
              style={
                categoriaAtiva === cat.value
                  ? { backgroundColor: "var(--cb-primary, #8B3D52)" }
                  : undefined
              }
            >
              {cat.label} ({cat.count})
            </button>
          ))}
        </div>
      )}

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
            {toUpperCase(p.nome)}
            {!categoriaAtiva ? ` · ${procedureCategoriaLabel(procedureCat(p))}` : ""}
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
