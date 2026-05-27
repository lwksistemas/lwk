/**
 * Sistema de Logs Condicional
 * Logs completos apenas em desenvolvimento.
 * Em produção, erros visíveis são sanitizados para evitar expor payloads sensíveis.
 */

const isDev = process.env.NODE_ENV === 'development';

type LogArg = unknown;

type ErrorLike = {
  name?: unknown;
  message?: unknown;
  code?: unknown;
  response?: {
    status?: unknown;
    data?: {
      code?: unknown;
    };
  };
  config?: {
    method?: unknown;
    url?: unknown;
  };
};

function sanitizeLogArg(arg: LogArg): LogArg {
  if (arg == null || typeof arg !== 'object') return arg;

  if (arg instanceof Error) {
    return {
      name: arg.name,
      message: arg.message,
    };
  }

  const maybeError = arg as ErrorLike;
  const looksLikeHttpError =
    'response' in maybeError ||
    'config' in maybeError ||
    'code' in maybeError ||
    'message' in maybeError;

  if (!looksLikeHttpError) return '[object]';

  return {
    status: maybeError.response?.status,
    code: maybeError.response?.data?.code ?? maybeError.code,
    method: maybeError.config?.method,
    url: maybeError.config?.url,
    message: typeof maybeError.message === 'string' ? maybeError.message : undefined,
  };
}

function sanitizeLogArgs(args: LogArg[]): LogArg[] {
  return args.map(sanitizeLogArg);
}

export const logger = {
  /**
   * Log de debug - apenas em desenvolvimento
   */
  log: (...args: LogArg[]) => {
    if (isDev) {
      console.log(...args);
    }
  },

  /**
   * Log de erro - completo em desenvolvimento, sanitizado em produção
   */
  error: (...args: LogArg[]) => {
    console.error(...(isDev ? args : sanitizeLogArgs(args)));
  },

  /**
   * Log de aviso - apenas em desenvolvimento
   */
  warn: (...args: LogArg[]) => {
    if (isDev) {
      console.warn(...args);
    }
  },

  /**
   * Log critico - completo em desenvolvimento, sanitizado em produção
   */
  critical: (message: string, ...args: LogArg[]) => {
    console.error(message, ...(isDev ? args : sanitizeLogArgs(args)));
  },
};
