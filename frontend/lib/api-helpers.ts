/**
 * Helpers para trabalhar com respostas da API
 * Seguindo boas práticas: DRY, type safety, error handling
 * 
 * @deprecated Funções de array movidas para array-helpers.ts
 * Importe de lá: import { ensureArray, ensureArrayResponse } from '@/lib/array-helpers'
 */

// Re-exportar para compatibilidade (será removido em versão futura)
export { ensureArray, ensureArrayResponse } from './array-helpers';

/**
 * Extrai dados de forma segura de uma resposta da API
 * 
 * @param response - Resposta do axios
 * @returns Array tipado ou array vazio
 */
export function extractArrayData<T>(response: any): T[] {
  // Usar função consolidada de array-helpers
  const { ensureArray } = require('./array-helpers');
  return ensureArray(response?.data) as T[];
}

/**
 * Valida se um objeto tem as propriedades necessárias
 * 
 * @param obj - Objeto a validar
 * @param requiredProps - Propriedades obrigatórias
 * @returns true se válido
 */
export function validateObject(obj: any, requiredProps: string[]): boolean {
  if (!obj || typeof obj !== 'object') {
    return false;
  }
  
  return requiredProps.every(prop => prop in obj);
}

/**
 * Formata erro da API para mensagem amigável
 * 
 * @param error - Erro do axios
 * @returns Mensagem de erro formatada
 */
export function formatApiError(error: any): string {
  // Erro de rede
  if (!error.response) {
    return 'Erro de conexão. Verifique sua internet.';
  }
  
  // Erro 401 - Não autenticado
  if (error.response.status === 401) {
    return 'Sessão expirada. Faça login novamente.';
  }
  
  // Erro 403 - Sem permissão
  if (error.response.status === 403) {
    return 'Você não tem permissão para esta ação.';
  }
  
  // Erro 404 - Não encontrado
  if (error.response.status === 404) {
    return 'Recurso não encontrado.';
  }
  
  // Erro 429 - Rate limit
  if (error.response.status === 429) {
    return 'Muitas requisições. Aguarde um momento.';
  }
  
  // Erro 500 - Servidor
  if (error.response.status >= 500) {
    return 'Erro no servidor. Tente novamente mais tarde.';
  }
  
  // Mensagem específica do backend
  const message = error.response?.data?.detail 
    || error.response?.data?.error 
    || error.response?.data?.message;
  
  if (message) {
    return message;
  }
  
  // Mensagem genérica
  return 'Erro ao processar requisição.';
}

/**
 * Executa múltiplas requisições em paralelo com tratamento de erro
 * 
 * @param requests - Array de promises
 * @returns Array de resultados (arrays vazios em caso de erro)
 */
export async function fetchMultiple<T>(...requests: Promise<any>[]): Promise<T[][]> {
  try {
    const responses = await Promise.all(requests);
    return responses.map(response => extractArrayData<T>(response));
  } catch (error) {
    console.error('Erro ao carregar dados:', error);
    // Retornar arrays vazios para cada requisição
    return requests.map(() => []);
  }
}
