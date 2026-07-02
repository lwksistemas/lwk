import { beforeEach, describe, expect, it, vi } from 'vitest';
import {
  deveConfirmarReenvioAssinatura,
  executarReenvioAssinatura,
  mensagemErroReenvioAssinatura,
  textoConfirmacaoReenvioAssinatura,
} from './crm-reenviar-assinatura';

const postMock = vi.fn();

vi.mock('@/lib/api-client', () => ({
  default: {
    post: (...args: unknown[]) => postMock(...args),
  },
}));

describe('crm-reenviar-assinatura', () => {
  beforeEach(() => {
    postMock.mockReset();
  });

  it('deveConfirmarReenvioAssinatura só em status pendentes', () => {
    expect(deveConfirmarReenvioAssinatura('aguardando_cliente')).toBe(true);
    expect(deveConfirmarReenvioAssinatura('aguardando_vendedor')).toBe(true);
    expect(deveConfirmarReenvioAssinatura('concluido')).toBe(false);
    expect(deveConfirmarReenvioAssinatura(undefined)).toBe(false);
  });

  it('textoConfirmacaoReenvioAssinatura diferencia cliente e vendedor', () => {
    const cliente = textoConfirmacaoReenvioAssinatura('proposta', 'aguardando_cliente');
    expect(cliente).toContain('cliente');
    const vendedor = textoConfirmacaoReenvioAssinatura('contrato', 'aguardando_vendedor');
    expect(vendedor).toContain('vendedor');
    expect(vendedor).toContain('contrato');
  });

  it('executarReenvioAssinatura chama endpoint correto', async () => {
    postMock.mockResolvedValue({ data: { message: 'Enviado' } });
    const msg = await executarReenvioAssinatura('proposta', 42);
    expect(postMock).toHaveBeenCalledWith('/crm-vendas/propostas/42/reenviar_para_assinatura/');
    expect(msg).toBe('Enviado');
  });

  it('mensagemErroReenvioAssinatura extrai detail da API', () => {
    const msg = mensagemErroReenvioAssinatura({
      response: { data: { detail: 'Sem permissão.' } },
    });
    expect(msg).toBe('Sem permissão.');
  });
});
