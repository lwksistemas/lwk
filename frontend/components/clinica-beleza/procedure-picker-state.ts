export type ProcedurePickerFilterState = {
  categoriaAtiva: string;
  busca: string;
  listaAberta: boolean;
};

/** Quantos chips cabem inteiros na largura (sem corte). */
export function quantosChipsCabem(
  larguraDisponivel: number,
  largurasChips: number[],
  gap = 6,
): number {
  if (larguraDisponivel <= 0 || largurasChips.length === 0) return 0;
  let used = 0;
  let count = 0;
  for (const w of largurasChips) {
    const next = count === 0 ? w : used + gap + w;
    if (next > larguraDisponivel + 0.5) break;
    used = next;
    count += 1;
  }
  return count;
}

/**
 * Quantos chips exibir na linha, reservando espaço para "+ Categorias"
 * quando nem todos cabem.
 */
export function quantosChipsVisiveisComMais(
  larguraTotal: number,
  largurasChips: number[],
  larguraMaisCategorias: number,
  gap = 6,
): number {
  if (larguraTotal <= 0 || largurasChips.length === 0) return 1;
  // Medição inválida (larguras zeradas) — mostra poucas chips e força "+ Categorias".
  if (largurasChips.every((w) => w <= 0)) {
    return Math.min(4, largurasChips.length);
  }
  const cabemTodos = quantosChipsCabem(larguraTotal, largurasChips, gap);
  if (cabemTodos >= largurasChips.length) return largurasChips.length;
  const reservado = Math.max(0, larguraTotal - larguraMaisCategorias - gap);
  return Math.max(1, quantosChipsCabem(reservado, largurasChips, gap));
}

/** Altura máxima da lista de selecionados: até 4 cards (~52px) + gaps. */
export const MAX_ALTURA_SELECIONADOS_PX = 4 * 52 + 3 * 6;

export function mostrarListaDisponiveis(state: ProcedurePickerFilterState): boolean {
  return state.listaAberta || Boolean(state.busca.trim());
}

/** Após adicionar um procedimento: fecha a lista, limpa busca e desmarca categoria. */
export function estadoAposAdicionarProcedimento(): ProcedurePickerFilterState {
  return { categoriaAtiva: "", busca: "", listaAberta: false };
}

/** Fecha a lista sem alterar a seleção de procedimentos. */
export function estadoFecharListaDisponiveis(
  state: ProcedurePickerFilterState,
): ProcedurePickerFilterState {
  return { ...state, categoriaAtiva: "", busca: "", listaAberta: false };
}

/**
 * Clique em "Todas" ou numa categoria.
 * - Abre a lista com o filtro clicado.
 * - Clicar de novo na mesma opção ativa fecha a lista.
 */
export function estadoToggleCategoria(
  state: ProcedurePickerFilterState,
  categoriaClicada: string,
): ProcedurePickerFilterState {
  const mesmaAberta =
    state.listaAberta && state.categoriaAtiva === categoriaClicada && !state.busca.trim();
  if (mesmaAberta) {
    return { ...state, categoriaAtiva: "", listaAberta: false };
  }
  return { ...state, categoriaAtiva: categoriaClicada, listaAberta: true };
}
