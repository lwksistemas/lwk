import { describe, expect, it } from 'vitest';
import {
  CRM_PERIODO_FINANCEIRO,
  CRM_PERIODO_PADRAO,
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
});
