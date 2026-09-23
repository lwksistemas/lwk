import { CLINICA_FORMA_PAGAMENTO_LABEL } from "@/lib/clinica-beleza-constants";
import type { FinanceiroPayment } from "./types";

/** Status exibido na lista: Parcial quando já houve entrada e ainda há saldo. */
export function statusPagamentoReceita(p: FinanceiroPayment): string {
  if (p.status === "PARTIAL" || p.status === "PAID" || p.status === "CANCELLED") {
    return p.status;
  }
  const total = Number(p.valor_total_efetivo ?? p.amount) || 0;
  const saldo = Number(p.saldo_devedor);
  if (!Number.isFinite(saldo) || total <= 0) return p.status;
  const pago = total - saldo;
  if (p.status === "PENDING" && pago > 0.01 && saldo > 0.01) {
    return "PARTIAL";
  }
  return p.status;
}

/** Pendente ainda não foi pago: a forma gravada é só o padrão Dinheiro. */
export function rotuloFormaPagamentoReceita(p: FinanceiroPayment): string {
  if (p.retorno_gratuito) return "Isento";
  const status = statusPagamentoReceita(p);
  if (status === "PENDING") {
    if (p.payment_method === "PRAZO") return CLINICA_FORMA_PAGAMENTO_LABEL.PRAZO;
    return "—";
  }
  return CLINICA_FORMA_PAGAMENTO_LABEL[p.payment_method] || p.payment_method || "—";
}
