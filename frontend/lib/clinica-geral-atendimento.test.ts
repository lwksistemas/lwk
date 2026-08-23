import { describe, expect, it } from 'vitest';
import { calcIMC, calcSC, emptyFicha, fichaParaSoap, formatTimer, mergeFicha, toggleItem } from '@/lib/clinica-geral-atendimento';

describe('clinica-geral-atendimento', () => {
  it('calcula IMC, SC e o cronômetro', () => {
    expect(calcIMC('70', '170')).toBe('24.2');
    expect(calcSC('70', '170')).toBe('1.82');
    expect(formatTimer(5)).toBe('00:05');
    expect(formatTimer(125)).toBe('02:05');
  });

  it('alterna tags e monta SOAP a partir da ficha', () => {
    const lista = toggleItem([], 'Depressão');
    expect(lista).toHaveLength(1);
    expect(toggleItem(lista, 'Depressão')).toEqual([]);
    const ficha = mergeFicha({
      ...emptyFicha(),
      queixas: [{ nome: 'Cefaléia', duracao: 'Até 24h' }],
      historia_doenca: 'Dor há 1 dia',
      diagnostico: 'Cefaleia tensional',
      tratamentos: [{ nome: 'Dipirona' }],
    });
    const soap = fichaParaSoap(ficha);
    expect(soap.subjetivo).toContain('Cefaléia');
    expect(soap.avaliacao).toBe('Cefaleia tensional');
    expect(soap.plano).toContain('Dipirona');
  });
});
