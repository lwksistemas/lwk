/**
 * Categorias de procedimentos por módulo (Soroterapia, Estética).
 *
 * Organização:
 * - Módulo: soroterapia | estetica
 * - Especialidades (estética): facial, corporal, capilar, depilacao, injetavel
 * - Gerais: geral, outro
 */

export const PROCEDURE_CATEGORIA_OPTIONS = [
  { value: "soroterapia", label: "Soroterapia", group: "módulo" },
  { value: "estetica", label: "Estética (geral)", group: "módulo" },
  { value: "facial", label: "Facial", group: "estética" },
  { value: "corporal", label: "Corporal", group: "estética" },
  { value: "capilar", label: "Capilar", group: "estética" },
  { value: "depilacao", label: "Depilação", group: "estética" },
  { value: "injetavel", label: "Injetável", group: "estética" },
  { value: "geral", label: "Geral", group: "outros" },
  { value: "outro", label: "Outro", group: "outros" },
] as const;

/** Normaliza categoria vinda da API (legado maiúsculo/título) para o value do select. */
export function resolveProcedureCategoriaSlug(raw: string | undefined | null): string {
  const norm = normalizeCategoria(raw || "");
  if (!norm) return "";
  const exact = PROCEDURE_CATEGORIA_OPTIONS.find((o) => o.value === norm);
  if (exact) return exact.value;
  const byLabel = PROCEDURE_CATEGORIA_OPTIONS.find((o) => normalizeCategoria(o.label) === norm);
  if (byLabel) return byLabel.value;
  if (norm.startsWith("depil")) return "depilacao";
  if (norm.includes("injeta") || norm.includes("botox") || norm.includes("preench")) return "injetavel";
  if (norm.includes("soro") || norm.includes("iv ")) return "soroterapia";
  return norm;
}

export function procedureCategoriaLabel(slug: string | undefined | null): string {
  const resolved = resolveProcedureCategoriaSlug(slug);
  return PROCEDURE_CATEGORIA_OPTIONS.find((o) => o.value === resolved)?.label ?? slug ?? "";
}

/** Palavras-chave que identificam procedimentos de cada módulo */
const MODULE_ALIASES: Record<string, string[]> = {
  soroterapia: ["soroterapia", "soro", "iv ", "vitamina", "imunidade", "detox", "disposicao"],
  estetica: [
    "estetica",
    "estética",
    "facial",
    "corporal",
    "capilar",
    "peeling",
    "botox",
    "preenchimento",
    "injetavel",
    "depilacao",
    "depilação",
  ],
};

function normalizeCategoria(value: string): string {
  return value
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .trim();
}

/** Verifica se a categoria do procedimento pertence ao módulo (ex.: soroterapia). */
export function procedureMatchesModule(categoria: string | undefined | null, module: string): boolean {
  if (!module) return true;
  const cat = normalizeCategoria(categoria || "");
  if (!cat) return false;
  const aliases = MODULE_ALIASES[module] || [module];
  return aliases.some((alias) => cat.includes(normalizeCategoria(alias)));
}

/** Categoria padrão ao criar procedimento dentro de um módulo */
export function defaultCategoriaForModule(module: string): string {
  if (module === "soroterapia") return "soroterapia";
  if (module === "estetica") return "estetica";
  return "";
}
