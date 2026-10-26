import { describe, expect, it } from 'vitest';

import { notificacaoMostraNoPainel } from './crm-header';

describe('notificacaoMostraNoPainel', () => {
  it('esconde o aviso que traz o link de assinatura', () => {
    const mensagem =
      'LUIZ HENRIQUE FELIX: o cliente já assinou. Finalize com sua assinatura: https://lwksistemas.com.br/assinar/token';
    expect(notificacaoMostraNoPainel(mensagem)).toBe(false);
  });

  it('mantém o aviso curto sem link', () => {
    expect(notificacaoMostraNoPainel('LUIZ HENRIQUE FELIX foi assinada por ambas as partes.')).toBe(true);
    expect(notificacaoMostraNoPainel('O cliente já assinou.')).toBe(true);
  });
});
