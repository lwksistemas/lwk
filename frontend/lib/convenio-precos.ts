/** Nome do convênio padrão cadastrado na loja. */
export const CONVENIO_PARTICULAR_LABEL = "Particular";

export function isConvenioParticularNome(nome: string | undefined | null): boolean {
  return (nome || '').trim().toLowerCase() === 'particular';
}

export function findConvenioParticular<T extends { id: number; nome: string }>(
  convenios: T[],
): T | undefined {
  return convenios.find((c) => isConvenioParticularNome(c.nome));
}

/** Ordena convênios com Particular primeiro. */
export function ordenarConveniosComParticularPrimeiro<T extends { nome: string }>(
  convenios: T[],
): T[] {
  return [...convenios].sort((a, b) => {
    const ap = isConvenioParticularNome(a.nome);
    const bp = isConvenioParticularNome(b.nome);
    if (ap && !bp) return -1;
    if (!ap && bp) return 1;
    return a.nome.localeCompare(b.nome, 'pt-BR');
  });
}

export type {
  ConvenioItem,
  ConvenioPrecoItem,
  ConvenioPrecoModo,
} from "@/lib/clinica-beleza-api";

import type { ConvenioPrecoItem, ConvenioPrecoModo } from "@/lib/clinica-beleza-api";

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
