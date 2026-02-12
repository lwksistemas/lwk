/**
 * API Clínica da Beleza - base URL e token para requisições
 */

function getAuthToken(): string | null {
  if (typeof window === "undefined") return null;
  return sessionStorage.getItem("access_token") || localStorage.getItem("token");
}

export function getClinicaBelezaHeaders(): HeadersInit {
  const token = getAuthToken();
  return {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
  };
}

export function getClinicaBelezaBaseUrl(): string {
  return `${process.env.NEXT_PUBLIC_API_URL}/clinica-beleza`;
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
