import { describe, expect, it } from 'vitest';
import { addDays, alertaAlergia, cardTone, displayName, formatBRL, formatHora, formatLivreHeading, minutosTeleRestantes, monthRange, slotTimes, slotTimesFromConfig, toISODate, whatsappHref } from '@/lib/clinica-geral-utils';

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

  it('gera slots a partir da configuração do consultório', () => {
    const slots = slotTimesFromConfig('09:00:00', '11:00', 30);
    expect(slots).toEqual(['09:00', '09:30', '10:00', '10:30']);
  });

  it('avança o dia da agenda', () => {
    expect(addDays('2026-08-24', 1)).toBe('2026-08-25');
    expect(formatHora('10:00:00')).toBe('10:00');
    expect(toISODate(new Date(2026, 7, 22))).toBe('2026-08-22');
  });

  it('sinaliza alergia e formata valor e cota de tele', () => {
    expect(alertaAlergia('dipirona, penicilina', 'Dipirona 500mg')).toBe(true);
    expect(alertaAlergia('penicilina', 'paracetamol')).toBe(false);
    expect(formatBRL('150.00')).toMatch(/150/);
    expect(minutosTeleRestantes(90, 600)).toBe(510);
    expect(cardTone('checkin').border).toBe('#1E88E5');
  });

  it('monta o atalho de horários livres e o WhatsApp', () => {
    expect(formatLivreHeading('2026-08-25', '2026-08-24')).toContain('Amanhã');
    expect(cardTone('agendado').bg).toBe('#C5E1A5');
    expect(whatsappHref('(16) 98140-2966')).toBe('https://wa.me/5516981402966');
    expect(monthRange(new Date(2026, 7, 22))).toEqual({ de: '2026-08-01', ate: '2026-08-31' });
  });
});
