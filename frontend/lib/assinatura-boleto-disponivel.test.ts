import { describe, expect, it, vi, afterEach } from 'vitest';
import { cobrancaBoletoPixDisponivel } from './assinatura-aviso';

describe('cobrancaBoletoPixDisponivel', () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it('libera dentro de 10 dias do vencimento', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2026, 6, 20));
    const out = cobrancaBoletoPixDisponivel('2026-07-29');
    expect(out.disponivel).toBe(true);
  });

  it('bloqueia antes da janela de 10 dias', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2026, 6, 6));
    const out = cobrancaBoletoPixDisponivel('2026-08-29');
    expect(out.disponivel).toBe(false);
    expect(out.mensagem).toContain('10 dias antes do vencimento');
    expect(out.mensagem).toContain('19/08/2026');
  });
});
