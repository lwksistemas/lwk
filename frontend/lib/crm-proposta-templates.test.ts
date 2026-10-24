import { describe, expect, it } from 'vitest';
import { avisoTemplatesDaPrestadora } from './crm-proposta-templates';

describe('templates da prestadora na proposta', () => {
  it('pede a oportunidade antes de listar templates', () => {
    expect(avisoTemplatesDaPrestadora({
      temOportunidade: false,
      prestadoraId: null,
      prestadoraNome: '',
      quantidade: 0,
    })).toBe('Escolha a oportunidade para ver os templates da prestadora.');
  });

  it('avisa quando a prestadora ainda não tem template', () => {
    expect(avisoTemplatesDaPrestadora({
      temOportunidade: true,
      prestadoraId: 9,
      prestadoraNome: 'ULTRASIS INFORMATICA LTDA',
      quantidade: 0,
    })).toBe('ULTRASIS INFORMATICA LTDA ainda não tem templates de proposta.');
  });

  it('some o aviso quando a prestadora tem template', () => {
    expect(avisoTemplatesDaPrestadora({
      temOportunidade: true,
      prestadoraId: 9,
      prestadoraNome: 'ULTRASIS INFORMATICA LTDA',
      quantidade: 2,
    })).toBe('');
  });
});
