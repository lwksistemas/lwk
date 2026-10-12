import { describe, expect, it } from 'vitest';
import { themeLabelForTipo } from '@/lib/loja-theme';
import {
  configuracoesPathForTipo,
  homePathForTipo,
  isTipoClinicaBeleza,
  isTipoCRMVendas,
} from '@/lib/loja-tipo';

describe('tipos em produção', () => {
  it('reconhece Clínica da Beleza e a estética unificada', () => {
    expect(isTipoClinicaBeleza('Clínica da Beleza')).toBe(true);
    expect(isTipoClinicaBeleza('Clínica de Estética')).toBe(true);
    expect(themeLabelForTipo('Clínica da Beleza')).toBe('Clínica da Beleza');
  });

  it('abre a clínica no dashboard e o CRM na home de vendas', () => {
    expect(homePathForTipo('clinicaharmonis', 'Clínica da Beleza')).toBe(
      '/loja/clinicaharmonis/dashboard',
    );
    expect(isTipoCRMVendas('CRM Vendas')).toBe(true);
    expect(homePathForTipo('felix', 'CRM Vendas')).toBe('/loja/felix/crm-vendas');
  });

  it('manda as configurações para o app dono', () => {
    expect(configuracoesPathForTipo('clinicaharmonis', 'Clínica da Beleza')).toBe(
      '/loja/clinicaharmonis/clinica-beleza/configuracoes',
    );
    expect(configuracoesPathForTipo('felix', 'CRM Vendas')).toBe(
      '/loja/felix/crm-vendas/configuracoes',
    );
  });
});
