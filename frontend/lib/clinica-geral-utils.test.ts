import { describe, expect, it } from 'vitest';
import { addDays, alertaAlergia, cardTone, daysFromToday, displayName, formatAgeYearsMonths, formatBRL, formatDateBR, formatDataExtenso, formatDaysOffset, formatEndereco, formatHora, formatLivreHeading, formatMesAnoCurto, formatNascimentoIdade, formatProntuarioSubtitulo, formatRelativo, minutosTeleRestantes, monthRange, slotTimes, slotTimesFromConfig, toISODate, whatsappHref } from '@/lib/clinica-geral-utils';

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

  it('mostra data de nascimento com idade em anos e meses', () => {
    const hoje = new Date(2026, 7, 23);
    expect(formatDateBR('1984-02-20')).toBe('20/02/1984');
    expect(formatAgeYearsMonths('1984-02-20', hoje)).toBe('42 anos e 6 meses');
    expect(formatNascimentoIdade('1984-02-20', hoje)).toBe('20/02/1984 (42 anos e 6 meses)');
    expect(formatProntuarioSubtitulo({
      data_nascimento: '1984-02-20',
      estado_civil: 'Solteiro(a)',
      cidade: 'São Paulo',
      uf: 'SP',
    }, hoje)).toBe('42 anos e 6 meses. Solteiro(a). São Paulo - SP');
    expect(formatAgeYearsMonths('2025-08-23', hoje)).toBe('1 ano');
    expect(formatAgeYearsMonths('2026-02-23', hoje)).toBe('6 meses');
  });

  it('mostra o deslocamento dos agendamentos e o endereço', () => {
    const hoje = new Date(2026, 7, 23);
    expect(formatDaysOffset(daysFromToday('2026-08-24', hoje))).toBe('+1 d');
    expect(formatDaysOffset(daysFromToday('2026-08-23', hoje))).toBe('0 d');
    expect(formatEndereco({
      logradouro: 'Avenida Brigadeiro Luis Antônio',
      numero: '2696',
      cidade: 'São Paulo',
      uf: 'SP',
      cep: '01402-000',
    })).toBe('Avenida Brigadeiro Luis Antônio 2696\nSão Paulo SP 01402-000');
  });

  it('formata data relativa do resumo clínico', () => {
    const agora = new Date(2026, 7, 23, 18, 50, 0);
    expect(formatMesAnoCurto('2026-08-23')).toBe('Ago/26');
    expect(formatDataExtenso('2026-08-23')).toBe('23 de agosto de 2026');
    expect(formatRelativo('2026-08-23', '18:25', agora)).toBe('Há 25 Minutos');
  });

  it('monta o atalho de horários livres e o WhatsApp', () => {
    expect(formatLivreHeading('2026-08-25', '2026-08-24')).toContain('Amanhã');
    expect(cardTone('agendado').bg).toBe('#C5E1A5');
    expect(whatsappHref('(16) 98140-2966')).toBe('https://wa.me/5516981402966');
    expect(monthRange(new Date(2026, 7, 22))).toEqual({ de: '2026-08-01', ate: '2026-08-31' });
  });
});
