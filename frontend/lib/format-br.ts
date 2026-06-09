/**
 * Formatadores brasileiros reutilizáveis (telefone, CPF e texto).
 * Usados para padronizar a exibição e as máscaras de digitação.
 */

/** Mantém apenas os dígitos de uma string. */
export function apenasDigitos(valor?: string | null): string {
  return (valor || "").replace(/\D/g, "");
}

/**
 * Formata telefone brasileiro de forma progressiva (máscara de digitação):
 * - Celular: (XX) XXXXX-XXXX (11 dígitos)
 * - Fixo:    (XX) XXXX-XXXX  (10 dígitos)
 */
export function formatTelefone(valor?: string | null): string {
  const d = apenasDigitos(valor).slice(0, 11);
  if (d.length === 0) return "";
  if (d.length <= 2) return `(${d}`;
  if (d.length <= 6) return `(${d.slice(0, 2)}) ${d.slice(2)}`;
  if (d.length <= 10) return `(${d.slice(0, 2)}) ${d.slice(2, 6)}-${d.slice(6)}`;
  return `(${d.slice(0, 2)}) ${d.slice(2, 7)}-${d.slice(7)}`;
}

/** Formata CPF no padrão XXX.XXX.XXX-XX (progressivo, até 11 dígitos). */
export function formatCpf(valor?: string | null): string {
  const d = apenasDigitos(valor).slice(0, 11);
  if (d.length <= 3) return d;
  if (d.length <= 6) return `${d.slice(0, 3)}.${d.slice(3)}`;
  if (d.length <= 9) return `${d.slice(0, 3)}.${d.slice(3, 6)}.${d.slice(6)}`;
  return `${d.slice(0, 3)}.${d.slice(3, 6)}.${d.slice(6, 9)}-${d.slice(9)}`;
}

/**
 * Converte texto para MAIÚSCULAS (usado em campos de cadastro como nome, empresa, cidade).
 * Retorna string vazia se valor for nulo/undefined.
 */
export function toUpperCase(valor?: string | null): string {
  return (valor || "").toUpperCase();
}
