/**
 * Sistema de captura e envio de erros para o suporte
 * Otimizado para não sobrecarregar o servidor
 */

interface ErrorLog {
  tipo: 'frontend' | 'api' | 'navegador';
  mensagem: string;
  stack?: string;
  url?: string;
  timestamp: string;
  userAgent?: string;
  extra?: Record<string, any>;
}

class ErrorLogger {
  private errors: ErrorLog[] = [];
  private maxErrors = 10; // Máximo de erros armazenados
  private sendTimeout: NodeJS.Timeout | null = null;
  private isSending = false;

  constructor() {
    if (typeof window !== 'undefined') {
      this.setupErrorHandlers();
    }
  }

  /**
   * Configura handlers globais de erro
   */
  private setupErrorHandlers() {
    // Capturar erros não tratados
    window.addEventListener('error', (event) => {
      this.logError({
        tipo: 'navegador',
        mensagem: event.message,
        stack: event.error?.stack,
        url: event.filename || window.location.href,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        extra: {
          lineno: event.lineno,
          colno: event.colno,
        },
      });
    });

    // Capturar promises rejeitadas não tratadas
    window.addEventListener('unhandledrejection', (event) => {
      this.logError({
        tipo: 'navegador',
        mensagem: `Promise rejeitada: ${event.reason}`,
        stack: event.reason?.stack,
        url: window.location.href,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
      });
    });
  }

  /**
   * Registra um erro
   */
  logError(error: ErrorLog) {
    // Adicionar ao array (FIFO - remove o mais antigo se exceder o limite)
    if (this.errors.length >= this.maxErrors) {
      this.errors.shift();
    }
    this.errors.push(error);

    // Limitar para não enviar muitas requisições
    // Apenas armazena localmente, será enviado quando abrir chamado
  }

  /**
   * Captura erro de API
   */
  logApiError(error: any, endpoint: string) {
    this.logError({
      tipo: 'api',
      mensagem: error.response?.data?.error || error.message || 'Erro na API',
      stack: error.stack,
      url: endpoint,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      extra: {
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data,
      },
    });
  }

  /**
   * Captura erro de frontend (React, etc)
   */
  logFrontendError(error: Error, componentStack?: string) {
    this.logError({
      tipo: 'frontend',
      mensagem: error.message,
      stack: error.stack,
      url: window.location.href,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      extra: {
        componentStack,
      },
    });
  }

  /**
   * Retorna todos os erros capturados
   */
  getErrors(): ErrorLog[] {
    return [...this.errors];
  }

  /**
   * Retorna erros formatados para envio ao suporte
   */
  getFormattedErrors(): string {
    if (this.errors.length === 0) {
      return '';
    }

    const sections: string[] = [];

    // Agrupar por tipo
    const errorsByType = this.errors.reduce((acc, error) => {
      if (!acc[error.tipo]) {
        acc[error.tipo] = [];
      }
      acc[error.tipo].push(error);
      return acc;
    }, {} as Record<string, ErrorLog[]>);

    // Formatar cada tipo
    Object.entries(errorsByType).forEach(([tipo, errors]) => {
      const tipoLabel = {
        frontend: '🔴 ERROS FRONTEND',
        api: '🟢 ERROS API/BACKEND',
        navegador: '🟡 ERROS NAVEGADOR',
      }[tipo] || tipo.toUpperCase();

      sections.push(`\n${tipoLabel}:\n${'='.repeat(50)}`);

      errors.forEach((error, index) => {
        sections.push(`\n[${index + 1}] ${new Date(error.timestamp).toLocaleString('pt-BR')}`);
        sections.push(`Mensagem: ${error.mensagem}`);
        if (error.url) sections.push(`URL: ${error.url}`);
        if (error.stack) sections.push(`Stack: ${error.stack.substring(0, 200)}...`);
        if (error.extra) {
          sections.push(`Detalhes: ${JSON.stringify(error.extra, null, 2)}`);
        }
        sections.push(''); // Linha em branco
      });
    });

    // Adicionar informações do sistema
    sections.push(`\n📊 INFORMAÇÕES DO SISTEMA:\n${'='.repeat(50)}`);
    sections.push(`Navegador: ${navigator.userAgent}`);
    sections.push(`URL Atual: ${window.location.href}`);
    sections.push(`Resolução: ${window.screen.width}x${window.screen.height}`);
    sections.push(`Idioma: ${navigator.language}`);
    sections.push(`Online: ${navigator.onLine ? 'Sim' : 'Não'}`);

    return sections.join('\n');
  }

  /**
   * Limpa todos os erros armazenados
   */
  clearErrors() {
    this.errors = [];
  }

  /**
   * Retorna estatísticas dos erros
   */
  getStats() {
    const stats = {
      total: this.errors.length,
      frontend: 0,
      api: 0,
      navegador: 0,
    };

    this.errors.forEach((error) => {
      if (error.tipo === 'frontend') stats.frontend++;
      else if (error.tipo === 'api') stats.api++;
      else if (error.tipo === 'navegador') stats.navegador++;
    });

    return stats;
  }
}

// Singleton
export const errorLogger = new ErrorLogger();

// Hook para React Error Boundary
export function useErrorLogger() {
  return {
    logError: (error: Error, errorInfo?: any) => {
      errorLogger.logFrontendError(error, errorInfo?.componentStack);
    },
  };
}
