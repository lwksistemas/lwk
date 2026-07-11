/** Persistência local do tema da clínica entre layouts (Dashboard ↔ Configurações). */

export type StoredClinicaTheme = {
  corPrimaria?: string | null;
  corSecundaria?: string | null;
  corFundoPagina?: string | null;
  updatedAt: number;
};

export function clinicaThemeStorageKey(slug: string): string {
  return `lwk:cb-theme:${slug.trim().toLowerCase()}`;
}

/** Slug da loja atual (URL ou session). */
export function resolveClinicaThemeSlug(explicit?: string | null): string | null {
  if (explicit?.trim()) return explicit.trim();
  if (typeof window === 'undefined') return null;
  const m = window.location.pathname.match(/^\/loja\/([^/]+)/);
  if (m?.[1]) {
    try {
      return decodeURIComponent(m[1]);
    } catch {
      return m[1];
    }
  }
  const fromSession = sessionStorage.getItem('loja_slug');
  return fromSession?.trim() || null;
}

function collectSlugAliases(primary?: string | null): string[] {
  const keys = new Set<string>();
  const add = (s: string | null | undefined) => {
    const v = (s || '').trim();
    if (v) keys.add(v.toLowerCase());
  };
  add(primary);
  if (typeof window !== 'undefined') {
    add(sessionStorage.getItem('loja_slug'));
    const m = window.location.pathname.match(/^\/loja\/([^/]+)/);
    if (m?.[1]) {
      try {
        add(decodeURIComponent(m[1]));
      } catch {
        add(m[1]);
      }
    }
  }
  return [...keys];
}

export function readClinicaThemeStorage(slug: string | null | undefined): StoredClinicaTheme | null {
  if (typeof window === 'undefined') return null;
  let best: StoredClinicaTheme | null = null;
  for (const alias of collectSlugAliases(slug)) {
    try {
      const raw = sessionStorage.getItem(clinicaThemeStorageKey(alias));
      if (!raw) continue;
      const parsed = JSON.parse(raw) as StoredClinicaTheme;
      if (!parsed || typeof parsed !== 'object') continue;
      if (!best || (parsed.updatedAt || 0) > (best.updatedAt || 0)) {
        best = parsed;
      }
    } catch {
      /* ignore */
    }
  }
  return best;
}

export function writeClinicaThemeStorage(
  slug: string | null | undefined,
  colors: Omit<StoredClinicaTheme, 'updatedAt'>,
): void {
  if (typeof window === 'undefined') return;
  const payload: StoredClinicaTheme = { ...colors, updatedAt: Date.now() };
  const raw = JSON.stringify(payload);
  for (const alias of collectSlugAliases(slug)) {
    try {
      sessionStorage.setItem(clinicaThemeStorageKey(alias), raw);
    } catch {
      /* quota / private mode */
    }
  }
}

export function clearClinicaThemeStorage(slug: string | null | undefined): void {
  if (typeof window === 'undefined') return;
  for (const alias of collectSlugAliases(slug)) {
    try {
      sessionStorage.removeItem(clinicaThemeStorageKey(alias));
    } catch {
      /* ignore */
    }
  }
}
