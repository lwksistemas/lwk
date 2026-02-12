/**
 * API Clínica da Beleza - base URL (com /api) e headers com tenant para requisições.
 * O backend exige X-Tenant-Slug ou X-Loja-ID para resolver a loja; sem isso usa o hostname (Heroku) e retorna 404.
 */

function getAuthToken(): string | null {
  if (typeof window === "undefined") return null;
  return sessionStorage.getItem("access_token") || localStorage.getItem("token");
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

export async function clinicaBelezaFetch(
  path: string,
  options: RequestInit = {}
): Promise<Response> {
  const base = getClinicaBelezaBaseUrl();
  const url = path.startsWith("http") ? path : `${base}${path.startsWith("/") ? path : `/${path}`}`;
  return fetch(url, {
    ...options,
    headers: { ...getClinicaBelezaHeaders(), ...options.headers },
  });
}
