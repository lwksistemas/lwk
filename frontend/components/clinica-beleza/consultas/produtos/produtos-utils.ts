import type { ConsultaProdutoItem, ProdutoEstoque } from "./produtos-types";

export function totalPorProduto(itens: ConsultaProdutoItem[]): Map<number, number> {
  const map = new Map<number, number>();
  for (const item of itens) {
    if (item.estoque_baixado) continue;
    map.set(item.produto, (map.get(item.produto) || 0) + Number(item.quantidade));
  }
  return map;
}

export function mensagemEstoqueInsuficiente(
  nome: string,
  necessario: number,
  disponivel: number,
  unidade: string,
): string {
  return `${nome}: necessário ${necessario} ${unidade}, disponível ${disponivel} ${unidade}.`;
}

export function listarAvisosEstoqueInsuficiente(
  itens: ConsultaProdutoItem[],
  produtos: ProdutoEstoque[],
  totaisConsulta: Map<number, number>,
): string[] {
  const avisos: string[] = [];
  for (const [produtoIdKey, total] of totaisConsulta) {
    const produto = produtos.find((p) => p.id === produtoIdKey);
    const disponivel = produto
      ? Number(produto.quantidade_atual)
      : Number(itens.find((i) => i.produto === produtoIdKey)?.quantidade_disponivel ?? 0);
    const nome =
      produto?.nome || itens.find((i) => i.produto === produtoIdKey)?.produto_nome || "Produto";
    const unidade =
      produto?.unidade_medida || itens.find((i) => i.produto === produtoIdKey)?.unidade_medida || "un";
    if (total > disponivel) {
      avisos.push(mensagemEstoqueInsuficiente(nome, total, disponivel, unidade));
    }
  }
  return avisos;
}

export function extractProdutosError(err: unknown, fallback: string): string {
  if (err && typeof err === "object" && "error" in err) {
    return String((err as { error: string }).error);
  }
  if (err && typeof err === "object" && "detail" in err) {
    return String((err as { detail: string }).detail);
  }
  return fallback;
}

export function avisoFormularioEstoque(
  produto: ProdutoEstoque | undefined,
  qtdInformada: number,
  qtdJaRegistrada: number,
): string {
  if (!produto || qtdInformada <= 0) return "";
  const disponivel = Number(produto.quantidade_atual);
  const unidade = produto.unidade_medida || "un";
  if (qtdJaRegistrada + qtdInformada > disponivel) {
    return mensagemEstoqueInsuficiente(
      produto.nome,
      qtdJaRegistrada + qtdInformada,
      disponivel,
      unidade,
    );
  }
  return "";
}
