import { describe, expect, it, vi, afterEach } from 'vitest';
import {
  cobrancaAbertaTemBoleto,
  deveMostrarProximaMensalidade,
  linhaTemBoletoDisponivel,
  numeroNotaParaExibir,
  rotuloNotaFiscal,
} from './assinatura-historico';

function chaveComNumero(numero: number): string {
  const n = String(numero).padStart(13, '0');
  return `354340222${'0'.repeat(14)}${n}2611${'0'.repeat(9)}1`;
}

describe('numeroNotaParaExibir', () => {
  it('mostra o número curto que já está gravado', () => {
    expect(numeroNotaParaExibir('2')).toBe('2');
    expect(rotuloNotaFiscal('61')).toBe('NF 61');
  });

  it('tira o número da chave de 50 dígitos e não devolve a chave', () => {
    const chave = chaveComNumero(3);
    expect(chave).toHaveLength(50);
    expect(numeroNotaParaExibir(chave)).toBe('3');
    expect(rotuloNotaFiscal(chave)).toBe('NF 3');
    expect(rotuloNotaFiscal(chave)).not.toContain(chave);
  });

  it('não mostra código longo que não é número de nota', () => {
    expect(numeroNotaParaExibir('1'.repeat(44))).toBe('');
    expect(numeroNotaParaExibir('')).toBe('');
    expect(rotuloNotaFiscal(null)).toBe('');
  });
});

describe('coluna de boleto', () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it('pago e cobrança fora da janela não têm boleto', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2026, 10, 7));
    expect(linhaTemBoletoDisponivel({
      is_paid: true,
      data_vencimento: '2026-11-10',
      pagamento_loja_id: 25,
      boleto_url: 'https://exemplo/boleto',
    })).toBe(false);
    expect(linhaTemBoletoDisponivel({
      is_paid: false,
      data_vencimento: '2026-12-10',
      pagamento_loja_id: 26,
    })).toBe(false);
    expect(cobrancaAbertaTemBoleto({
      data_vencimento: '2026-12-10',
      boleto_url: 'https://exemplo/boleto',
    })).toBe(false);
  });

  it('dentro da janela, com pagamento, o boleto aparece', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2026, 10, 7));
    expect(linhaTemBoletoDisponivel({
      is_paid: false,
      data_vencimento: '2026-11-10',
      pagamento_loja_id: 26,
    })).toBe(true);
  });
});

describe('deveMostrarProximaMensalidade', () => {
  it('esconde a próxima mensalidade quando o boleto daquele vencimento já está na lista', () => {
    expect(
      deveMostrarProximaMensalidade(
        [{ is_paid: false, data_vencimento: '2026-11-10' }],
        '2026-11-10',
        false,
      ),
    ).toBe(false);
  });

  it('mostra a próxima mensalidade quando ainda não há boleto daquele vencimento', () => {
    expect(
      deveMostrarProximaMensalidade(
        [{ is_paid: true, data_vencimento: '2026-09-02' }],
        '2026-11-10',
        false,
      ),
    ).toBe(true);
  });

  it('não mostra outra linha quando a cobrança em aberto já será exibida', () => {
    expect(deveMostrarProximaMensalidade([], '2026-11-10', true)).toBe(false);
  });
});
