import type { ConvenioItem } from "@/lib/clinica-beleza-api";
import { entityActive, procedureCategoria } from "@/lib/clinica-beleza-entities";
import { procedureMatchesModule } from "@/lib/clinica-beleza-categories";
import { formatCurrency } from "@/lib/financeiro-helpers";
import type { Procedure, ProcedimentoFormState } from "./procedimentos-page-types";

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
): { activeList: Procedure[]; filteredList: Procedure[]; hiddenByCategoryCount: number } {
  const activeList = list.filter((p) => entityActive(p));
  const filteredList =
    moduleKey && !showAllCategories
      ? activeList.filter((p) => procedureMatchesModule(procedureCategoria(p), moduleKey))
      : activeList;
  const hiddenByCategoryCount =
    moduleKey && !showAllCategories ? activeList.length - filteredList.length : 0;
  return { activeList, filteredList, hiddenByCategoryCount };
}

export function mapPrecosConvenioFromApi(
  rows: { convenio: number; preco?: string | null }[],
): Record<number, string> {
  const map: Record<number, string> = {};
  for (const r of rows) {
    if (r.preco != null && r.preco !== "") {
      map[r.convenio] = String(r.preco);
    }
  }
  return map;
}
