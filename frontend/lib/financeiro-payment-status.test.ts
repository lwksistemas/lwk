import { describe, expect, it } from "vitest";
import {
  rotuloDataLancamentoReceita,
  rotuloFormaPagamentoReceita,
  rotuloVencimentoPrazo,
  statusPagamentoReceita,
} from "@/components/clinica-beleza/financeiro-page/payment-status";
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
    data_vencimento: null,
    vencido: false,
    dias_atraso: 0,
    retorno_gratuito: false,
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

  it("não mostra Dinheiro enquanto o lançamento está pendente", () => {
    expect(rotuloFormaPagamentoReceita(payment({ status: "PENDING", payment_method: "CASH" }))).toBe("—");
    expect(rotuloFormaPagamentoReceita(payment({ status: "PAID", payment_method: "CASH" }))).toBe("Dinheiro");
    expect(rotuloFormaPagamentoReceita(payment({ status: "PENDING", payment_method: "PRAZO" }))).toBe("A prazo");
  });

  it("preenche Recebido em com o dia do recebimento em qualquer forma", () => {
    expect(rotuloDataLancamentoReceita(payment({ status: "PENDING", payment_date: null }))).toBe("—");
    expect(
      rotuloDataLancamentoReceita(payment({ status: "PAID", saldo_devedor: 0, payment_method: "PIX", payment_date: "2026-09-23" })),
    ).toBe("23/09/2026");
    expect(
      rotuloDataLancamentoReceita(
        payment({ status: "PAID", saldo_devedor: 0, payment_method: "CREDIT_CARD", payment_date: "2026-09-23T18:10:00-03:00" }),
      ),
    ).toBe("23/09/2026");
    expect(
      rotuloDataLancamentoReceita(
        payment({ status: "PARTIAL", saldo_devedor: 40, payment_method: "DEBIT_CARD", payment_date: "2026-09-23T18:10:00-03:00" }),
      ),
    ).toBe("23/09/2026");
    expect(
      rotuloDataLancamentoReceita(
        payment({ status: "PAID", saldo_devedor: 0, retorno_gratuito: true, payment_date: "2026-09-23" }),
      ),
    ).toBe("—");
  });

  it("mostra o vencimento só enquanto o pagamento está a prazo", () => {
    expect(
      rotuloVencimentoPrazo(payment({ status: "PENDING", payment_method: "PRAZO", data_vencimento: "2026-10-23" })),
    ).toBe("23/10/2026");
    expect(
      rotuloVencimentoPrazo(payment({ status: "PAID", saldo_devedor: 0, payment_method: "PIX", data_vencimento: "2026-10-23" })),
    ).toBeNull();
  });

  it("respeita PARTIAL e PAID da API", () => {
    expect(statusPagamentoReceita(payment({ status: "PARTIAL", saldo_devedor: 300 }))).toBe("PARTIAL");
    expect(statusPagamentoReceita(payment({ status: "PAID", saldo_devedor: 0 }))).toBe("PAID");
  });
});
