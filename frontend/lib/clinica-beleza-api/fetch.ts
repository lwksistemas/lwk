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
    headers: (() => {
      const merged = { ...getClinicaBelezaHeadersWithLoja(loja), ...options.headers };
      // FormData: remover Content-Type para que o browser sete multipart/form-data com boundary
      if (options.body instanceof FormData) {
        delete (merged as Record<string, string>)["Content-Type"];
      }
      return merged;
    })(),
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
  // Reportar erros de API ao suporte (exceto 429/401 e Memed 404 esperado sem prescritor)
  const pathNorm = path.startsWith("/") ? path : `/${path}`;
  const memedToken404 =
    response.status === 404 && pathNorm.startsWith("/memed/token");
  if (!response.ok && response.status !== 429 && response.status !== 401 && !memedToken404) {
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
        const pathDisplay = `/clinica-beleza${pathNorm}`;
        reportarErroApiParaSuporte(method, pathDisplay, response.status, bodyText);
      } catch {
        // ignora falha ao reportar
      }
    })();
  }
  return response;
}
