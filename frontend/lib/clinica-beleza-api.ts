/**
 * API Clínica da Beleza - base URL (com /api) e headers com tenant para requisições.
 * O backend exige X-Tenant-Slug ou X-Loja-ID para resolver a loja; sem isso usa o hostname (Heroku) e retorna 404.
 * Em 401 com código de sessão (ex.: DIFFERENT_SESSION), faz logout e redireciona para login (sessão única).
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

export function getClinicaBelezaHeaders(): HeadersInit {
  const token = getAuthToken();
  const headers: HeadersInit = {
    "Content-Type": "application/json",
  };
  if (token) {
    (headers as Record<string, string>)["Authorization"] = `Bearer ${token}`;
  }
  if (typeof window !== "undefined") {
    let lojaId = sessionStorage.getItem("current_loja_id");
    let lojaSlug = sessionStorage.getItem("loja_slug");
    // Fallback: slug da URL (ex: /loja/teste-5889/clinica-beleza/agenda)
    if (!lojaId && !lojaSlug && typeof window !== "undefined") {
      const match = window.location.pathname.match(/^\/loja\/([^/]+)\//);
      if (match) lojaSlug = match[1];
    }
    if (lojaId) (headers as Record<string, string>)["X-Loja-ID"] = lojaId;
    else if (lojaSlug) (headers as Record<string, string>)["X-Tenant-Slug"] = lojaSlug;
  }
  return headers;
}

export function getClinicaBelezaBaseUrl(): string {
  return `${getApiBaseUrl()}/clinica-beleza`;
}

/**
 * Fetch para API Clínica da Beleza. Em 401 com código de sessão (outra sessão ativa), faz logout e redireciona.
 * Use este método para que o bloqueio de sessão única funcione em todas as telas da loja.
 */
export async function clinicaBelezaFetch(
  path: string,
  options: RequestInit = {}
): Promise<Response> {
  const base = getClinicaBelezaBaseUrl();
  const url = path.startsWith("http") ? path : `${base}${path.startsWith("/") ? path : `/${path}`}`;
  const response = await fetch(url, {
    ...options,
    headers: { ...getClinicaBelezaHeaders(), ...options.headers },
  });
  if (response.status === 401) {
    const handled = await handle401SessionResponse(response);
    if (handled) throw new Error("SESSION_ENDED");
  }
  return response;
}
