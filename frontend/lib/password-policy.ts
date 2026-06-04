/** Alinhado com backend/core/password_validation.py */
export const PASSWORD_MIN_LENGTH = 8;

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
  return null;
}
