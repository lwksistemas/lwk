import { describe, expect, it } from 'vitest';
import { parseNfseEmissaoResult } from './nfse-helpers';

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
});
