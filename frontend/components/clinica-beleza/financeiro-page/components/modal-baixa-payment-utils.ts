const TOLERANCIA = 0.01;

function round2(n: number): number {
  return Math.round(n * 100) / 100;
}

/** Desconto que cobre o saldo quita sem exigir valor recebido. */
export function baixaPagamentoPodeConfirmar(params: {
  saldoDevedor: number;
  valorRecebido: number;
  desconto: number;
}): { pode: boolean; valorEnviado: number; quitaTotal: boolean; descontoExcede: boolean } {
  const saldo = Math.max(0, params.saldoDevedor);
  const desconto = Math.max(0, params.desconto);
  const recebido = Math.max(0, params.valorRecebido);
  if (desconto > saldo + TOLERANCIA) {
    return { pode: false, valorEnviado: 0, quitaTotal: false, descontoExcede: true };
  }
  const restante = round2(Math.max(0, saldo - desconto));
  const valorEnviado = round2(Math.min(recebido, restante));
  const cobre = desconto + valorEnviado >= saldo - TOLERANCIA;
  const quitaTotal = cobre && (desconto > TOLERANCIA || valorEnviado > TOLERANCIA);
  const pode = valorEnviado > TOLERANCIA || (desconto > TOLERANCIA && quitaTotal);
  return { pode, valorEnviado, quitaTotal, descontoExcede: false };
}
