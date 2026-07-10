export type FormaPagamentoCodigo = "CASH" | "CREDIT_CARD" | "DEBIT_CARD" | "PIX" | "TRANSFER";

export interface EntradaPagamentoLinha {
  id: string;
  payment_method: FormaPagamentoCodigo | string;
  valor: string;
  /** Parcelas do cartão de crédito (só UI/recibo). */
  parcelas?: string;
  valorParcela?: string;
}

const TOLERANCIA = 0.01;

export function parseMoneyInput(value: string | number | null | undefined): number {
  if (value === null || value === undefined || value === "") return 0;
  const n = typeof value === "number" ? value : Number(String(value).replace(",", "."));
  return Number.isFinite(n) ? n : 0;
}

/** Total a receber = base (saldo ou total) − desconto, mínimo 0. */
export function calcularTotalLiquido(base: number, desconto: number): number {
  return Math.max(0, round2(base - Math.max(0, desconto)));
}

export function somaEntradas(entradas: EntradaPagamentoLinha[]): number {
  return round2(entradas.reduce((acc, e) => acc + parseMoneyInput(e.valor), 0));
}

export function round2(n: number): number {
  return Math.round(n * 100) / 100;
}

export function valoresQuaseIguais(a: number, b: number): boolean {
  return Math.abs(a - b) <= TOLERANCIA;
}

export function novaLinhaEntrada(
  payment_method: string = "CASH",
  valor: number | string = "",
): EntradaPagamentoLinha {
  return {
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    payment_method,
    valor: valor === "" ? "" : String(round2(Number(valor))),
    parcelas: "1",
    valorParcela: "",
  };
}

export function validateReceberForm(params: {
  totalLiquido: number;
  desconto: number;
  base: number;
  entradas: EntradaPagamentoLinha[];
  markAsPaid: boolean;
}): string | null {
  const { totalLiquido, desconto, base, entradas, markAsPaid } = params;
  if (desconto < 0) return "Desconto não pode ser negativo.";
  if (desconto > base + TOLERANCIA) return "Desconto não pode ser maior que o total.";
  if (totalLiquido <= 0) return "Total a receber deve ser maior que zero.";
  if (!entradas.length) return "Adicione ao menos uma forma de pagamento.";

  for (let i = 0; i < entradas.length; i++) {
    const v = parseMoneyInput(entradas[i].valor);
    if (v <= 0) return `Informe o valor da forma ${i + 1}.`;
  }

  const soma = somaEntradas(entradas);
  if (soma <= 0) return "Informe um valor maior que zero.";
  if (soma > totalLiquido + TOLERANCIA) {
    return `Soma das formas (${soma.toFixed(2)}) excede o total a receber (${totalLiquido.toFixed(2)}).`;
  }
  if (markAsPaid && !valoresQuaseIguais(soma, totalLiquido)) {
    return `Para quitar, a soma das formas deve ser igual ao total a receber (${totalLiquido.toFixed(2)}).`;
  }
  if (!markAsPaid && valoresQuaseIguais(soma, 0)) {
    return "Informe um valor maior que zero.";
  }
  return null;
}

export function buildReceberPayload(params: {
  desconto: number;
  entradas: EntradaPagamentoLinha[];
  markAsPaid: boolean;
  totalLiquido: number;
}): {
  desconto: string;
  entradas: Array<{ payment_method: string; valor: string }>;
  mark_as_paid: boolean;
} {
  const soma = somaEntradas(params.entradas);
  return {
    desconto: String(round2(Math.max(0, params.desconto))),
    entradas: params.entradas.map((e) => ({
      payment_method: e.payment_method,
      valor: String(round2(parseMoneyInput(e.valor))),
    })),
    mark_as_paid: params.markAsPaid && valoresQuaseIguais(soma, params.totalLiquido),
  };
}

export function formatEntradasResumo(
  entradas: EntradaPagamentoLinha[],
  labels: Record<string, string>,
): string {
  return entradas
    .filter((e) => parseMoneyInput(e.valor) > 0)
    .map((e) => {
      const label = labels[e.payment_method] || e.payment_method;
      return `${label}: R$ ${parseMoneyInput(e.valor).toFixed(2)}`;
    })
    .join(" · ");
}
