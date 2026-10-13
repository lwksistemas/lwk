/** Junta o que já estava escrito com a fala reconhecida, sem duplicar o trecho parcial. */
export function juntarTextoFalado(base: string, finais: string, parcial: string): string {
  const falado = `${finais} ${parcial}`.replace(/\s+/g, " ").trim();
  if (!falado) return base;
  const inicio = base.replace(/\s+$/, "");
  if (!inicio) return falado;
  return `${inicio} ${falado}`;
}
