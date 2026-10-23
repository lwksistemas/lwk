export interface CategoriaComissao {
  id: number;
  nome: string;
  pai?: number | null;
  ordem?: number;
}

/** Categorias de topo que têm serviço nesta prestadora. Subpastas não entram na lista. */
export function categoriasParaComissao<T extends CategoriaComissao>(
  categorias: T[],
  servicos: Array<{ categoria: number | null }>,
): T[] {
  const porId = new Map(categorias.map((categoria) => [categoria.id, categoria]));
  const raizes = new Set<number>();
  for (const servico of servicos) {
    if (servico.categoria == null) continue;
    const raiz = raizDaCategoria(porId, servico.categoria);
    if (raiz != null) raizes.add(raiz);
  }
  return categorias
    .filter((categoria) => raizes.has(categoria.id))
    .sort(
      (a, b) =>
        (a.ordem ?? 0) - (b.ordem ?? 0) || a.nome.localeCompare(b.nome, 'pt-BR'),
    );
}

/** A categoria escolhida e todas as subpastas dela. */
export function idsNaCategoria(
  categorias: Array<{ id: number; pai?: number | null }>,
  categoriaId: number,
): Set<number> {
  const filhos = new Map<number, number[]>();
  for (const categoria of categorias) {
    if (categoria.pai == null) continue;
    const lista = filhos.get(categoria.pai) ?? [];
    lista.push(categoria.id);
    filhos.set(categoria.pai, lista);
  }
  const ids = new Set<number>();
  const pilha = [categoriaId];
  while (pilha.length > 0) {
    const id = pilha.pop();
    if (id == null || ids.has(id)) continue;
    ids.add(id);
    for (const filho of filhos.get(id) ?? []) pilha.push(filho);
  }
  return ids;
}

function raizDaCategoria(
  porId: Map<number, CategoriaComissao>,
  categoriaId: number,
): number | null {
  let atual = porId.get(categoriaId);
  const vistos = new Set<number>();
  while (atual && !vistos.has(atual.id)) {
    vistos.add(atual.id);
    if (atual.pai == null) return atual.id;
    atual = porId.get(atual.pai);
  }
  return null;
}
