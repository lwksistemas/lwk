import { describe, expect, it } from 'vitest';
import {
  buildPrecosMap,
  calcularPrecoEfetivo,
  precoProcedimento,
} from './convenio-precos';

describe('calcularPrecoEfetivo', () => {
  it('modo fixo retorna o valor informado', () => {
    expect(calcularPrecoEfetivo(200, 'fixo', 150)).toBe(150);
  });

  it('modo percentual calcula sobre o particular', () => {
    expect(calcularPrecoEfetivo(200, 'percentual', 80)).toBe(160);
  });
});

describe('buildPrecosMap', () => {
  it('usa preco_efetivo quando presente', () => {
    const map = buildPrecosMap([
      { procedure: 1, preco: 100, preco_efetivo: 90 },
    ]);
    expect(map[1]).toBe(90);
  });

  it('calcula percentual quando preco_efetivo ausente', () => {
    const map = buildPrecosMap(
      [{ procedure: 2, modo: 'percentual', preco: 50, preco_particular: 200 }],
    );
    expect(map[2]).toBe(100);
  });
});

describe('precoProcedimento', () => {
  it('sem convênio retorna preço particular', () => {
    expect(precoProcedimento(1, 120, '', {})).toBe(120);
  });

  it('com convênio usa mapa de preços', () => {
    expect(precoProcedimento(1, 120, 3, { 1: 80 })).toBe(80);
  });
});
