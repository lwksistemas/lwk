import type { LojaInfo } from "@/types/dashboard";

function cacheKey(slug: string) {
  return `cb_loja_info_${(slug || "").trim().toLowerCase()}`;
}

/** Lê info_publica cacheada no sessionStorage (slug ou atalho). */
export function readLojaInfoPublicaCache(slug: string): LojaInfo | null {
  if (typeof window === "undefined" || !slug) return null;
  try {
    const raw = sessionStorage.getItem(cacheKey(slug));
    if (!raw) return null;
    const data = JSON.parse(raw) as LojaInfo;
    return data?.id ? data : null;
  } catch {
    return null;
  }
}

/** Grava info_publica sob slug da URL, slug canônico e atalho. */
export function writeLojaInfoPublicaCache(urlSlug: string, data: LojaInfo) {
  if (typeof window === "undefined" || !data?.id) return;
  const payload = JSON.stringify(data);
  const keys = new Set(
    [urlSlug, data.slug || "", data.atalho || ""]
      .map((s) => s.trim().toLowerCase())
      .filter(Boolean),
  );
  for (const key of keys) {
    sessionStorage.setItem(cacheKey(key), payload);
  }
  sessionStorage.setItem("current_loja_id", String(data.id));
  if (data.slug) sessionStorage.setItem("loja_slug", data.slug);
}
