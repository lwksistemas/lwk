/**
 * Utilitários para o CRM Vendas.
 * Centraliza helpers de tratamento de respostas da API.
 */

/**
 * Normaliza resposta paginada ou array da API para um array de itens.
 * A API pode retornar { results: T[] } (DRF pagination) ou T[] diretamente.
 */
export function normalizeListResponse<T>(data: T[] | { results: T[] } | null | undefined): T[] {
  if (data == null) return [];
  if (Array.isArray(data)) return data;
  return (data as { results: T[] }).results ?? [];
}
