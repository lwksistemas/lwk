import { describe, expect, it } from 'vitest';
import {
  COMISSAO_AGREGADO_ID,
  isLancamentoComissaoAgregado,
  prepararLancamentosParaTabela,
} from './crm-financeiro-display';
import type { LancamentoFinanceiro } from './crm-financeiro-types';

const base: LancamentoFinanceiro = {
  id: 1,
  vendedor: 1,
  vendedor_nome: 'João',
  grupo: 1,
  grupo_nome: 'Comissão de vendas',
  tipo: 'receita',
  tipo_display: 'Receita',
  origem: 'comissao_venda',
  origem_display: 'Comissão de venda',
  descricao: 'Comissão — Opp 1',
  valor: 375,
  status: 'pendente',
  status_display: 'Pendente',
  data_vencimento: '2026-06-15',
  data_pagamento: null,
  oportunidade: 1,
  oportunidade_titulo: 'Opp 1',
  observacoes: '',
  editavel: false,
};

describe('prepararLancamentosParaTabela', () => {
  it('agrega comissões pendentes em uma linha total', () => {
    const itens = [
      base,
      { ...base, id: 2, valor: 750, descricao: 'Comissão — Opp 2' },
      { ...base, id: 3, origem: 'manual', descricao: 'Bônus', editavel: true },
    ];
    const out = prepararLancamentosParaTabela(itens);
    expect(out).toHaveLength(2);
    expect(out[0].id).toBe(COMISSAO_AGREGADO_ID.pendente);
    expect(out[0].descricao).toBe('Comissão de vendas');
    expect(out[0].valor).toBe(1125);
    expect(out[1].descricao).toBe('Bônus');
  });

  it('separa pago e pendente em linhas distintas', () => {
    const itens = [
      base,
      { ...base, id: 2, status: 'pago', status_display: 'Pago', valor: 500 },
    ];
    const out = prepararLancamentosParaTabela(itens);
    expect(out).toHaveLength(2);
    expect(out.find((i) => i.id === COMISSAO_AGREGADO_ID.pendente)?.valor).toBe(375);
    expect(out.find((i) => i.id === COMISSAO_AGREGADO_ID.pago)?.valor).toBe(500);
  });

  it('identifica linha agregada', () => {
    expect(isLancamentoComissaoAgregado({ ...base, id: COMISSAO_AGREGADO_ID.pendente })).toBe(true);
    expect(isLancamentoComissaoAgregado(base)).toBe(false);
  });
});
