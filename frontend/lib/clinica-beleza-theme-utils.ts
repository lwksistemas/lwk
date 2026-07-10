/** Utilitários de cor para tema da Clínica da Beleza. */

const HEX6 = /^#[0-9A-Fa-f]{6}$/;
const HEX3 = /^#[0-9A-Fa-f]{3}$/;

/** Fallback estático (fora do ThemeProvider / charts que precisam de hex). */
export const CB_PRIMARY_FALLBACK = '#8b3d52';

/**
 * Use em style={{ backgroundColor / color }} — resolve a cor da loja
 * quando ClinicaBelezaThemeProvider está montado.
 */
export const CB_PRIMARY_CSS = `var(--cb-primary, ${CB_PRIMARY_FALLBACK})`;
export const CB_PRIMARY_LIGHT_CSS = 'var(--cb-primary-light, #f5e6ea)';

/** Mistura a cor primária do tema com transparente (ex.: fundos suaves). */
export function cbPrimaryAlpha(percent: number): string {
  const p = Math.max(0, Math.min(100, Math.round(percent)));
  return `color-mix(in srgb, ${CB_PRIMARY_CSS} ${p}%, transparent)`;
}

export function normalizeHexColor(value?: string | null): string | null {
  if (!value) return null;
  const v = value.trim();
  if (HEX6.test(v)) return v.toLowerCase();
  if (HEX3.test(v)) {
    return `#${v[1]}${v[1]}${v[2]}${v[2]}${v[3]}${v[3]}`.toLowerCase();
  }
  return null;
}

/** Mistura hex com branco (amount 0–1; quanto maior, mais claro). */
export function lightenHex(hex: string, amount = 0.9): string | null {
  const n = normalizeHexColor(hex);
  if (!n) return null;
  const r = parseInt(n.slice(1, 3), 16);
  const g = parseInt(n.slice(3, 5), 16);
  const b = parseInt(n.slice(5, 7), 16);
  const mix = (c: number) => Math.round(c + (255 - c) * amount);
  const toHex = (c: number) => mix(c).toString(16).padStart(2, '0');
  return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
}
