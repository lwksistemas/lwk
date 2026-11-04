import { describe, expect, it } from "vitest";
import { montarEntradasPdv, somaEntradasPdv } from "@/components/clinica-beleza/pdv/pdv-utils";

describe("montarEntradasPdv", () => {
  it("uma linha vazia recebe o total", () => {
    const entradas = montarEntradasPdv([{ forma: "PIX", valor: "" }], 100);
    expect(entradas).toEqual([{ payment_method: "PIX", valor: 100 }]);
    expect(somaEntradasPdv(entradas)).toBe(100);
  });

  it("divide o procedimento em pix, dinheiro e cartão", () => {
    const entradas = montarEntradasPdv(
      [
        { forma: "PIX", valor: "500" },
        { forma: "CASH", valor: "300,00" },
        { forma: "CREDIT_CARD", valor: "200" },
      ],
      1000,
    );
    expect(somaEntradasPdv(entradas)).toBe(1000);
    expect(entradas.map((item) => item.payment_method)).toEqual(["PIX", "CASH", "CREDIT_CARD"]);
  });

  it("soma parcial não fecha o total", () => {
    const entradas = montarEntradasPdv(
      [
        { forma: "PIX", valor: "500" },
        { forma: "CASH", valor: "" },
      ],
      1000,
    );
    expect(somaEntradasPdv(entradas)).toBe(500);
  });
});
