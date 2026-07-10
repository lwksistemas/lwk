import type { ImportResult, ProdutoPreview } from "./estoque-importar-xml-types";
import { ESTOQUE_CATEGORIAS } from "./estoque-types";

export const ESTOQUE_IMPORT_CATEGORIAS = ESTOQUE_CATEGORIAS;

export const DEFAULT_ESTOQUE_IMPORT_CATEGORIA = "outro";

export function formatXmlFileSizeKb(sizeBytes: number): string {
  return `${(sizeBytes / 1024).toFixed(0)} KB`;
}

export function formatImportResultSummary(criados: number, atualizados: number): string {
  const parts: string[] = [];
  if (criados > 0) parts.push(`${criados} novo${criados !== 1 ? "s" : ""}`);
  if (atualizados > 0) {
    parts.push(`${atualizados} atualizado${atualizados !== 1 ? "s" : ""} (estoque somado)`);
  }
  return parts.join(" · ");
}

export function formatProdutoPreviewLine(p: ProdutoPreview): string {
  const preco = parseFloat(p.preco_custo || "0").toFixed(2);
  const lote = p.lote ? ` · Lote: ${p.lote}` : "";
  const cat = p.categoria ? ` · ${p.categoria}` : "";
  const motivo = p.categoria_motivo ? ` (${p.categoria_motivo})` : "";
  return `${p.quantidade} ${p.unidade_medida} × R$ ${preco}${lote}${cat}${motivo}`;
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
          opts.produtos.map((p) => ({
            nome: p.nome,
            categoria: p.categoria,
            // slug é a fonte da verdade; ID só como dica (backend re-resolve)
            categoria_id: p.categoria_id ?? undefined,
          })),
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
