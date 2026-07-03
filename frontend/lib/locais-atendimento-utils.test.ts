import { describe, expect, it } from "vitest";
import {
  formatCurrencyBR,
  parseValorInput,
  valorToInput,
} from "@/components/clinica-beleza/consultas/locais-atendimento/locais-atendimento-utils";

describe("parseValorInput", () => {
  it("aceita decimal com vírgula BR", () => {
    expect(parseValorInput("1.234,56")).toBe(1234.56);
  });

  it("aceita decimal com ponto", () => {
    expect(parseValorInput("150.5")).toBe(150.5);
  });

  it("retorna NaN para vazio", () => {
    expect(parseValorInput("")).toBeNaN();
  });
});

describe("valorToInput", () => {
  it("converte número para string", () => {
    expect(valorToInput(120)).toBe("120");
  });

  it("retorna vazio para null", () => {
    expect(valorToInput(null)).toBe("");
  });
});

describe("formatCurrencyBR", () => {
  it("formata em BRL", () => {
    expect(formatCurrencyBR(100)).toMatch(/R\$\s?100,00/);
  });
});
