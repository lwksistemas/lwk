/**
 * Sistema de Logs Condicional
 * Logs de debug apenas em desenvolvimento
 * Logs de erro sempre visíveis
 */

const isDev = process.env.NODE_ENV === 'development';

export const logger = {
  /**
   * Log de debug - apenas em desenvolvimento
   */
  log: (...args: any[]) => {
    if (isDev) {
      console.log(...args);
    }
  },

  /**
   * Log de erro - sempre visível
   */
  error: (...args: any[]) => {
    console.error(...args);
  },

  /**
   * Log de aviso - apenas em desenvolvimento
   */
  warn: (...args: any[]) => {
    if (isDev) {
      console.warn(...args);
    }
  },

  /**
   * Log crítico - sempre visível com emoji
   */
  critical: (message: string, ...args: any[]) => {
    console.error('🚨', message, ...args);
  },
};
