import { describe, expect, it } from 'vitest';
import { CLINICA_BELEZA_NAV_ITEMS } from '@/components/clinica-beleza/clinica-beleza-nav';
import { ROTAS_CLINICA_E2E, ROTAS_RELATORIOS_CLINICA } from '@/lib/clinica-beleza-rotas';

describe('rotas de teste da clínica', () => {
  it('cobre cada caminho do menu', () => {
    const caminhos = CLINICA_BELEZA_NAV_ITEMS.flatMap((item) => {
      const lista: string[] = [];
      if (item.path) lista.push(item.path.split('?')[0]);
      for (const filho of item.children ?? []) lista.push(filho.path.split('?')[0]);
      return lista;
    });
    for (const caminho of caminhos) {
      expect(ROTAS_CLINICA_E2E, caminho).toContain(caminho);
    }
  });

  it('cobre os relatórios do hub', () => {
    for (const rota of ROTAS_RELATORIOS_CLINICA) {
      expect(ROTAS_CLINICA_E2E).toContain(rota);
    }
  });

  it('não repete rota', () => {
    expect(new Set(ROTAS_CLINICA_E2E).size).toBe(ROTAS_CLINICA_E2E.length);
  });
});
