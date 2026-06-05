/** Valor vazio no select = atendimento particular (preço cadastrado do procedimento). */
export const CONVENIO_PARTICULAR_LABEL = "Particular";

export interface ConvenioItem {
  id: number;
  nome: string;
  codigo?: string;
  is_active?: boolean;
}

export interface ConvenioPrecoItem {
  id?: number;
  procedure: number;
  procedure_name?: string;
  preco: string | number;
}

export function buildPrecosMap(precos: ConvenioPrecoItem[]): Record<number, number> {
  const map: Record<number, number> = {};
  for (const row of precos) {
    map[row.procedure] = Number(row.preco) || 0;
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
