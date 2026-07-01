/**
 * Formatadores brasileiros reutilizáveis (telefone, CPF/CNPJ, CEP e texto).
 * Usados para padronizar a exibição e as máscaras de digitação.
 */

export { formatCpfCnpj } from '@/lib/consulta-cnpj';

/** Mantém apenas os dígitos de uma string. */
export function apenasDigitos(valor?: string | null): string {
  return (valor || "").replace(/\D/g, "");
}

/** Remove código do país 55 para máscara local (ex.: 5516999621823 → 16999621823). */
export function telefoneLocalBr(valor?: string | null): string {
  let d = apenasDigitos(valor);
  if (d.startsWith("55") && d.length >= 12) {
    d = d.slice(2);
  }
  return d;
}

/**
 * Formata telefone brasileiro de forma progressiva (máscara de digitação):
 * - Celular: (XX) XXXXX-XXXX (11 dígitos)
 * - Fixo:    (XX) XXXX-XXXX  (10 dígitos)
 * Aceita valor já salvo com 55 (ex.: 5516999621823).
 */
export function formatTelefone(valor?: string | null): string {
  const d = telefoneLocalBr(valor).slice(0, 11);
  if (d.length === 0) return "";
  if (d.length <= 2) return `(${d}`;
  if (d.length <= 6) return `(${d.slice(0, 2)}) ${d.slice(2)}`;
  if (d.length <= 10) return `(${d.slice(0, 2)}) ${d.slice(2, 6)}-${d.slice(6)}`;
  return `(${d.slice(0, 2)}) ${d.slice(2, 7)}-${d.slice(7)}`;
}

/** Salva telefone BR com código do país 55 (WhatsApp). Ex.: (16) 99962-1823 → 5516999621823 */
export function telefoneInternacionalBr(valor?: string | null): string {
  const d = apenasDigitos(valor);
  if (!d) return "";
  if (d.startsWith("55") && d.length >= 12) return d.slice(0, 15);
  if (d.length === 11 && !d.startsWith("1")) return `55${d}`;
  if (d.length === 11) {
    const ddd = parseInt(d.slice(0, 2), 10);
    if (ddd >= 11 && ddd <= 99 && d[2] === "9") return `55${d}`;
  }
  if (d.length === 10) return `55${d}`;
  return d.slice(0, 15);
}

/** Nomes de campos de telefone usados nos cadastros LWK. */
export const TELEFONE_FIELD_NAMES = [
  "telefone",
  "phone",
  "celular",
  "whatsapp",
  "owner_telefone",
  "whatsapp_numero",
  "telefone_whatsapp",
  "telefone_comercial",
  "telefone_residencial",
] as const;

export function isTelefoneField(name: string): boolean {
  return (TELEFONE_FIELD_NAMES as readonly string[]).includes(name);
}

/** Converte campos de telefone para 55... antes de enviar à API. */
export function applyTelefoneInternacionalPayload<T extends object>(
  data: T,
  fields: readonly string[] = TELEFONE_FIELD_NAMES,
): T {
  const out = { ...data } as Record<string, unknown>;
  for (const field of fields) {
    const val = out[field];
    if (typeof val === "string" && val.trim()) {
      out[field] = telefoneInternacionalBr(val);
    }
  }
  return out as T;
}

/** Formata campos de telefone para exibição no formulário (DD) XXXXX-XXXX. */
export function applyTelefoneFormatPayload<T extends object>(
  data: T,
  fields: readonly string[] = TELEFONE_FIELD_NAMES,
): T {
  const out = { ...data } as Record<string, unknown>;
  for (const field of fields) {
    const val = out[field];
    if (typeof val === "string" && val.trim()) {
      out[field] = formatTelefone(val);
    }
  }
  return out as T;
}

/** Formata CPF no padrão XXX.XXX.XXX-XX (progressivo, até 11 dígitos). */
export function formatCpf(valor?: string | null): string {
  const d = apenasDigitos(valor).slice(0, 11);
  if (d.length <= 3) return d;
  if (d.length <= 6) return `${d.slice(0, 3)}.${d.slice(3)}`;
  if (d.length <= 9) return `${d.slice(0, 3)}.${d.slice(3, 6)}.${d.slice(6)}`;
  return `${d.slice(0, 3)}.${d.slice(3, 6)}.${d.slice(6, 9)}-${d.slice(9)}`;
}

/** Formata CEP no padrão XXXXX-XXX (progressivo, até 8 dígitos). */
export function formatCep(valor?: string | null): string {
  const d = apenasDigitos(valor).slice(0, 8);
  if (d.length <= 5) return d;
  return `${d.slice(0, 5)}-${d.slice(5)}`;
}

/** Normaliza CEP para 8 dígitos (completa zeros à esquerda quando a API omite). */
export function normalizeCepDigits(valor?: string | null): string {
  let d = apenasDigitos(valor);
  if (!d) return '';
  if (d.length < 8) d = d.padStart(8, '0');
  return d.slice(0, 8);
}

export function cepDigitosValidos(valor?: string | null): boolean {
  return apenasDigitos(valor).length === 8;
}

/**
 * Converte texto para MAIÚSCULAS (usado em campos de cadastro como nome, empresa, cidade).
 * Retorna string vazia se valor for nulo/undefined.
 */
export function toUpperCase(valor?: string | null): string {
  return (valor || "").toUpperCase();
}
