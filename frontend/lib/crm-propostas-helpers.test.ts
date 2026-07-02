import { describe, expect, it } from 'vitest';
import { propostaConfirmCopy, propostaOcultaColunaAssinatura } from './crm-propostas-helpers';

describe('crm-propostas-helpers', () => {
  it('propostaOcultaColunaAssinatura em cancelada, pedido ou assinatura concluída', () => {
    expect(propostaOcultaColunaAssinatura({ status: 'cancelada' })).toBe(true);
    expect(propostaOcultaColunaAssinatura({ status: 'pedido' })).toBe(true);
    expect(
      propostaOcultaColunaAssinatura({ status: 'enviada', status_assinatura: 'concluido' }),
    ).toBe(true);
    expect(
      propostaOcultaColunaAssinatura({ status: 'enviada', status_assinatura: 'aguardando_cliente' }),
    ).toBe(false);
  });

  it('propostaConfirmCopy retorna textos de confirmação', () => {
    const assinada = propostaConfirmCopy({
      type: 'marcar_assinado',
      id: 1,
      titulo: 'Proposta A',
    });
    expect(assinada?.confirmLabel).toBe('Marcar assinada');
    expect(assinada?.message).toContain('Proposta A');

    const pedido = propostaConfirmCopy({
      type: 'confirmar_pedido',
      id: 2,
      titulo: 'Proposta B',
    });
    expect(pedido?.confirmLabel).toBe('Confirmar pedido');
    expect(propostaConfirmCopy(null)).toBeNull();
  });
});
