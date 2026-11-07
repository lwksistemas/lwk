import {
  CLINICA_FORMA_PAGAMENTO_CORRIGIVEL,
  CLINICA_FORMA_PAGAMENTO_LABEL,
} from "@/lib/clinica-beleza-constants";
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

/** Aparência da linha: recebido em verde, pendente em âmbar, cancelado riscado. */
export function classeLinhaReceita(status: string): string {
  if (status === "CANCELLED") {
    return "border-b border-gray-200 bg-gray-100/90 text-gray-500 dark:border-neutral-700 dark:bg-neutral-900/60 dark:text-gray-400";
  }
  if (status === "PENDING") {
    return "border-b border-amber-100 bg-amber-50/80 dark:border-amber-900/40 dark:bg-amber-950/25";
  }
  if (status === "PARTIAL") {
    return "border-b border-orange-100 bg-orange-50/70 dark:border-orange-900/40 dark:bg-orange-950/20";
  }
  return "border-b border-gray-100 dark:border-neutral-700";
}

export function classeValorReceita(status: string): string {
  if (status === "CANCELLED") return "text-gray-400 line-through decoration-gray-400";
  if (status === "PENDING") return "text-amber-800 dark:text-amber-200";
  if (status === "PARTIAL") return "text-orange-800 dark:text-orange-200";
  if (status === "PAID") return "text-green-700 dark:text-green-400";
  return "";
}

export function classeSeloReceita(status: string): string {
  if (status === "CANCELLED") return "bg-gray-300 text-gray-700 dark:bg-neutral-600 dark:text-gray-100";
  if (status === "PENDING") return "bg-amber-100 text-amber-900 dark:bg-amber-900/40 dark:text-amber-200";
  if (status === "PARTIAL") return "bg-orange-100 text-orange-900 dark:bg-orange-900/40 dark:text-orange-200";
  if (status === "PAID") return "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300";
  return "bg-gray-100 dark:bg-neutral-600";
}

/**
 * Data do recebimento na coluna Recebido em.
 * Vale para dinheiro, PIX, cartão e transferência. Pendente fica em branco.
 */
export function rotuloDataLancamentoReceita(p: FinanceiroPayment): string {
  if (p.retorno_gratuito) return "—";
  const status = statusPagamentoReceita(p);
  if (status !== "PAID" && status !== "PARTIAL") return "—";
  return formatarDataLancamento(p.payment_date);
}

function formatarDataLancamento(value: string | null): string {
  if (!value) return "—";
  const dia = value.slice(0, 10);
  if (/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    return dia.split("-").reverse().join("/");
  }
  const data = new Date(value);
  if (Number.isNaN(data.getTime())) return "—";
  return data.toLocaleDateString("pt-BR", {
    timeZone: "America/Sao_Paulo",
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

/** Vencimento de quem ainda está a prazo. Some depois do recebimento. */
export function rotuloVencimentoPrazo(p: FinanceiroPayment): string | null {
  if (rotuloFormaPagamentoReceita(p) !== CLINICA_FORMA_PAGAMENTO_LABEL.PRAZO) return null;
  const dia = String(p.data_vencimento || "").slice(0, 10);
  if (!/^\d{4}-\d{2}-\d{2}$/.test(dia)) return null;
  return dia.split("-").reverse().join("/");
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

const FORMAS_CORRIGIVEIS = new Set<string>(CLINICA_FORMA_PAGAMENTO_CORRIGIVEL);

/** Pago ou parcial com valor recebido: a secretaria pode ter escolhido a forma errada. */
export function podeCorrigirFormaPagamento(p: FinanceiroPayment): boolean {
  if (p.retorno_gratuito) return false;
  const status = statusPagamentoReceita(p);
  if (status !== "PAID" && status !== "PARTIAL") return false;
  if (!FORMAS_CORRIGIVEIS.has(p.payment_method)) return false;
  const recebido = Number(p.amount);
  return Number.isFinite(recebido) && recebido > 0.009;
}
