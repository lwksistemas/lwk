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

export function quantidadeEntrada(p: ProdutoPreview): string {
  const q = Number(p.quantidade);
  const fator = Number(p.fator || "1");
  if (!Number.isFinite(q) || !Number.isFinite(fator) || fator <= 0) return p.quantidade;
  const entra = Math.round(q * fator * 100) / 100;
  return String(entra);
}

export function itemPrecisaConfirmacao(p: ProdutoPreview): boolean {
  if (p.acao !== "vincular" && p.acao !== "novo" && p.acao !== "ignorar") return true;
  return p.acao === "vincular" && !p.produto_id;
}

export function resumoConferencia(produtos: ProdutoPreview[]) {
  let vinculados = 0;
  let novos = 0;
  let ignorados = 0;
  let pendentes = 0;
  for (const p of produtos) {
    if (itemPrecisaConfirmacao(p)) {
      pendentes += 1;
      continue;
    }
    if (p.acao === "vincular") vinculados += 1;
    else if (p.acao === "novo") novos += 1;
    else ignorados += 1;
  }
  return { vinculados, novos, ignorados, pendentes };
}

export function textoResumoConferencia(resumo: {
  vinculados: number;
  novos: number;
  ignorados: number;
  pendentes: number;
}): string {
  const partes = [
    `${resumo.vinculados} vinculado${resumo.vinculados !== 1 ? "s" : ""}`,
    `${resumo.novos} novo${resumo.novos !== 1 ? "s" : ""}`,
    `${resumo.ignorados} ignorado${resumo.ignorados !== 1 ? "s" : ""}`,
  ];
  if (resumo.pendentes > 0) {
    partes.push(`${resumo.pendentes} para confirmar`);
  }
  return partes.join(" · ");
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
  const convertido = Number.isFinite(fator) && fator !== 1
    ? ` · entra ${quantidadeEntrada(p)} ${p.unidade_estoque || p.unidade_medida}`
    : "";
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
