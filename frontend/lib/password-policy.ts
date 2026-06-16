/**
 * Política de senha — alinhado com backend/core/password_validation.py
 *
 * Requisitos:
 * - Mínimo 6 caracteres
 * - Pelo menos uma letra (maiúscula ou minúscula)
 * - Pelo menos um número
 * - Pelo menos um caractere especial (!@#$%^&* etc.)
 */
export const PASSWORD_MIN_LENGTH = 6;

export interface PasswordRule {
  id: string;
  texto: string;
  check: (password: string) => boolean;
}

export const PASSWORD_RULES: PasswordRule[] = [
  { id: 'min_length', texto: `No mínimo ${PASSWORD_MIN_LENGTH} caracteres`, check: (p) => p.length >= PASSWORD_MIN_LENGTH },
  { id: 'letter', texto: 'Pelo menos uma letra (A-Z ou a-z)', check: (p) => /[A-Za-z]/.test(p) },
  { id: 'number', texto: 'Pelo menos um número (0-9)', check: (p) => /\d/.test(p) },
  { id: 'special_char', texto: 'Pelo menos um caractere especial (ex: !@#$%)', check: (p) => /[!@#$%^&*()\-_=+\[\]{}|;:'",.<>/?\\`~]/.test(p) },
];

/**
 * Valida senha conforme política.
 * Retorna mensagem de erro ou null se OK.
 */
export function validatePasswordPolicy(password: string): string | null {
  if (!password || password.length < PASSWORD_MIN_LENGTH) {
    return `A senha deve ter no mínimo ${PASSWORD_MIN_LENGTH} caracteres.`;
  }
  if (!/[A-Za-z]/.test(password)) {
    return 'A senha deve conter pelo menos uma letra.';
  }
  if (!/\d/.test(password)) {
    return 'A senha deve conter pelo menos um número.';
  }
  if (!/[!@#$%^&*()\-_=+\[\]{}|;:'",.<>/?\\`~]/.test(password)) {
    return 'A senha deve conter pelo menos um caractere especial (ex: !@#$%).';
  }
  return null;
}

/**
 * Retorna o estado de cada regra para feedback em tempo real.
 */
export function checkPasswordRules(password: string): { rule: PasswordRule; passed: boolean }[] {
  return PASSWORD_RULES.map((rule) => ({
    rule,
    passed: password ? rule.check(password) : false,
  }));
}
