import { describe, expect, it } from 'vitest';
import { getFinanceiroConfirmCopy } from './crm-financeiro-confirm';
import type { LancamentoFinanceiro } from './crm-financeiro-types';

const lancamento = {
  id: 1,
  descricao: 'Teste lançamento',
} as LancamentoFinanceiro;

describe('crm-financeiro-confirm', () => {
  it('retorna copy para excluir lançamento', () => {
    const copy = getFinanceiroConfirmCopy({ type: 'excluir_lancamento', item: lancamento });
    expect(copy?.title).toBe('Excluir lançamento');
    expect(copy?.variant).toBe('danger');
    expect(copy?.message).toContain('Teste lançamento');
  });

  it('retorna null sem ação', () => {
    expect(getFinanceiroConfirmCopy(null)).toBeNull();
  });
});
