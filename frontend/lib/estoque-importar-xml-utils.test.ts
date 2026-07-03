import { describe, expect, it } from "vitest";
import {
  buildEstoqueImportFormData,
  extractEstoqueImportError,
  formatImportResultSummary,
  formatProdutoPreviewLine,
  formatXmlFileSizeKb,
  hasEstoqueImportChanges,
} from "@/components/clinica-beleza/estoque/estoque-importar-xml-utils";

describe("formatXmlFileSizeKb", () => {
  it("converte bytes para KB", () => {
    expect(formatXmlFileSizeKb(2048)).toBe("2 KB");
  });
});

describe("formatImportResultSummary", () => {
  it("resume criados e atualizados", () => {
    expect(formatImportResultSummary(2, 1)).toBe("2 novos · 1 atualizado (estoque somado)");
    expect(formatImportResultSummary(1, 0)).toBe("1 novo");
  });
});

describe("formatProdutoPreviewLine", () => {
  it("monta linha com lote opcional", () => {
    const line = formatProdutoPreviewLine({
      nome: "Prod",
      unidade_medida: "UN",
      quantidade: "10",
      preco_custo: "15.5",
      lote: "A1",
      validade: null,
    });
    expect(line).toContain("10 UN");
    expect(line).toContain("Lote: A1");
  });
});

describe("buildEstoqueImportFormData", () => {
  it("inclui confirmar quando solicitado", () => {
    const file = { name: "nota.xml" } as File;
    const form = buildEstoqueImportFormData(file, "outro", true);
    expect(form.get("confirmar")).toBe("true");
    expect(form.get("categoria")).toBe("outro");
  });
});

describe("hasEstoqueImportChanges", () => {
  it("detecta alterações", () => {
    expect(hasEstoqueImportChanges({ criados: 0, atualizados: 0, erros: [], nota: { numero: "", fornecedor: "", data_emissao: "" } })).toBe(false);
    expect(hasEstoqueImportChanges({ criados: 1, atualizados: 0, erros: [], nota: { numero: "", fornecedor: "", data_emissao: "" } })).toBe(true);
  });
});

describe("extractEstoqueImportError", () => {
  it("extrai mensagem da API", () => {
    expect(extractEstoqueImportError({ error: "XML inválido" })).toBe("XML inválido");
    expect(extractEstoqueImportError({})).toBe("Erro ao processar XML.");
  });
});
