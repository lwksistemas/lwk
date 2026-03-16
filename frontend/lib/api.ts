const API_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/api\/?$/, "") || "http://localhost:8000";
const API_BASE = `${API_URL}/api`;

const FETCH_TIMEOUT = 10000; // 10s para produção

export async function getHomepage() {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), FETCH_TIMEOUT);

  try {
    const res = await fetch(`${API_BASE}/homepage/`, {
      cache: "no-store",
      signal: controller.signal,
      headers: { "Accept": "application/json" },
    });
    clearTimeout(timeoutId);

    if (!res.ok) {
      throw new Error(`Erro ao carregar homepage: ${res.status}`);
    }

    return res.json();
  } catch (err) {
    clearTimeout(timeoutId);
    throw err;
  }
}
