/** Formata CNPJ para exibição (14 dígitos → 00.000.000/0000-00) */
export function formatCnpjDisplay(value: string): string {
  const n = (value || '').replace(/\D/g, '');
  if (n.length <= 2) return n;
  if (n.length <= 5) return n.slice(0, 2) + '.' + n.slice(2);
  if (n.length <= 8) return n.slice(0, 2) + '.' + n.slice(2, 5) + '.' + n.slice(5);
  if (n.length <= 12) return n.slice(0, 2) + '.' + n.slice(2, 5) + '.' + n.slice(5, 8) + '/' + n.slice(8);
  return n.slice(0, 2) + '.' + n.slice(2, 5) + '.' + n.slice(5, 8) + '/' + n.slice(8, 12) + '-' + n.slice(12, 14);
}
