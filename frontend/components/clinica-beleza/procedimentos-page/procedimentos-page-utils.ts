import type { ConvenioItem } from "@/lib/clinica-beleza-api";
import { entityActive, procedureCategoria } from "@/lib/clinica-beleza-entities";
import {
  PROCEDURE_CATEGORIA_OPTIONS,
  procedureMatchesModule,
  resolveProcedureCategoriaSlug,
} from "@/lib/clinica-beleza-categories";
import { formatCurrency } from "@/lib/financeiro-helpers";
import type { Procedure, ProcedimentoFormState } from "./procedimentos-page-types";
import type { ProcedimentoCategoriaCard } from "./ProcedimentosCategoriasGrid";

export function buildPrecosMapFromMatrix(
  precos: { procedure: number; convenio: number; preco: string }[],
): Record<string, string> {
  const map: Record<string, string> = {};
  for (const row of precos) {
    map[`${row.procedure}:${row.convenio}`] = row.preco;
  }
  return map;
}

export function formatPrecoCelula(
  precosMap: Record<string, string>,
  procId: number,
  convId: number,
): string {
  const val = precosMap[`${procId}:${convId}`];
  return val != null && val !== "" ? formatCurrency(Number(val)) : "—";
}

export function buildPrecosConvenioPayload(
  convenios: ConvenioItem[],
  precosConvenio: Record<number, string>,
) {
  return convenios.map((c) => {
    const raw = precosConvenio[c.id]?.trim();
    return {
      convenio: c.id,
      preco: raw ? raw.replace(",", ".") : null,
    };
  });
}

export function validateProcedimentoForm(
  form: ProcedimentoFormState,
  convenios: ConvenioItem[],
  precosConvenio: Record<number, string>,
  presetCategoria: string,
): string | null {
  if (!form.name.trim()) return "Nome é obrigatório.";
  const categoria = form.categoria.trim() || presetCategoria;
  if (!categoria) return "Categoria é obrigatória.";
  const duration = parseInt(form.duration, 10);
  if (isNaN(duration) || duration < 1) {
    return "Duração deve ser um número positivo (minutos).";
  }
  const temAlgumPreco = convenios.some((c) => precosConvenio[c.id]?.trim());
  if (convenios.length > 0 && !temAlgumPreco) {
    return "Informe o valor praticado em pelo menos um convênio.";
  }
  return null;
}

export function buildProcedimentoSaveBody(
  form: ProcedimentoFormState,
  presetCategoria: string,
): Record<string, unknown> {
  const categoria = form.categoria.trim() || presetCategoria;
  const duration = parseInt(form.duration, 10);
  return {
    name: form.name.trim(),
    description: form.description.trim() || null,
    price: "0.00",
    duration,
    active: true,
    category: categoria,
    termo_consentimento: form.termo_consentimento_ativo ? form.termo_consentimento.trim() : "",
    termo_consentimento_ativo: form.termo_consentimento_ativo,
  };
}

export function filterProcedimentosList(
  list: Procedure[],
  moduleKey: string,
  showAllCategories: boolean,
  categoriaSlug = "",
): { activeList: Procedure[]; filteredList: Procedure[]; hiddenByCategoryCount: number } {
  const activeList = list.filter((p) => entityActive(p));
  let scoped =
    moduleKey && !showAllCategories
      ? activeList.filter((p) => procedureMatchesModule(procedureCategoria(p), moduleKey))
      : activeList;

  if (categoriaSlug) {
    const want = resolveProcedureCategoriaSlug(categoriaSlug);
    scoped = scoped.filter(
      (p) => resolveProcedureCategoriaSlug(procedureCategoria(p)) === want,
    );
  }

  const hiddenByCategoryCount =
    moduleKey && !showAllCategories && !categoriaSlug
      ? activeList.length - scoped.length
      : 0;
  return { activeList, filteredList: scoped, hiddenByCategoryCount };
}

/** Cards da grade de categorias (contagem a partir da lista carregada). */
export function buildProcedimentoCategoriaCards(
  list: Procedure[],
  moduleKey = "",
): ProcedimentoCategoriaCard[] {
  const active = list.filter((p) => entityActive(p));
  const scoped = moduleKey
    ? active.filter((p) => procedureMatchesModule(procedureCategoria(p), moduleKey))
    : active;

  const counts = new Map<string, number>();
  for (const p of scoped) {
    const slug = resolveProcedureCategoriaSlug(procedureCategoria(p)) || "outro";
    counts.set(slug, (counts.get(slug) || 0) + 1);
  }

  const options = PROCEDURE_CATEGORIA_OPTIONS.filter((o) => {
    if (!moduleKey) return true;
    return procedureMatchesModule(o.value, moduleKey);
  });

  const cards: { value: string; label: string; count: number }[] = options.map((o) => ({
    value: o.value,
    label: o.label,
    count: counts.get(o.value) || 0,
  }));

  for (const [slug, count] of counts) {
    if (!cards.some((c) => c.value === slug)) {
      const label =
        PROCEDURE_CATEGORIA_OPTIONS.find((o) => o.value === slug)?.label ?? slug;
      cards.push({ value: slug as string, label, count });
    }
  }

  return cards.sort((a, b) => b.count - a.count || a.label.localeCompare(b.label));
}

export function mapPrecosConvenioFromApi(
  rows: { convenio: number; preco?: string | number | null }[],
): Record<number, string> {
  const map: Record<number, string> = {};
  for (const r of rows) {
    if (r.preco != null && r.preco !== "") {
      map[r.convenio] = String(r.preco);
    }
  }
  return map;
}
