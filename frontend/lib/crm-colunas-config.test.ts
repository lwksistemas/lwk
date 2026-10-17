import { describe, expect, it } from 'vitest';
import {
  DEFAULT_COLUNAS_CONTRATOS,
  DEFAULT_COLUNAS_PROPOSTAS,
  colunasDocumentoNaLista,
  colunasVisiveisFromConfig,
  COLUNAS_PROPOSTAS_DISPONIVEIS,
} from './crm-colunas-config';

describe('colunas de propostas e contratos', () => {
  it('lista vazia usa as colunas padrão da proposta', () => {
    const colunas = colunasVisiveisFromConfig([], COLUNAS_PROPOSTAS_DISPONIVEIS, DEFAULT_COLUNAS_PROPOSTAS);
    expect(colunas.map((c) => c.key)).toEqual(DEFAULT_COLUNAS_PROPOSTAS);
    expect(colunas.find((c) => c.key === 'prestador')?.label).toBe('Prestador');
  });

  it('esconde assinatura quando a listagem não precisa dela', () => {
    const colunas = [
      { key: 'numero', label: 'Número' },
      { key: 'assinatura', label: 'Assinatura' },
    ];
    expect(colunasDocumentoNaLista(colunas, false).map((c) => c.key)).toEqual(['numero']);
    expect(colunasDocumentoNaLista(colunas, true).map((c) => c.key)).toEqual(['numero', 'assinatura']);
  });
});
