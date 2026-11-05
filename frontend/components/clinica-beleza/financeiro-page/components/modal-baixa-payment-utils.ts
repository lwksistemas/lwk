const TOLERANCIA = 0.01;

export interface LinhaBaixa {
  valor: string;
}

function valorLinha(valor: string): number {
  const n = Number(String(valor).replace(",", "."));
  return Number.isFinite(n) ? Math.max(0, round2(n)) : 0;
}

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

/** Mesma regra do Receber pagamento: desconto à esquerda e uma ou mais formas. */
export function validarBaixaFormas(params: {
  saldoDevedor: number;
  desconto: number;
  entradas: LinhaBaixa[];
  quitar: boolean;
}): string | null {
  const saldo = Math.max(0, round2(params.saldoDevedor));
  const desconto = Math.max(0, round2(params.desconto));
  if (desconto > saldo + TOLERANCIA) return "Desconto não pode ser maior que o saldo devedor.";
  const totalLiquido = round2(Math.max(0, saldo - desconto));
  if (totalLiquido <= TOLERANCIA && desconto > TOLERANCIA) return null;
  if (totalLiquido <= TOLERANCIA) return "Informe o valor recebido ou um desconto que quite o saldo.";
  const valores = params.entradas.map((linha) => valorLinha(linha.valor));
  for (let i = 0; i < valores.length; i += 1) {
    if (valores[i] <= TOLERANCIA) return `Informe o valor da forma ${i + 1}.`;
  }
  const soma = round2(valores.reduce((acc, valor) => acc + valor, 0));
  if (soma <= TOLERANCIA) return "Informe o valor recebido ou um desconto que quite o saldo.";
  if (soma > totalLiquido + TOLERANCIA) {
    return `Soma das formas (${soma.toFixed(2)}) excede o total a receber (${totalLiquido.toFixed(2)}).`;
  }
  if (params.quitar && Math.abs(soma - totalLiquido) > TOLERANCIA) {
    return `Para quitar, a soma das formas deve ser igual ao total a receber (${totalLiquido.toFixed(2)}).`;
  }
  return null;
}
