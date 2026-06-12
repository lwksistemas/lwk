/**
 * Categorias de procedimentos / estoque por módulo (Soroterapia, Estética).
 */

export const PROCEDURE_CATEGORIA_OPTIONS = [
  { value: 'soroterapia', label: 'Soroterapia' },
  { value: 'estetica', label: 'Estética' },
  { value: 'facial', label: 'Facial' },
  { value: 'corporal', label: 'Corporal' },
  { value: 'capilar', label: 'Capilar' },
  { value: 'depilacao', label: 'Depilação' },
  { value: 'injetavel', label: 'Injetável' },
  { value: 'geral', label: 'Geral' },
  { value: 'outro', label: 'Outro' },
] as const;

/** Normaliza categoria vinda da API (legado maiúsculo/título) para o value do select. */
export function resolveProcedureCategoriaSlug(raw: string | undefined | null): string {
  const norm = normalizeCategoria(raw || '');
  if (!norm) return '';
  const exact = PROCEDURE_CATEGORIA_OPTIONS.find((o) => o.value === norm);
  if (exact) return exact.value;
  const byLabel = PROCEDURE_CATEGORIA_OPTIONS.find((o) => normalizeCategoria(o.label) === norm);
  if (byLabel) return byLabel.value;
  if (norm.startsWith('depil')) return 'depilacao';
  return norm;
}

export function procedureCategoriaLabel(slug: string | undefined | null): string {
  const resolved = resolveProcedureCategoriaSlug(slug);
  return PROCEDURE_CATEGORIA_OPTIONS.find((o) => o.value === resolved)?.label ?? slug ?? '';
}

/** Palavras-chave que identificam procedimentos de cada módulo */
const MODULE_ALIASES: Record<string, string[]> = {
  soroterapia: ['soroterapia', 'soro', 'iv ', 'vitamina', 'imunidade', 'detox', 'disposicao'],
  estetica: ['estetica', 'estética', 'facial', 'corporal', 'capilar', 'peeling', 'botox', 'preenchimento'],
};

function normalizeCategoria(value: string): string {
  return value
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .trim();
}

/** Verifica se a categoria do procedimento pertence ao módulo (ex.: soroterapia). */
export function procedureMatchesModule(categoria: string | undefined | null, module: string): boolean {
  if (!module) return true;
  const cat = normalizeCategoria(categoria || '');
  if (!cat) return false;
  const aliases = MODULE_ALIASES[module] || [module];
  return aliases.some((alias) => cat.includes(normalizeCategoria(alias)));
}

/** Categoria padrão ao criar procedimento dentro de um módulo */
export function defaultCategoriaForModule(module: string): string {
  if (module === 'soroterapia') return 'soroterapia';
  if (module === 'estetica') return 'estetica';
  return '';
}
