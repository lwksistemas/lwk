import { describe, expect, it } from "vitest";
import {
  buildEstoqueImportFormData,
  extractEstoqueImportError,
  formatImportResultSummary,
  formatProdutoPreviewLine,
  formatXmlFileSizeKb,
  hasEstoqueImportChanges,
  aplicarDecisaoAosIguais,
  custoTotalConvertido,
  custoUnitarioConvertido,
  itemPrecisaConfirmacao,
  quantidadeEntrada,
  juntarNumerosNota,
  resumoConferencia,
  textoItensPendentes,
  textoResumoConferencia,
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

describe("conferência da NF-e", () => {
  const base = {
    nome: "ACIDO",
    unidade_medida: "CX",
    quantidade: "2",
    preco_custo: "100",
    lote: "",
    validade: null,
  };

  it("converte caixa em unidades de estoque", () => {
    expect(quantidadeEntrada({ ...base, fator: "5" })).toBe("10");
    expect(formatProdutoPreviewLine({ ...base, fator: "5", unidade_estoque: "UN" })).toContain("entra 10 UN");
  });

  it("resume vinculados, novos e o que ainda precisa de confirmação", () => {
    const resumo = resumoConferencia([
      { ...base, acao: "vincular", produto_id: 1 },
      { ...base, acao: "novo" },
      { ...base, acao: "ignorar" },
      { ...base, acao: "" },
    ]);
    expect(resumo).toMatchObject({ vinculados: 1, novos: 1, ignorados: 1, pendentes: 1, pendentesNumeros: [4] });
    expect(textoResumoConferencia(resumo)).toBe("1 vinculado · 1 novo · 1 ignorado");
    expect(textoItensPendentes(resumo.pendentesNumeros)).toBe("Falta confirmar o item 4.");
    expect(juntarNumerosNota([35, 45, 98])).toBe("35, 45 e 98");
    expect(textoItensPendentes([35, 45, 98])).toBe("Falta confirmar os itens 35, 45 e 98.");
    expect(itemPrecisaConfirmacao({ ...base, acao: "vincular" })).toBe(true);
  });

  it("mostra o custo do frasco e aplica a decisão só nas linhas idênticas", () => {
    expect(custoUnitarioConvertido({ ...base, preco_custo: "262", fator: "5" })).toBe("52.40");
    expect(custoTotalConvertido({ ...base, preco_custo: "262", fator: "5" })).toBe("524.00");
    const produtos = [
      { ...base, nome: "AGULHA", grupo: "nome:AGULHA", acao: "vincular" as const, produto_id: 9, produto_nome: "Agulha", lote: "A", validade: "2027-01-01" },
      { ...base, nome: "AGULHA", grupo: "nome:AGULHA", acao: "" as const, lote: "B", validade: "2028-01-01" },
      { ...base, nome: "OUTRO", grupo: "nome:OUTRO", acao: "" as const, lote: "C" },
    ];
    const aplicados = aplicarDecisaoAosIguais(produtos, 0);
    expect(aplicados[1].acao).toBe("vincular");
    expect(aplicados[1].produto_id).toBe(9);
    expect(aplicados[1].lote).toBe("B");
    expect(aplicados[1].validade).toBe("2028-01-01");
    expect(aplicados[2].acao).toBe("");
    expect(itemPrecisaConfirmacao({ ...base, acao: "vincular", produto_id: 1, exige_lote: true })).toBe(true);
  });
});

describe("extractEstoqueImportError", () => {
  it("extrai mensagem da API", () => {
    expect(extractEstoqueImportError({ error: "XML inválido" })).toBe("XML inválido");
    expect(extractEstoqueImportError({})).toBe("Erro ao processar XML.");
  });
});
