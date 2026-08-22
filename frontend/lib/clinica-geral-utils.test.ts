import { describe, expect, it } from 'vitest';
import { addDays, displayName, formatHora, slotTimes, toISODate } from '@/lib/clinica-geral-utils';

describe('clinica-geral-utils', () => {
  it('formata nome social como na ficha', () => {
    expect(displayName('Daniel Souza Felix', 'Lindo')).toBe('Lindo (Daniel Souza Felix)');
    expect(displayName('Mariela', '')).toBe('Mariela');
  });

  it('gera slots de 15 minutos das 08h às 18h', () => {
    const slots = slotTimes();
    expect(slots[0]).toBe('08:00');
    expect(slots).toContain('08:15');
    expect(slots).toContain('17:45');
    expect(slots).not.toContain('18:00');
  });

  it('avança o dia da agenda', () => {
    expect(addDays('2026-08-24', 1)).toBe('2026-08-25');
    expect(formatHora('10:00:00')).toBe('10:00');
    expect(toISODate(new Date(2026, 7, 22))).toBe('2026-08-22');
  });
});
