/**
 * Cliente API otimizado para Clínica da Beleza
 */

import { clearSessionAndRedirect, getLoginUrlForRedirect, getCurrentApiBaseUrl } from "@/lib/api-client";
import { USE_JWT_HTTPONLY_COOKIES } from "@/lib/auth-cookies";

const SESSION_CODES = [
  "DIFFERENT_SESSION",
  "NO_SESSION",
  "TIMEOUT",
  "SESSION_CONFLICT",
  "SESSION_TIMEOUT",
] as const;

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
    credentials: USE_JWT_HTTPONLY_COOKIES ? "include" : options.credentials,
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

/** Normaliza resposta da API: array direto ou envelope paginado { results, count }. */
export function parseClinicaBelezaListResponse<T>(data: unknown): T[] {
  if (Array.isArray(data)) return data as T[];
  if (data && typeof data === 'object' && 'results' in data) {
    const results = (data as { results?: unknown }).results;
    return Array.isArray(results) ? (results as T[]) : [];
  }
  return [];
}

/**
 * Cliente API otimizado com métodos tipados
 */
export class ClinicaBelezaAPI {
  /** GET que retorna sempre um array (compatível com paginação opcional). */
  static async getList<T = unknown>(path: string, params?: Record<string, unknown>): Promise<T[]> {
    const data = await ClinicaBelezaAPI.get(path, params);
    return parseClinicaBelezaListResponse<T>(data);
  }

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

  static templates = {
    list: async (params?: { tipo?: string; page?: number; page_size?: number }) => {
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
    create: (data: { nome: string; valor_consulta: number | string }) =>
      ClinicaBelezaAPI.post<LocalAtendimentoItem>('/locais-atendimento/', data),
    update: (id: number, data: { nome?: string; valor_consulta?: number | string }) =>
      ClinicaBelezaAPI.put<LocalAtendimentoItem>(`/locais-atendimento/${id}/`, data),
    delete: (id: number) =>
      ClinicaBelezaAPI.delete(`/locais-atendimento/${id}/`),
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

/** Local de atendimento para consultas */
export interface LocalAtendimentoItem {
  id: number;
  nome: string;
  valor_consulta: string | number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
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
