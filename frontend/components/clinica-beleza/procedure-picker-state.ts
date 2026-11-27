export type ProcedurePickerFilterState = {
  categoriaAtiva: string;
  busca: string;
  listaAberta: boolean;
};

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
