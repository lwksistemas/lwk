/**
 * Helpers offline compartilhados — Clínica da Beleza (pacientes, profissionais, procedimentos).
 */

export function isBrowserOffline(): boolean {
  return typeof navigator !== 'undefined' && !navigator.onLine;
}

export function isFetchNetworkError(message: string): boolean {
  const lower = message.toLowerCase();
  return lower.includes('fetch') || message === 'Failed to fetch';
}

export function isRegistroPendenteSync(id: number): boolean {
  return id < 0;
}

/** Verificar duplicata ao criar ou ao editar registro ainda não sincronizado (id negativo). */
export function deveVerificarDuplicataOffline(editing: { id: number } | null | undefined): boolean {
  if (!editing) return true;
  return isRegistroPendenteSync(editing.id);
}

export function temDuplicataNaLista<T>(list: T[], predicate: (item: T) => boolean): boolean {
  return list.some(predicate);
}

/**
 * Fallback quando a API falha por rede ao criar: bloqueia só criação com item já na lista local.
 */
export function bloquearCriacaoDuplicadaOffline<T>(
  editing: { id: number } | null | undefined,
  list: T[],
  predicateNovo: (item: T) => boolean,
): boolean {
  if (editing) return false;
  return temDuplicataNaLista(list, predicateNovo);
}

export function gerarIdTemporarioOffline(): number {
  return -Date.now();
}
