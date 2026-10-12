import { describe, expect, it } from 'vitest';
import {
  filtrarNfsesPorBusca,
  montarMotivoCancelamento,
  nfsePodeCancelar,
  nfsePodeExcluirLoja,
  nfsePodeSincronizar,
  nfseProvedorLabel,
  nfseSyncEndpoint,
} from './nfse-helpers';

describe('regras de NFS-e na loja', () => {
  it('só cancela e sincroniza o que o status permite', () => {
    expect(nfsePodeCancelar('emitida')).toBe(true);
    expect(nfsePodeCancelar('erro')).toBe(false);
    expect(nfsePodeExcluirLoja('pendente')).toBe(true);
    expect(nfsePodeExcluirLoja('emitida')).toBe(false);
    expect(nfsePodeExcluirLoja('cancelada')).toBe(false);
    expect(nfsePodeSincronizar('erro')).toBe(true);
    expect(nfsePodeSincronizar('cancelada', { provedor: 'issnet' })).toBe(true);
    expect(nfsePodeSincronizar('cancelada', { provedor: 'asaas' })).toBe(false);
  });

  it('escolhe o endpoint e o rótulo do provedor', () => {
    expect(nfseSyncEndpoint({ provedor: 'issnet' })).toBe('sincronizar-issnet');
    expect(nfseSyncEndpoint({ provedor: 'asaas' })).toBe('sincronizar-asaas');
    expect(nfseSyncEndpoint({ provedor: '' })).toBeNull();
    expect(nfseProvedorLabel('nacional')).toContain('Nacional');
    expect(montarMotivoCancelamento('2', '  ')).toBeTruthy();
    expect(montarMotivoCancelamento('9', 'Texto livre')).toBe('Texto livre');
  });

  it('filtra por número, nome ou documento', () => {
    const notas = [
      { numero_nf: '55', tomador_nome: 'Ana', tomador_cpf_cnpj: '123' },
      { numero_nf: '56', tomador_nome: 'Bruno', tomador_cpf_cnpj: '456' },
    ];
    expect(filtrarNfsesPorBusca(notas, '  ')).toHaveLength(2);
    expect(filtrarNfsesPorBusca(notas, 'bru')).toEqual([notas[1]]);
    expect(filtrarNfsesPorBusca(notas, '123')).toEqual([notas[0]]);
  });
});
