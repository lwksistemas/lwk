export type DescontoTipo = "fixo" | "percentual";

export function aplicarDescontoProtocolo(
  bruto: number,
  tipo: DescontoTipo,
  valor: number,
): { desconto: number; liquido: number } {
  const total = Math.round(bruto * 100) / 100;
  const informado = Math.round((Number.isFinite(valor) ? valor : 0) * 100) / 100;
  let desconto = 0;
  if (tipo === "percentual") {
    const pct = Math.min(100, Math.max(0, informado));
    desconto = Math.round(total * pct) / 100;
  } else {
    desconto = Math.min(total, Math.max(0, informado));
  }
  desconto = Math.round(desconto * 100) / 100;
  return { desconto, liquido: Math.round((total - desconto) * 100) / 100 };
}
