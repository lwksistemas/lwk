import { describe, expect, it } from 'vitest';

import { nomeCanonicoAssinatura, nomesParaAssinatura } from './crm-assinatura-vendedor';

describe('nomesParaAssinatura', () => {
  it('lista os vendedores cadastrados e mantém o nome que já veio da oportunidade', () => {
    expect(
      nomesParaAssinatura(
        [{ nome: 'ANA' }, { nome: '  ' }, { nome: 'BRUNO' }, { nome: 'ANA' }],
        'CARLA',
      ),
    ).toEqual(['ANA', 'BRUNO', 'CARLA']);
  });

  it('não repete o vendedor quando a oportunidade traz outra grafia', () => {
    expect(
      nomesParaAssinatura(
        [{ nome: 'FELIPE COSTA FELIX' }, { nome: 'LUIZ HENRIQUE FELIX' }],
        'Luiz Henrique Felix',
      ),
    ).toEqual(['FELIPE COSTA FELIX', 'LUIZ HENRIQUE FELIX']);
    expect(
      nomeCanonicoAssinatura([{ nome: 'LUIZ HENRIQUE FELIX' }], 'Luiz Henrique Felix'),
    ).toBe('LUIZ HENRIQUE FELIX');
  });
});