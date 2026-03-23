/**
 * Tratamento centralizado de erros.
 * 
 * Segue Clean Code:
 * - Tratamento consistente de erros
 * - Mensagens amigáveis ao usuário
 * - Logging estruturado
 */
import axios from 'axios';

/**
 * Classe customizada para erros de API.
 */
export class ApiError extends Error {
  constructor(
    message: string,
    public statusCode: number,
    public details?: any
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

/**
 * Extrai mensagem de erro amigável de diferentes tipos de erro.
 * 
 * @param error - Erro capturado
 * @returns Mensagem de erro formatada
 */
export function handleApiError(error: unknown): string {
  // Erro customizado ApiError
  if (error instanceof ApiError) {
    return error.message;
  }

  // Erro do Axios
  if (axios.isAxiosError(error)) {
    // Erro de resposta do servidor
    if (error.response) {
      const { status, data } = error.response;

      // Mensagens específicas por status code
      switch (status) {
        case 400:
          return data?.detail || 'Dados inválidos. Verifique os campos e tente novamente.';
        case 401:
          return 'Sessão expirada. Faça login novamente.';
        case 403:
          return 'Você não tem permissão para realizar esta ação.';
        case 404:
          return 'Recurso não encontrado.';
        case 409:
          return data?.detail || 'Conflito. Este registro já existe.';
        case 422:
          return data?.detail || 'Erro de validação. Verifique os dados informados.';
        case 500:
          return 'Erro interno do servidor. Tente novamente mais tarde.';
        case 503:
          return 'Serviço temporariamente indisponível. Tente novamente em alguns instantes.';
        default:
          return data?.detail || `Erro ${status}. Tente novamente.`;
      }
    }

    // Erro de rede (sem resposta do servidor)
    if (error.request) {
      return 'Erro de conexão. Verifique sua internet e tente novamente.';
    }

    // Erro na configuração da requisição
    return 'Erro ao processar requisição. Tente novamente.';
  }

  // Erro genérico
  if (error instanceof Error) {
    return error.message;
  }

  // Erro desconhecido
  return 'Erro inesperado. Tente novamente.';
}

/**
 * Loga erro no console (desenvolvimento) ou serviço de logging (produção).
 * 
 * @param error - Erro a ser logado
 * @param context - Contexto adicional (componente, ação, etc)
 */
export function logError(error: unknown, context?: string) {
  const errorMessage = handleApiError(error);
  const timestamp = new Date().toISOString();

  // Log estruturado
  console.error({
    timestamp,
    context,
    message: errorMessage,
    error,
  });

  // TODO: Em produção, enviar para serviço de logging (Sentry, LogRocket, etc)
  // if (process.env.NODE_ENV === 'production') {
  //   sendToLoggingService({ timestamp, context, message: errorMessage, error });
  // }
}

/**
 * Wrapper para tratamento de erros em funções assíncronas.
 * 
 * @param fn - Função assíncrona a ser executada
 * @param context - Contexto para logging
 * @returns Resultado da função ou erro tratado
 */
export async function withErrorHandling<T>(
  fn: () => Promise<T>,
  context?: string
): Promise<{ data?: T; error?: string }> {
  try {
    const data = await fn();
    return { data };
  } catch (error) {
    logError(error, context);
    return { error: handleApiError(error) };
  }
}

/**
 * Valida se uma resposta de API é válida.
 * 
 * @param response - Resposta da API
 * @returns true se válida, lança erro se inválida
 */
export function validateApiResponse(response: any): boolean {
  if (!response) {
    throw new ApiError('Resposta vazia do servidor', 500);
  }

  if (response.error) {
    throw new ApiError(response.error, response.status || 500);
  }

  return true;
}

/**
 * Extrai mensagens de erro de validação de campos.
 * 
 * @param error - Erro de validação
 * @returns Objeto com mensagens por campo
 */
export function extractFieldErrors(error: unknown): Record<string, string> {
  if (!axios.isAxiosError(error)) {
    return {};
  }

  const data = error.response?.data;
  if (!data || typeof data !== 'object') {
    return {};
  }

  const fieldErrors: Record<string, string> = {};

  // Iterar sobre campos com erro
  Object.entries(data).forEach(([field, messages]) => {
    if (Array.isArray(messages)) {
      fieldErrors[field] = messages[0]; // Primeira mensagem
    } else if (typeof messages === 'string') {
      fieldErrors[field] = messages;
    }
  });

  return fieldErrors;
}
