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
  "telefone_contato",
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

/** Valida CPF pelos dígitos verificadores (11 dígitos). */
export function cpfValido(valor?: string | null): boolean {
  const cpf = apenasDigitos(valor);
  if (cpf.length !== 11) return false;
  if (/^(\d)\1{10}$/.test(cpf)) return false;

  const calc = (base: string): number => {
    let total = 0;
    for (let i = 0; i < base.length; i++) {
      total += Number(base[i]) * (base.length + 1 - i);
    }
    const resto = total % 11;
    return resto < 2 ? 0 : 11 - resto;
  };

  if (calc(cpf.slice(0, 9)) !== Number(cpf[9])) return false;
  if (calc(cpf.slice(0, 10)) !== Number(cpf[10])) return false;
  return true;
}

/** Valida CNPJ pelos dígitos verificadores (14 dígitos). */
export function cnpjValido(valor?: string | null): boolean {
  const cnpj = apenasDigitos(valor);
  if (cnpj.length !== 14) return false;
  if (/^(\d)\1{13}$/.test(cnpj)) return false;

  const calc = (base: string, weights: number[]): number => {
    let total = 0;
    for (let i = 0; i < weights.length; i++) {
      total += Number(base[i]) * weights[i];
    }
    const resto = total % 11;
    return resto < 2 ? 0 : 11 - resto;
  };

  const w1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2];
  const w2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2];
  if (calc(cnpj.slice(0, 12), w1) !== Number(cnpj[12])) return false;
  if (calc(cnpj.slice(0, 13), w2) !== Number(cnpj[13])) return false;
  return true;
}

/** True se for CPF (11) ou CNPJ (14) com dígitos verificadores válidos. */
export function cpfCnpjValido(valor?: string | null): boolean {
  const d = apenasDigitos(valor);
  if (d.length === 11) return cpfValido(d);
  if (d.length === 14) return cnpjValido(d);
  return false;
}

/** Mensagem amigável para CPF/CNPJ inválido (vazio se ok). */
export function mensagemCpfCnpjInvalido(valor?: string | null): string | null {
  const d = apenasDigitos(valor);
  if (!d) return "Informe o CPF ou CNPJ.";
  if (d.length < 11) return "CPF incompleto. Digite os 11 dígitos.";
  if (d.length > 11 && d.length < 14) return "CNPJ incompleto. Digite os 14 dígitos.";
  if (d.length === 11 && !cpfValido(d)) return "CPF inválido. Verifique os números digitados.";
  if (d.length === 14 && !cnpjValido(d)) return "CNPJ inválido. Verifique os números digitados.";
  if (d.length !== 11 && d.length !== 14) return "Informe um CPF (11 dígitos) ou CNPJ (14 dígitos) válido.";
  return null;
}

/**
 * Converte texto para MAIÚSCULAS (usado em campos de cadastro como nome, empresa, cidade).
 * Retorna string vazia se valor for nulo/undefined.
 */
export function toUpperCase(valor?: string | null): string {
  return (valor || "").toUpperCase();
}
