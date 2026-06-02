/**
 * Cliente API otimizado para Clínica da Beleza
 */

import { clearSessionAndRedirect, getLoginUrlForRedirect, getCurrentApiBaseUrl } from "@/lib/api-client";

const SESSION_CODES = [
  "DIFFERENT_SESSION",
  "NO_SESSION",
  "TIMEOUT",
  "SESSION_CONFLICT",
  "SESSION_TIMEOUT",
] as const;

function getAuthToken(): string | null {
  if (typeof window === "undefined") return null;
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
  options: RequestInit = {},
  loja?: { id?: number; slug?: string } | null,
): Promise<Response> {
  const base = getClinicaBelezaBaseUrl();
  const url = path.startsWith("http") ? path : `${base}${path.startsWith("/") ? path : `/${path}`}`;
  const method = (options.method || "GET").toUpperCase();
  const response = await fetch(url, {
    ...options,
    headers: { ...getClinicaBelezaHeadersWithLoja(loja), ...options.headers },
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

/** Item estruturado de uma prescrição emitida na Memed. */
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

  static consultas = {
    list: (params?: { patient?: number; professional?: number; status?: string; appointment?: number }) =>
      ClinicaBelezaAPI.get('/consultas/', params),
    /** Abre uma consulta avulsa (sem agendamento na agenda) a partir do cadastro do cliente. */
    criar: (data: { patient: number; professional: number; procedure?: number; procedures_ids?: number[]; iniciar?: boolean }) =>
      ClinicaBelezaAPI.post('/consultas/', data),
    get: (id: number) => ClinicaBelezaAPI.get(`/consultas/${id}/`),
    update: (id: number, data: Record<string, unknown>) => ClinicaBelezaAPI.patch(`/consultas/${id}/`, data),
    /** Exclui uma consulta (somente se não estiver concluída). */
    excluir: (id: number) => ClinicaBelezaAPI.delete(`/consultas/${id}/`),
    aplicarProtocolo: (id: number, protocolId: number) =>
      ClinicaBelezaAPI.post(`/consultas/${id}/aplicar-protocolo/`, { protocol_id: protocolId }),
    iniciar: (id: number) => ClinicaBelezaAPI.post(`/consultas/${id}/iniciar/`, {}),
    finalizar: (
      id: number,
      data?: { payment_method?: string; mark_as_paid?: boolean; amount?: number | string },
    ) => ClinicaBelezaAPI.post(`/consultas/${id}/finalizar/`, data ?? {}),
    evolucoes: {
      list: (consultaId: number) => ClinicaBelezaAPI.get(`/consultas/${consultaId}/evolucoes/`),
      create: (consultaId: number, data: Record<string, unknown>) =>
        ClinicaBelezaAPI.post(`/consultas/${consultaId}/evolucoes/`, data),
    },
    historicoCliente: (patientId: number) =>
      ClinicaBelezaAPI.get(`/patients/${patientId}/consultas/`),
  };

  static anamnese = {
    get: (patientId: number) => ClinicaBelezaAPI.get(`/patients/${patientId}/anamnese/`),
    save: (patientId: number, data: Record<string, unknown>) =>
      ClinicaBelezaAPI.put(`/patients/${patientId}/anamnese/`, data),
  };

  static professionals = {
    /** Status Memed (Em análise, Ativo, etc.) por id do profissional. */
    memedStatus: () =>
      ClinicaBelezaAPI.get<Record<string, {
        state: string;
        label: string;
        status?: string;
        terms_accepted?: boolean;
        tem_token?: boolean;
        environment?: string;
      }>>('/professionals/memed-status/'),
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

    /** Registra no histórico do paciente uma prescrição emitida na Memed. */
    salvarPrescricao: (
      consultaId: number,
      data: { prescricao_id?: string; resumo?: string; itens?: unknown[]; pdf_url?: string; professional?: number | null },
    ) => ClinicaBelezaAPI.post(`/consultas/${consultaId}/prescricoes/`, data),

    /** Lista as prescrições registradas para um paciente (histórico). */
    listarPrescricoesPaciente: (patientId: number) =>
      ClinicaBelezaAPI.get<PrescricaoMemedItem[]>(`/patients/${patientId}/prescricoes/`),
  };
}
