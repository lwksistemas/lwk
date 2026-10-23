import { describe, expect, it } from 'vitest';

import { nomesParaAssinatura } from './crm-assinatura-vendedor';

describe('nomesParaAssinatura', () => {
  it('lista os vendedores cadastrados e mantém o nome que já veio da oportunidade', () => {
    expect(
      nomesParaAssinatura(
        [{ nome: 'ANA' }, { nome: '  ' }, { nome: 'BRUNO' }, { nome: 'ANA' }],
        'CARLA',
      ),
    ).toEqual(['ANA', 'BRUNO', 'CARLA']);
  });
});