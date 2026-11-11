import { describe, expect, it } from 'vitest';
import { emissaoConcluida, mensagemEmissaoNota, notaRecemEmitida, parseNfseEmissaoResult } from './nfse-helpers';

describe('parseNfseEmissaoResult', () => {
  it('detecta emissão enfileirada (202)', () => {
    const result = parseNfseEmissaoResult(202, {
      success: true,
      queued: true,
      message: 'NFS-e enfileirada para emissão.',
    });
    expect(result.queued).toBe(true);
    expect(result.message).toContain('enfileirada');
  });

  it('detecta emissão imediata (201)', () => {
    const result = parseNfseEmissaoResult(201, {
      success: true,
      message: 'NFS-e emitida com sucesso',
    });
    expect(result.queued).toBe(false);
    expect(result.message).toContain('sucesso');
  });

  it('reconhece a nota nova e o status final', () => {
    const lista = [
      { id: 8, status: 'emitida', numero_nf: '100' },
      { id: 12, status: 'emitida', numero_nf: '141' },
      { id: 9, status: 'erro', erro: 'rejeitada', numero_nf: '' },
    ];
    expect(notaRecemEmitida(lista, [8, 9])?.id).toBe(12);
    expect(notaRecemEmitida(lista, [8, 9, 12])).toBeNull();
    expect(emissaoConcluida({ id: 12, status: 'emitida', numero_nf: '141' })).toBe(true);
    expect(emissaoConcluida({ id: 3, status: 'pendente', numero_nf: '' })).toBe(false);
    expect(mensagemEmissaoNota({ id: 12, status: 'emitida', numero_nf: '141' }).text).toContain('141');
    expect(mensagemEmissaoNota({ id: 9, status: 'erro', erro: 'rejeitada' }).text).toContain('rejeitada');
  });

  it('usa o texto padrão quando a API não manda mensagem', () => {
    expect(parseNfseEmissaoResult(202, { success: true, queued: true }).message).toContain('enfileirada');
    expect(parseNfseEmissaoResult(201, { success: true }).message).toContain('emitida');
  });
});
