import { describe, expect, it } from 'vitest';
import type { Oportunidade } from '@/components/crm-vendas/PipelineBoard';
import {
  dataReferenciaOportunidade,
  filtrarOportunidadesPipeline,
  oportunidadeNoPeriodo,
} from './crm-pipeline';

function opp(partial: Partial<Oportunidade> & { id: number }): Oportunidade {
  return {
    titulo: 'Teste',
    etapa: 'prospecting',
    valor: 0,
    ...partial,
  } as Oportunidade;
}

describe('oportunidadeNoPeriodo', () => {
  it('sem filtro de datas inclui tudo', () => {
    const op = opp({ id: 1, created_at: '2026-01-15T10:00:00Z' });
    expect(oportunidadeNoPeriodo(op, '', '')).toBe(true);
  });

  it('closed_won usa data_fechamento_ganho', () => {
    const op = opp({
      id: 2,
      etapa: 'closed_won',
      data_fechamento_ganho: '2026-06-10',
      created_at: '2026-01-01T10:00:00Z',
    });
    expect(oportunidadeNoPeriodo(op, '2026-06-01', '2026-06-30')).toBe(true);
    expect(oportunidadeNoPeriodo(op, '2026-07-01', '2026-07-31')).toBe(false);
  });

  it('closed_lost usa data_fechamento_perdido', () => {
    const op = opp({
      id: 3,
      etapa: 'closed_lost',
      data_fechamento_perdido: '2026-05-20',
    });
    expect(oportunidadeNoPeriodo(op, '2026-05-01', '2026-05-31')).toBe(true);
  });
});

describe('filtrarOportunidadesPipeline', () => {
  const base = [
    opp({ id: 1, etapa: 'prospecting', vendedor: 10, created_at: '2026-06-05T12:00:00Z' }),
    opp({ id: 2, etapa: 'closed_won', vendedor: 20, data_fechamento_ganho: '2026-06-15' }),
  ];

  it('filtra por etapa', () => {
    const out = filtrarOportunidadesPipeline(base, {
      etapa: 'closed_won',
      dataInicio: '',
      dataFim: '',
    });
    expect(out).toHaveLength(1);
    expect(out[0].id).toBe(2);
  });

  it('filtra por vendedor', () => {
    const out = filtrarOportunidadesPipeline(base, {
      vendedor: '10',
      dataInicio: '',
      dataFim: '',
    });
    expect(out).toHaveLength(1);
    expect(out[0].id).toBe(1);
  });
});

describe('dataReferenciaOportunidade', () => {
  it('ganho prioriza data_fechamento_ganho', () => {
    const op = opp({
      id: 4,
      etapa: 'closed_won',
      data_fechamento_ganho: '2026-06-12T15:00:00Z',
      created_at: '2026-01-01T10:00:00Z',
    });
    expect(dataReferenciaOportunidade(op)).toBe('2026-06-12');
  });
});
