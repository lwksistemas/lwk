export function cepSomenteDigitos(cep: string): string {
  return cep.replace(/\D/g, "");
}

export function isCepCompleto(cep: string): boolean {
  return cepSomenteDigitos(cep).length === 8;
}
