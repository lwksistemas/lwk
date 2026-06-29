export interface EstoqueProduto {
  id: number;
  nome: string;
  categoria: string;
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

export const estoqueCategoriaLabel = (val: string) => {
  const norm = normalizeEstoqueCategoria(val);
  return ESTOQUE_CATEGORIAS.find((c) => c.value === norm)?.label ?? val;
};

export const extractEstoqueApiError = (err: unknown, fallback: string): string => {
  if (err && typeof err === "object" && "error" in err) {
    return String((err as { error: string }).error);
  }
  if (err && typeof err === "object" && "detail" in err) {
    return String((err as { detail: string }).detail);
  }
  if (err && typeof err === "object") {
    const parts = Object.entries(err as Record<string, unknown>).flatMap(([key, val]) => {
      if (Array.isArray(val)) return val.map((v) => `${key}: ${v}`);
      if (typeof val === "string") return [`${key}: ${val}`];
      return [];
    });
    if (parts.length) return parts.join("; ");
  }
  return fallback;
};

export const ESTOQUE_INPUT_CLASS =
  "w-full px-3 py-2 border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100 text-sm";
