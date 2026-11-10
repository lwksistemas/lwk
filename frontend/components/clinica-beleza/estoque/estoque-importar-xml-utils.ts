import type { AcaoImportacaoXml, ImportResult, ProdutoPreview } from "./estoque-importar-xml-types";
import { ESTOQUE_CATEGORIAS } from "./estoque-types";

export const ESTOQUE_IMPORT_CATEGORIAS = ESTOQUE_CATEGORIAS;

export const DEFAULT_ESTOQUE_IMPORT_CATEGORIA = "outro";

export function formatXmlFileSizeKb(sizeBytes: number): string {
  return `${(sizeBytes / 1024).toFixed(0)} KB`;
}

export function formatImportResultSummary(criados: number, atualizados: number, ignorados = 0): string {
  const parts: string[] = [];
  if (criados > 0) parts.push(`${criados} novo${criados !== 1 ? "s" : ""}`);
  if (atualizados > 0) {
    parts.push(`${atualizados} atualizado${atualizados !== 1 ? "s" : ""} (estoque somado)`);
  }
  if (ignorados > 0) parts.push(`${ignorados} ignorado${ignorados !== 1 ? "s" : ""}`);
  return parts.join(" · ") || "Nenhum item lançado";
}

export function custoUnitarioConvertido(p: ProdutoPreview): string {
  const preco = Number(p.preco_custo);
  const fator = Number(p.fator || "1");
  if (!Number.isFinite(preco) || !Number.isFinite(fator) || fator <= 0) return "0.00";
  return (Math.round((preco / fator) * 100) / 100).toFixed(2);
}

export function custoTotalConvertido(p: ProdutoPreview): string {
  const unitario = Number(custoUnitarioConvertido(p));
  const entra = Number(quantidadeEntrada(p));
  if (!Number.isFinite(unitario) || !Number.isFinite(entra)) return "0.00";
  return (Math.round(unitario * entra * 100) / 100).toFixed(2);
}

export function opcoesEntradaEstoque(p: ProdutoPreview): {
  id: "nota" | "conteudo";
  fator: string;
  unidade: string;
  rotulo: string;
}[] | null {
  const dentro = Number(p.embalagem_quantidade || "0");
  if (!Number.isFinite(dentro) || dentro <= 1) return null;
  const conteudo = p.embalagem_unidade || "unidade";
  const nota = p.unidade_medida || "un";
  const preco = Number(p.preco_custo || "0");
  const quantidade = Number(p.quantidade || "0");
  if (!Number.isFinite(preco) || !Number.isFinite(quantidade)) return null;
  const entra = Math.round(quantidade * dentro * 100) / 100;
  const unitario = Math.round((preco / dentro) * 100) / 100;
  return [
    {
      id: "nota",
      fator: "1",
      unidade: nota,
      rotulo: `Como na nota — ${quantidade} ${nota} a R$ ${preco.toFixed(2)}`,
    },
    {
      id: "conteudo",
      fator: String(dentro),
      unidade: conteudo,
      rotulo: `Por ${conteudo} — entra ${entra} · R$ ${unitario.toFixed(2)} cada`,
    },
  ];
}

export function quantidadeEntrada(p: ProdutoPreview): string {
  const q = Number(p.quantidade);
  const fator = Number(p.fator || "1");
  if (!Number.isFinite(q) || !Number.isFinite(fator) || fator <= 0) return p.quantidade;
  const entra = Math.round(q * fator * 100) / 100;
  return String(entra);
}

export function itemPrecisaConfirmacao(p: ProdutoPreview): boolean {
  if (p.acao !== "vincular" && p.acao !== "novo" && p.acao !== "ignorar") return true;
  if (p.acao === "vincular" && !p.produto_id) return true;
  if (p.exige_lote && p.acao !== "ignorar") {
    if (!(p.lote || "").trim() || !(p.validade || "").trim()) return true;
  }
  return false;
}

export function aplicarDecisaoAosIguais(produtos: ProdutoPreview[], indice: number): ProdutoPreview[] {
  const origem = produtos[indice];
  const grupo = origem?.grupo;
  if (!origem || !grupo) return produtos;
  return produtos.map((item, i) => {
    if (i === indice || item.grupo !== grupo) return item;
    return {
      ...item,
      acao: origem.acao,
      produto_id: origem.produto_id,
      produto_nome: origem.produto_nome,
      exige_lote: origem.exige_lote,
      candidatos: origem.candidatos,
    };
  });
}

export function resumoConferencia(produtos: ProdutoPreview[]) {
  let vinculados = 0;
  let novos = 0;
  let ignorados = 0;
  const pendentesNumeros: number[] = [];
  produtos.forEach((p, indice) => {
    if (itemPrecisaConfirmacao(p)) {
      pendentesNumeros.push(indice + 1);
      return;
    }
    if (p.acao === "vincular") vinculados += 1;
    else if (p.acao === "novo") novos += 1;
    else ignorados += 1;
  });
  return { vinculados, novos, ignorados, pendentes: pendentesNumeros.length, pendentesNumeros };
}

export function textoResumoConferencia(resumo: {
  vinculados: number;
  novos: number;
  ignorados: number;
  pendentes: number;
}): string {
  return [
    `${resumo.vinculados} vinculado${resumo.vinculados !== 1 ? "s" : ""}`,
    `${resumo.novos} novo${resumo.novos !== 1 ? "s" : ""}`,
    `${resumo.ignorados} ignorado${resumo.ignorados !== 1 ? "s" : ""}`,
  ].join(" · ");
}

/** "35, 45 e 98" na ordem da nota. */
export function juntarNumerosNota(numeros: number[]): string {
  if (numeros.length <= 1) return numeros.join("");
  if (numeros.length === 2) return `${numeros[0]} e ${numeros[1]}`;
  return `${numeros.slice(0, -1).join(", ")} e ${numeros[numeros.length - 1]}`;
}

export function textoItensPendentes(numeros: number[]): string {
  if (numeros.length === 0) return "";
  const lista = juntarNumerosNota(numeros);
  if (numeros.length === 1) return `Falta confirmar o item ${lista}.`;
  return `Falta confirmar os itens ${lista}.`;
}

export function produtoParaConfirmacao(p: ProdutoPreview) {
  return {
    nome: p.nome,
    categoria: p.categoria,
    categoria_id: p.categoria_id ?? undefined,
    acao: (p.acao || "") as AcaoImportacaoXml,
    produto_id: p.produto_id ?? undefined,
    fator: p.fator || "1",
    validade: p.validade || undefined,
    lote: p.lote || undefined,
  };
}

export function formatProdutoPreviewLine(p: ProdutoPreview): string {
  const preco = parseFloat(p.preco_custo || "0").toFixed(2);
  const lote = p.lote ? ` · Lote: ${p.lote}` : "";
  const cat = p.categoria ? ` · ${p.categoria}` : "";
  const motivo = p.categoria_motivo ? ` (${p.categoria_motivo})` : "";
  const fator = Number(p.fator || "1");
  const unidade = p.unidade_estoque || p.unidade_medida;
  const liquido = Number(p.valor_desconto || "0") > 0 || Number(p.valor_despesas || "0") > 0 ? " líquido" : "";
  const convertido = Number.isFinite(fator) && fator !== 1
    ? `${liquido} · entra ${quantidadeEntrada(p)} ${unidade} · custo R$ ${custoUnitarioConvertido(p)}/${unidade}`
    : liquido;
  return `${p.quantidade} ${p.unidade_medida} × R$ ${preco}${convertido}${lote}${cat}${motivo}`;
}

export function buildEstoqueImportFormData(
  arquivo: File,
  categoria: string,
  confirmar: boolean,
  opts?: {
    categoriaId?: number | null;
    produtos?: ProdutoPreview[];
  },
): FormData {
  const formData = new FormData();
  formData.append("arquivo", arquivo);
  formData.append("categoria", categoria);
  if (opts?.categoriaId) formData.append("categoria_id", String(opts.categoriaId));
  if (confirmar) {
    formData.append("confirmar", "true");
    if (opts?.produtos?.length) {
      formData.append(
        "produtos",
        JSON.stringify(
          opts.produtos.map((p) => produtoParaConfirmacao(p)),
        ),
      );
    }
  }
  return formData;
}

export function hasEstoqueImportChanges(resultado: ImportResult): boolean {
  return resultado.criados > 0 || resultado.atualizados > 0;
}

export function extractEstoqueImportError(data: unknown): string {
  if (
    data &&
    typeof data === "object" &&
    "error" in data &&
    typeof (data as { error?: unknown }).error === "string"
  ) {
    return (data as { error: string }).error;
  }
  return "Erro ao processar XML.";
}
