/**
 * Error Handler - Tratamento consolidado de erros de API
 * 
 * Centraliza o tratamento de erros para:
 * - Mensagens consistentes para o usuário
 * - Código mais limpo (elimina try-catch duplicados)
 * - Fácil manutenção e tradução
 * - Logging centralizado (futuro)
 */

interface ApiError {
  response?: {
    data?: any;
    status?: number;
    statusText?: string;
  };
  message?: string;
}

/**
 * Extrai mensagem de erro amigável de uma resposta de API
 * 
 * @param error - Erro capturado do try-catch
 * @returns Mensagem de erro formatada para exibir ao usuário
 * 
 * @example
 * ```typescript
 * try {
 *   await apiClient.post('/endpoint', data);
 * } catch (err) {
 *   showMsg('error', handleApiError(err));
 * }
 * ```
 */
export function handleApiError(error: unknown): string {
  const e = error as ApiError;
  
  // Erro de validação (400 Bad Request)
  if (e.response?.status === 400) {
    const data = e.response.data;
    
    // Mensagem de erro direta
    if (typeof data?.detail === 'string') {
      return data.detail;
    }
    
    // Erros de campo (ex: { titulo: ['Este campo é obrigatório'] })
    if (data && typeof data === 'object') {
      for (const key in data) {
        const value = data[key];
        
        // Array de erros
        if (Array.isArray(value) && value.length > 0) {
          const fieldName = getFieldLabel(key);
          return `${fieldName}: ${value[0]}`;
        }
        
        // String direta
        if (typeof value === 'string') {
          const fieldName = getFieldLabel(key);
          return `${fieldName}: ${value}`;
        }
      }
    }
    
    return 'Dados inválidos. Verifique os campos e tente novamente.';
  }
  
  // Erro de autenticação (401 Unauthorized)
  if (e.response?.status === 401) {
    return 'Sessão expirada. Faça login novamente.';
  }
  
  // Erro de permissão (403 Forbidden)
  if (e.response?.status === 403) {
    return 'Você não tem permissão para realizar esta ação.';
  }
  
  // Recurso não encontrado (404 Not Found)
  if (e.response?.status === 404) {
    return 'Recurso não encontrado.';
  }
  
  // Conflito (409 Conflict)
  if (e.response?.status === 409) {
    const data = e.response.data;
    if (typeof data?.detail === 'string') {
      return data.detail;
    }
    return 'Conflito ao processar a requisição. Verifique os dados.';
  }
  
  // Erro de servidor (500 Internal Server Error)
  if (e.response?.status === 500) {
    return 'Erro no servidor. Tente novamente mais tarde.';
  }
  
  // Erro de serviço indisponível (503 Service Unavailable)
  if (e.response?.status === 503) {
    return 'Serviço temporariamente indisponível. Tente novamente em alguns minutos.';
  }
  
  // Erro de rede (sem resposta do servidor)
  if (!e.response) {
    if (e.message?.toLowerCase().includes('network')) {
      return 'Erro de conexão. Verifique sua internet e tente novamente.';
    }
    return 'Não foi possível conectar ao servidor. Verifique sua conexão.';
  }
  
  // Erro genérico com mensagem
  if (e.message) {
    return e.message;
  }
  
  // Fallback genérico
  return 'Erro inesperado. Tente novamente.';
}

/**
 * Converte nome de campo técnico para label amigável
 * 
 * @param fieldName - Nome do campo da API (ex: 'titulo', 'cpf_cnpj')
 * @returns Label formatado (ex: 'Título', 'CPF/CNPJ')
 */
function getFieldLabel(fieldName: string): string {
  const labels: Record<string, string> = {
    // Campos comuns
    'titulo': 'Título',
    'subtitulo': 'Subtítulo',
    'descricao': 'Descrição',
    'nome': 'Nome',
    'email': 'Email',
    'senha': 'Senha',
    'password': 'Senha',
    'username': 'Usuário',
    
    // Campos específicos
    'cpf_cnpj': 'CPF/CNPJ',
    'telefone': 'Telefone',
    'celular': 'Celular',
    'endereco': 'Endereço',
    'cep': 'CEP',
    'cidade': 'Cidade',
    'estado': 'Estado',
    'uf': 'UF',
    'bairro': 'Bairro',
    'numero': 'Número',
    'complemento': 'Complemento',
    
    // Campos de homepage
    'botao_texto': 'Texto do botão',
    'icone': 'Ícone',
    'imagem': 'Imagem',
    'slug': 'Slug',
    'ordem': 'Ordem',
    'ativo': 'Ativo',
    
    // Campos de loja
    'cor_primaria': 'Cor primária',
    'cor_secundaria': 'Cor secundária',
    'logo': 'Logo',
    'login_background': 'Imagem de fundo',
    'login_logo': 'Logo do login',
    
    // Campos de CRM
    'valor': 'Valor',
    'data': 'Data',
    'status': 'Status',
    'observacoes': 'Observações',
    'observacao': 'Observação',
  };
  
  // Retorna label customizado ou formata o nome do campo
  return labels[fieldName] || formatFieldName(fieldName);
}

/**
 * Formata nome de campo técnico para exibição
 * 
 * @param fieldName - Nome do campo (ex: 'nome_completo')
 * @returns Nome formatado (ex: 'Nome completo')
 */
function formatFieldName(fieldName: string): string {
  return fieldName
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

/**
 * Verifica se o erro é de autenticação (401)
 * Útil para redirecionar para login
 * 
 * @param error - Erro capturado
 * @returns true se for erro 401
 */
export function isAuthError(error: unknown): boolean {
  const e = error as ApiError;
  return e.response?.status === 401;
}

/**
 * Verifica se o erro é de permissão (403)
 * 
 * @param error - Erro capturado
 * @returns true se for erro 403
 */
export function isPermissionError(error: unknown): boolean {
  const e = error as ApiError;
  return e.response?.status === 403;
}

/**
 * Verifica se o erro é de validação (400)
 * 
 * @param error - Erro capturado
 * @returns true se for erro 400
 */
export function isValidationError(error: unknown): boolean {
  const e = error as ApiError;
  return e.response?.status === 400;
}

/**
 * Extrai erros de campo específicos para exibir em formulários
 * 
 * @param error - Erro capturado
 * @returns Objeto com erros por campo { campo: 'mensagem' }
 * 
 * @example
 * ```typescript
 * const fieldErrors = getFieldErrors(error);
 * // { titulo: 'Este campo é obrigatório', email: 'Email inválido' }
 * ```
 */
export function getFieldErrors(error: unknown): Record<string, string> {
  const e = error as ApiError;
  const errors: Record<string, string> = {};
  
  if (e.response?.status === 400 && e.response.data) {
    const data = e.response.data;
    
    for (const key in data) {
      const value = data[key];
      
      if (Array.isArray(value) && value.length > 0) {
        errors[key] = value[0];
      } else if (typeof value === 'string') {
        errors[key] = value;
      }
    }
  }
  
  return errors;
}
