function valorErroParaTexto(val: unknown): string {
  if (val == null) return '';
  if (typeof val === 'string') return val;
  if (typeof val === 'number' || typeof val === 'boolean') return String(val);
  if (Array.isArray(val)) return val.map(valorErroParaTexto).filter(Boolean).join(' ');
  if (typeof val === 'object') {
    try {
      return JSON.stringify(val);
    } catch {
      return '';
    }
  }
  return '';
}

/**
 * Formata corpo JSON de erro (fetch/axios) em mensagem legível.
 * DRF: { detail }, { error }, ou { campo: ["msg"] }.
 * Aceita o objeto Axios inteiro (quem passar `error` em vez de `error.response.data`).
 */
export function formatApiErrorBody(data: unknown): string {
  if (data == null) return '';
  if (typeof data === 'string') return data;
  if (typeof data !== 'object') return String(data);
  const obj = data as Record<string, unknown>;
  if ('response' in obj && obj.response && typeof obj.response === 'object') {
    const nested = formatApiErrorBody((obj.response as { data?: unknown }).data);
    if (nested) return nested;
  }
  if (typeof obj.error === 'string') return obj.error;
  const detail = obj.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail.map((d) => (typeof d === 'string' ? d : valorErroParaTexto(d))).join(' · ');
  }
  const camposAmigaveis = new Set([
    'non_field_errors', 'cpf', 'cnpj', 'cpf_cnpj', 'documento', 'atalho', 'owner_username', 'owner_email', 'slug',
  ]);
  const fieldMessages = Object.entries(obj)
    .filter(([k]) => k !== 'detail' && k !== 'error' && k !== 'response' && k !== 'config' && k !== 'request')
    .map(([key, val]) => {
      const msg = valorErroParaTexto(val);
      if (!msg) return '';
      if (camposAmigaveis.has(key)) return msg;
      return `${key}: ${msg}`;
    })
    .filter(Boolean);
  if (fieldMessages.length) return fieldMessages.join(' · ');
  return '';
}

/**
 * Helper para formatar erros de resposta da API (4xx/5xx).
 * DRF costuma retornar { detail: "..." } ou { campo: ["msg1", "msg2"] } em 400.
 */
export function formatApiError(err: unknown): string {
  if (!err || typeof err !== 'object') return 'Erro desconhecido';
  const ax = err as { response?: { data?: unknown; status?: number } };
  const data = ax.response?.data;
  const fromBody = formatApiErrorBody(data);
  if (fromBody) return fromBody;
  if (data == null) {
    const status = ax.response?.status;
    if (status === 404) return 'Recurso não encontrado.';
    if (status === 403) return 'Sem permissão para esta ação.';
    if (status === 429) return 'Muitas tentativas. Aguarde alguns minutos e tente de novo.';
    if (status === 500) return 'Erro interno do servidor. Tente novamente.';
    return 'Erro ao processar a requisição.';
  }
  return 'Erro ao processar a requisição.';
}

/**
 * Retorna um objeto com erros por campo (para exibir em labels).
 * Ex: { preco: "Campo obrigatório.", nome: "Este campo não pode ser vazio." }
 */
export function getFieldErrors(err: unknown): Record<string, string> {
  const result: Record<string, string> = {};
  if (!err || typeof err !== 'object') return result;
  const ax = err as { response?: { data?: Record<string, unknown> } };
  const data = ax.response?.data;
  if (!data || typeof data !== 'object') return result;
  const obj = data as Record<string, unknown>;
  for (const [key, val] of Object.entries(obj)) {
    if (key === 'detail') continue;
    if (Array.isArray(val)) result[key] = val.map((v) => String(v)).join(' ');
    else if (val != null) result[key] = String(val);
  }
  return result;
}
