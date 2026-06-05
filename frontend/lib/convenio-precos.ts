/** Valor vazio no select = atendimento particular (preço cadastrado do procedimento). */
export const CONVENIO_PARTICULAR_LABEL = "Particular";

export interface ConvenioItem {
  id: number;
  nome: string;
  codigo?: string;
  is_active?: boolean;
}

export type ConvenioPrecoModo = 'fixo' | 'percentual';

export interface ConvenioPrecoItem {
  id?: number;
  procedure: number;
  procedure_name?: string;
  preco_particular?: string | number;
  modo?: ConvenioPrecoModo;
  preco: string | number;
  preco_efetivo?: string | number;
}

export function calcularPrecoEfetivo(
  precoParticular: number,
  modo: ConvenioPrecoModo,
  valor: number,
): number {
  if (modo === 'percentual') {
    return Math.round(precoParticular * (valor / 100) * 100) / 100;
  }
  return valor;
}

export function buildPrecosMap(
  precos: ConvenioPrecoItem[],
  particularPorId?: Record<number, number>,
): Record<number, number> {
  const map: Record<number, number> = {};
  for (const row of precos) {
    if (row.preco_efetivo != null && row.preco_efetivo !== '') {
      map[row.procedure] = Number(row.preco_efetivo) || 0;
      continue;
    }
    const particular = (particularPorId?.[row.procedure] ?? Number(row.preco_particular)) || 0;
    const modo = row.modo || 'fixo';
    map[row.procedure] = calcularPrecoEfetivo(particular, modo, Number(row.preco) || 0);
  }
  return map;
}

export function precoProcedimento(
  procedureId: number,
  precoParticular: number,
  convenioId: number | "",
  precosMap: Record<number, number>,
): number {
  if (!convenioId) return precoParticular;
  if (precosMap[procedureId] !== undefined) return precosMap[procedureId];
  return precoParticular;
}
