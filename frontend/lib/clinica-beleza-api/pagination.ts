export const CLINICA_BELEZA_PAGE_SIZE = 20;

export interface ClinicaBelezaPaginatedResult<T> {
  items: T[];
  count: number;
  page: number;
  pageSize: number;
  totalPages: number;
  hasMore: boolean;
}

/** Monta URL de listagem com query params (paginação opcional). */
export function buildClinicaBelezaListUrl(
  path: string,
  params?: Record<string, string | number | undefined | null>,
): string {
  const search = new URLSearchParams();
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== null && value !== '') {
        search.set(key, String(value));
      }
    }
  }
  const qs = search.toString();
  if (!qs) return path;
  const sep = path.includes('?') ? '&' : '?';
  return `${path}${sep}${qs}`;
}

/** Normaliza envelope paginado ou array direto (retrocompatível). */
export function parseClinicaBelezaPaginatedResponse<T>(
  data: unknown,
  fallbackPage = 1,
  fallbackPageSize = CLINICA_BELEZA_PAGE_SIZE,
): ClinicaBelezaPaginatedResult<T> {
  if (Array.isArray(data)) {
    return {
      items: data as T[],
      count: data.length,
      page: 1,
      pageSize: data.length || fallbackPageSize,
      totalPages: 1,
      hasMore: false,
    };
  }
  if (
    data &&
    typeof data === 'object' &&
    ('detail' in data || 'error' in data) &&
    !('results' in data)
  ) {
    throw data;
  }
  if (data && typeof data === 'object' && 'results' in data) {
    const envelope = data as {
      results?: unknown;
      count?: number;
      page?: number;
      page_size?: number;
      total_pages?: number;
    };
    const items = Array.isArray(envelope.results) ? (envelope.results as T[]) : [];
    const page = envelope.page ?? fallbackPage;
    const pageSize = envelope.page_size ?? fallbackPageSize;
    const totalPages = envelope.total_pages ?? 1;
    const count = envelope.count ?? items.length;
    return {
      items,
      count,
      page,
      pageSize,
      totalPages,
      hasMore: page < totalPages,
    };
  }
  return {
    items: [],
    count: 0,
    page: fallbackPage,
    pageSize: fallbackPageSize,
    totalPages: 1,
    hasMore: false,
  };
}

/** Normaliza resposta da API: array direto ou envelope paginado { results, count }. */
export function parseClinicaBelezaListResponse<T>(data: unknown): T[] {
  return parseClinicaBelezaPaginatedResponse<T>(data).items;
}

/** Evita "Unexpected token '<'" quando o servidor retorna HTML (erro 500/502). */
export async function parseClinicaBelezaResponseBody(res: Response): Promise<unknown> {
  const text = await res.text();
  if (!text.trim()) return {};
  try {
    return JSON.parse(text);
  } catch {
    if (text.trimStart().toLowerCase().startsWith("<!doctype") || text.trimStart().startsWith("<html")) {
      throw {
        detail: `Erro no servidor (${res.status}). Tente novamente em instantes.`,
      };
    }
    throw { detail: text.slice(0, 400) };
  }
}
