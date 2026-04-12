/**
 * Helpers para trabalhar com respostas da API
 * 
 * @deprecated Funções de array movidas para array-helpers.ts
 * @deprecated formatApiError movida para api-errors.ts
 */

// Re-exportar para compatibilidade
export { ensureArray, ensureArrayResponse } from './array-helpers';
export { formatApiError } from './api-errors';

/**
 * Extrai dados de forma segura de uma resposta da API
 * @deprecated Use ensureArray de array-helpers.ts
 */
export function extractArrayData<T>(response: any): T[] {
  const { ensureArray } = require('./array-helpers');
  return ensureArray(response?.data) as T[];
}
