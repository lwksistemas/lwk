/**
 * Cliente API otimizado para Clínica da Beleza
 */

import { clearSessionAndRedirect, getLoginUrlForRedirect, getCurrentApiBaseUrl, SESSION_CODES, tryRefreshAccessToken } from "@/lib/api-client";
import { USE_JWT_HTTPONLY_COOKIES } from "@/lib/auth-cookies";

function getAuthToken(): string | null {
  if (typeof window === "undefined" || USE_JWT_HTTPONLY_COOKIES) return null;
  return sessionStorage.getItem("access_token");
}

/** Se a resposta for 401 com código de sessão única, faz logout e redireciona. Retorna true se fez redirect. */
export async function handle401SessionResponse(response: Response): Promise<boolean> {
  if (response.status !== 401) return false;
  let data: { code?: string; message?: string; detail?: { code?: string; message?: string } } = {};
  try {
    data = await response.clone().json();
  } catch {
    return false;
  }
  const code = data?.code ?? (data?.detail && typeof data.detail === "object" ? data.detail.code : undefined);
  if (code && SESSION_CODES.includes(code as (typeof SESSION_CODES)[number])) {
    const msg =
      (typeof data?.message === "string" ? data.message : undefined) ??
      (data?.detail && typeof data.detail === "object" && typeof data.detail.message === "string"
        ? data.detail.message
        : undefined) ??
      "Sua sessão foi encerrada. Faça login novamente.";
    clearSessionAndRedirect(getLoginUrlForRedirect(), msg);
    return true;
  }
  return false;
}

/** Base da API (com /api), a partir de NEXT_PUBLIC_API_URL / getCurrentApiBaseUrl. */
export function getApiBaseUrl(): string {
  if (typeof window !== "undefined") return getCurrentApiBaseUrl();
  const base = process.env.NEXT_PUBLIC_API_URL || "";
  if (base.endsWith("/api")) return base;
  return base ? `${base.replace(/\/$/, "")}/api` : "";
}

/**
 * Headers com auth + tenant (X-Loja-ID ou X-Tenant-Slug).
 * Use loja quando disponível (ex.: dashboard com props) para evitar "Contexto de loja não encontrado".
 */
export function getClinicaBelezaHeadersWithLoja(
  loja?: { id?: number; slug?: string } | null
): Record<string, string> {
  const token = getAuthToken();
  const h: Record<string, string> = { "Content-Type": "application/json" };
  if (token) h["Authorization"] = `Bearer ${token}`;
  // Enviar session_id para validação de sessão única no backend
  if (typeof window !== "undefined") {
    const sessionId = sessionStorage.getItem("session_id");
    if (sessionId) h["X-Session-ID"] = sessionId;
  }
  let lojaId: string | null = loja?.id != null ? String(loja.id) : null;
  let lojaSlug: string | null = loja?.slug ?? null;
  const pathLojaMatch =
    typeof window !== "undefined"
      ? window.location.pathname.match(/^\/loja\/([^/]+)/)
      : null;
  const slugFromPath = pathLojaMatch?.[1] ?? null;
  if (typeof window !== "undefined") {
    if (!lojaSlug && slugFromPath) lojaSlug = slugFromPath;
    if (!lojaSlug) lojaSlug = sessionStorage.getItem("loja_slug");
    if (!lojaId) lojaId = sessionStorage.getItem("current_loja_id");
    // Alinhado ao api-client: slug da URL tem prioridade; ID stale causa listas vazias.
    if (slugFromPath && (token || sessionStorage.getItem("session_id"))) {
      const stored = sessionStorage.getItem("loja_slug");
      if (stored !== slugFromPath) {
        sessionStorage.setItem("loja_slug", slugFromPath);
        sessionStorage.removeItem("current_loja_id");
        lojaId = null;
        lojaSlug = slugFromPath;
      }
    }
  }
  const isLojaDashboardComSlug = Boolean(pathLojaMatch && lojaSlug);
  if (lojaSlug) h["X-Tenant-Slug"] = lojaSlug;
  if (lojaId && !isLojaDashboardComSlug) h["X-Loja-ID"] = lojaId;
  return h;
}

export function getClinicaBelezaHeaders(): HeadersInit {
  return getClinicaBelezaHeadersWithLoja();
}

export function getClinicaBelezaBaseUrl(): string {
  return `${getApiBaseUrl()}/clinica-beleza`;
}

/** Retorna loja_slug para uso em reporte de erros (sessionStorage ou pathname). */
function getLojaSlugForReport(): string {
  if (typeof window === "undefined") return "";
  const fromSession = sessionStorage.getItem("loja_slug");
  if (fromSession?.trim()) return fromSession.trim();
  const match = window.location.pathname.match(/^\/loja\/([^/]+)(\/|$)/);
  return match?.[1]?.trim() || "";
}

/**
 * Envia erro de API para o painel do suporte (erros no navegador). Fire-and-forget.
 * Assim o suporte vê falhas como 400/500 da API da loja no mesmo lugar que erros JS.
 */
function reportarErroApiParaSuporte(
  method: string,
  path: string,
  status: number,
  body: string
): void {
  const lojaSlug = getLojaSlugForReport();
  if (!lojaSlug) return;
  const mensagem = `API: ${method} ${path} — ${status} — ${body.slice(0, 400)}`;
  const payload = {
    mensagem,
    stack: "",
    url: typeof window !== "undefined" ? window.location.href : "",
    loja_slug: lojaSlug,
  };
  const apiBase = getApiBaseUrl();
  if (!apiBase) return;
  fetch(`${apiBase}/suporte/registrar-erro-frontend/`, {
    method: "POST",
    headers: { ...getClinicaBelezaHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  }).catch(() => {});
}

/**
 * Fetch para API Clínica da Beleza. Em 401 com código de sessão (outra sessão ativa), faz logout e redireciona.
 * Use este método para que o bloqueio de sessão única funcione em todas as telas da loja.
 * Erros 4xx/5xx são reportados ao suporte para aparecer em "Erros no navegador".
 */
export async function clinicaBelezaFetch(
  path: string,
  options: RequestInit = {},
  loja?: { id?: number; slug?: string } | null,
  retried = false,
): Promise<Response> {
  const base = getClinicaBelezaBaseUrl();
  const url = path.startsWith("http") ? path : `${base}${path.startsWith("/") ? path : `/${path}`}`;
  const method = (options.method || "GET").toUpperCase();
  const response = await fetch(url, {
    ...options,
    credentials: USE_JWT_HTTPONLY_COOKIES ? "include" : options.credentials,
    headers: { ...getClinicaBelezaHeadersWithLoja(loja), ...options.headers },
  });
  if (response.status === 401) {
    const handled = await handle401SessionResponse(response);
    if (handled) throw new Error("SESSION_ENDED");

    if (!retried) {
      const refreshed = await tryRefreshAccessToken();
      if (refreshed) {
        return clinicaBelezaFetch(path, options, loja, true);
      }
    }

    clearSessionAndRedirect(
      getLoginUrlForRedirect(),
      "Sessão expirada. Faça login novamente.",
    );
    throw new Error("SESSION_ENDED");
  }
  // Reportar erros de API ao suporte (exceto 429/401 — evita loop ao atingir rate limit)
  if (!response.ok && response.status !== 429 && response.status !== 401) {
    const clone = response.clone();
    (async () => {
      try {
        let bodyText = "";
        try {
          bodyText = JSON.stringify(await clone.json());
        } catch {
          try {
            bodyText = await clone.text();
          } catch {
            bodyText = String(response.status);
          }
        }
        const pathDisplay = `/clinica-beleza${path.startsWith("/") ? path : `/${path}`}`;
        reportarErroApiParaSuporte(method, pathDisplay, response.status, bodyText);
      } catch {
        // ignora falha ao reportar
      }
    })();
  }
  return response;
}

/** Item estruturado de uma prescrição emitida na Memed. */
export interface PacienteFotoItem {
  id: number;
  cloudinary_url: string;
  origem: string;
  origem_display: string;
  consulta_id: number;
  consulta_data: string;
  created_at: string;
}

export interface PrescricaoMemedItemDetalhe {
  nome?: string;
  posologia?: string;
  tipo?: string;
  receituario?: string;
}

/** Prescrição Memed registrada no histórico do paciente. */
export interface PrescricaoMemedItem {
  id: number;
  consulta: number | null;
  patient: number;
  patient_name?: string;
  professional: number | null;
  professional_name?: string | null;
  prescricao_id: string;
  resumo: string;
  itens: PrescricaoMemedItemDetalhe[];
  pdf_url?: string;
  created_at: string;
}

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

/**
 * Cliente API otimizado com métodos tipados
 */
export class ClinicaBelezaAPI {
  /** GET que retorna sempre um array (compatível com paginação opcional). */
  static async getList<T = unknown>(
    path: string,
    params?: Record<string, unknown>,
    loja?: { id?: number; slug?: string } | null,
  ): Promise<T[]> {
    const data = await ClinicaBelezaAPI.get(path, params, loja);
    return parseClinicaBelezaListResponse<T>(data);
  }

  /**
   * GET request
   */
  static async get<T = any>(
    path: string,
    params?: Record<string, any>,
    loja?: { id?: number; slug?: string } | null,
  ): Promise<T> {
    const url = params ? buildClinicaBelezaListUrl(path, params) : path;
    const res = await clinicaBelezaFetch(url, {}, loja);
    const data = await parseClinicaBelezaResponseBody(res);
    if (!res.ok) throw data;
    return data as T;
  }
  
  /**
   * POST request
   */
  static async post<T = any>(
    path: string,
    data: any,
    loja?: { id?: number; slug?: string } | null,
  ): Promise<T> {
    const res = await clinicaBelezaFetch(path, {
      method: 'POST',
      body: JSON.stringify(data),
    }, loja);
    const body = await parseClinicaBelezaResponseBody(res);
    if (!res.ok) throw body;
    return body as T;
  }
  
  /**
   * PUT request
   */
  static async put<T = any>(
    path: string,
    data: any,
    loja?: { id?: number; slug?: string } | null,
  ): Promise<T> {
    const res = await clinicaBelezaFetch(path, {
      method: 'PUT',
      body: JSON.stringify(data),
    }, loja);
    const body = await parseClinicaBelezaResponseBody(res);
    if (!res.ok) throw body;
    return body as T;
  }
  
  /**
   * PATCH request
   */
  static async patch<T = any>(
    path: string,
    data: any,
    loja?: { id?: number; slug?: string } | null,
  ): Promise<T> {
    const res = await clinicaBelezaFetch(path, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }, loja);
    const body = await parseClinicaBelezaResponseBody(res);
    if (!res.ok) throw body;
    return body as T;
  }
  
  /**
   * DELETE request
   */
  static async delete(path: string): Promise<void> {
    await clinicaBelezaFetch(path, { method: 'DELETE' });
  }

  static consultas = {
    list: (params?: { patient?: number; professional?: number; status?: string; appointment?: number }) =>
      ClinicaBelezaAPI.get('/consultas/', params),
    /** Abre uma consulta avulsa (sem agendamento na agenda) a partir do cadastro do cliente. */
    criar: (data: {
      patient: number;
      professional: number;
      procedure?: number;
      procedures_ids?: number[];
      iniciar?: boolean;
      local_atendimento?: number;
      valor_consulta?: number | string;
      convenio?: number | null;
    }) =>
      ClinicaBelezaAPI.post('/consultas/', data),
    get: (id: number) => ClinicaBelezaAPI.get(`/consultas/${id}/`),
    update: (id: number, data: Record<string, unknown>) => ClinicaBelezaAPI.patch(`/consultas/${id}/`, data),
    /** Exclui uma consulta (somente se não estiver concluída). */
    excluir: (id: number) => ClinicaBelezaAPI.delete(`/consultas/${id}/`),
    aplicarProtocolo: (id: number, protocolId: number) =>
      ClinicaBelezaAPI.post(`/consultas/${id}/aplicar-protocolo/`, { protocol_id: protocolId }),
    iniciar: (id: number, body?: { professional?: number }) => ClinicaBelezaAPI.post(`/consultas/${id}/iniciar/`, body || {}),
    finalizar: (
      id: number,
      data?: {
        payment_method?: string;
        mark_as_paid?: boolean;
        amount?: number | string;
        local_atendimento?: number;
      },
    ) => ClinicaBelezaAPI.post(`/consultas/${id}/finalizar/`, data ?? {}),
    evolucoes: {
      list: (consultaId: number) => ClinicaBelezaAPI.get(`/consultas/${consultaId}/evolucoes/`),
      create: (consultaId: number, data: Record<string, unknown>) =>
        ClinicaBelezaAPI.post(`/consultas/${consultaId}/evolucoes/`, data),
    },
    historicoCliente: (patientId: number, params?: { page?: number; page_size?: number }) =>
      ClinicaBelezaAPI.getList(`/patients/${patientId}/consultas/`, {
        page: 1,
        page_size: 100,
        ...params,
      }),
    produtos: {
      list: (consultaId: number) =>
        ClinicaBelezaAPI.get(`/consultas/${consultaId}/produtos/`),
      add: (
        consultaId: number,
        data: { produto: number; quantidade: number; lote?: string; validade?: string },
      ) => ClinicaBelezaAPI.post(`/consultas/${consultaId}/produtos/`, data),
      remove: (consultaId: number, itemId: number) =>
        ClinicaBelezaAPI.delete(`/consultas/${consultaId}/produtos/${itemId}/`),
    },
    fotos: {
      list: (consultaId: number) =>
        ClinicaBelezaAPI.get<{
          patient_id: number;
          patient_nome: string;
          fotos: PacienteFotoItem[];
        }>(`/consultas/${consultaId}/fotos/`),
      salvar: (consultaId: number, cloudinaryUrl: string, publicId?: string) =>
        ClinicaBelezaAPI.post<{ message: string; foto: PacienteFotoItem }>(
          `/consultas/${consultaId}/fotos/`,
          { cloudinary_url: cloudinaryUrl, cloudinary_public_id: publicId || '' },
        ),
      gerarQr: (consultaId: number) =>
        ClinicaBelezaAPI.post<{
          url: string;
          qr_base64: string;
          expira_em_horas: number;
        }>(`/consultas/${consultaId}/fotos/qr/`, {
          frontend_origin: typeof window !== 'undefined' ? window.location.origin : '',
        }),
      excluir: (consultaId: number, fotoId: number) =>
        ClinicaBelezaAPI.delete(`/consultas/${consultaId}/fotos/${fotoId}/`),
    },
    termoConsentimento: {
      get: (consultaId: number) =>
        ClinicaBelezaAPI.get<{
          exige_termo: boolean;
          status_assinatura_termo: string;
          tem_conteudo: boolean;
          termos_procedimentos: Array<{
            id: number;
            procedure_id: number;
            procedure_nome: string;
            status: string;
            status_display: string;
            tem_conteudo: boolean;
          }>;
        }>(`/consultas/${consultaId}/termo-consentimento/`),
      enviar: (consultaId: number, procedureId?: number, canal: 'email' | 'whatsapp' = 'email') =>
        ClinicaBelezaAPI.post<{
          message: string;
          status_assinatura_termo: string;
          enviados?: string[];
        }>(
          `/consultas/${consultaId}/termo-consentimento/enviar/`,
          { ...(procedureId ? { procedure_id: procedureId } : {}), canal },
        ),
      reenviar: (consultaId: number, procedureId: number, canal: 'email' | 'whatsapp' = 'email') =>
        ClinicaBelezaAPI.post<{ message: string; procedure_nome?: string }>(
          `/consultas/${consultaId}/termo-consentimento/reenviar/`,
          { procedure_id: procedureId, canal },
        ),
      pdfUrl: (consultaId: number, procedureId: number) => {
        const base = getClinicaBelezaBaseUrl();
        return `${base}/consultas/${consultaId}/termo-consentimento/pdf/?procedure_id=${procedureId}`;
      },
      downloadPdf: async (consultaId: number, procedureId: number) => {
        const res = await clinicaBelezaFetch(
          `/consultas/${consultaId}/termo-consentimento/pdf/?procedure_id=${procedureId}`,
        );
        if (!res.ok) throw new Error('Erro ao baixar PDF do termo.');
        return res.blob();
      },
    },
  };

  static anamnese = {
    get: (patientId: number) => ClinicaBelezaAPI.get(`/patients/${patientId}/anamnese/`),
    save: (patientId: number, data: Record<string, unknown>) =>
      ClinicaBelezaAPI.put(`/patients/${patientId}/anamnese/`, data),
  };

  static patients = {
    list: (params?: { active?: boolean; page?: number; page_size?: number }) =>
      ClinicaBelezaAPI.getList('/patients/', params),
    get: (id: number) => ClinicaBelezaAPI.get(`/patients/${id}/`),
    create: (data: Record<string, unknown>) => ClinicaBelezaAPI.post('/patients/', data),
    update: (id: number, data: Record<string, unknown>) =>
      ClinicaBelezaAPI.put(`/patients/${id}/`, data),
    delete: (id: number) => ClinicaBelezaAPI.delete(`/patients/${id}/`),
  };

  static professionals = {
    list: (params?: { active?: boolean; with_schedule?: boolean; page?: number; page_size?: number }) =>
      ClinicaBelezaAPI.getList('/professionals/', params),
    get: (id: number) => ClinicaBelezaAPI.get(`/professionals/${id}/`),
    create: (data: Record<string, unknown>) =>
      ClinicaBelezaAPI.post('/professionals/', data),
    update: (id: number, data: Record<string, unknown>) =>
      ClinicaBelezaAPI.put(`/professionals/${id}/`, data),
    delete: (id: number) => ClinicaBelezaAPI.delete(`/professionals/${id}/`),
    comissoes: {
      list: (id: number) => ClinicaBelezaAPI.get(`/professionals/${id}/comissoes/`),
      save: (id: number, payload: unknown[]) =>
        ClinicaBelezaAPI.post(`/professionals/${id}/comissoes/`, payload),
    },
    horarios: {
      get: (id: number) => ClinicaBelezaAPI.get(`/professionals/${id}/horarios-trabalho/`),
      save: (id: number, data: unknown) =>
        ClinicaBelezaAPI.put(`/professionals/${id}/horarios-trabalho/`, data),
    },
    adminStatus: () => ClinicaBelezaAPI.get('/professionals/admin-status/'),
    toggleAdmin: (data: Record<string, unknown>) =>
      ClinicaBelezaAPI.post('/professionals/toggle-admin/', data),
  };

  static loja = {
    info: () =>
      ClinicaBelezaAPI.get<{
        owner_username?: string;
        owner_email?: string;
        owner_telefone?: string;
      }>('/loja-info/'),
  };

  static financeiro = {
    resumo: (params?: { mes?: number; ano?: number }) =>
      ClinicaBelezaAPI.get('/financeiro/resumo/', params),
    despesas: {
      list: (params?: { status?: string; categoria?: number; date?: string; page?: number; page_size?: number }) =>
        ClinicaBelezaAPI.getList('/despesas/', params),
      create: (data: Record<string, unknown>) =>
        ClinicaBelezaAPI.post('/despesas/', data),
      update: (id: number, data: Record<string, unknown>) =>
        ClinicaBelezaAPI.put(`/despesas/${id}/`, data),
      delete: (id: number) => ClinicaBelezaAPI.delete(`/despesas/${id}/`),
      categorias: () => ClinicaBelezaAPI.getList<{ id: number; nome: string }>('/despesas/categorias/'),
    },
  };

  static estoque = {
    list: (
      params?: { categoria?: string; search?: string; page?: number; page_size?: number },
      loja?: { id?: number; slug?: string } | null,
    ) => ClinicaBelezaAPI.getList('/estoque/', params, loja),
    get: (id: number) => ClinicaBelezaAPI.get(`/estoque/${id}/`),
    create: (data: Record<string, unknown>, loja?: { id?: number; slug?: string } | null) =>
      ClinicaBelezaAPI.post('/estoque/', data, loja),
    update: (id: number, data: Record<string, unknown>, loja?: { id?: number; slug?: string } | null) =>
      ClinicaBelezaAPI.put(`/estoque/${id}/`, data, loja),
    delete: (id: number) => ClinicaBelezaAPI.delete(`/estoque/${id}/`),
    resumo: (loja?: { id?: number; slug?: string } | null) =>
      ClinicaBelezaAPI.get('/estoque/resumo/', undefined, loja),
    movimentar: (id: number, data: { tipo: string; quantidade: number; motivo?: string }) =>
      ClinicaBelezaAPI.post(`/estoque/${id}/movimentar/`, data),
  };

  static memed = {
    /** Token do prescritor + URL do script da Memed (api-key/secret-key ficam no backend). */
    token: (params?: { professional?: number; prescritor?: string; uf?: string }) =>
      ClinicaBelezaAPI.get<{
        token: string;
        script_url: string;
        environment: string;
        prescritor?: { nome?: string; sobrenome?: string; crm?: string; uf?: string };
        clinica?: {
          local_name?: string;
          address?: string;
          city?: string;
          state?: string;
          phone?: string;
        };
      }>('/memed/token/', params as Record<string, string> | undefined),

    timbrado: {
      get: () => ClinicaBelezaAPI.get('/memed/timbrado/'),
    },

    /** Registra no histórico do paciente uma prescrição emitida na Memed. */
    salvarPrescricao: (
      consultaId: number,
      data: { prescricao_id?: string; resumo?: string; itens?: unknown[]; pdf_url?: string; professional?: number | null },
    ) => ClinicaBelezaAPI.post(`/consultas/${consultaId}/prescricoes/`, data),

    /** Lista prescrições Memed registradas nesta consulta. */
    listarPrescricoesConsulta: (consultaId: number) =>
      ClinicaBelezaAPI.get<PrescricaoMemedItem[]>(`/consultas/${consultaId}/prescricoes/`),

    /** Lista as prescrições registradas para um paciente (histórico). */
    listarPrescricoesPaciente: (patientId: number) =>
      ClinicaBelezaAPI.getList<PrescricaoMemedItem>(`/patients/${patientId}/prescricoes/`),

    /** Busca/salva PDF da prescrição na Memed e retorna URL para impressão. */
    obterPdf: (prescricaoId: number) =>
      ClinicaBelezaAPI.post<{ pdf_url: string }>(`/prescricoes-memed/${prescricaoId}/pdf/`, {}),
  };

  static templates = {
    list: async (params?: { tipo?: string; page?: number; page_size?: number; professional?: number }) => {
      const data = await ClinicaBelezaAPI.get<
        DocumentTemplateItem[] | { results: DocumentTemplateItem[]; count: number }
      >('/templates/', params);
      if (Array.isArray(data)) {
        return { results: data, count: data.length };
      }
      return { results: data?.results ?? [], count: data?.count ?? 0 };
    },
    get: (id: number) => ClinicaBelezaAPI.get<DocumentTemplateItem>(`/templates/${id}/`),
    create: (data: { nome: string; tipo: string; conteudo: string }) =>
      ClinicaBelezaAPI.post<DocumentTemplateItem>('/templates/', data),
    update: (id: number, data: Partial<{ nome: string; tipo: string; conteudo: string }>) =>
      ClinicaBelezaAPI.put<DocumentTemplateItem>(`/templates/${id}/`, data),
    delete: (id: number) => ClinicaBelezaAPI.delete(`/templates/${id}/`),
  };

  static documentos = {
    list: (consultaId: number) =>
      ClinicaBelezaAPI.get<DocumentoClinicoItem[]>(`/consultas/${consultaId}/documentos/`),
    create: (consultaId: number, data: { tipo: string; conteudo?: string; template_id?: number; titulo?: string }) =>
      ClinicaBelezaAPI.post<DocumentoClinicoItem>(`/consultas/${consultaId}/documentos/`, data),
    delete: (consultaId: number, docId: number) =>
      ClinicaBelezaAPI.delete(`/consultas/${consultaId}/documentos/${docId}/`),
  };

  static prontuario = {
    get: (patientId: number, secao?: string) =>
      ClinicaBelezaAPI.get<ProntuarioData>(`/patients/${patientId}/prontuario/`, secao ? { secao } : undefined),
    pdfUrl: (patientId: number, secao?: string) => {
      const base = getClinicaBelezaBaseUrl();
      const query = secao ? `?secao=${secao}` : '';
      return `${base}/patients/${patientId}/prontuario/pdf/${query}`;
    },
    documentoPdfUrl: (docId: number) => {
      const base = getClinicaBelezaBaseUrl();
      return `${base}/documentos/${docId}/pdf/`;
    },
  };

  static locaisAtendimento = {
    list: () =>
      ClinicaBelezaAPI.get<LocalAtendimentoItem[]>('/locais-atendimento/'),
    create: (data: { nome: string; valor_consulta: number | string; tempo_consulta_minutos?: number }) =>
      ClinicaBelezaAPI.post<LocalAtendimentoItem>('/locais-atendimento/', data),
    update: (id: number, data: { nome?: string; valor_consulta?: number | string; tempo_consulta_minutos?: number; is_padrao?: boolean }) =>
      ClinicaBelezaAPI.patch<LocalAtendimentoItem>(`/locais-atendimento/${id}/`, data),
    delete: (id: number) =>
      ClinicaBelezaAPI.delete(`/locais-atendimento/${id}/`),
  };

  static nomesAgenda = {
    list: () =>
      ClinicaBelezaAPI.get<NomeAgendaItem[]>('/nomes-agenda/'),
    create: (data: { nome: string }) =>
      ClinicaBelezaAPI.post<NomeAgendaItem>('/nomes-agenda/', data),
    update: (id: number, data: { nome?: string; is_padrao?: boolean }) =>
      ClinicaBelezaAPI.patch<NomeAgendaItem>(`/nomes-agenda/${id}/`, data),
    delete: (id: number) =>
      ClinicaBelezaAPI.delete(`/nomes-agenda/${id}/`),
  };

  static retorno = {
    getConfig: () => ClinicaBelezaAPI.get<AgendaRetornoConfigItem>('/retorno/config/'),
    updateConfig: (data: Partial<Pick<AgendaRetornoConfigItem, 'retorno_procedimento_ativo' | 'retorno_consulta_ativo' | 'dias_retorno_consulta'>>) =>
      ClinicaBelezaAPI.patch<AgendaRetornoConfigItem>('/retorno/config/', data),
    listRegras: () => ClinicaBelezaAPI.get<RetornoProcedimentoRegraItem[]>('/retorno/procedimentos/'),
    createRegra: (data: { procedure: number; dias_retorno: number }) =>
      ClinicaBelezaAPI.post<RetornoProcedimentoRegraItem>('/retorno/procedimentos/', data),
    updateRegra: (id: number, data: { dias_retorno?: number; is_active?: boolean }) =>
      ClinicaBelezaAPI.patch<RetornoProcedimentoRegraItem>(`/retorno/procedimentos/${id}/`, data),
    deleteRegra: (id: number) => ClinicaBelezaAPI.delete(`/retorno/procedimentos/${id}/`),
    verificar: (params: {
      patient_id: number;
      procedure_ids?: number[];
      retorno_procedure_id?: number;
      exclude_appointment_id?: number;
    }) => {
      const qs = new URLSearchParams({ patient_id: String(params.patient_id) });
      if (params.procedure_ids?.length) {
        qs.set('procedure_ids', params.procedure_ids.join(','));
      }
      if (params.retorno_procedure_id) {
        qs.set('retorno_procedure_id', String(params.retorno_procedure_id));
      }
      if (params.exclude_appointment_id) {
        qs.set('exclude_appointment_id', String(params.exclude_appointment_id));
      }
      return ClinicaBelezaAPI.get<RetornoVerificacaoResult>(`/retorno/verificar/?${qs.toString()}`);
    },
  };

  static campanhas = {
    list: () => ClinicaBelezaAPI.get('/campanhas/'),
    get: (id: number) => ClinicaBelezaAPI.get(`/campanhas/${id}/`),
    create: (data: Record<string, unknown>) => ClinicaBelezaAPI.post('/campanhas/', data),
    update: (id: number, data: Record<string, unknown>) => ClinicaBelezaAPI.put(`/campanhas/${id}/`, data),
    delete: (id: number) => ClinicaBelezaAPI.delete(`/campanhas/${id}/`),
    enviar: (id: number) => ClinicaBelezaAPI.post(`/campanhas/${id}/enviar/`, {}),
  };

  static protocolos = {
    list: (params?: { categoria?: string; procedure?: number; page?: number; page_size?: number }) =>
      ClinicaBelezaAPI.getList('/protocolos/', params),
    get: (id: number) => ClinicaBelezaAPI.get(`/protocolos/${id}/`),
    create: (data: Record<string, unknown>) => ClinicaBelezaAPI.post('/protocolos/', data),
    update: (id: number, data: Record<string, unknown>) =>
      ClinicaBelezaAPI.put(`/protocolos/${id}/`, data),
    delete: (id: number) => ClinicaBelezaAPI.delete(`/protocolos/${id}/`),
  };

  static procedures = {
    list: (params?: { categoria?: string; active?: boolean; page?: number; page_size?: number }) =>
      ClinicaBelezaAPI.getList('/procedures/', params),
    get: (id: number) => ClinicaBelezaAPI.get(`/procedures/${id}/`),
    create: (data: Record<string, unknown>) => ClinicaBelezaAPI.post('/procedures/', data),
    update: (id: number, data: Record<string, unknown>) =>
      ClinicaBelezaAPI.put(`/procedures/${id}/`, data),
    delete: (id: number) => ClinicaBelezaAPI.delete(`/procedures/${id}/`),
    convenioPrecosMatrix: () =>
      ClinicaBelezaAPI.get<ProcedimentoConvenioPrecosMatrix>('/procedures/convenio-precos-matrix/'),
    precosConvenio: (id: number) =>
      ClinicaBelezaAPI.get<ProcedureConvenioPrecoItem[]>(`/procedures/${id}/precos-convenio/`),
    savePrecosConvenio: (
      id: number,
      precos: { convenio: number; preco: number | string | null }[],
    ) =>
      ClinicaBelezaAPI.put<ConvenioPrecoItem[]>(`/procedures/${id}/precos-convenio/`, { precos }),
  };

  static convenios = {
    list: (params?: { todos?: boolean; page?: number; page_size?: number }) =>
      ClinicaBelezaAPI.getList<ConvenioItem>('/convenios/', params),
    get: (id: number) => ClinicaBelezaAPI.get<ConvenioDetailItem>(`/convenios/${id}/`),
    create: (data: { nome: string; codigo?: string }) =>
      ClinicaBelezaAPI.post<ConvenioDetailItem>('/convenios/', data),
    update: (id: number, data: { nome?: string; codigo?: string; is_active?: boolean }) =>
      ClinicaBelezaAPI.put<ConvenioDetailItem>(`/convenios/${id}/`, data),
    delete: (id: number) => ClinicaBelezaAPI.delete(`/convenios/${id}/`),
    precos: (id: number) => ClinicaBelezaAPI.get<ConvenioPrecoItem[]>(`/convenios/${id}/precos/`),
    savePrecos: (
      id: number,
      precos: { procedure: number; modo?: ConvenioPrecoModo; preco: number | string | null }[],
    ) =>
      ClinicaBelezaAPI.put<ConvenioPrecoItem[]>(`/convenios/${id}/precos/`, { precos }),
  };
}

/** Convênio (plano) */
export interface ConvenioItem {
  id: number;
  nome: string;
  codigo?: string;
  is_active?: boolean;
}

export type ConvenioPrecoModo = 'fixo' | 'percentual';

export interface ConvenioPrecoItem {
  id?: number;
  procedure: number;
  procedure_name?: string;
  preco_particular?: string | number;
  modo?: ConvenioPrecoModo;
  preco: string | number;
  preco_efetivo?: string | number;
}

export interface ConvenioDetailItem extends ConvenioItem {
  precos?: ConvenioPrecoItem[];
  created_at?: string;
  updated_at?: string;
}

export interface ProcedimentoConvenioPrecosMatrix {
  convenios: ConvenioItem[];
  precos: { procedure: number; convenio: number; preco: string }[];
}

export interface ProcedureConvenioPrecoItem {
  convenio: number;
  convenio_codigo?: string;
  convenio_nome?: string;
  modo?: ConvenioPrecoModo;
  preco: string | number | null;
  preco_efetivo?: number | null;
}

/** Local de atendimento para consultas */
export interface LocalAtendimentoItem {
  id: number;
  nome: string;
  valor_consulta: string | number;
  tempo_consulta_minutos?: number | null;
  is_padrao?: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/** Nome de agenda (categoria do calendário) */
export interface NomeAgendaItem {
  id: number;
  nome: string;
  is_padrao?: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/** Configuração de retorno gratuito (isenção da taxa de consulta) */
export interface AgendaRetornoConfigItem {
  id: number;
  retorno_procedimento_ativo: boolean;
  retorno_consulta_ativo: boolean;
  dias_retorno_consulta: number;
  created_at: string;
  updated_at: string;
  loja_id?: number;
}

export interface RetornoProcedimentoRegraItem {
  id: number;
  procedure: number;
  procedure_name: string;
  dias_retorno: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  loja_id?: number;
}

export interface RetornoVerificacaoResult {
  elegivel: boolean;
  tipo?: 'procedimento' | 'consulta' | null;
  procedure_id?: number | null;
  procedure_nome?: string | null;
  dias_retorno?: number | null;
  dias_restantes?: number | null;
  consulta_origem_id?: number | null;
  mensagem?: string | null;
  config?: AgendaRetornoConfigItem;
  regras_procedimento?: RetornoProcedimentoRegraItem[];
}

/** Template de documento clínico */
export interface DocumentTemplateItem {
  id: number;
  professional: number;
  nome: string;
  tipo: string;
  conteudo: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/** Documento clínico gerado durante consulta */
export interface DocumentoClinicoItem {
  id: number;
  consulta: number;
  patient: number;
  professional: number;
  professional_name: string | null;
  template: number | null;
  tipo: string;
  titulo: string;
  conteudo: string;
  created_at: string;
}

/** Dados do prontuário agrupado por seção */
export interface ProntuarioData {
  receituario: ProntuarioDocItem[];
  pedido_exame: ProntuarioDocItem[];
  atestado: ProntuarioDocItem[];
  documento_personalizado: ProntuarioDocItem[];
  evolucao: ProntuarioEvolucaoItem[];
  anamnese: ProntuarioAnamneseItem | null;
}

export interface ProntuarioDocItem {
  id: number;
  tipo: string;
  titulo: string;
  conteudo: string;
  professional_name: string | null;
  consulta_id: number | null;
  created_at: string | null;
  pdf_url?: string;
  source: 'documento_clinico' | 'memed';
}

export interface ProntuarioEvolucaoItem {
  id: number;
  descricao: string;
  procedimento_realizado: string;
  produtos_utilizados: string;
  orientacoes: string;
  professional_name: string | null;
  consulta_id: number | null;
  created_at: string | null;
}

export interface ProntuarioAnamneseItem {
  id: number;
  queixa_principal: string;
  historico_medico: string;
  medicamentos_uso: string;
  alergias: string;
  tipo_pele: string;
  observacoes: string;
  created_at: string | null;
  updated_at: string | null;
}
