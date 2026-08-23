import { describe, expect, it } from 'vitest';
import { RECURSOS_MENU, RELATORIOS_MENU } from '@/lib/clinica-geral-types';
import {
  configuracoesPathForTipo,
  homePathForTipo,
  isTipoClinicaBeleza,
  isTipoClinicaGeral,
} from '@/lib/loja-tipo';

describe('isTipoClinicaGeral', () => {
  it('reconhece Clínica Geral e consultório médico', () => {
    expect(isTipoClinicaGeral('Clínica Geral')).toBe(true);
    expect(isTipoClinicaGeral('Consultorio Medico')).toBe(true);
    expect(isTipoClinicaGeral('Clinica Médica')).toBe(true);
  });

  it('não confunde com Clínica da Beleza nem Radiologia', () => {
    expect(isTipoClinicaGeral('Clínica da Beleza')).toBe(false);
    expect(isTipoClinicaGeral('Clínica de Estética')).toBe(false);
    expect(isTipoClinicaGeral('Radiologia')).toBe(false);
    expect(isTipoClinicaBeleza('Clínica Geral')).toBe(false);
    expect(isTipoClinicaBeleza('Clínica da Beleza')).toBe(true);
  });

  it('expõe as opções de relatórios da agenda', () => {
    expect(RELATORIOS_MENU.map((r) => r.tipo)).toEqual([
      'atendimentos',
      'indicacao',
      'financeiro',
      'status',
      'outros',
    ]);
  });

  it('não mistura recursos com relatórios', () => {
    const recursos = RECURSOS_MENU.map((r) => r.label);
    const relatorios = RELATORIOS_MENU.map((r) => r.label);
    expect(recursos).toEqual(['faturamento', 'lotes TISS']);
    expect(recursos.some((label) => relatorios.includes(label))).toBe(false);
  });

  it('manda o app para a agenda', () => {
    expect(homePathForTipo('clinicageral', 'Clínica Geral')).toBe(
      '/loja/clinicageral/clinica-geral/agenda',
    );
  });

  it('manda configurações para o hub do consultório', () => {
    expect(configuracoesPathForTipo('clinicageral', 'Clínica Geral')).toBe(
      '/loja/clinicageral/clinica-geral/configuracoes',
    );
  });
});
