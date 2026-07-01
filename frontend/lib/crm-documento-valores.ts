import { formatCrmBrl } from '@/lib/crm-utils';

export type CrmDescontoTipo = 'percentual' | 'valor';

export function calcularValorComDesconto(
  valorTotal: string | number,
  descontoTipo: CrmDescontoTipo | string,
  descontoValor: string | number,
): number {
  const base = typeof valorTotal === 'string' ? parseFloat(valorTotal) || 0 : valorTotal || 0;
  const desc = typeof descontoValor === 'string' ? parseFloat(descontoValor) || 0 : descontoValor || 0;
  if (desc <= 0) return base;
  if (descontoTipo === 'percentual') return Math.max(base - (base * desc) / 100, 0);
  return Math.max(base - desc, 0);
}

export function formatarValorComDesconto(
  valorTotal: string | number,
  descontoTipo: CrmDescontoTipo | string,
  descontoValor: string | number,
): string {
  return formatCrmBrl(calcularValorComDesconto(valorTotal, descontoTipo, descontoValor));
}
