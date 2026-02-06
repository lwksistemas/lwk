/**
 * Helpers para trabalhar com respostas da API
 * Seguindo boas práticas: DRY, type safety, error handling
 */

/**
 * Garante que a resposta da API seja sempre um array
 * Previne erros "X.map is not a function"
 * 
 * @param data - Dados da resposta da API
 * @returns Array tipado ou array vazio
 */
export function ensureArray<T>(data: any): T[] {
  // Se já é array, retornar
  if (Array.isArray(data)) {
    return data;
  }
  
  // Se é null ou undefined, retornar array vazio
  if (data === null || data === undefined) {
    console.warn('ensureArray: dados null/undefined, retornando []');
    return [];
  }
  
  // Se é objeto com propriedade results (paginação DRF)
  if (typeof data === 'object' && Array.isArray(data.results)) {
    return data.results;
  }
  
  // Se é objeto com propriedade data
  if (typeof data === 'object' && Array.isArray(data.data)) {
    return data.data;
  }
  
  // Caso contrário, retornar array vazio
  console.warn('ensureArray: tipo inesperado, retornando []', typeof data);
  return [];
}

/**
 * Extrai dados de forma segura de uma resposta da API
 * 
 * @param response - Resposta do axios
 * @returns Array tipado ou array vazio
 */
export function extractArrayData<T>(response: any): T[] {
  return ensureArray<T>(response?.data);
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
