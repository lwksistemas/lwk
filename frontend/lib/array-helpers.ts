/**
 * Helper para garantir que um valor seja sempre um array
 * Previne erros "X.map is not a function"
 */
export function ensureArray<T>(value: any): T[] {
  if (Array.isArray(value)) {
    return value;
  }
  
  // Se for null ou undefined, retornar array vazio
  if (value === null || value === undefined) {
    return [];
  }
  
  // Se for um objeto com propriedade results (paginação DRF)
  if (typeof value === 'object' && Array.isArray(value.results)) {
    return value.results;
  }
  
  // Caso contrário, retornar array vazio
  console.warn('ensureArray: valor não é array, retornando []', value);
  return [];
}

/**
 * Helper para garantir que response.data seja sempre um array
 */
export function ensureArrayResponse<T>(response: any): T[] {
  return ensureArray<T>(response?.data);
}
