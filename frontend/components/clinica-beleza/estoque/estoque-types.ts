import { formatApiErrorBody } from "@/lib/api-errors";

export interface EstoqueCategoria {
  id: number;
  nome: string;
  slug: string;
  cor: string;
  ordem: number;
  is_active: boolean;
  produtos_count?: number;
}

export interface EstoqueProduto {
  id: number;
  nome: string;
  /** ID da categoria (FK). */
  categoria: number | null;
  categoria_slug?: string;
  categoria_display?: string;
  categoria_cor?: string;
  marca?: string;
  quantidade_atual: number;
  quantidade_minima: number;
  preco_custo: number | string;
  validade: string | null;
  lote?: string;
  numero_nota?: string;
  status?: string;
  dias_alerta_validade?: number;
}

export interface EstoqueResumo {
  total_produtos: number;
  estoque_baixo: number;
  validade_proxima: number;
  valor_total_estoque: number;
}

export interface EstoqueMovimentacaoHistorico {
  tipo: string;
  quantidade: number;
  motivo: string;
  created_at: string;
  tipo_display: string;
}

/** Fallback estático (antes da API carregar). */
export const ESTOQUE_CATEGORIAS = [
  { value: "injetavel", label: "Injetável" },
  { value: "soroterapia", label: "Soroterapia" },
  { value: "cosmético", label: "Cosmético" },
  { value: "medicamentos", label: "Medicamentos" },
  { value: "descartavel", label: "Descartável" },
  { value: "equipamento", label: "Equipamento" },
  { value: "outro", label: "Outro" },
] as const;

const CATEGORIA_VALUES = new Set(ESTOQUE_CATEGORIAS.map((c) => c.value));

export const normalizeEstoqueCategoria = (val?: string | null): string => {
  if (!val) return "outro";
  if (val === "cosmetico") return "cosmético";
  if (val === "Medicamentos" || val === "medicamento") return "medicamentos";
  if (CATEGORIA_VALUES.has(val as (typeof ESTOQUE_CATEGORIAS)[number]["value"])) return val;
  return "outro";
};

export const estoqueCategoriaLabel = (
  val: string | number | null | undefined,
  categorias?: EstoqueCategoria[],
) => {
  if (val == null || val === "") return "—";
  if (typeof val === "number" && categorias) {
    return categorias.find((c) => c.id === val)?.nome ?? String(val);
  }
  const slug = String(val);
  if (categorias) {
    const bySlug = categorias.find((c) => c.slug === slug);
    if (bySlug) return bySlug.nome;
    const byNome = categorias.find((c) => c.nome === slug);
    if (byNome) return byNome.nome;
  }
  const norm = normalizeEstoqueCategoria(slug);
  return ESTOQUE_CATEGORIAS.find((c) => c.value === norm)?.label ?? slug;
};

export const extractEstoqueApiError = (err: unknown, fallback: string): string => {
  return formatApiErrorBody(err) || fallback;
};

export const ESTOQUE_INPUT_CLASS =
  "w-full px-3 py-2 border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100 text-sm";
