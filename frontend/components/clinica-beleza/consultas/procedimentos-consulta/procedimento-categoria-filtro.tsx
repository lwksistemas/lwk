"use client";

import { useMemo, useState } from "react";
import {
  PROCEDURE_CATEGORIA_OPTIONS,
  procedureCategoriaLabel,
  procedureItemCategoriaSlug,
} from "@/lib/clinica-beleza-categories";

export type CategoriaChip = { value: string; label: string; count: number };

type ComCategoria = { categoria?: string | null; category?: string | null };

export function listarCategoriasProcedimento<T extends ComCategoria>(itens: T[]): CategoriaChip[] {
  const counts = new Map<string, number>();
  for (const p of itens) {
    const slug = procedureItemCategoriaSlug(p);
    counts.set(slug, (counts.get(slug) || 0) + 1);
  }
  const cards: CategoriaChip[] = PROCEDURE_CATEGORIA_OPTIONS.filter((o) => (counts.get(o.value) || 0) > 0).map(
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
}

export function filtrarProcedimentosPorCategoria<T extends ComCategoria>(
  itens: T[],
  categoriaAtiva: string,
): T[] {
  if (!categoriaAtiva) return itens;
  return itens.filter((p) => procedureItemCategoriaSlug(p) === categoriaAtiva);
}

export function useProcedimentoCategoriaFiltro<T extends ComCategoria>(itens: T[]) {
  const [categoriaAtiva, setCategoriaAtiva] = useState("");
  const categoriasDisponiveis = useMemo(() => listarCategoriasProcedimento(itens), [itens]);
  const filtrados = useMemo(
    () => filtrarProcedimentosPorCategoria(itens, categoriaAtiva),
    [itens, categoriaAtiva],
  );
  return { categoriaAtiva, setCategoriaAtiva, categoriasDisponiveis, filtrados };
}

export function ProcedimentoCategoriaChips({
  categoriasDisponiveis,
  categoriaAtiva,
  onChange,
}: {
  categoriasDisponiveis: CategoriaChip[];
  categoriaAtiva: string;
  onChange: (slug: string) => void;
}) {
  if (categoriasDisponiveis.length <= 1) return null;
  return (
    <div className="flex flex-wrap gap-1.5">
      <button
        type="button"
        onClick={() => onChange("")}
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
          onClick={() => onChange(cat.value)}
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
  );
}
