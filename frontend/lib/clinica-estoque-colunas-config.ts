/** Definições de colunas configuráveis na listagem de Estoque (clínica). */

import {
  colunasVisiveisFromConfig,
  type CrmColunaDef,
} from '@/lib/crm-colunas-config';

export type EstoqueColunaDef = CrmColunaDef;

export const COLUNAS_ESTOQUE_DISPONIVEIS: EstoqueColunaDef[] = [
  { key: 'nome', label: 'Nome' },
  { key: 'marca', label: 'Fornecedor' },
  { key: 'categoria', label: 'Categoria' },
  { key: 'quantidade_atual', label: 'Qtd' },
  { key: 'quantidade_minima', label: 'Mínimo' },
  { key: 'preco_custo', label: 'Preço Custo' },
  { key: 'lote', label: 'Lote' },
  { key: 'numero_nota', label: 'Nota' },
  { key: 'validade', label: 'Validade' },
  { key: 'status', label: 'Status' },
];

/** Padrão = todas as colunas atuais (Ações fica sempre fixa). */
export const DEFAULT_COLUNAS_ESTOQUE = COLUNAS_ESTOQUE_DISPONIVEIS.map((c) => c.key);

export function resolveColunasEstoque(
  keys: string[] | undefined | null,
): EstoqueColunaDef[] {
  return colunasVisiveisFromConfig(
    keys,
    COLUNAS_ESTOQUE_DISPONIVEIS,
    DEFAULT_COLUNAS_ESTOQUE,
  );
}
