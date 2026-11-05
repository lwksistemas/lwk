import { describe, expect, it } from "vitest";
import { clientePresente, consultaQuitadaNoPdv, montarEntradasPdv, paymentIdReciboPdv, pdvPodeReceberAtendimento, reciboPdvDisponivel, rotuloStatusPdv, seloCaixaPdv, somaEntradasPdv } from "@/components/clinica-beleza/pdv/pdv-utils";

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

  it("mostra Pago só quando o valor devido foi recebido", () => {
    expect(consultaQuitadaNoPdv({ valor_pago: 100, valor_restante: 0 })).toBe(true);
    expect(seloCaixaPdv({ valor_pago: 100, valor_restante: 0, payment_method: "PIX" })).toBe("pago");
    expect(rotuloStatusPdv("COMPLETED", "pago")).toBe("Pago");
    expect(consultaQuitadaNoPdv({ valor_pago: 40, valor_restante: 60 })).toBe(false);
    expect(rotuloStatusPdv("COMPLETED", null)).toBe("Finalizada");
    expect(consultaQuitadaNoPdv({ valor_pago: 0, valor_restante: 0 })).toBe(false);
    expect(seloCaixaPdv({ valor_pago: 0, valor_restante: 100, payment_method: "PRAZO" })).toBe("prazo");
    expect(pdvPodeReceberAtendimento({ valor_pago: 0, valor_restante: 100, payment_method: "PRAZO" })).toBe(false);
    expect(reciboPdvDisponivel({ payment_id: 393, valor_pago: 0, valor_restante: 450, payment_method: "PRAZO" })).toBe(true);
    expect(reciboPdvDisponivel({ payment_id: 81, valor_pago: 450, valor_restante: 0, payment_method: "PIX" })).toBe(true);
    expect(reciboPdvDisponivel({ payment_id: null, valor_pago: 0, valor_restante: 100, payment_method: "PIX" })).toBe(false);
    expect(paymentIdReciboPdv(null, null)).toBe(0);
    expect(paymentIdReciboPdv({ id: 10, payment_id: 393 }, null)).toBe(393);
    expect(paymentIdReciboPdv({ id: 10, payment_id: null }, { consultaId: 10, paymentId: 81 })).toBe(81);
    expect(paymentIdReciboPdv(null, { consultaId: 10, paymentId: 81 })).toBe(0);
    expect(pdvPodeReceberAtendimento({ valor_pago: 0, valor_restante: 100, payment_method: "PIX" })).toBe(true);
    expect(clientePresente("CONFIRMED")).toBe(true);
    expect(clientePresente("IN_PROGRESS")).toBe(true);
    expect(clientePresente("COMPLETED")).toBe(true);
    expect(clientePresente("SCHEDULED")).toBe(false);
    expect(clientePresente("CLIENT_CONFIRMED")).toBe(false);
    expect(clientePresente("PHONE_CONFIRMED")).toBe(false);
    expect(rotuloStatusPdv("COMPLETED", "prazo")).toBe("A prazo");
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
