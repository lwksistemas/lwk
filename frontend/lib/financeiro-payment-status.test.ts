import { describe, expect, it } from "vitest";
import { statusPagamentoReceita } from "@/components/clinica-beleza/financeiro-page/payment-status";
import type { FinanceiroPayment } from "@/components/clinica-beleza/financeiro-page/types";

const payment = (partial: Partial<FinanceiroPayment>): FinanceiroPayment =>
  ({
    id: 1,
    appointment: 1,
    amount: "530",
    valor_total: "530",
    valor_total_efetivo: 530,
    saldo_devedor: 530,
    payment_method: "CASH",
    status: "PENDING",
    payment_date: null,
    comissao_percentual: 0,
    comissao_valor: "0",
    paciente_nome: "Luiz",
    profissional_nome: "Dra.",
    procedimento_nome: "Vitamina C",
    data_atendimento: "2026-08-28T09:00:00",
    created_at: "2026-08-28T09:00:00",
    ...partial,
  });

describe("statusPagamentoReceita", () => {
  it("mantém Pendente quando não houve entrada", () => {
    expect(statusPagamentoReceita(payment({ status: "PENDING", saldo_devedor: 530 }))).toBe("PENDING");
  });

  it("mostra Parcial quando já pago e ainda há saldo", () => {
    expect(
      statusPagamentoReceita(
        payment({ status: "PENDING", valor_total_efetivo: 530, saldo_devedor: 300 }),
      ),
    ).toBe("PARTIAL");
  });

  it("respeita PARTIAL e PAID da API", () => {
    expect(statusPagamentoReceita(payment({ status: "PARTIAL", saldo_devedor: 300 }))).toBe("PARTIAL");
    expect(statusPagamentoReceita(payment({ status: "PAID", saldo_devedor: 0 }))).toBe("PAID");
  });
});
