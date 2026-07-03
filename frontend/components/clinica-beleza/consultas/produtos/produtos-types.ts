export interface ConsultaProdutoItem {
  id: number;
  produto: number;
  produto_nome: string;
  quantidade: number | string;
  lote: string;
  validade: string | null;
  unidade_medida?: string;
  quantidade_disponivel?: number | string;
  estoque_baixado?: boolean;
}

export interface ProdutoEstoque {
  id: number;
  nome: string;
  lote?: string;
  validade?: string | null;
  quantidade_atual: number | string;
  unidade_medida?: string;
}

export const PRODUTOS_INPUT_CLASS =
  "w-full px-3 py-2 text-sm border dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100";
