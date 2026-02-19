/**
 * Cliente API otimizado para Clínica da Beleza
 */

import { clearSessionAndRedirect, getLoginUrlForRedirect } from "@/lib/api-client";

const SESSION_CODES = [
  "DIFFERENT_SESSION",
  "NO_SESSION",
  "TIMEOUT",
  "SESSION_CONFLICT",
  "SESSION_TIMEOUT",
] as const;

function getAuthToken(): string | null {
  if (typeof window === "undefined") return null;
  return sessionStorage.getItem("access_token") || localStorage.getItem("token");
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

/** Base da API (com /api): ex. https://xxx.herokuapp.com/api */
export function getApiBaseUrl(): string {
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
  let lojaId: string | null = loja?.id != null ? String(loja.id) : null;
  let lojaSlug: string | null = loja?.slug ?? null;
  if (typeof window !== "undefined") {
    if (!lojaId) lojaId = sessionStorage.getItem("current_loja_id");
    if (!lojaSlug) lojaSlug = sessionStorage.getItem("loja_slug");
    if (!lojaSlug) {
      const match = window.location.pathname.match(/^\/loja\/([^/]+)\//);
      if (match) lojaSlug = match[1];
    }
  }
  if (lojaId) h["X-Loja-ID"] = lojaId;
  else if (lojaSlug) h["X-Tenant-Slug"] = lojaSlug;
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
  options: RequestInit = {}
): Promise<Response> {
  const base = getClinicaBelezaBaseUrl();
  const url = path.startsWith("http") ? path : `${base}${path.startsWith("/") ? path : `/${path}`}`;
  const method = (options.method || "GET").toUpperCase();
  const response = await fetch(url, {
    ...options,
    headers: { ...getClinicaBelezaHeaders(), ...options.headers },
  });
  if (response.status === 401) {
    const handled = await handle401SessionResponse(response);
    if (handled) throw new Error("SESSION_ENDED");
    // Token expirado ou inválido (sem código de sessão): mensagem amigável e redirect
    clearSessionAndRedirect(
      getLoginUrlForRedirect(),
      "Sessão expirada ou token inválido. Faça login novamente."
    );
    throw new Error("SESSION_ENDED");
  }
  // Reportar erros de API ao suporte (4xx/5xx) para aparecer no painel "Erros no navegador"
  if (!response.ok) {
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

/**
 * Cliente API otimizado com métodos tipados
 */
export class ClinicaBelezaAPI {
  /**
   * GET request
   */
  static async get<T = any>(path: string, params?: Record<string, any>): Promise<T> {
    const queryString = params ? '?' + new URLSearchParams(params).toString() : '';
    const res = await clinicaBelezaFetch(`${path}${queryString}`);
    return res.json();
  }
  
  /**
   * POST request
   */
  static async post<T = any>(path: string, data: any): Promise<T> {
    const res = await clinicaBelezaFetch(path, {
      method: 'POST',
      body: JSON.stringify(data)
    });
    return res.json();
  }
  
  /**
   * PUT request
   */
  static async put<T = any>(path: string, data: any): Promise<T> {
    const res = await clinicaBelezaFetch(path, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
    return res.json();
  }
  
  /**
   * PATCH request
   */
  static async patch<T = any>(path: string, data: any): Promise<T> {
    const res = await clinicaBelezaFetch(path, {
      method: 'PATCH',
      body: JSON.stringify(data)
    });
    return res.json();
  }
  
  /**
   * DELETE request
   */
  static async delete(path: string): Promise<void> {
    await clinicaBelezaFetch(path, { method: 'DELETE' });
  }
  
  // Métodos específicos para endpoints comuns
  
  static dashboard = {
    get: (params?: { period?: string; professional?: number }) => 
      ClinicaBelezaAPI.get('/dashboard/', params),
  };
  
  static appointments = {
    list: (params?: { date?: string; status?: string; professional?: number }) =>
      ClinicaBelezaAPI.get('/appointments/', params),
    get: (id: number) => 
      ClinicaBelezaAPI.get(`/appointments/${id}/`),
    create: (data: any) => 
      ClinicaBelezaAPI.post('/appointments/', data),
    update: (id: number, data: any) => 
      ClinicaBelezaAPI.put(`/appointments/${id}/`, data),
    delete: (id: number) => 
      ClinicaBelezaAPI.delete(`/appointments/${id}/`),
  };
  
  static patients = {
    list: () => ClinicaBelezaAPI.get('/patients/'),
    get: (id: number) => ClinicaBelezaAPI.get(`/patients/${id}/`),
    create: (data: any) => ClinicaBelezaAPI.post('/patients/', data),
    update: (id: number, data: any) => ClinicaBelezaAPI.put(`/patients/${id}/`, data),
    delete: (id: number) => ClinicaBelezaAPI.delete(`/patients/${id}/`),
  };
  
  static professionals = {
    list: () => ClinicaBelezaAPI.get('/professionals/'),
    get: (id: number) => ClinicaBelezaAPI.get(`/professionals/${id}/`),
    create: (data: any) => ClinicaBelezaAPI.post('/professionals/', data),
    update: (id: number, data: any) => ClinicaBelezaAPI.put(`/professionals/${id}/`, data),
    delete: (id: number) => ClinicaBelezaAPI.delete(`/professionals/${id}/`),
  };
  
  static procedures = {
    list: () => ClinicaBelezaAPI.get('/procedures/'),
    get: (id: number) => ClinicaBelezaAPI.get(`/procedures/${id}/`),
    create: (data: any) => ClinicaBelezaAPI.post('/procedures/', data),
    update: (id: number, data: any) => ClinicaBelezaAPI.put(`/procedures/${id}/`, data),
    delete: (id: number) => ClinicaBelezaAPI.delete(`/procedures/${id}/`),
  };
  
  static agenda = {
    list: (params?: { start?: string; end?: string; professional?: number }) =>
      ClinicaBelezaAPI.get('/agenda/', params),
    today: () => ClinicaBelezaAPI.get('/agenda/hoje/'),
    create: (data: any) => ClinicaBelezaAPI.post('/agenda/create/', data),
    update: (id: number, data: any) => ClinicaBelezaAPI.patch(`/agenda/${id}/update/`, data),
    delete: (id: number) => ClinicaBelezaAPI.delete(`/agenda/${id}/delete/`),
    reenviarMensagem: (id: number) => ClinicaBelezaAPI.post(`/agenda/${id}/reenviar-mensagem/`, {}),
  };
  
  static bloqueios = {
    list: (params?: { start?: string; end?: string; professional?: number }) =>
      ClinicaBelezaAPI.get('/bloqueios/', params),
    get: (id: number) => ClinicaBelezaAPI.get(`/bloqueios/${id}/`),
    create: (data: any) => ClinicaBelezaAPI.post('/bloqueios/', data),
    update: (id: number, data: any) => ClinicaBelezaAPI.put(`/bloqueios/${id}/`, data),
    delete: (id: number) => ClinicaBelezaAPI.delete(`/bloqueios/${id}/`),
  };
  
  static campanhas = {
    list: () => ClinicaBelezaAPI.get('/campanhas/'),
    get: (id: number) => ClinicaBelezaAPI.get(`/campanhas/${id}/`),
    create: (data: any) => ClinicaBelezaAPI.post('/campanhas/', data),
    update: (id: number, data: any) => ClinicaBelezaAPI.put(`/campanhas/${id}/`, data),
    delete: (id: number) => ClinicaBelezaAPI.delete(`/campanhas/${id}/`),
    enviar: (id: number) => ClinicaBelezaAPI.post(`/campanhas/${id}/enviar/`, {}),
  };
}
