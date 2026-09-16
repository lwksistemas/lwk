import { describe, expect, it } from "vitest";
import {
  buildReceberPayload,
  calcularTotalLiquido,
  somaEntradas,
  validateReceberForm,
  type EntradaPagamentoLinha,
} from "@/components/clinica-beleza/consultas/modal-receber-consulta-utils";

function linha(method: string, valor: string): EntradaPagamentoLinha {
  return { id: "1", payment_method: method, valor };
}

describe("calcularTotalLiquido", () => {
  it("aplica desconto", () => {
    expect(calcularTotalLiquido(700, 200)).toBe(500);
    expect(calcularTotalLiquido(700, 0)).toBe(700);
    expect(calcularTotalLiquido(100, 150)).toBe(0);
  });
});

describe("validateReceberForm", () => {
  it("exige soma igual ao líquido para quitar", () => {
    expect(
      validateReceberForm({
        totalLiquido: 500,
        desconto: 200,
        base: 700,
        entradas: [
          linha("CREDIT_CARD", "200"),
          { id: "2", payment_method: "PIX", valor: "200" },
          { id: "3", payment_method: "DEBIT_CARD", valor: "100" },
        ],
        markAsPaid: true,
      }),
    ).toBeNull();

    expect(
      validateReceberForm({
        totalLiquido: 500,
        desconto: 200,
        base: 700,
        entradas: [linha("PIX", "300")],
        markAsPaid: true,
      }),
    ).toContain("quitar");
  });

  it("permite desconto igual ao total (nada a receber)", () => {
    expect(
      validateReceberForm({
        totalLiquido: 0,
        desconto: 150,
        base: 150,
        entradas: [linha("CASH", "0")],
        markAsPaid: true,
      }),
    ).toBeNull();
  });

  it("ainda bloqueia total zero sem desconto", () => {
    expect(
      validateReceberForm({
        totalLiquido: 0,
        desconto: 0,
        base: 150,
        entradas: [linha("CASH", "0")],
        markAsPaid: true,
      }),
    ).toBe("Total a receber deve ser maior que zero.");
  });

  it("permite parcial sem quitar", () => {
    expect(
      validateReceberForm({
        totalLiquido: 500,
        desconto: 0,
        base: 500,
        entradas: [linha("PIX", "300")],
        markAsPaid: false,
      }),
    ).toBeNull();
  });
});

describe("buildReceberPayload", () => {
  it("monta desconto e entradas", () => {
    const body = buildReceberPayload({
      desconto: 200,
      totalLiquido: 500,
      markAsPaid: true,
      entradas: [
        linha("CREDIT_CARD", "200"),
        { id: "2", payment_method: "PIX", valor: "200" },
        { id: "3", payment_method: "DEBIT_CARD", valor: "100" },
      ],
    });
    expect(body.desconto).toBe("200");
    expect(body.mark_as_paid).toBe(true);
    expect(body.entradas).toHaveLength(3);
    expect(somaEntradas(body.entradas.map((e, i) => ({ id: String(i), ...e })))).toBe(500);
    expect(body.valor_procedimentos).toBeUndefined();
  });

  it("desconto integral envia entradas vazias e quita", () => {
    const body = buildReceberPayload({
      desconto: 150,
      totalLiquido: 0,
      markAsPaid: true,
      entradas: [linha("CASH", "0")],
    });
    expect(body.desconto).toBe("150");
    expect(body.entradas).toEqual([]);
    expect(body.mark_as_paid).toBe(true);
  });

  it("inclui valor_procedimentos quando o admin altera", () => {
    const body = buildReceberPayload({
      desconto: 0,
      totalLiquido: 80,
      markAsPaid: true,
      entradas: [linha("CASH", "80")],
      valorProcedimentos: 80,
    });
    expect(body.valor_procedimentos).toBe("80");
  });
});
