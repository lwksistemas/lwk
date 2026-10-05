/** Converte o campo de comissão para a API. Vazio grava ausência de comissão. */
export function valorComissaoParaApi(valor: string | number | null | undefined): number | null {
  if (valor === null || valor === undefined) return null;
  const texto = String(valor).trim();
  if (!texto) return null;
  const numero = Number(texto.replace(',', '.'));
  if (!Number.isFinite(numero)) return null;
  return numero;
}
