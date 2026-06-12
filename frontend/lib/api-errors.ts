/**
 * Formata corpo JSON de erro (fetch/axios) em mensagem legível.
 * DRF: { detail }, { error }, ou { campo: ["msg"] }.
 */
export function formatApiErrorBody(data: unknown): string {
  if (data == null) return '';
  if (typeof data === 'string') return data;
  if (typeof data !== 'object') return String(data);
  const obj = data as Record<string, unknown>;
  if (typeof obj.error === 'string') return obj.error;
  const detail = obj.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail.map((d) => (typeof d === 'string' ? d : JSON.stringify(d))).join(' · ');
  }
  const fieldMessages = Object.entries(obj)
    .filter(([k]) => k !== 'detail' && k !== 'error')
    .map(([key, val]) => {
      const msg = Array.isArray(val) ? val.map((v) => String(v)).join(' ') : String(val);
      return `${key}: ${msg}`;
    });
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
