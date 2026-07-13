/**
 * Helper para garantir que um valor seja sempre um array
 * Previne erros "X.map is not a function"
 */
import { logger } from './logger';

export function ensureArray<T>(value: unknown): T[] {
  if (Array.isArray(value)) {
    return value;
  }

  // Se for null ou undefined, retornar array vazio
  if (value === null || value === undefined) {
    return [];
  }

  // Se for um objeto com propriedade results (paginação DRF)
  if (typeof value === 'object' && Array.isArray((value as { results?: unknown }).results)) {
    return (value as { results: T[] }).results;
  }
  
  // Caso contrário, retornar array vazio
  logger.warn('ensureArray: valor não é array, retornando []', value);
  return [];
}

/**
 * Helper para garantir que response.data seja sempre um array
 */
export function ensureArrayResponse<T>(response: unknown): T[] {
  const data = response && typeof response === 'object' ? (response as Record<string, unknown>).data : undefined;
  return ensureArray<T>(data);
}
