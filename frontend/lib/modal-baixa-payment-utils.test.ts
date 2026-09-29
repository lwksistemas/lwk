import { describe, expect, it } from "vitest";
import { baixaPagamentoPodeConfirmar } from "@/components/clinica-beleza/financeiro-page/components/modal-baixa-payment-utils";

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
