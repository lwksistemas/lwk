import { describe, expect, it } from 'vitest';
import { valorComissaoParaApi } from './crm-oportunidade-comissao';

describe('valorComissaoParaApi', () => {
  it('campo vazio grava ausência de comissão', () => {
    expect(valorComissaoParaApi('')).toBeNull();
    expect(valorComissaoParaApi('   ')).toBeNull();
    expect(valorComissaoParaApi(null)).toBeNull();
  });

  it('zero e valor preenchido são gravados', () => {
    expect(valorComissaoParaApi('0')).toBe(0);
    expect(valorComissaoParaApi('375')).toBe(375);
    expect(valorComissaoParaApi('63,50')).toBe(63.5);
  });
});
