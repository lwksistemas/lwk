import { describe, expect, it } from 'vitest';
import { calcularValorComDesconto, formatarValorComDesconto } from './crm-documento-valores';

describe('calcularValorComDesconto', () => {
  it('sem desconto retorna valor base', () => {
    expect(calcularValorComDesconto(1000, 'percentual', 0)).toBe(1000);
  });

  it('desconto percentual', () => {
    expect(calcularValorComDesconto(1000, 'percentual', 10)).toBe(900);
  });

  it('desconto em valor fixo', () => {
    expect(calcularValorComDesconto(1000, 'valor', 150)).toBe(850);
  });

  it('não retorna negativo', () => {
    expect(calcularValorComDesconto(100, 'valor', 200)).toBe(0);
  });

  it('aceita strings numéricas', () => {
    expect(calcularValorComDesconto('500', 'percentual', '20')).toBe(400);
  });
});

describe('formatarValorComDesconto', () => {
  it('formata em BRL', () => {
    expect(formatarValorComDesconto(1000, 'percentual', 10)).toContain('900');
  });
});
