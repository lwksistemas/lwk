export const FORMAS_PDV = [
  { id: "PIX", label: "PIX" },
  { id: "CASH", label: "Dinheiro" },
  { id: "CREDIT_CARD", label: "Cartão de crédito" },
  { id: "DEBIT_CARD", label: "Cartão de débito" },
  { id: "TRANSFER", label: "Transferência" },
  { id: "PRAZO", label: "A prazo" },
] as const;

export function hojeIso(): string {
  const agora = new Date();
  const mes = String(agora.getMonth() + 1).padStart(2, "0");
  const dia = String(agora.getDate()).padStart(2, "0");
  return `${agora.getFullYear()}-${mes}-${dia}`;
}

export function quandoRecibo(iso?: string): string {
  const data = iso ? new Date(iso) : new Date();
  if (Number.isNaN(data.getTime())) return "";
  const hora = data.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
  return `${data.toLocaleDateString("pt-BR")} às ${hora}`;
}

export function horaCurta(iso: string | undefined): string {
  if (!iso) return "";
  const data = new Date(iso);
  if (Number.isNaN(data.getTime())) return "";
  return data.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
}

export function clientePresente(status: string | undefined): boolean {
  return status === "CONFIRMED" || status === "IN_PROGRESS" || status === "COMPLETED";
}

export function podeMarcarPresente(status: string | undefined): boolean {
  return !clientePresente(status) && status !== "CANCELLED" && status !== "NO_SHOW";
}

export function podeAlterarServico(status: string | undefined): boolean {
  return status === "CONFIRMED" || status === "IN_PROGRESS";
}

export function rotuloStatus(status: string | undefined): string {
  if (status === "IN_PROGRESS") return "Atendimento";
  if (status === "CONFIRMED") return "Presente";
  if (status === "COMPLETED") return "Finalizada";
  if (status === "CANCELLED") return "Cancelado";
  if (status === "NO_SHOW") return "Faltou";
  if (status === "CLIENT_CONFIRMED") return "Confirmado";
  if (status === "PHONE_CONFIRMED") return "Confirmado";
  return "Aguardando";
}

/** Só no PDV: o valor devido entrou por inteiro. A agenda continua com o status do atendimento. */
export function consultaQuitadaNoPdv(consulta: {
  valor_pago?: number | string | null;
  valor_restante?: number | string | null;
} | null | undefined): boolean {
  if (!consulta || consulta.valor_restante == null || consulta.valor_restante === "") return false;
  const pago = Number(consulta.valor_pago || 0);
  const restante = Number(consulta.valor_restante);
  return pago > 0.009 && Number.isFinite(restante) && restante <= 0.009;
}

export type SeloCaixaPdv = "pago" | "prazo" | null;

/** Pago quando o valor entrou. A prazo quando o recebimento ficou para depois. */
export function seloCaixaPdv(consulta: {
  valor_pago?: number | string | null;
  valor_restante?: number | string | null;
  payment_method?: string | null;
} | null | undefined): SeloCaixaPdv {
  if (consultaQuitadaNoPdv(consulta)) return "pago";
  const metodo = String(consulta?.payment_method || "").toUpperCase();
  const restante = consulta?.valor_restante;
  if (metodo === "PRAZO" && restante != null && restante !== "" && Number(restante) > 0.009) return "prazo";
  return null;
}

/** Recibo do PDV fica disponível depois de pago ou a prazo. */
export function reciboPdvDisponivel(consulta: {
  payment_id?: number | null;
  valor_pago?: number | string | null;
  valor_restante?: number | string | null;
  payment_method?: string | null;
} | null | undefined): boolean {
  const selo = seloCaixaPdv(consulta);
  return (selo === "pago" || selo === "prazo") && Number(consulta?.payment_id || 0) > 0;
}

/** A prazo já lançado só é recebido no Financeiro. O PDV não quita essa venda. */
export function pdvPodeReceberAtendimento(consulta: {
  valor_pago?: number | string | null;
  valor_restante?: number | string | null;
  payment_method?: string | null;
} | null | undefined): boolean {
  return seloCaixaPdv(consulta) !== "prazo";
}

export function rotuloStatusPdv(status: string | undefined, selo: SeloCaixaPdv): string {
  if (selo === "pago") return "Pago";
  if (selo === "prazo") return "A prazo";
  return rotuloStatus(status);
}

export function classeStatusPdv(status: string | undefined, selo: SeloCaixaPdv = null): string {
  if (selo === "pago") return "bg-sky-100 text-sky-800";
  if (selo === "prazo") return "bg-orange-100 text-orange-800";
  if (status === "IN_PROGRESS") return "bg-amber-100 text-amber-800";
  if (status === "CONFIRMED") return "bg-emerald-50 text-emerald-700";
  if (status === "COMPLETED") return "bg-emerald-100 text-emerald-800";
  if (status === "CANCELLED") return "bg-red-50 text-red-700";
  return "bg-gray-100 text-gray-500";
}

export function reais(valor: number): number {
  return Math.round((Number.isFinite(valor) ? valor : 0) * 100) / 100;
}

export function valorLinhaPagamento(valor: string): number {
  const numero = Number(String(valor).replace(",", "."));
  return reais(Number.isFinite(numero) ? numero : 0);
}

/** Uma linha vazia usa o total. Várias linhas usam o valor digitado em cada forma. */
export function montarEntradasPdv(
  linhas: { forma: string; valor: string }[],
  total: number,
): { payment_method: string; valor: number }[] {
  const preenchidas = linhas.map((linha) => ({
    payment_method: linha.forma,
    valor: valorLinhaPagamento(linha.valor),
  }));
  if (preenchidas.length === 1 && preenchidas[0].valor <= 0) {
    preenchidas[0] = { ...preenchidas[0], valor: reais(total) };
  }
  return preenchidas.filter((linha) => linha.valor > 0);
}

export function somaEntradasPdv(entradas: { valor: number }[]): number {
  return reais(entradas.reduce((acc, linha) => acc + linha.valor, 0));
}
