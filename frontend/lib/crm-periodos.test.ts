import { describe, expect, it } from 'vitest';
import {
  CRM_PERIODO_FINANCEIRO,
  CRM_PERIODO_PADRAO,
  CRM_PIPELINE_PERIODO_PADRAO,
  crmDatasPeriodo,
  crmLabelsPeriodo,
} from './crm-periodos';

describe('CRM períodos', () => {
  it('listas incluem personalizado', () => {
    expect(CRM_PERIODO_PADRAO.some((p) => p.value === 'personalizado')).toBe(true);
    expect(CRM_PERIODO_FINANCEIRO.some((p) => p.value === 'personalizado')).toBe(true);
  });

  it('crmLabelsPeriodo usa fallback mes_atual', () => {
    const labels = crmLabelsPeriodo('periodo_desconhecido');
    expect(labels.receita).toBe('Receita do mês');
  });

  it('crmLabelsPeriodo retorna labels do trimestre', () => {
    const labels = crmLabelsPeriodo('trimestre_atual');
    expect(labels.comissaoSub).toContain('trimestre');
  });

  it('crmDatasPeriodo mes_atual cobre o mês corrente', () => {
    const ref = new Date(2026, 6, 6); // 06/07/2026
    const range = crmDatasPeriodo('mes_atual', ref);
    expect(range).toEqual({ dataInicio: '2026-07-01', dataFim: '2026-07-31' });
  });

  it('pipeline período padrão é mes_atual', () => {
    expect(CRM_PIPELINE_PERIODO_PADRAO).toBe('mes_atual');
  });
});
