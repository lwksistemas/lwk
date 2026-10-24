import { fetchAllPaginatedResults } from '@/lib/crm-utils';
import type { CrmPropostaTemplate } from '@/lib/crm-proposta-form-types';

export function carregarTemplatesDaPrestadora(prestadoraId: number | null | undefined) {
  if (!prestadoraId) return Promise.resolve([] as CrmPropostaTemplate[]);
  return fetchAllPaginatedResults<CrmPropostaTemplate>('/crm-vendas/proposta-templates/', {
    prestadora: prestadoraId,
  });
}

export function avisoTemplatesDaPrestadora(opts: {
  temOportunidade: boolean;
  prestadoraId: number | null;
  prestadoraNome: string;
  quantidade: number;
}): string {
  if (opts.quantidade > 0) return '';
  if (!opts.temOportunidade) {
    return 'Escolha a oportunidade para ver os templates da prestadora.';
  }
  if (!opts.prestadoraId) return 'Esta oportunidade não tem empresa prestadora.';
  const nome = opts.prestadoraNome.trim() || 'Esta prestadora';
  return `${nome} ainda não tem templates de proposta.`;
}
