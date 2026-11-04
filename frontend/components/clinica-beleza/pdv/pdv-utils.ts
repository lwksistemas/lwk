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

export function rotuloStatus(status: string | undefined): string {
  if (status === "CONFIRMED" || status === "IN_PROGRESS") return "Presente";
  if (status === "COMPLETED") return "Finalizada";
  if (status === "CANCELLED") return "Cancelado";
  if (status === "NO_SHOW") return "Faltou";
  if (status === "CLIENT_CONFIRMED") return "Confirmado";
  if (status === "PHONE_CONFIRMED") return "Confirmado";
  return "Aguardando";
}

export function reais(valor: number): number {
  return Math.round((Number.isFinite(valor) ? valor : 0) * 100) / 100;
}
