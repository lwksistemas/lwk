import { describe, expect, it } from "vitest";
import {
  baixaPagamentoPodeConfirmar,
  validarBaixaFormas,
} from "@/components/clinica-beleza/financeiro-page/components/modal-baixa-payment-utils";

describe("baixaPagamentoPodeConfirmar", () => {
  it("habilita quitar quando o desconto cobre o saldo e não há valor recebido", () => {
    expect(
      baixaPagamentoPodeConfirmar({ saldoDevedor: 150, valorRecebido: 0, desconto: 150 }),
    ).toEqual({ pode: true, valorEnviado: 0, quitaTotal: true, descontoExcede: false });
  });

  it("não soma o valor recebido em cima do desconto que já quitou", () => {
    expect(
      baixaPagamentoPodeConfirmar({ saldoDevedor: 150, valorRecebido: 150, desconto: 150 }),
    ).toEqual({ pode: true, valorEnviado: 0, quitaTotal: true, descontoExcede: false });
  });

  it("exige valor recebido quando o desconto não cobre o saldo", () => {
    expect(
      baixaPagamentoPodeConfirmar({ saldoDevedor: 150, valorRecebido: 0, desconto: 50 }),
    ).toMatchObject({ pode: false, quitaTotal: false });
  });

  it("quita com recebido e desconto somados", () => {
    expect(
      baixaPagamentoPodeConfirmar({ saldoDevedor: 150, valorRecebido: 100, desconto: 50 }),
    ).toEqual({ pode: true, valorEnviado: 100, quitaTotal: true, descontoExcede: false });
  });

  it("recusa desconto maior que o saldo", () => {
    expect(
      baixaPagamentoPodeConfirmar({ saldoDevedor: 150, valorRecebido: 0, desconto: 200 }),
    ).toMatchObject({ pode: false, descontoExcede: true });
  });
});

describe("validarBaixaFormas", () => {
  it("aceita desconto que quita sem forma de pagamento", () => {
    expect(validarBaixaFormas({ saldoDevedor: 150, desconto: 150, entradas: [], quitar: true })).toBeNull();
  });

  it("aceita duas formas que fecham o saldo", () => {
    expect(
      validarBaixaFormas({
        saldoDevedor: 2500,
        desconto: 0,
        entradas: [{ valor: "1000" }, { valor: "1500" }],
        quitar: true,
      }),
    ).toBeNull();
  });

  it("pede o valor completo quando a opção de quitar está marcada", () => {
    expect(
      validarBaixaFormas({
        saldoDevedor: 2500,
        desconto: 0,
        entradas: [{ valor: "1000" }],
        quitar: true,
      }),
    ).toMatch(/Para quitar/);
  });

  it("permite entrada parcial quando não quita", () => {
    expect(
      validarBaixaFormas({
        saldoDevedor: 2500,
        desconto: 0,
        entradas: [{ valor: "1000" }],
        quitar: false,
      }),
    ).toBeNull();
  });
});
